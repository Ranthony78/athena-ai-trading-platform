"""
backend/apps/market_data/services/historical_distribution_service.py

Computes real empirical statistics from stored candles — daily gap
frequency, intraday range percentiles, and matched-horizon intraday
outcomes — so the AI analysis prompt uses measured base rates rather than
probabilities invented from qualitative judgment alone.

Deliberately narrow scope for this first pass: index-level daily OHLCV
only (Nifty/Bank Nifty), which is the data Athena already stores via
CandleService. Per-strike option-expiry statistics (e.g. "OTM by N points
expired worthless X% of the time") need historical *options* candle data
across many past expiries, which is a separate, larger data requirement —
not attempted here until that's confirmed to exist.
"""

from datetime import timedelta
from statistics import median
from zoneinfo import ZoneInfo

from django.utils import timezone

from ..repositories.candle_repository import CandleRepository


class HistoricalDistributionService:
    """
    Read-only statistical service. Never fabricates data — if there isn't
    enough history to compute a stat meaningfully, it says so explicitly
    (sample_size + a low-confidence flag) rather than returning a number
    that looks authoritative but isn't.
    """

    MIN_SAMPLE_SIZE = 30  # below this, treat the stat as unreliable
    INTRADAY_MIN_SAMPLE_SIZE = 30
    INTRADAY_TIME_TOLERANCE_MINUTES = 30

    @classmethod
    def _daily_candles(cls, symbol: str, lookback: int = 1260, exclude_date=None):
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
        candles = list(reversed(list(qs)))
        if exclude_date:
            candles = [
                candle
                for candle in candles
                if timezone.localtime(
                    candle.candle_time, ZoneInfo("Asia/Kolkata")
                ).date()
                != exclude_date
            ]
        return candles

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
            "gap_up_normal": 0,
            "gap_up_mild": 0,
            "gap_up_large": 0,
            "gap_up_extreme": 0,
            "gap_down_normal": 0,
            "gap_down_mild": 0,
            "gap_down_large": 0,
            "gap_down_extreme": 0,
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
    def intraday_range_stats(cls, symbol: str, exclude_date=None) -> dict:
        """
        Percentile distribution of daily point range (high - low), and of
        upside/downside move from the day's open. Useful for sanity-checking
        an "expected move" figure against what's actually happened.
        """
        candles = cls._daily_candles(symbol, exclude_date=exclude_date)
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
    def close_direction_given_gap(
        cls, symbol: str, gap_bucket: str, exclude_date=None
    ) -> dict:
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
        candles = cls._daily_candles(symbol, exclude_date=exclude_date)
        if len(candles) < 2:
            return cls._insufficient_data(
                symbol, "close_direction_given_gap", len(candles)
            )

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
            return cls._insufficient_data(
                symbol, f"close_direction_given_gap[{gap_bucket}]", total
            )

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

    @classmethod
    def intraday_direction_base_rate(
        cls,
        symbol: str,
        timeframe: str,
        horizon_minutes: int,
        reference_minute: int = None,
        include_completed_today: bool = False,
    ) -> dict:
        """Return an empirical three-way outcome distribution for this horizon.

        One observation is selected per completed trading day, near the same
        time of day as the request (or a supplied reference minute). The look-ahead target remains in
        that same session. Both the sampled price and horizon outcome use
        one-minute candle closes, matching the outcome tracker. The selected
        analysis timeframe is recorded for audit but is not used to stretch
        the probability horizon.
        """
        from collections import defaultdict

        from ..repositories.candle_repository import CandleRepository

        # Score the same one-minute close that the outcome tracker later
        # uses. Coarser bars cannot support a shorter forecast horizon, and
        # silently substituting their close would make calibration misleading.
        if (
            timeframe not in {"1m", "3m", "5m", "15m", "30m", "1h"}
            or horizon_minutes <= 0
        ):
            return cls._insufficient_data(symbol, "intraday_direction_base_rate", 0)

        candles = CandleRepository.get_by_symbol_and_timeframe(
            symbol=symbol,
            timeframe="1m",
            limit=100000,
            source="ZERODHA",
        )
        now = timezone.localtime()
        today = now.date()
        # Only completed bars sufficiently before now may be predictors.
        cutoff = now - timedelta(minutes=horizon_minutes + 1)
        days = defaultdict(list)
        candle_rows = list(reversed(list(candles)))
        today_rows = [
            (timezone.localtime(row.candle_time), row)
            for row in candle_rows
            if timezone.localtime(row.candle_time).date() == today
        ]
        today_is_complete = (
            include_completed_today
            and now.hour * 60 + now.minute >= 15 * 60 + 30
            and today_rows
            and max(stamp.hour * 60 + stamp.minute for stamp, _ in today_rows)
            >= 15 * 60 + 25
        )
        for candle in candle_rows:
            candle_time = timezone.localtime(candle.candle_time)
            is_today = candle_time.date() == today
            if candle_time.date() > today or (is_today and not today_is_complete):
                continue
            if is_today and candle_time.hour * 60 + candle_time.minute > 15 * 60 + 30:
                continue
            if not is_today and reference_minute is None and candle_time >= cutoff:
                continue
            days[candle_time.date()].append((candle_time, candle))

        current_minute = (
            reference_minute
            if reference_minute is not None
            else now.hour * 60 + now.minute
        )
        outcomes = {"up": 0, "down": 0, "sideways": 0}
        sample_size = 0
        tolerance = cls.INTRADAY_TIME_TOLERANCE_MINUTES
        sample_dates = []

        for day_candles in days.values():
            day_candles.sort(key=lambda row: row[0])
            starts = [
                row
                for row in day_candles
                if row[0].hour * 60 + row[0].minute <= current_minute
            ]
            if not starts:
                continue
            start_time, start = min(
                starts,
                key=lambda row: abs(
                    (row[0].hour * 60 + row[0].minute) - current_minute
                ),
            )
            if (
                abs((start_time.hour * 60 + start_time.minute) - current_minute)
                > tolerance
            ):
                continue

            target_time = start_time + timedelta(minutes=horizon_minutes)
            end_row = next((row for row in day_candles if row[0] >= target_time), None)
            if not end_row or (end_row[0] - target_time) >= timedelta(minutes=1):
                continue
            start_price, end_price = float(start.close), float(end_row[1].close)
            if start_price <= 0:
                continue
            change_pct = (end_price - start_price) / start_price * 100
            if change_pct > 0.05:
                outcomes["up"] += 1
            elif change_pct < -0.05:
                outcomes["down"] += 1
            else:
                outcomes["sideways"] += 1
            sample_size += 1
            sample_dates.append(start_time.date())

        if sample_size < cls.INTRADAY_MIN_SAMPLE_SIZE:
            return cls._insufficient_data(
                symbol, "intraday_direction_base_rate", sample_size
            )

        percentages = {
            key: round(value / sample_size * 100, 1) for key, value in outcomes.items()
        }
        # Keep the displayed split summing to exactly 100 after rounding.
        percentages["sideways"] = round(
            100 - percentages["up"] - percentages["down"], 1
        )
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "outcome_candle_timeframe": "1m",
            "horizon_minutes": horizon_minutes,
            "reference_minute_ist": reference_minute,
            "time_of_day_tolerance_minutes": tolerance,
            "sideways_band_pct": 0.05,
            "sample_size": sample_size,
            "low_confidence": sample_size < 100,
            "source": "stored completed Zerodha one-minute candles",
            "latest_sample_date": max(sample_dates).isoformat(),
            "upside_pct": percentages["up"],
            "downside_pct": percentages["down"],
            "sideways_pct": percentages["sideways"],
        }

    @staticmethod
    def _insufficient_data(symbol: str, stat_name: str, sample_size: int) -> dict:
        return {
            "symbol": symbol,
            "stat": stat_name,
            "sample_size": sample_size,
            "error": (
                f"Not enough usable stored candle observations ({sample_size}) to compute "
                f"a reliable {stat_name}. Needs more backfilled historical data "
                f"before this is trustworthy — do not feed a low-sample "
                f"result into the AI prompt as if it were a stable base rate."
            ),
        }
