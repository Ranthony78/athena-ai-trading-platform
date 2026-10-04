from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase, TestCase

from .services import time_block_service as tb

IST = ZoneInfo("Asia/Kolkata")
FIRST = "09:15 – 10:30"
LAST = "13:30 – 15:30"


def day_candles(day, start_price, blocks):
    """
    Build a session. `blocks` maps a window name to (net_points, range_points);
    candles walk linearly from the window open to its close with a symmetric
    wick sized so the window range is as requested.
    """
    candles = []
    price = start_price
    for name, start, end in tb.WINDOWS:
        net, rng = blocks.get(name, (0, 2))
        count = (tb._minutes(end) - tb._minutes(start)) // tb.CANDLE_MINUTES
        step = net / count
        wick = max((rng - abs(net)) / 2, 0)
        for i in range(count):
            open_ = price
            close = price + step
            minute = tb._minutes(start) + i * tb.CANDLE_MINUTES
            at = datetime(
                day.year, day.month, day.day, minute // 60, minute % 60, tzinfo=IST
            )
            candles.append(
                {
                    "time": at,
                    "open": open_,
                    "close": close,
                    "high": max(open_, close)
                    + (wick if i == 0 or i == count - 1 else 0),
                    "low": min(open_, close)
                    - (wick if i == 0 or i == count - 1 else 0),
                }
            )
            price = close
    return candles


def sessions(n, blocks, start_price=1000.0, first_day=date(2026, 9, 1)):
    out = []
    for i in range(n):
        out += day_candles(first_day + timedelta(days=i), start_price, blocks)
    return out


def by_name(results):
    return {r["window"]: r for r in results}


class AnalyseTests(SimpleTestCase):

    def test_consistent_up_window_leans_up_and_is_directional(self):
        # First window rises 10 points on a 10-point range every day.
        data = sessions(12, {FIRST: (10, 10)})
        first = by_name(tb.analyse(data))[FIRST]

        self.assertEqual(first["sessions"], 12)
        self.assertEqual(first["bias"], "Leans up")
        self.assertEqual(first["up_share_pct"], 100.0)
        self.assertEqual(first["trend_strength"], "Strong")
        self.assertFalse(first["low_confidence"])
        self.assertAlmostEqual(first["avg_range_pct"], 1.0, delta=0.05)

    def test_choppy_window_has_no_lean_and_weak_trend(self):
        # Zero net move on a wide range.
        data = sessions(12, {FIRST: (0, 12)})
        first = by_name(tb.analyse(data))[FIRST]

        self.assertEqual(first["bias"], "No consistent lean")
        self.assertEqual(first["trend_strength"], "Weak")

    def test_down_window_leans_down(self):
        data = sessions(12, {LAST: (-8, 8)})
        self.assertEqual(by_name(tb.analyse(data))[LAST]["bias"], "Leans down")

    def test_volatility_is_relative_across_windows(self):
        blocks = {
            "09:15 – 10:30": (0, 30),
            "10:30 – 12:00": (0, 10),
            "12:00 – 13:30": (0, 4),
            "13:30 – 15:30": (0, 12),
        }
        results = by_name(tb.analyse(sessions(12, blocks)))

        self.assertEqual(results["09:15 – 10:30"]["volatility"], "High")
        self.assertEqual(results["12:00 – 13:30"]["volatility"], "Low")
        self.assertEqual(results["10:30 – 12:00"]["volatility"], "Moderate")

    def test_thin_sample_is_flagged_and_too_thin_has_no_labels(self):
        flagged = by_name(tb.analyse(sessions(7, {FIRST: (10, 10)})))[FIRST]
        self.assertTrue(flagged["low_confidence"])
        self.assertEqual(flagged["bias"], "Leans up")

        thin = by_name(tb.analyse(sessions(3, {FIRST: (10, 10)})))[FIRST]
        self.assertEqual(thin["sessions"], 3)
        self.assertIsNone(thin["bias"])
        self.assertIsNone(thin["volatility"])

    def test_incomplete_window_is_not_counted(self):
        data = sessions(12, {FIRST: (10, 10)})

        # Keep only the 09:15 candle of the first window on every day: coverage
        # falls under 80%.
        def in_first_window(candle):
            minute = tb._minutes(candle["time"].astimezone(IST).time())
            return 9 * 60 + 15 <= minute < 10 * 60 + 30

        data = [
            c
            for c in data
            if not in_first_window(c) or (c["time"].hour, c["time"].minute) == (9, 15)
        ]
        self.assertEqual(by_name(tb.analyse(data))[FIRST]["sessions"], 0)

    def test_uses_only_the_most_recent_sessions(self):
        old = sessions(10, {FIRST: (-10, 10)}, first_day=date(2026, 7, 1))
        recent = sessions(20, {FIRST: (10, 10)}, first_day=date(2026, 9, 1))
        first = by_name(tb.analyse(old + recent, sessions=20))[FIRST]

        self.assertEqual(first["sessions"], 20)
        self.assertEqual(first["bias"], "Leans up")

    def test_no_candles_gives_empty_windows(self):
        results = tb.analyse([])
        self.assertEqual(len(results), 4)
        self.assertTrue(all(r["sessions"] == 0 and r["bias"] is None for r in results))


class BuildTests(TestCase):

    def test_reads_stored_15m_candles(self):
        from .models import Candle, Instrument

        instrument = Instrument.objects.create(
            instrument_token=260105,
            exchange="NSE",
            symbol="BANKNIFTY",
            trading_symbol="NIFTY BANK",
            instrument_type="IDX",
        )
        Candle.objects.bulk_create(
            Candle(
                instrument=instrument,
                timeframe="15m",
                candle_time=c["time"],
                open=round(c["open"], 2),
                high=round(c["high"], 2),
                low=round(c["low"], 2),
                close=round(c["close"], 2),
            )
            for c in sessions(8, {FIRST: (10, 10)})
        )

        result = tb.TimeBlockService.build("BANKNIFTY")

        first = by_name(result["blocks"])[FIRST]
        self.assertEqual(first["sessions"], 8)
        self.assertEqual(first["bias"], "Leans up")
        self.assertTrue(first["low_confidence"])
        self.assertEqual(result["through"], "2026-09-08")

    def test_old_data_is_flagged_stale(self):
        from unittest.mock import patch

        self.test_reads_stored_15m_candles()
        with patch("django.utils.timezone.localdate", return_value=date(2026, 9, 12)):
            self.assertFalse(tb.TimeBlockService.build("BANKNIFTY")["stale"])
        with patch("django.utils.timezone.localdate", return_value=date(2026, 10, 20)):
            self.assertTrue(tb.TimeBlockService.build("BANKNIFTY")["stale"])

    def test_unknown_symbol_is_none(self):
        self.assertIsNone(tb.TimeBlockService.build("NOSUCH"))
