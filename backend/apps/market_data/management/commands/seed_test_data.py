import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.market_data.models import Instrument, Candle

# Same illustrative base prices used in the mock market data provider,
# so seeded candles and mock quotes look consistent with each other.
# These are NOT real prices — synthetic test data only.
TEST_INSTRUMENTS = [
    {"symbol": "NIFTY", "trading_symbol": "NIFTY 50", "exchange": "NSE",
     "instrument_token": 900001, "base_price": 24500.00},
    {"symbol": "BANKNIFTY", "trading_symbol": "NIFTY BANK", "exchange": "NSE",
     "instrument_token": 900002, "base_price": 52000.00},
    {"symbol": "FINNIFTY", "trading_symbol": "NIFTY FIN SERVICE", "exchange": "NSE",
     "instrument_token": 900003, "base_price": 23500.00},
    {"symbol": "MIDCPNIFTY", "trading_symbol": "NIFTY MID SELECT", "exchange": "NSE",
     "instrument_token": 900004, "base_price": 13000.00},
    {"symbol": "SENSEX", "trading_symbol": "SENSEX", "exchange": "BSE",
     "instrument_token": 900005, "base_price": 80500.00},
]

CANDLE_COUNT = 100
TIMEFRAME = "15m"


class Command(BaseCommand):
    """
    Seed a small set of core index instruments and synthetic 15m candles
    for local development and testing ONLY.

    This is NOT real market data — it's a random walk seeded from
    illustrative base prices, purely so the AI analysis / indicator
    pipeline has something to compute against during development.

    Usage:
        python manage.py seed_test_data
        python manage.py seed_test_data --clear   # wipe existing seeded data first
    """

    help = "Seed core index instruments + synthetic candles for local dev/testing (NOT real data)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--clear",
            action="store_true",
            default=False,
            help="Delete existing seeded instruments/candles before reseeding.",
        )

    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.WARNING(
            "Seeding SYNTHETIC test data — not real market prices. "
            "Do not use this for anything beyond local pipeline testing."
        ))

        if options["clear"]:
            tokens = [i["instrument_token"] for i in TEST_INSTRUMENTS]
            deleted, _ = Instrument.objects.filter(
                instrument_token__in=tokens
            ).delete()
            self.stdout.write(f"Cleared {deleted} existing seeded records (instruments + candles).")

        for spec in TEST_INSTRUMENTS:
            instrument, created = Instrument.objects.update_or_create(
                instrument_token=spec["instrument_token"],
                defaults={
                    "exchange_token": spec["instrument_token"],
                    "exchange": spec["exchange"],
                    "symbol": spec["symbol"],
                    "trading_symbol": spec["trading_symbol"],
                    "instrument_type": "IDX",
                    "lot_size": 1,
                    "tick_size": Decimal("0.05"),
                    "is_active": True,
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} instrument: {spec['symbol']}")

            self._seed_candles(instrument, spec["base_price"])

        self.stdout.write(self.style.SUCCESS(
            f"\nSeeded {len(TEST_INSTRUMENTS)} instruments with "
            f"{CANDLE_COUNT} synthetic {TIMEFRAME} candles each."
        ))

    def _seed_candles(self, instrument: Instrument, base_price: float) -> None:
        """Generate a synthetic random-walk candle series ending near now."""
        rng = random.Random(instrument.instrument_token)  # deterministic per instrument
        now = timezone.now()

        # Work backwards from now in 15-minute steps
        price = base_price
        candles = []

        for i in range(CANDLE_COUNT, 0, -1):
            candle_time = now - timedelta(minutes=15 * i)

            drift = rng.uniform(-0.004, 0.004)
            open_price = price
            close_price = round(price * (1 + drift), 2)
            high_price = round(max(open_price, close_price) * (1 + rng.uniform(0, 0.002)), 2)
            low_price = round(min(open_price, close_price) * (1 - rng.uniform(0, 0.002)), 2)
            volume = rng.randint(500000, 2000000)

            candles.append(Candle(
                instrument=instrument,
                timeframe=TIMEFRAME,
                candle_time=candle_time,
                open=Decimal(str(open_price)),
                high=Decimal(str(high_price)),
                low=Decimal(str(low_price)),
                close=Decimal(str(close_price)),
                volume=volume,
            ))

            price = close_price

        # Clear existing seeded candles for this instrument+timeframe, then bulk insert
        Candle.objects.filter(
            instrument=instrument,
            timeframe=TIMEFRAME,
        ).delete()

        Candle.objects.bulk_create(candles, ignore_conflicts=True)
