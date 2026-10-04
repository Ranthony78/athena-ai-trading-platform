"""
Permission for real broker orders: kill switch, master switch, per-user
arming that lapses at the end of the day, and the admin-only master control.
"""

from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    LiveTradingArming,
    LiveTradingAuditEvent,
    LiveTradingControl,
    ZerodhaConfig,
)
from .services.live_trading_service import CONFIRM_PHRASE, LiveTradingService

User = get_user_model()
IST = ZoneInfo("Asia/Kolkata")
MORNING = datetime(2026, 10, 5, 10, 0, tzinfo=IST)
EVENING = datetime(2026, 10, 5, 16, 0, tzinfo=IST)
ORDER_TARGET = "apps.zerodha.services.kite_service.KiteService.place_order"
SESSION_TARGET = "apps.market_data.engine.market_state.MarketState.session_info"

ORDER = {
    "confirm_live_order": True,
    "tradingsymbol": "NIFTY26O0622400PE",
    "exchange": "NFO",
    "transaction_type": "BUY",
    "quantity": 65,
    "order_type": "LIMIT",
    "price": 1.0,
    "product": "NRML",
}


def make_user(name="trader", staff=False, connected=True):
    user = User.objects.create_user(
        username=name,
        email=f"{name}@example.com",
        password="pw12345678",
        is_staff=staff,
    )
    ZerodhaConfig.objects.create(
        user=user,
        access_token="token" if connected else "",
        is_connected=connected,
        token_expires_at=timezone.now() + timedelta(days=5) if connected else None,
    )
    return user


def master_on():
    LiveTradingControl.objects.update_or_create(pk=1, defaults={"enabled": True})


class PermissionTests(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_by_default_nothing_is_allowed(self):
        allowed, reason = LiveTradingService.can_place(self.user, MORNING)
        self.assertFalse(allowed)
        self.assertIn("not enabled", reason)

    def test_master_on_but_not_armed_is_still_blocked(self):
        master_on()
        allowed, reason = LiveTradingService.can_place(self.user, MORNING)
        self.assertFalse(allowed)
        self.assertIn("not armed", reason)

    def test_master_on_and_armed_is_allowed(self):
        master_on()
        LiveTradingService.arm(self.user, CONFIRM_PHRASE, MORNING)
        self.assertEqual(LiveTradingService.can_place(self.user, MORNING), (True, ""))

    @override_settings(LIVE_TRADING_LOCKED=True)
    def test_the_server_lock_beats_everything(self):
        master_on()
        LiveTradingArming.objects.create(
            user=self.user,
            armed_at=MORNING,
            expires_at=MORNING + timedelta(hours=5),
            disclaimer_version="t",
        )
        allowed, reason = LiveTradingService.can_place(self.user, MORNING)
        self.assertFalse(allowed)
        self.assertIn("locked", reason)

    @override_settings(LIVE_TRADING_ENABLED=True)
    def test_the_older_environment_flag_counts_as_master_on(self):
        self.assertTrue(LiveTradingService.master_enabled())
        LiveTradingService.arm(self.user, CONFIRM_PHRASE, MORNING)
        self.assertTrue(LiveTradingService.can_place(self.user, MORNING)[0])

    def test_one_users_arming_does_not_cover_another(self):
        master_on()
        other = make_user("other")
        LiveTradingService.arm(self.user, CONFIRM_PHRASE, MORNING)
        self.assertTrue(LiveTradingService.can_place(self.user, MORNING)[0])
        self.assertFalse(LiveTradingService.can_place(other, MORNING)[0])


class ArmingTests(TestCase):

    def setUp(self):
        self.user = make_user()
        master_on()

    def test_arming_lapses_at_the_end_of_the_session(self):
        state = LiveTradingService.arm(self.user, CONFIRM_PHRASE, MORNING)

        expires = datetime.fromisoformat(state["armed_until"]).astimezone(IST)
        self.assertEqual((expires.hour, expires.minute), (15, 30))
        self.assertTrue(
            LiveTradingService.can_place(self.user, expires - timedelta(minutes=1))[0]
        )
        self.assertFalse(LiveTradingService.can_place(self.user, expires)[0])
        self.assertFalse(
            LiveTradingService.can_place(self.user, expires + timedelta(hours=1))[0]
        )

    def test_wrong_or_missing_phrase_is_refused(self):
        for phrase in ("", "i understand", "I UNDERSTAND", None):
            with self.assertRaises(ValueError):
                LiveTradingService.arm(self.user, phrase, MORNING)
        self.assertFalse(LiveTradingArming.objects.exists())

    def test_cannot_arm_after_the_close(self):
        with self.assertRaises(ValueError) as caught:
            LiveTradingService.arm(self.user, CONFIRM_PHRASE, EVENING)
        self.assertIn("session has ended", str(caught.exception))

    def test_cannot_arm_without_a_valid_zerodha_session(self):
        loose = make_user("loose", connected=False)
        with self.assertRaises(ValueError) as caught:
            LiveTradingService.arm(loose, CONFIRM_PHRASE, MORNING)
        self.assertIn("Connect Zerodha", str(caught.exception))

    def test_cannot_arm_when_the_master_is_off_or_locked(self):
        LiveTradingControl.objects.update(enabled=False)
        with self.assertRaises(ValueError):
            LiveTradingService.arm(self.user, CONFIRM_PHRASE, MORNING)
        master_on()
        with override_settings(LIVE_TRADING_LOCKED=True), self.assertRaises(ValueError):
            LiveTradingService.arm(self.user, CONFIRM_PHRASE, MORNING)

    def test_disarm_stops_orders_immediately(self):
        LiveTradingService.arm(self.user, CONFIRM_PHRASE, MORNING)
        LiveTradingService.disarm(self.user, MORNING)
        self.assertFalse(LiveTradingService.can_place(self.user, MORNING)[0])

    def test_arming_twice_leaves_one_open_arming(self):
        LiveTradingService.arm(self.user, CONFIRM_PHRASE, MORNING)
        LiveTradingService.arm(self.user, CONFIRM_PHRASE, MORNING)
        open_ = LiveTradingArming.objects.filter(disarmed_at__isnull=True)
        self.assertEqual(open_.count(), 1)

    def test_state_reports_what_the_screen_needs(self):
        state = LiveTradingService.state(self.user, MORNING)
        self.assertTrue(state["can_arm"])
        self.assertFalse(state["armed"])
        self.assertEqual(state["confirm_phrase"], CONFIRM_PHRASE)
        self.assertTrue(state["disclaimer"]["lines"])
        self.assertFalse(state["is_admin"])


class MasterSwitchTests(TestCase):

    def test_only_staff_can_change_it(self):
        user = make_user()
        with self.assertRaises(PermissionError):
            LiveTradingService.set_master(user, True)
        self.assertFalse(LiveTradingService.master_enabled())

    def test_staff_can_turn_it_on_and_off(self):
        admin = make_user("admin", staff=True)
        LiveTradingService.set_master(admin, True, MORNING)
        self.assertTrue(LiveTradingService.master_enabled())
        LiveTradingService.set_master(admin, False, MORNING)
        self.assertFalse(LiveTradingService.master_enabled())

    def test_turning_it_off_cancels_everyones_arming_for_good(self):
        admin = make_user("admin", staff=True)
        trader = make_user("trader")
        LiveTradingService.set_master(admin, True, MORNING)
        LiveTradingService.arm(trader, CONFIRM_PHRASE, MORNING)

        LiveTradingService.set_master(admin, False, MORNING)
        LiveTradingService.set_master(admin, True, MORNING)

        # The old arming must not come back to life.
        self.assertFalse(LiveTradingService.can_place(trader, MORNING)[0])

    def test_changes_are_recorded(self):
        admin = make_user("admin", staff=True)
        trader = make_user("trader")
        LiveTradingService.set_master(admin, True, MORNING)
        LiveTradingService.arm(trader, CONFIRM_PHRASE, MORNING)
        LiveTradingService.disarm(trader, MORNING)
        actions = list(
            LiveTradingAuditEvent.objects.order_by("created_at").values_list(
                "action", flat=True
            )
        )
        self.assertEqual(actions, ["MASTER_ON", "ARM", "DISARM"])


class EndpointTests(APITestCase):

    def setUp(self):
        self.user = make_user()
        self.admin = make_user("admin", staff=True)

    def post(self, name, data=None, user=None):
        self.client.force_authenticate(user=user or self.user)
        return self.client.post(reverse(name), data or {}, format="json")

    def test_status_requires_login(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(reverse("live-trading")).status_code, 401)

    def test_a_normal_user_cannot_flip_the_master(self):
        response = self.post("live-trading-master", {"enabled": True})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(LiveTradingService.master_enabled())

    def test_master_needs_a_real_boolean(self):
        for bad in ("true", 1, None):
            response = self.post(
                "live-trading-master", {"enabled": bad}, user=self.admin
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_flips_master_and_user_then_arms_over_the_api(self):
        self.assertEqual(
            self.post("live-trading-master", {"enabled": True}, self.admin).status_code,
            200,
        )

        with patch(
            "apps.zerodha.services.live_trading_service.timezone.now",
            return_value=MORNING,
        ):
            wrong = self.post("live-trading-arm", {"phrase": "yes"})
            self.assertEqual(wrong.status_code, status.HTTP_400_BAD_REQUEST)
            ok = self.post("live-trading-arm", {"phrase": CONFIRM_PHRASE})
            self.assertEqual(ok.status_code, 200)
            self.assertTrue(ok.data["data"]["armed"])

            self.client.force_authenticate(user=self.user)
            state = self.client.get(reverse("live-trading")).data["data"]
            self.assertTrue(state["can_place"])

    def test_zerodha_status_reports_permission_for_the_dashboard(self):
        self.client.force_authenticate(user=self.user)
        data = self.client.get(reverse("zerodha-status")).data["data"]
        self.assertIs(data["live_orders_enabled"], False)
        self.assertIn("live_trading", data)


class OrderGateTests(APITestCase):
    """The order endpoint itself refuses until every layer allows it."""

    def setUp(self):
        self.user = make_user()
        self.client.force_authenticate(user=self.user)
        self.url = reverse("zerodha-orders")
        patcher = patch(SESSION_TARGET, return_value={"is_live": True})
        patcher.start()
        self.addCleanup(patcher.stop)

    def send(self):
        with patch(ORDER_TARGET, return_value={"order_id": "X"}) as place:
            response = self.client.post(self.url, ORDER, format="json")
        return response, place

    def test_unarmed_user_cannot_send_even_with_the_master_on(self):
        master_on()
        response, place = self.send()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        place.assert_not_called()

    def test_armed_user_can_send_during_market_hours(self):
        master_on()
        LiveTradingArming.objects.create(
            user=self.user,
            armed_at=timezone.now(),
            expires_at=timezone.now() + timedelta(hours=1),
            disclaimer_version="t",
        )
        response, place = self.send()
        self.assertEqual(response.status_code, 200)
        place.assert_called_once()

    def test_market_hours_still_apply_to_an_armed_user(self):
        master_on()
        LiveTradingArming.objects.create(
            user=self.user,
            armed_at=timezone.now(),
            expires_at=timezone.now() + timedelta(hours=1),
            disclaimer_version="t",
        )
        with patch(SESSION_TARGET, return_value={"is_live": False}):
            response, place = self.send()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        place.assert_not_called()

    def test_expired_arming_is_refused(self):
        master_on()
        LiveTradingArming.objects.create(
            user=self.user,
            armed_at=timezone.now() - timedelta(hours=3),
            expires_at=timezone.now() - timedelta(hours=1),
            disclaimer_version="t",
        )
        response, place = self.send()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        place.assert_not_called()

    @override_settings(LIVE_TRADING_LOCKED=True)
    def test_locked_server_refuses_an_armed_user(self):
        master_on()
        LiveTradingArming.objects.create(
            user=self.user,
            armed_at=timezone.now(),
            expires_at=timezone.now() + timedelta(hours=1),
            disclaimer_version="t",
        )
        response, place = self.send()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("locked", response.data["message"])
        place.assert_not_called()

    def test_turning_the_master_off_stops_an_armed_user_at_once(self):
        admin = make_user("admin", staff=True)
        master_on()
        LiveTradingArming.objects.create(
            user=self.user,
            armed_at=timezone.now(),
            expires_at=timezone.now() + timedelta(hours=1),
            disclaimer_version="t",
        )
        LiveTradingService.set_master(admin, False)
        response, place = self.send()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        place.assert_not_called()
