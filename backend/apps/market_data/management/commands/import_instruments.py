import csv
import logging
import time
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.market_data.repositories.instrument_repository import InstrumentRepository

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Import market instruments from a Zerodha-format CSV file.

    Zerodha CSV columns:
        instrument_token, exchange_token, tradingsymbol, name,
        last_price, expiry, strike, tick_size, lot_size,
        instrument_type, segment, exchange

    Usage:
        # Import all exchanges
        python manage.py import_instruments --file data/instruments.csv

        # Import NFO only
        python manage.py import_instruments --file data/instruments.csv --exchange NFO

        # Deactivate all before fresh import
        python manage.py import_instruments --file data/instruments.csv --deactivate-first

        # Dry run — no DB writes
        python manage.py import_instruments --file data/instruments.csv --dry-run
    """

    help = "Import market instruments from Zerodha CSV"

    # Exchanges we care about
    SUPPORTED_EXCHANGES = {"NSE", "BSE", "NFO", "MCX"}

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="Path to the Zerodha instruments CSV file",
        )
        parser.add_argument(
            "--exchange",
            type=str,
            default=None,
            help="Import only this exchange (NSE, BSE, NFO, MCX)",
        )
        parser.add_argument(
            "--deactivate-first",
            action="store_true",
            default=False,
            help="Mark all existing instruments inactive before import",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Parse and validate CSV without writing to DB",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Number of records per DB transaction batch (default: 500)",
        )

    def handle(self, *args, **options) -> None:
        csv_file = options["file"]
        exchange_filter = options.get("exchange", "").upper() if options.get("exchange") else None
        deactivate_first = options.get("deactivate_first", False)
        dry_run = options.get("dry_run", False)
        batch_size = options.get("batch_size", 500)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be written to DB."))

        if exchange_filter and exchange_filter not in self.SUPPORTED_EXCHANGES:
            self.stderr.write(
                f"Unsupported exchange: {exchange_filter}. "
                f"Choose from: {', '.join(self.SUPPORTED_EXCHANGES)}"
            )
            return

        # ------------------------------------------------------------------
        # Step 1 — Deactivate existing if requested
        # ------------------------------------------------------------------
        if deactivate_first and not dry_run:
            count = InstrumentRepository.deactivate_all()
            self.stdout.write(f"Deactivated {count} existing instruments.")

        # ------------------------------------------------------------------
        # Step 2 — Read and parse CSV
        # ------------------------------------------------------------------
        self.stdout.write(f"Reading file: {csv_file}")
        start_time = time.time()

        try:
            rows = self._read_csv(csv_file)
        except FileNotFoundError:
            self.stderr.write(f"File not found: {csv_file}")
            return
        except Exception as e:
            self.stderr.write(f"Failed to read CSV: {e}")
            return

        self.stdout.write(f"Total rows in file: {len(rows)}")

        # ------------------------------------------------------------------
        # Step 3 — Filter by exchange
        # ------------------------------------------------------------------
        if exchange_filter:
            rows = [r for r in rows if r.get("exchange", "").upper() == exchange_filter]
            self.stdout.write(f"Rows after exchange filter ({exchange_filter}): {len(rows)}")

        # ------------------------------------------------------------------
        # Step 4 — Process in batches
        # ------------------------------------------------------------------
        imported = 0
        updated = 0
        skipped = 0
        errors = 0

        batches = [rows[i:i + batch_size] for i in range(0, len(rows), batch_size)]
        total_batches = len(batches)

        self.stdout.write(f"Processing {len(rows)} rows in {total_batches} batches...")

        for batch_num, batch in enumerate(batches, start=1):
            self.stdout.write(f"  Batch {batch_num}/{total_batches}...", ending="\r")

            batch_imported, batch_updated, batch_skipped, batch_errors = self._process_batch(
                batch=batch,
                dry_run=dry_run,
            )

            imported += batch_imported
            updated += batch_updated
            skipped += batch_skipped
            errors += batch_errors

        # ------------------------------------------------------------------
        # Step 5 — Summary
        # ------------------------------------------------------------------
        elapsed = time.time() - start_time

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"\n{'[DRY RUN] ' if dry_run else ''}Import complete in {elapsed:.1f}s\n"
            f"  Created : {imported}\n"
            f"  Updated : {updated}\n"
            f"  Skipped : {skipped}\n"
            f"  Errors  : {errors}\n"
            f"  Total   : {imported + updated + skipped}"
        ))

        if errors > 0:
            self.stdout.write(
                self.style.WARNING(f"  {errors} rows had errors — check logs for details.")
            )

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _read_csv(self, csv_file: str) -> list[dict]:
        """Read and return all rows from CSV as list of dicts."""
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _process_batch(
        self,
        batch: list[dict],
        dry_run: bool,
    ) -> tuple[int, int, int, int]:
        """
        Process a batch of CSV rows.
        Returns (imported, updated, skipped, errors).
        """
        imported = 0
        updated = 0
        skipped = 0
        errors = 0

        for row in batch:
            try:
                parsed = self._parse_row(row)

                if parsed is None:
                    skipped += 1
                    continue

                if dry_run:
                    imported += 1
                    continue

                token = parsed.pop("instrument_token")

                with transaction.atomic():
                    _, created = InstrumentRepository.upsert_from_import(
                        token=token,
                        defaults=parsed,
                    )

                if created:
                    imported += 1
                else:
                    updated += 1

            except Exception as e:
                errors += 1
                logger.error(
                    f"Error processing row: "
                    f"{row.get('tradingsymbol', 'unknown')} — {e}"
                )

        return imported, updated, skipped, errors

    def _parse_row(self, row: dict) -> dict | None:
        """
        Parse and validate a single CSV row.
        Returns a defaults dict ready for upsert, or None to skip.
        """
        exchange = row.get("exchange", "").strip().upper()

        # Skip unsupported exchanges
        if exchange not in self.SUPPORTED_EXCHANGES:
            return None

        # Skip rows with no token
        raw_token = row.get("instrument_token", "").strip()
        if not raw_token:
            return None

        try:
            instrument_token = int(float(raw_token))
        except (ValueError, TypeError):
            logger.warning(f"Invalid instrument_token: {raw_token}")
            return None

        # trading symbol — Zerodha uses 'tradingsymbol'
        trading_symbol = row.get("tradingsymbol", "").strip()
        if not trading_symbol:
            return None

        # underlying symbol — use 'name' field from Zerodha CSV
        symbol = row.get("name", "").strip() or trading_symbol

        # instrument type
        instrument_type_raw = row.get("instrument_type", "").strip().upper()
        instrument_type = self._resolve_instrument_type(
            exchange=exchange,
            instrument_type_raw=instrument_type_raw,
        )

        # option type
        option_type = ""
        if instrument_type_raw in ("CE", "PE"):
            option_type = instrument_type_raw

        # expiry
        expiry = None
        raw_expiry = row.get("expiry", "").strip()
        if raw_expiry:
            expiry = self._parse_expiry(raw_expiry)

        # strike
        strike = None
        raw_strike = row.get("strike", "").strip()
        if raw_strike:
            try:
                strike_val = float(raw_strike)
                strike = strike_val if strike_val > 0 else None
            except (ValueError, TypeError):
                strike = None

        # lot size
        try:
            lot_size = int(float(row.get("lot_size", 1) or 1))
        except (ValueError, TypeError):
            lot_size = 1

        # tick size
        try:
            tick_size = float(row.get("tick_size", 0.05) or 0.05)
        except (ValueError, TypeError):
            tick_size = 0.05

        # exchange token
        try:
            exchange_token = int(float(row.get("exchange_token", 0) or 0))
        except (ValueError, TypeError):
            exchange_token = 0

        return {
            "instrument_token": instrument_token,
            "exchange_token": exchange_token,
            "exchange": exchange,
            "symbol": symbol,
            "trading_symbol": trading_symbol,
            "instrument_type": instrument_type,
            "option_type": option_type,
            "expiry": expiry,
            "strike": strike,
            "lot_size": lot_size,
            "tick_size": tick_size,
            "is_active": True,
        }

    def _resolve_instrument_type(
        self,
        exchange: str,
        instrument_type_raw: str,
    ) -> str:
        """
        Map Zerodha instrument_type field to our internal instrument_type.
        """
        mapping = {
            "CE": "CE",
            "PE": "PE",
            "FUT": "FUT",
            "EQ": "EQ",
            "INDEX": "IDX",
            "IDX": "IDX",
        }
        return mapping.get(instrument_type_raw, "EQ")

    def _parse_expiry(self, raw_expiry: str):
        """
        Parse expiry date string to date object.
        Zerodha uses YYYY-MM-DD format.
        """
        formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%Y/%m/%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(raw_expiry, fmt).date()
            except ValueError:
                continue

        logger.warning(f"Could not parse expiry date: {raw_expiry}")
        return None