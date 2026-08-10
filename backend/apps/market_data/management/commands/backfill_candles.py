"""
backend/apps/market_data/management/commands/backfill_candles.py

Backfills historical candles for one or more symbols, using the existing
CandleService.fetch_and_store() — no new persistence logic, this drives
it over a real date range with the right authenticated user, chunked to
stay within Kite's real per-request day limits for intraday intervals.

Usage:
    # Backfill 5 years of daily candles for Nifty and Bank Nifty
    python manage.py backfill_candles --symbols NIFTY,BANKNIFTY --years 5

    # 3 months of 5-minute candles, auto-chunked into safe windows
    python manage.py backfill_candles --symbols NIFTY,BANKNIFTY --timeframe 5m --months 3

    # Explicit date range
    python manage.py backfill_candles --symbols NIFTY --from-date 2026-08-01 --to-date 2026-08-09 --timeframe 5m

    # Clean existing candles for this symbol+timeframe before loading fresh data
    python manage.py backfill_candles --symbols NIFTY,BANKNIFTY --timeframe 5m --months 3 --clean

    # Dry run — shows what would be fetched/deleted, no DB writes
    python manage.py backfill_candles --symbols NIFTY --years 5 --dry-run
"""

import logging
from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.market_data.services.candle_service import CandleService
from apps.zerodha.repositories.zerodha_repository import ZerodhaConfigRepository

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Backfill historical candles for one or more symbols from Zerodha"

    # Kite's real per-request day limits vary slightly by source (90 vs
    # 100 days for 5minute across different docs/forum posts as of this
    # writing) — these values are set with a safety margin BELOW the
    # lowest reported figure for each interval, so chunking never risks
    # hitting the real cap regardless of which number is currently
    # accurate. Verify against Kite's live docs if you see truncated
    # results despite chunking.
    CHUNK_DAYS = {
        "1m": 55,
        "3m": 85,
        "5m": 85,
        "10m": 85,
        "15m": 170,
        "30m": 170,
        "1h": 350,
        "1d": 1900,
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--symbols",
            type=str,
            required=True,
            help="Comma-separated symbols, e.g. NIFTY,BANKNIFTY",
        )
        parser.add_argument("--timeframe", type=str, default="1d")
        parser.add_argument("--years", type=int, default=None)
        parser.add_argument("--months", type=int, default=None)
        parser.add_argument("--from-date", type=str, default=None)
        parser.add_argument("--to-date", type=str, default=None)
        parser.add_argument(
            "--user-id",
            type=int,
            default=None,
            help="User whose Zerodha connection to use. Defaults to the "
                 "first user with an active, token-valid Zerodha config.",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Delete existing candles for this symbol+timeframe "
                 "(across all dates, not just the fetch range) before "
                 "loading fresh data — clears out stale/fragmentary rows "
                 "from earlier one-off fetches.",
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        symbols = [s.strip().upper() for s in options["symbols"].split(",") if s.strip()]
        timeframe = options["timeframe"]
        dry_run = options["dry_run"]
        clean = options["clean"]

        if options["from_date"] and options["to_date"]:
            from_date_str, to_date_str = options["from_date"], options["to_date"]
        elif options["months"]:
            to_date_str = date.today().isoformat()
            from_date_str = (date.today() - timedelta(days=options["months"] * 30)).isoformat()
        else:
            years = options["years"] or 5
            to_date_str = date.today().isoformat()
            from_date_str = (date.today() - timedelta(days=years * 365)).isoformat()

        user = self._resolve_user(options["user_id"])
        chunks = self._build_chunks(from_date_str, to_date_str, timeframe)

        self.stdout.write(
            f"Backfilling {symbols} [{timeframe}] from {from_date_str} to "
            f"{to_date_str} as user={user} — {len(chunks)} chunk(s)"
        )
        if clean:
            self.stdout.write(self.style.WARNING(
                f"--clean set: will delete ALL existing {timeframe} candles "
                f"for {symbols} before loading fresh data."
            ))

        if dry_run:
            for c_from, c_to in chunks:
                self.stdout.write(f"  would fetch: {c_from} to {c_to}")
            self.stdout.write(self.style.WARNING("Dry run — no DB writes."))
            return

        if clean:
            self._clean_existing(symbols, timeframe)

        service = CandleService(user=user)

        for symbol in symbols:
            total = 0
            for c_from, c_to in chunks:
                try:
                    count = service.fetch_and_store(
                        symbol=symbol,
                        timeframe=timeframe,
                        from_date=c_from,
                        to_date=c_to,
                    )
                    total += count
                    self.stdout.write(f"  {symbol} [{c_from} → {c_to}]: {count} candles")
                except Exception as e:
                    logger.error(f"backfill_candles failed for {symbol} [{c_from}→{c_to}]: {e}")
                    self.stdout.write(self.style.ERROR(
                        f"  {symbol} [{c_from} → {c_to}]: failed — {e}"
                    ))
            self.stdout.write(self.style.SUCCESS(f"{symbol}: {total} candles stored total"))

    def _build_chunks(self, from_date_str: str, to_date_str: str, timeframe: str) -> list[tuple[str, str]]:
        """Split the requested range into windows safely under Kite's
        real per-request limit for this timeframe."""
        chunk_days = self.CHUNK_DAYS.get(timeframe, 55)  # conservative default
        start = datetime.strptime(from_date_str, "%Y-%m-%d").date()
        end = datetime.strptime(to_date_str, "%Y-%m-%d").date()

        chunks = []
        cursor = start
        while cursor <= end:
            chunk_end = min(cursor + timedelta(days=chunk_days - 1), end)
            chunks.append((cursor.isoformat(), chunk_end.isoformat()))
            cursor = chunk_end + timedelta(days=1)
        return chunks

    def _clean_existing(self, symbols: list[str], timeframe: str) -> None:
        from apps.market_data.repositories.instrument_repository import InstrumentRepository
        from apps.market_data.repositories.candle_repository import CandleRepository

        for symbol in symbols:
            instrument = InstrumentRepository.get_by_symbol(symbol)
            if not instrument:
                continue
            deleted, _ = CandleRepository.model.objects.filter(
                instrument=instrument, timeframe=timeframe
            ).delete()
            self.stdout.write(f"  cleaned {symbol} [{timeframe}]: {deleted} old candles deleted")

    @staticmethod
    def _resolve_user(user_id):
        if user_id:
            try:
                return User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise CommandError(f"No user with id={user_id}")

        config = ZerodhaConfigRepository.model.objects.filter(
            is_connected=True
        ).first()

        if config and config.is_token_valid:
            return config.user

        raise CommandError(
            "No user with a valid Zerodha connection found. Reconnect via "
            "/zerodha in the app first, then re-run this command — or pass "
            "--user-id explicitly."
        )