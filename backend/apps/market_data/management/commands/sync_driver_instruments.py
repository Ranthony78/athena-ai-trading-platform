import csv
import io

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.market_data.management.commands.import_instruments import (
    Command as ImportInstrumentsCommand,
)
from apps.market_data.repositories.instrument_repository import InstrumentRepository
from apps.zerodha.services.mcp_service import ZerodhaKiteMCPService


class Command(BaseCommand):
    help = "Refresh read-only MCX crude and CDS USD/INR futures from an authenticated Kite session."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username", required=True,
            help="Athena username with an active Zerodha session",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Fetch and validate contracts without writing them",
        )

    def handle(self, *args, **options):
        user_model = get_user_model()
        try:
            user = user_model.objects.get(username=options["username"])
        except user_model.DoesNotExist as exc:
            raise CommandError("Athena user was not found.") from exc

        importer = ImportInstrumentsCommand()
        service = ZerodhaKiteMCPService(user)
        targets = {
            "MCX": {"CRUDEOIL", "CRUDEOILM"},
            "CDS": {"USDINR"},
        }
        selected_by_exchange = {}

        for exchange, symbols in targets.items():
            try:
                csv_text = service.get_instruments_csv(exchange)
            except Exception as exc:
                raise CommandError(
                    f"Could not retrieve the {exchange} catalog ({type(exc).__name__}); no catalog rows were written."
                ) from None

            selected = []
            try:
                for row in csv.DictReader(io.StringIO(csv_text)):
                    if row.get("instrument_type", "").strip().upper() != "FUT":
                        continue
                    if row.get("name", "").strip().upper() not in symbols:
                        continue
                    parsed = importer._parse_row(row)
                    if parsed:
                        selected.append(parsed)
            except Exception as exc:
                raise CommandError(
                    f"Could not parse the {exchange} catalog ({type(exc).__name__}); no catalog rows were written."
                ) from None

            selected_by_exchange[exchange] = selected

        total = sum(len(items) for items in selected_by_exchange.values())
        if options["dry_run"]:
            for exchange, selected in selected_by_exchange.items():
                self.stdout.write(f"{exchange}: validated {len(selected)} futures (dry run; no writes).")
            self.stdout.write(self.style.SUCCESS(f"Driver futures catalog validated: {total} (dry run)."))
            return

        # Fetch and parse both exchanges before writing either one, so a
        # partial upstream failure cannot leave a half-refreshed catalog.
        with transaction.atomic():
            for exchange, selected in selected_by_exchange.items():
                if not selected:
                    self.stdout.write(self.style.WARNING(f"{exchange}: no matching active futures were returned."))
                    continue
                for parsed in selected:
                    token = parsed.pop("instrument_token")
                    InstrumentRepository.upsert_from_import(token=token, defaults=parsed)
                self.stdout.write(f"{exchange}: refreshed {len(selected)} futures.")

        self.stdout.write(self.style.SUCCESS(f"Driver futures catalog processed: {total}."))
