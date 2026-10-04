"""
Tests for the live-trading gate on ZerodhaOrderListAPIView.post().

Placing a real broker order must be blocked unless LIVE_TRADING_ENABLED
is explicitly True, independent of whatever MARKET_PROVIDER resolves to
elsewhere. Covers: gate blocks when disabled, gate allows when enabled,
and the existing 401-on-expired-token behavior still works once past
the gate.
"""

import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .exceptions import ZerodhaTokenExpiredError
from .models import LiveTradingArming

User = get_user_model()

ORDER_PAYLOAD = {
    "confirm_live_order": True,
    "tradingsymbol": "NIFTY24SEP24000CE",
    "exchange": "NFO",
    "transaction_type": "BUY",
    "quantity": 25,
    "order_type": "MARKET",
    "product": "MIS",
}

PLACE_ORDER_TARGET = "apps.zerodha.services.kite_service.KiteService.place_order"
SESSION_INFO_TARGET = "apps.market_data.engine.market_state.MarketState.session_info"


class LiveTradingGateTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="livetrader", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("zerodha-orders")

        # Real orders also need this user to have armed them for today.
        LiveTradingArming.objects.create(
            user=self.user,
            armed_at=timezone.now(),
            expires_at=timezone.now() + timedelta(hours=1),
            disclaimer_version="test",
        )

        # The view also requires regular market hours; pin the session so
        # these tests don't depend on the wall clock.
        session_patcher = patch(SESSION_INFO_TARGET, return_value={"is_live": True})
        session_patcher.start()
        self.addCleanup(session_patcher.stop)

    @override_settings(LIVE_TRADING_ENABLED=False)
    def test_gate_blocks_when_disabled(self):
        """POST is rejected with 403 and never reaches KiteService."""
        with patch(PLACE_ORDER_TARGET) as mock_place_order:
            response = self.client.post(self.url, ORDER_PAYLOAD, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        mock_place_order.assert_not_called()

    @override_settings(LIVE_TRADING_ENABLED=True)
    def test_gate_allows_when_enabled(self):
        """With the flag on, the request reaches KiteService.place_order."""
        with patch(
            PLACE_ORDER_TARGET,
            return_value={"success": True, "order_id": "TEST123"},
        ) as mock_place_order:
            response = self.client.post(self.url, ORDER_PAYLOAD, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        mock_place_order.assert_called_once()

    @override_settings(LIVE_TRADING_ENABLED=True)
    def test_blocks_outside_market_hours(self):
        """Even with the flag on, orders are rejected when the market is closed."""
        with (
            patch(SESSION_INFO_TARGET, return_value={"is_live": False}),
            patch(PLACE_ORDER_TARGET) as mock_place_order,
        ):
            response = self.client.post(self.url, ORDER_PAYLOAD, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        mock_place_order.assert_not_called()

    @override_settings(LIVE_TRADING_ENABLED=True)
    def test_requires_explicit_order_confirmation(self):
        """Missing or false confirm_live_order never reaches KiteService."""
        for confirm in (None, False):
            payload = dict(ORDER_PAYLOAD)
            if confirm is None:
                payload.pop("confirm_live_order")
            else:
                payload["confirm_live_order"] = confirm

            with patch(PLACE_ORDER_TARGET) as mock_place_order:
                response = self.client.post(self.url, payload, format="json")

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(response.data["success"])
            mock_place_order.assert_not_called()

    @override_settings(LIVE_TRADING_ENABLED=True)
    def test_expired_token_still_returns_401_past_the_gate(self):
        """Existing token-expiry handling is unaffected by the gate."""
        with patch(
            PLACE_ORDER_TARGET,
            side_effect=ZerodhaTokenExpiredError("access token is expired"),
        ):
            response = self.client.post(self.url, ORDER_PAYLOAD, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])


class LiveTradingSettingTests(SimpleTestCase):
    """
    Real broker orders are off unless the server environment turns them on.

    Each case starts the real settings module in a fresh process, because that
    is the only way to see what production would actually do.
    """

    BACKEND_DIR = Path(__file__).resolve().parents[2]

    def live_flag(self, settings_module, value):
        env = {
            **os.environ,
            "DJANGO_SECRET_KEY": "k" * 50,
            "CORS_ALLOWED_ORIGINS": "",
            "LIVE_TRADING_ENABLED": value,
        }
        code = (
            "import os, django; "
            f"os.environ['DJANGO_SETTINGS_MODULE']='{settings_module}'; "
            "django.setup(); "
            "from django.conf import settings; "
            "print(settings.LIVE_TRADING_ENABLED)"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=self.BACKEND_DIR,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def test_production_is_off_unless_the_environment_says_exactly_True(self):
        # An empty value stands in for "not set" and keeps a developer's .env
        # from leaking into the test; the others are near misses.
        for value in ("", "False", "false", "0", "yes", "true", "TRUE", " True"):
            self.assertEqual(
                self.live_flag("config.settings.production", value),
                "False",
                repr(value),
            )

    def test_production_turns_on_when_the_environment_asks_for_it(self):
        self.assertEqual(self.live_flag("config.settings.production", "True"), "True")

    def test_development_stays_off_even_if_the_environment_asks(self):
        self.assertEqual(self.live_flag("config.settings.development", "True"), "False")
