"""
Permission for real broker orders.

An order is allowed only when ALL of these hold:
  1. the server is not locked (LIVE_TRADING_LOCKED, set in the environment);
  2. the master switch is on (an administrator's choice in the app, or the
     older LIVE_TRADING_ENABLED environment flag);
  3. the user has armed live orders and that arming has not lapsed.
The view adds two more checks: regular market hours, and the per-order
confirmation.

Arming lapses at the end of the trading day (15:30 IST), is cancelled when
the master switch goes off, and requires a valid Zerodha session. Nothing
here places an order.
"""

import logging
from datetime import datetime, time
from typing import Optional
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from ..models import LiveTradingArming, LiveTradingAuditEvent, LiveTradingControl

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")
MARKET_CLOSE = time(15, 30)

DISCLAIMER_VERSION = "2026-10-v1"
CONFIRM_PHRASE = "I UNDERSTAND THE RISKS"
DISCLAIMER_LINES = [
    "Live orders use real money in your own Zerodha account and can lose more than you expect.",
    "Orders are sent to your broker. Once accepted they may fill immediately and cannot be undone by Athena.",
    "Athena is analysis software. Nothing it shows is investment advice or a recommendation to trade.",
    "Probabilities and filters describe past data under stated assumptions. They are not forecasts.",
    "You are responsible for every order and for following your broker's and the exchange's and SEBI's rules.",
    "Arming lasts until the end of today's session. You will need to arm again each day.",
]


def _control() -> LiveTradingControl:
    control = LiveTradingControl.objects.first()
    if control is None:
        control = LiveTradingControl.objects.create(enabled=False)
    return control


def _log(user, action: str, detail: str = "") -> None:
    LiveTradingAuditEvent.objects.create(user=user, action=action, detail=detail[:200])


class LiveTradingService:

    # ------------------------------------------------------------------
    # Reading the state
    # ------------------------------------------------------------------

    @staticmethod
    def locked() -> bool:
        return bool(getattr(settings, "LIVE_TRADING_LOCKED", False))

    @staticmethod
    def master_enabled() -> bool:
        # The older environment flag still counts as turning the master on.
        if getattr(settings, "LIVE_TRADING_ENABLED", False) is True:
            return True
        return _control().enabled

    @staticmethod
    def armed_until(user, now: Optional[datetime] = None) -> Optional[datetime]:
        now = now or timezone.now()
        arming = (
            LiveTradingArming.objects.filter(
                user=user, disarmed_at__isnull=True, expires_at__gt=now
            )
            .order_by("-expires_at")
            .first()
        )
        return arming.expires_at if arming else None

    @classmethod
    def can_place(cls, user, now: Optional[datetime] = None) -> tuple[bool, str]:
        """(allowed, reason). The reason is shown to the user when blocked."""
        if cls.locked():
            return False, "Live trading is locked by the server."
        if not cls.master_enabled():
            return False, (
                "Live orders are not enabled on this installation. "
                "An administrator can turn them on in Settings."
            )
        if cls.armed_until(user, now) is None:
            return False, (
                "Live orders are not armed for you today. "
                "Arm them in Settings after reading the risk notice."
            )
        return True, ""

    @classmethod
    def state(cls, user, now: Optional[datetime] = None) -> dict:
        now = now or timezone.now()
        allowed, reason = cls.can_place(user, now)
        can_arm, arm_reason = cls._can_arm(user, now)
        until = cls.armed_until(user, now)
        return {
            "locked": cls.locked(),
            "master_enabled": cls.master_enabled(),
            "armed": until is not None,
            "armed_until": until.isoformat() if until else None,
            "can_place": allowed,
            "blocked_reason": reason,
            "can_arm": can_arm,
            "arm_blocked_reason": arm_reason,
            "is_admin": bool(user.is_staff),
            "confirm_phrase": CONFIRM_PHRASE,
            "disclaimer": {"version": DISCLAIMER_VERSION, "lines": DISCLAIMER_LINES},
        }

    # ------------------------------------------------------------------
    # Changing it
    # ------------------------------------------------------------------

    @classmethod
    def _can_arm(cls, user, now: datetime) -> tuple[bool, str]:
        if cls.locked():
            return False, "Live trading is locked by the server."
        if not cls.master_enabled():
            return False, "An administrator must enable live orders first."
        if not cls._zerodha_ready(user):
            return False, "Connect Zerodha and log in today before arming."
        if now.astimezone(IST).time() >= MARKET_CLOSE:
            return False, "The session has ended. Arm again before tomorrow's open."
        return True, ""

    @staticmethod
    def _zerodha_ready(user) -> bool:
        from ..repositories.zerodha_repository import ZerodhaConfigRepository

        config = ZerodhaConfigRepository.model.objects.filter(user=user).first()
        return bool(config and config.is_token_valid)

    @classmethod
    def arm(cls, user, phrase: str, now: Optional[datetime] = None) -> dict:
        """Arm for the rest of today's session. Raises ValueError with a user message."""
        now = now or timezone.now()
        if (phrase or "").strip() != CONFIRM_PHRASE:
            raise ValueError(f'Type "{CONFIRM_PHRASE}" exactly to arm live orders.')
        can_arm, reason = cls._can_arm(user, now)
        if not can_arm:
            raise ValueError(reason)

        local = now.astimezone(IST)
        expires = datetime.combine(local.date(), MARKET_CLOSE, tzinfo=IST)
        cls._close_open_armings(user, now)
        LiveTradingArming.objects.create(
            user=user,
            armed_at=now,
            expires_at=expires,
            disclaimer_version=DISCLAIMER_VERSION,
        )
        _log(user, "ARM", f"until {expires.isoformat()} · notice {DISCLAIMER_VERSION}")
        return cls.state(user, now)

    @classmethod
    def disarm(cls, user, now: Optional[datetime] = None) -> dict:
        now = now or timezone.now()
        closed = cls._close_open_armings(user, now)
        if closed:
            _log(user, "DISARM", "by the user")
        return cls.state(user, now)

    @staticmethod
    def _close_open_armings(user, now: datetime) -> int:
        return LiveTradingArming.objects.filter(
            user=user, disarmed_at__isnull=True, expires_at__gt=now
        ).update(disarmed_at=now)

    @classmethod
    def set_master(cls, user, enabled: bool, now: Optional[datetime] = None) -> dict:
        """Staff only. Turning it off also cancels everyone's arming."""
        if not user.is_staff:
            raise PermissionError("Only an administrator can change this.")
        now = now or timezone.now()
        control = _control()
        control.enabled = bool(enabled)
        control.changed_by = user
        control.save()
        if not enabled:
            LiveTradingArming.objects.filter(
                disarmed_at__isnull=True, expires_at__gt=now
            ).update(disarmed_at=now)
        _log(user, "MASTER_ON" if enabled else "MASTER_OFF")
        return cls.state(user, now)
