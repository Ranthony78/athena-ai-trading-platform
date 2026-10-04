from django.test import SimpleTestCase

from .services.prompt_service import PromptService


def chain(strikes):
    return [
        {"strike": float(s), "option_type": side, "ltp": 10.0, "oi": 5}
        for s in strikes
        for side in ("CE", "PE")
    ]


class RowsNearAtmTests(SimpleTestCase):

    def test_keeps_five_strikes_each_side_with_only_price_fields(self):
        rows = PromptService._rows_near_atm(chain(range(100, 3100, 100)), 1500.0)

        strikes = sorted({r["strike"] for r in rows})
        self.assertEqual(strikes[0], 1000.0)
        self.assertEqual(strikes[-1], 2000.0)
        self.assertEqual(len(strikes), 11)
        self.assertEqual(set(rows[0]), {"strike", "option_type", "ltp"})

    def test_near_the_edge_keeps_what_exists(self):
        rows = PromptService._rows_near_atm(chain(range(100, 500, 100)), 100.0)
        self.assertEqual(
            sorted({r["strike"] for r in rows}), [100.0, 200.0, 300.0, 400.0]
        )

    def test_atm_not_in_the_chain_gives_nothing(self):
        self.assertEqual(PromptService._rows_near_atm(chain([100, 200]), 150.0), [])
