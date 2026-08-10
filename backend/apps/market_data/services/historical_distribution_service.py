"""
backend/apps/market_data/services/historical_distribution_service.py

New file.

Computes real empirical statistics from stored daily candles — gap
frequency and intraday range percentiles — so the AI analysis prompt can
reason over actual historical base rates instead of the model inventing a
probability from qualitative judgment alone.

Deliberately narrow scope for this first pass: index-level daily OHLCV
only (Nifty/Bank Nifty), which is the data Athena already stores via
CandleService. Per-strike option-expiry statistics (e.g. "OTM by N points
expired worthless X% of the time") need historical *options* candle data
across many past expiries, which is a separate, larger data requirement —
not attempted here until that's confirmed to exist.
"""

from decimal import Decimal
from statistics import median

from ..repositories.candle_repository import CandleRepository


class HistoricalDistributionService:
    """
    Read-only statistical service. Never fabricates data — if there isn't
    enough history to compute a stat meaningfully, it says so explicitly
    (sample_size + a low-confidence flag) rather than returning a number
    that looks authoritative but isn't.
    """

    MIN_SAMPLE_SIZE = 30  # below this, treat the stat as unreliable

    @classmethod
    def _daily_candles(cls, symbol: str, lookback: int = 1260):
        """
        ~1260 trading days ≈ 5 years. Pulled via the existing repository
        method rather than a raw query, per Athena's layering rules.
        """
        qs = CandleRepository.get_by_symbol_and_timeframe(
            symbol=symbol,
            timeframe="1d",
            limit=lookback,
        )
        # Repository returns newest-first (see Candle.Meta.ordering);
        # gap/percentile math wants chronological order.
        return list(reversed(list(qs)))

    @classmethod
    def gap_stats(cls, symbol: str) -> dict:
        """
        Classifies each day's open vs. the prior day's close into
        normal / mild / large / extreme gap, up or down, matching the
        thresholds discussed for Athena's gap-analysis prompt step.
        """
        candles = cls._daily_candles(symbol)
        if len(candles) < 2:
            return cls._insufficient_data(symbol, "gap_stats", len(candles))

        buckets = {
            "gap_up_normal": 0, "gap_up_mild": 0, "gap_up_large": 0, "gap_up_extreme": 0,
            "gap_down_normal": 0, "gap_down_mild": 0, "gap_down_large": 0, "gap_down_extreme": 0,
        }
        total = 0

        for prev, curr in zip(candles, candles[1:]):
            prev_close = prev.close
            today_open = curr.open
            if not prev_close:
                continue

            gap_pct = float((today_open - prev_close) / prev_close * 100)
            direction = "up" if gap_pct >= 0 else "down"
            magnitude = abs(gap_pct)

            if magnitude <= 0.3:
                size = "normal"
            elif magnitude <= 0.8:
                size = "mild"
            elif magnitude <= 1.5:
                size = "large"
            else:
                size = "extreme"

            buckets[f"gap_{direction}_{size}"] += 1
            total += 1

        if total < cls.MIN_SAMPLE_SIZE:
            return cls._insufficient_data(symbol, "gap_stats", total)

        return {
            "symbol": symbol,
            "sample_size": total,
            "low_confidence": total < 100,
            "distribution_pct": {
                k: round(v / total * 100, 1) for k, v in buckets.items()
            },
        }

    @classmethod
    def intraday_range_stats(cls, symbol: str) -> dict:
        """
        Percentile distribution of daily point range (high - low), and of
        upside/downside move from the day's open. Useful for sanity-checking
        an "expected move" figure against what's actually happened.
        """
        candles = cls._daily_candles(symbol)
        if len(candles) < cls.MIN_SAMPLE_SIZE:
            return cls._insufficient_data(symbol, "intraday_range_stats", len(candles))

        ranges = []
        up_moves = []
        down_moves = []

        for c in candles:
            if c.open is None or c.high is None or c.low is None:
                continue
            ranges.append(float(c.high - c.low))
            up_moves.append(float(c.high - c.open))
            down_moves.append(float(c.open - c.low))

        def percentile(values: list[float], p: float) -> float:
            if not values:
                return 0.0
            s = sorted(values)
            idx = int(round(p / 100 * (len(s) - 1)))
            return round(s[idx], 2)

        return {
            "symbol": symbol,
            "sample_size": len(ranges),
            "low_confidence": len(ranges) < 100,
            "range_points": {
                "median": round(median(ranges), 2) if ranges else 0,
                "p95": percentile(ranges, 95),
                "p5": percentile(ranges, 5),
            },
            "upside_from_open_points": {
                "median": round(median(up_moves), 2) if up_moves else 0,
                "p95": percentile(up_moves, 95),
            },
            "downside_from_open_points": {
                "median": round(median(down_moves), 2) if down_moves else 0,
                "p95": percentile(down_moves, 95),
            },
        }

    @classmethod
    def close_direction_given_gap(cls, symbol: str, gap_bucket: str) -> dict:
        """
        Real conditional statistic: for historical days that opened with
        the SAME gap classification as today (e.g. "gap_down_mild"), what
        fraction closed up / down / roughly flat relative to their own
        open? This is a genuinely different question from gap_stats
        (which only measures how often that gap size occurs at all) —
        this answers what Probability Assessment actually needs: given
        today's gap type, what's the historical base rate for how the
        rest of the day plays out.

        "Flat" is defined as |close - open| within 0.15% of open — a
        documented threshold choice, not a fabricated statistic.

        gap_bucket must be one of the 8 keys gap_stats() produces, e.g.
        "gap_down_mild", "gap_up_normal".
        """
        candles = cls._daily_candles(symbol)
        if len(candles) < 2:
            return cls._insufficient_data(symbol, "close_direction_given_gap", len(candles))

        FLAT_THRESHOLD_PCT = 0.15
        up = down = flat = 0

        for prev, curr in zip(candles, candles[1:]):
            prev_close = prev.close
            today_open = curr.open
            today_close = curr.close
            if not prev_close or not today_open:
                continue

            gap_pct = float((today_open - prev_close) / prev_close * 100)
            direction = "up" if gap_pct >= 0 else "down"
            magnitude = abs(gap_pct)

            if magnitude <= 0.3:
                size = "normal"
            elif magnitude <= 0.8:
                size = "mild"
            elif magnitude <= 1.5:
                size = "large"
            else:
                size = "extreme"

            this_bucket = f"gap_{direction}_{size}"
            if this_bucket != gap_bucket:
                continue

            move_from_open_pct = float((today_close - today_open) / today_open * 100)
            if abs(move_from_open_pct) <= FLAT_THRESHOLD_PCT:
                flat += 1
            elif move_from_open_pct > 0:
                up += 1
            else:
                down += 1

        total = up + down + flat
        if total < 10:  # lower bar than MIN_SAMPLE_SIZE — this slices
                         # the data 8 ways, so 30+ per bucket is unrealistic
                         # at 5 years of history; 10 is the honest floor
                         # below which this is flagged low-confidence.
            return cls._insufficient_data(symbol, f"close_direction_given_gap[{gap_bucket}]", total)

        return {
            "symbol": symbol,
            "gap_bucket": gap_bucket,
            "sample_size": total,
            "low_confidence": total < 20,
            "up_pct": round(up / total * 100, 1),
            "down_pct": round(down / total * 100, 1),
            "flat_pct": round(flat / total * 100, 1),
            "flat_threshold_pct": FLAT_THRESHOLD_PCT,
        }

    @staticmethod
    def _insufficient_data(symbol: str, stat_name: str, sample_size: int) -> dict:
        return {
            "symbol": symbol,
            "stat": stat_name,
            "sample_size": sample_size,
            "error": (
                f"Not enough stored daily candles ({sample_size}) to compute "
                f"a reliable {stat_name}. Needs backfilled historical data "
                f"before this is trustworthy — do not feed a low-sample "
                f"result into the AI prompt as if it were a stable base rate."
            ),
        }