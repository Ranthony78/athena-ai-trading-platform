"""
Tests for the strategies API after rule-based execution was retired.

Strategies are read-only over the API: list/detail/signals still work,
create/update/delete are gone, and the run endpoints answer 410 Gone.
The strategy models and StrategyEngine stay in place for backtesting.
"""

from datetime import datetime
from datetime import timezone as dt_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.market_data.models import Instrument

from .models import Strategy, StrategySignal

User = get_user_model()


class StrategiesReadOnlyAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="strategist", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.strategy = Strategy.objects.create(
            name="EMA 9/21",
            strategy_type="EMA_CROSSOVER",
            timeframe="15m",
        )

    def test_list_and_detail_still_work(self):
        response = self.client.get(reverse("strategy-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([s["name"] for s in response.data["data"]], ["EMA 9/21"])

        response = self.client.get(reverse("strategy-detail", args=[self.strategy.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["id"], self.strategy.pk)

    def test_create_update_delete_are_not_allowed(self):
        payload = {"name": "New", "strategy_type": "RSI", "timeframe": "5m"}
        detail = reverse("strategy-detail", args=[self.strategy.pk])

        self.assertEqual(
            self.client.post(
                reverse("strategy-list"), payload, format="json"
            ).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.put(detail, payload, format="json").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.delete(detail).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        # Nothing was created, changed or removed.
        self.assertEqual(Strategy.objects.count(), 1)
        self.strategy.refresh_from_db()
        self.assertEqual(self.strategy.name, "EMA 9/21")

    def test_run_endpoints_are_retired(self):
        for name, payload in (
            ("strategy-run", {"strategy_id": self.strategy.pk, "symbol": "NIFTY"}),
            ("strategy-run-all", {"symbols": ["NIFTY"]}),
        ):
            response = self.client.post(reverse(name), payload, format="json")

            self.assertEqual(response.status_code, status.HTTP_410_GONE)
            self.assertFalse(response.data["success"])
            self.assertIn("retired", response.data["message"])

    def test_retired_run_endpoint_never_executes_the_engine(self):
        from unittest.mock import patch

        with (
            patch("apps.strategies.services.strategy_engine.StrategyEngine.run") as run,
            patch(
                "apps.strategies.services.strategy_engine.StrategyEngine.run_all"
            ) as run_all,
        ):
            self.client.post(
                reverse("strategy-run"),
                {"strategy_id": self.strategy.pk, "symbol": "NIFTY"},
                format="json",
            )
            self.client.post(
                reverse("strategy-run-all"), {"symbols": ["NIFTY"]}, format="json"
            )

        run.assert_not_called()
        run_all.assert_not_called()

    def test_signal_endpoints_still_work(self):
        self.assertEqual(
            self.client.get(reverse("signal-list")).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.client.get(reverse("signal-by-symbol", args=["NIFTY"])).status_code,
            status.HTTP_200_OK,
        )

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        for name in ("strategy-list", "signal-list"):
            self.assertIn(
                self.client.get(reverse(name)).status_code,
                (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
            )
        self.assertIn(
            self.client.post(reverse("strategy-run"), {}, format="json").status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )


class SignalVisibilityTests(APITestCase):
    """A user sees their own signals and unowned legacy ones, never another user's."""

    def setUp(self):
        self.alice = User.objects.create_user(
            "alice", "alice@example.com", "pw-Alice-123"
        )
        self.bob = User.objects.create_user("bob", "bob@example.com", "pw-Bob-12345")
        self.instrument = Instrument.objects.create(
            instrument_token=777000001,
            exchange="NSE",
            symbol="NIFTY 50",
            # get_by_symbol("NIFTY") resolves the short code to this real index name.
            trading_symbol="NIFTY 50",
            instrument_type="IDX",
        )
        self.strategy = Strategy.objects.create(
            name="EMA 9/21", strategy_type="EMA_CROSSOVER", timeframe="15m"
        )
        self.alices = self.make_signal(self.alice)
        self.bobs = self.make_signal(self.bob)
        self.legacy = self.make_signal(None)
        self.client.force_authenticate(self.alice)

    def make_signal(self, user, status="ACTIVE"):
        return StrategySignal.objects.create(
            strategy=self.strategy,
            instrument=self.instrument,
            user=user,
            signal="BUY",
            status=status,
            price_at_signal="22500.00",
            timeframe="15m",
            signal_time=timezone.now(),
        )

    def ids(self, url_name, *args, **params):
        response = self.client.get(reverse(url_name, args=args), params)
        self.assertEqual(response.status_code, 200)
        return {row["id"] for row in response.data["data"]}

    def test_todays_signals_exclude_other_users(self):
        self.assertEqual(self.ids("signal-list"), {self.alices.id, self.legacy.id})

    def test_active_signals_exclude_other_users(self):
        self.assertEqual(
            self.ids("signal-list", active="1"), {self.alices.id, self.legacy.id}
        )

    def test_signals_by_symbol_exclude_other_users(self):
        self.assertEqual(
            self.ids("signal-by-symbol", "NIFTY"), {self.alices.id, self.legacy.id}
        )

    def test_each_user_sees_only_their_own(self):
        self.client.force_authenticate(self.bob)

        self.assertEqual(self.ids("signal-list"), {self.bobs.id, self.legacy.id})

    def test_a_user_with_no_signals_sees_only_unowned_legacy_ones(self):
        carol = User.objects.create_user("carol", "carol@example.com", "pw-Carol-1234")
        self.client.force_authenticate(carol)

        self.assertEqual(self.ids("signal-list"), {self.legacy.id})

    def test_todays_signals_use_the_local_date_not_the_utc_date(self):
        """Regression: at 02:00 IST it is still the previous day in UTC."""
        # 2026-10-03 20:30 UTC is 2026-10-04 02:00 IST.
        night = datetime(2026, 10, 3, 20, 30, tzinfo=dt_timezone.utc)
        StrategySignal.objects.all().delete()
        late = self.make_signal(self.alice)
        StrategySignal.objects.filter(pk=late.pk).update(signal_time=night)

        with patch("django.utils.timezone.now", return_value=night):
            response = self.client.get(reverse("signal-list"))

        self.assertEqual({row["id"] for row in response.data["data"]}, {late.id})
