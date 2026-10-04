from django.test import SimpleTestCase

from .services.session_metrics_service import SessionMetrics
from .services.strike_selection_service import StrikeSelectionService


class PctChangeTests(SimpleTestCase):

    def test_change(self):
        self.assertEqual(SessionMetrics.pct_change(10.0, 11.0), 10.0)

    def test_bad_input_is_none(self):
        for previous, current in ((None, 5), (0, 5), (5, None), ("x", 5), (5, -1)):
            self.assertIsNone(SessionMetrics.pct_change(previous, current))


class GapRetraceTests(SimpleTestCase):

    def test_gap_up_half_filled(self):
        result = SessionMetrics.gap_retrace(100, 102, 101)
        self.assertEqual(result["direction"], "UP")
        self.assertEqual(result["retrace_pct"], 50.0)

    def test_gap_down_partly_filled(self):
        result = SessionMetrics.gap_retrace(100, 98, 98.5)
        self.assertEqual(result["direction"], "DOWN")
        self.assertEqual(result["retrace_pct"], 25.0)

    def test_retrace_is_clamped(self):
        self.assertEqual(SessionMetrics.gap_retrace(100, 102, 99)["retrace_pct"], 100.0)
        self.assertEqual(SessionMetrics.gap_retrace(100, 102, 104)["retrace_pct"], 0.0)

    def test_tiny_gap_is_flat_with_no_retrace(self):
        result = SessionMetrics.gap_retrace(1000, 1000.5, 1001)
        self.assertEqual(result["direction"], "FLAT")
        self.assertIsNone(result["retrace_pct"])

    def test_missing_inputs_are_none(self):
        self.assertIsNone(SessionMetrics.gap_retrace(None, 102, 101))
        self.assertIsNone(SessionMetrics.gap_retrace(100, 0, 101))


class VolumeConfirmationTests(SimpleTestCase):

    @staticmethod
    def bars(spec):
        return [{"open": o, "close": c, "volume": v} for o, c, v in spec]

    def test_buying(self):
        result = SessionMetrics.volume_confirmation(
            self.bars([(1, 2, 100)] * 4 + [(2, 1, 50)])
        )
        self.assertEqual(result["verdict"], "BUYING")
        self.assertEqual(result["up_volume"], 400)
        self.assertEqual(result["down_volume"], 50)

    def test_selling_and_balanced(self):
        selling = self.bars([(2, 1, 100)] * 4 + [(1, 2, 50)])
        self.assertEqual(
            SessionMetrics.volume_confirmation(selling)["verdict"], "SELLING"
        )
        balanced = self.bars([(1, 2, 100)] * 2 + [(2, 1, 70)] * 3)
        self.assertEqual(
            SessionMetrics.volume_confirmation(balanced)["verdict"], "BALANCED"
        )

    def test_too_few_bars_or_no_volume_is_none(self):
        self.assertIsNone(
            SessionMetrics.volume_confirmation(self.bars([(1, 2, 9)] * 3))
        )
        self.assertIsNone(
            SessionMetrics.volume_confirmation(self.bars([(1, 2, 0)] * 6))
        )

    def test_malformed_bar_is_none(self):
        self.assertIsNone(SessionMetrics.volume_confirmation([{"open": 1}] * 6))


def row(option_type, strike, ltp=0, oi=0):
    return {"option_type": option_type, "strike": strike, "ltp": ltp, "oi": oi}


class OptionHelperTests(SimpleTestCase):

    def test_premium_matched_put_picks_closest(self):
        rows = [
            row("PE", 100, 40),
            row("PE", 200, 98),
            row("PE", 300, 160),
            row("CE", 400, 100),
        ]
        match = StrikeSelectionService.premium_matched_put(rows, 100)
        self.assertEqual(match["strike"], 200)
        self.assertEqual(match["premium_gap_pct"], 2.0)

    def test_poor_match_is_none(self):
        rows = [row("PE", 100, 40), row("PE", 300, 160)]
        self.assertIsNone(StrikeSelectionService.premium_matched_put(rows, 100))

    def test_no_priced_puts_or_bad_premium_is_none(self):
        self.assertIsNone(
            StrikeSelectionService.premium_matched_put([row("PE", 1, 0)], 100)
        )
        self.assertIsNone(
            StrikeSelectionService.premium_matched_put([row("PE", 1, 5)], 0)
        )

    def test_oi_walls_split_around_spot(self):
        rows = [
            row("CE", 24000, oi=900),
            row("CE", 24200, oi=500),
            row("CE", 23800, oi=9999),  # below spot: not a call wall
            row("PE", 23800, oi=700),
            row("PE", 23600, oi=300),
            row("PE", 24200, oi=9999),  # above spot: not a put wall
        ]
        walls = StrikeSelectionService.oi_walls(rows, 23900)
        self.assertEqual(walls["call_wall"], {"strike": 24000, "oi": 900})
        self.assertEqual(walls["put_wall"], {"strike": 23800, "oi": 700})

    def test_oi_walls_absent_when_no_oi_or_bad_spot(self):
        empty = {"call_wall": None, "put_wall": None}
        self.assertEqual(
            StrikeSelectionService.oi_walls([row("CE", 24000, oi=0)], 23900), empty
        )
        self.assertEqual(
            StrikeSelectionService.oi_walls([row("CE", 24000, oi=5)], 0), empty
        )
