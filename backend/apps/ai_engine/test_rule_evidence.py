from django.test import SimpleTestCase

from .services.rule_evidence_service import RuleEvidenceService


class DailyMoveComparisonTests(SimpleTestCase):
    def test_option_audit_uses_bid_ask_mid_and_preserves_unknown_filters(self):
        options = {"atm_call": {"best_bid": 99, "best_ask": 101}, "atm_put": {"best_bid": 79, "best_ask": 81}}
        result = RuleEvidenceService._option_buying_audit(options, 40, 15)
        self.assertEqual(result["straddle_mid_points"], 180)
        self.assertEqual(result["straddle_ask_debit_points"], 182)
        self.assertEqual(result["filters"][0]["status"], "INVALID_UNITS")
        self.assertEqual(result["filters"][1]["status"], "REFERENCE_ONLY")
        self.assertIsNone(result["net_expectancy"])
        self.assertIsNone(result["edge_scores"])

    def test_crossed_or_missing_quotes_cannot_create_straddle_reference(self):
        for call in ({"best_bid": 102, "best_ask": 101}, {"best_bid": "NaN", "best_ask": 101}, {}):
            result = RuleEvidenceService._option_buying_audit({"atm_call": call, "atm_put": {"best_bid": 79, "best_ask": 81}}, 40, 15)
            self.assertIsNone(result["straddle_mid_points"])
            self.assertEqual(result["filters"][1]["status"], "UNAVAILABLE")

    def test_daily_blend_preserves_both_inputs(self):
        rows = [{"open": 20000, "close": 20100}] * 15
        result = RuleEvidenceService._daily_move_comparison(200, rows)
        self.assertEqual(result["status"], "available")
        self.assertEqual(result["historical_mean_absolute_open_close_points"], 100)
        self.assertEqual(result["vix_daily_one_sigma_points"], 200)
        self.assertEqual(result["experimental_daily_blend_points"], 150)

    def test_invalid_recent_session_cannot_be_replaced_with_older_data(self):
        rows = [{"open": "NaN", "close": 20100}] + [{"open": 20000, "close": 20100}] * 15
        result = RuleEvidenceService._daily_move_comparison(200, rows)
        self.assertEqual(result["sample_size"], 14)
        self.assertIsNone(result["experimental_daily_blend_points"])

    def test_flat_days_are_valid_but_missing_vix_blocks_blend(self):
        rows = [{"open": 20000, "close": 20000}] * 15
        result = RuleEvidenceService._daily_move_comparison(None, rows)
        self.assertEqual(result["historical_mean_absolute_open_close_points"], 0)
        self.assertIsNone(result["experimental_daily_blend_points"])
