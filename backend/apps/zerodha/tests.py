"""
Tests for the live-trading gate on ZerodhaOrderListAPIView.post().

Placing a real broker order must be blocked unless LIVE_TRADING_ENABLED
is explicitly True, independent of whatever MARKET_PROVIDER resolves to
elsewhere. Covers: gate blocks when disabled, gate allows when enabled,
and the existing 401-on-expired-token behavior still works once past
the gate.
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .exceptions import ZerodhaTokenExpiredError

User = get_user_model()

ORDER_PAYLOAD = {
    "tradingsymbol": "NIFTY24SEP24000CE",
    "exchange": "NFO",
    "transaction_type": "BUY",
    "quantity": 25,
    "order_type": "MARKET",
    "product": "MIS",
}

PLACE_ORDER_TARGET = "apps.zerodha.services.kite_service.KiteService.place_order"


class LiveTradingGateTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="livetrader", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("zerodha-orders")

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
    def test_expired_token_still_returns_401_past_the_gate(self):
        """Existing token-expiry handling is unaffected by the gate."""
        with patch(
            PLACE_ORDER_TARGET,
            side_effect=ZerodhaTokenExpiredError("access token is expired"),
        ):
            response = self.client.post(self.url, ORDER_PAYLOAD, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])
