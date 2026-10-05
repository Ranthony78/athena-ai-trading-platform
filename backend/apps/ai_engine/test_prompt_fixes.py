from django.test import SimpleTestCase

from apps.ai_engine.services.prompt_service import PromptService


def _context(**extra):
    return {
        "analysis_mode": "LIVE",
        "latest_candle": {"time": "2026-10-05 15:15 IST", "close": 1.0},
        "breadth": {
            "advances": 9,
            "declines": 3,
            "unchanged": 0,
            "sample_size": 12,
            "of_total": 12,
            "low_confidence": False,
        },
        "rule_evidence": {
            "version": "x",
            "option_buying_audit": {
                "filters": [{"key": "A", "status": "INVALID_UNITS"}]
            },
        },
        **extra,
    }


class PromptFixTests(SimpleTestCase):
    def test_breadth_heading_follows_the_index(self):
        bank = PromptService._format_market_prompt("BANKNIFTY", "15m", _context())
        self.assertIn("## 4. Market Breadth (Bank Nifty)", bank)
        self.assertIn("12/12 Bank Nifty constituents", bank)
        nifty = PromptService._format_market_prompt("NIFTY", "15m", _context())
        self.assertIn("## 4. Market Breadth (Nifty 50)", nifty)

    def test_old_option_buying_audit_is_not_sent(self):
        text = PromptService._format_market_prompt("NIFTY", "15m", _context())
        self.assertNotIn("option_buying_audit", text)
        self.assertNotIn("INVALID_UNITS", text)
        self.assertNotIn("option_buying_audit", PromptService.CONTRACT)
        self.assertIn("filter engine", PromptService.CONTRACT)

    def test_header_time_is_labelled_ist(self):
        text = PromptService._format_market_prompt("NIFTY", "15m", _context())
        self.assertIn("**Latest stored candle:** 2026-10-05 15:15 IST", text)
