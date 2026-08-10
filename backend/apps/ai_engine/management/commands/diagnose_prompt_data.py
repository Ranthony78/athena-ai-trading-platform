"""
backend/apps/ai_engine/management/commands/diagnose_prompt_data.py

New file.

Tests every data source PromptService pulls from — independently, one at
a time — and reports exactly what came back real vs. None. This isolates
whether "all fields showing Unavailable" is a data-fetch problem (real
bug, needs fixing here) or a model-compliance problem (the data reaches
the prompt fine, Claude just isn't filling in the JSON fields from it).

Usage:
    python manage.py diagnose_prompt_data --symbol NIFTY --user-id 1

If --user-id is omitted, it tries the same "first user with a valid
Zerodha token" resolution as backfill_candles.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = "Test every PromptService data source independently against real data"

    def add_arguments(self, parser):
        parser.add_argument("--symbol", type=str, default="NIFTY")
        parser.add_argument("--user-id", type=int, default=None)

    def handle(self, *args, **options):
        symbol = options["symbol"].upper()
        user = self._resolve_user(options["user_id"])

        self.stdout.write(f"Diagnosing PromptService data sources for {symbol} as user={user}\n")
        self.stdout.write("=" * 70)

        results = []

        results.append(self._check("Quote (live)", lambda: self._get_quote(symbol, user)))
        results.append(self._check("Gap analysis", lambda: self._get_gap(symbol, user)))
        results.append(self._check("Historical base rate (Section 3)", lambda: self._get_historical(symbol)))
        results.append(self._check("India VIX (Section 1)", lambda: self._get_vix(user)))
        results.append(self._check("Market breadth (Section 4)", lambda: self._get_breadth(user)))
        results.append(self._check("News sentiment (Section 5)", lambda: self._get_news()))
        results.append(self._check("Session structure (Section 7)", lambda: self._get_session_structure(symbol)))
        results.append(self._check("ATM options (Section 10)", lambda: self._get_options(symbol, user)))

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 70)
        real_count = sum(1 for r in results if r)
        self.stdout.write(f"{real_count}/{len(results)} data sources returned real data.\n")

        if real_count == len(results):
            self.stdout.write(self.style.SUCCESS(
                "All data sources are working. If the AI's JSON output still "
                "shows these fields as null, that's a MODEL-COMPLIANCE issue, "
                "not a data-fetch issue — the prompt has the data, Claude "
                "just isn't using it. Check the raw JSON block from a real "
                "analysis run to confirm the fields are present-but-null vs "
                "missing entirely."
            ))
        elif real_count == 0:
            self.stdout.write(self.style.ERROR(
                "No data sources returned real data — check your Zerodha "
                "connection is active and token valid (visit /zerodha in "
                "the app)."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "Some data sources work, some don't — see individual results "
                "above for which ones need attention."
            ))

    def _check(self, label, fn):
        try:
            result = fn()
            if result:
                self.stdout.write(self.style.SUCCESS(f"✓ {label}: REAL DATA"))
                self.stdout.write(f"    {str(result)[:200]}")
                return True
            else:
                self.stdout.write(self.style.WARNING(f"✗ {label}: None/empty"))
                return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ {label}: EXCEPTION — {e}"))
            return False

    # ------------------------------------------------------------------

    @staticmethod
    def _get_quote(symbol, user):
        from apps.market_data.services.market_service import MarketService
        return MarketService(user=user).quote(symbol) if user else None

    @staticmethod
    def _get_gap(symbol, user):
        from apps.ai_engine.services.prompt_service import PromptService
        quote = PromptService._safe_get_quote(symbol, user)
        return PromptService._calculate_gap(quote)

    @staticmethod
    def _get_historical(symbol):
        from apps.market_data.services.historical_distribution_service import (
            HistoricalDistributionService,
        )
        gap = HistoricalDistributionService.gap_stats(symbol)
        return None if gap.get("error") else gap

    @staticmethod
    def _get_vix(user):
        from apps.ai_engine.services.prompt_service import PromptService
        return PromptService._safe_get_vix(user)

    @staticmethod
    def _get_breadth(user):
        from apps.market_data.services.market_breadth_service import MarketBreadthService
        return MarketBreadthService.get_breadth(user) if user else None

    @staticmethod
    def _get_news():
        from apps.market_data.services.news_sentiment_service import NewsSentimentService
        return NewsSentimentService.get_macro_sentiment()

    @staticmethod
    def _get_session_structure(symbol):
        from apps.market_data.services.session_structure_service import SessionStructureService
        return SessionStructureService.get_today_structure(symbol)

    @staticmethod
    def _get_options(symbol, user):
        from apps.ai_engine.services.prompt_service import PromptService
        return PromptService._safe_option_analysis(symbol, user)

    @staticmethod
    def _resolve_user(user_id):
        if user_id:
            try:
                return User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise CommandError(f"No user with id={user_id}")

        from apps.zerodha.repositories.zerodha_repository import ZerodhaConfigRepository
        config = ZerodhaConfigRepository.model.objects.filter(is_connected=True).first()
        if config and config.is_token_valid:
            return config.user

        raise CommandError(
            "No user with a valid Zerodha connection found. Reconnect via "
            "/zerodha in the app first, or pass --user-id explicitly."
        )