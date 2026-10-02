"""
Tests for the strategies API after rule-based execution was retired.

Strategies are read-only over the API: list/detail/signals still work,
create/update/delete are gone, and the run endpoints answer 410 Gone.
The strategy models and StrategyEngine stay in place for backtesting.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Strategy

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

        response = self.client.get(
            reverse("strategy-detail", args=[self.strategy.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["id"], self.strategy.pk)

    def test_create_update_delete_are_not_allowed(self):
        payload = {"name": "New", "strategy_type": "RSI", "timeframe": "5m"}
        detail = reverse("strategy-detail", args=[self.strategy.pk])

        self.assertEqual(
            self.client.post(reverse("strategy-list"), payload, format="json").status_code,
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

        with patch(
            "apps.strategies.services.strategy_engine.StrategyEngine.run"
        ) as run, patch(
            "apps.strategies.services.strategy_engine.StrategyEngine.run_all"
        ) as run_all:
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
