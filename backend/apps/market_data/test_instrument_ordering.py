from datetime import date

from django.test import TestCase

from .models import Instrument


def make(token, symbol, trading_symbol, expiry=None, strike=None, kind="EQ"):
    return Instrument.objects.create(
        instrument_token=token,
        exchange="NFO" if expiry else "NSE",
        symbol=symbol,
        trading_symbol=trading_symbol,
        instrument_type=kind,
        expiry=expiry,
        strike=strike,
    )


class InstrumentOrderingTests(TestCase):
    """The same order on SQLite and PostgreSQL: empty values first, then ties by trading symbol."""

    def test_underlying_comes_before_its_derivatives(self):
        make(1, "NIFTY", "NIFTY26OCTFUT", date(2026, 10, 27), None, "FUT")
        make(2, "NIFTY", "NIFTY 50", None, None, "IDX")
        make(3, "NIFTY", "NIFTY2610622400CE", date(2026, 10, 6), 22400, "CE")

        names = list(Instrument.objects.values_list("trading_symbol", flat=True))

        self.assertEqual(names, ["NIFTY 50", "NIFTY2610622400CE", "NIFTY26OCTFUT"])

    def test_within_an_expiry_no_strike_comes_before_strikes(self):
        expiry = date(2026, 10, 6)
        make(1, "NIFTY", "B-CE", expiry, 22500, "CE")
        make(2, "NIFTY", "A-FUT", expiry, None, "FUT")
        make(3, "NIFTY", "C-CE", expiry, 22400, "CE")

        names = list(Instrument.objects.values_list("trading_symbol", flat=True))

        self.assertEqual(names, ["A-FUT", "C-CE", "B-CE"])

    def test_exact_ties_are_ordered_by_trading_symbol(self):
        make(1, "GOLDBOND", "SGBOCT27-GB")
        make(2, "GOLDBOND", "SGBJAN27-GB")
        make(3, "GOLDBOND", "SGBAPR27-GB")

        names = list(Instrument.objects.values_list("trading_symbol", flat=True))

        self.assertEqual(names, ["SGBAPR27-GB", "SGBJAN27-GB", "SGBOCT27-GB"])
