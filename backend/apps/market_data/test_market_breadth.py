from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from .services.market_breadth_service import (
    BANKNIFTY_CONSTITUENTS,
    NIFTY50_CONSTITUENTS,
    MarketBreadthService,
)

REPO = "apps.market_data.repositories.instrument_repository.InstrumentRepository"
MARKET = "apps.market_data.services.market_service.MarketService"


def run(index, changes, resolvable=None):
    """Run get_breadth with canned change_percent values."""
    quotes = [{"change_percent": c} if c is not None else None for c in changes]
    fake = SimpleNamespace(quotes=lambda symbols: quotes)
    with (
        patch(f"{REPO}.get_by_symbol", side_effect=lambda s: object()),
        patch(MARKET, return_value=fake),
    ):
        return MarketBreadthService.get_breadth(object(), index=index)


class BreadthTests(SimpleTestCase):

    def test_lists_have_no_duplicates(self):
        self.assertEqual(len(set(BANKNIFTY_CONSTITUENTS)), 12)
        self.assertEqual(len(set(NIFTY50_CONSTITUENTS)), 50)

    def test_banknifty_counts_and_total(self):
        result = run("BANKNIFTY", [1, 1, 1, -1, -1, 0, 2, 2, 2, 2, -3, 1])
        self.assertEqual(
            (result["advances"], result["declines"], result["unchanged"]), (8, 3, 1)
        )
        self.assertEqual(result["of_total"], 12)
        self.assertEqual(result["index"], "BANKNIFTY")
        self.assertFalse(result["low_confidence"])

    def test_missing_quotes_flag_low_confidence(self):
        result = run("BANKNIFTY", [1, -1, None, None, None, None, None, None, None])
        self.assertEqual(result["sample_size"], 2)
        self.assertTrue(result["low_confidence"])

    def test_default_index_is_nifty(self):
        self.assertEqual(run("NIFTY", [1] * 50)["of_total"], 50)

    def test_unknown_index_or_no_user_is_none(self):
        self.assertIsNone(MarketBreadthService.get_breadth(object(), index="SENSEX"))
        self.assertIsNone(MarketBreadthService.get_breadth(None, index="BANKNIFTY"))
