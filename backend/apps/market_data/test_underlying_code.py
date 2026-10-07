from django.test import SimpleTestCase

from apps.market_data.repositories.instrument_repository import InstrumentRepository


class UnderlyingCodeTests(SimpleTestCase):
    def test_long_index_names_map_to_contract_codes(self):
        # Options are filed under NIFTY/BANKNIFTY; the index rows carry
        # Zerodha's long names. The 7 Oct 09:30 SELL found no contract
        # because "NIFTY 50" was passed through unchanged.
        code = InstrumentRepository.underlying_code
        self.assertEqual(code("NIFTY 50"), "NIFTY")
        self.assertEqual(code("nifty bank"), "BANKNIFTY")
        self.assertEqual(code("NIFTY"), "NIFTY")
        self.assertEqual(code("RELIANCE"), "RELIANCE")
