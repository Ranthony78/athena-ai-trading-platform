import logging

from django.utils import timezone

from ..models import Notification, NotificationPreference
from ..repositories.notification_repository import (
    NotificationPreferenceRepository,
    NotificationRepository,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Core notification service.
    Creates in-app notifications and dispatches
    to external channels (email, Telegram).
    """

    # ------------------------------------------------------------------
    # Send notification
    # ------------------------------------------------------------------

    @staticmethod
    def send(
        user,
        notification_type: str,
        title: str,
        message: str,
        data: dict = None,
        channels: list[str] = None,
    ) -> Notification:
        """
        Create and dispatch a notification.

        Args:
            user:              Recipient user
            notification_type: Type from Notification.TYPE_CHOICES
            title:             Short title
            message:           Full message body
            data:              Additional structured data
            channels:          Override channels (default: from preferences)

        Returns:
            The created in-app Notification instance
        """
        # Always create in-app notification
        notification = NotificationRepository.create(
            user=user,
            notification_type=notification_type,
            channel="IN_APP",
            status="SENT",
            title=title,
            message=message,
            data=data or {},
            sent_at=timezone.now(),
        )

        # Get preferences
        prefs, _ = NotificationPreferenceRepository.get_or_create_for_user(user)

        # Check quiet hours
        if NotificationService._is_quiet_hours(prefs):
            logger.info(
                f"NotificationService: quiet hours — "
                f"skipping external channels for {user.username}"
            )
            return notification

        # Dispatch to external channels
        dispatch_channels = channels or NotificationService._get_channels(
            prefs=prefs,
            notification_type=notification_type,
        )

        for channel in dispatch_channels:
            try:
                NotificationService._dispatch(
                    user=user,
                    prefs=prefs,
                    channel=channel,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    data=data or {},
                )
            except Exception as e:
                logger.error(
                    f"NotificationService dispatch error "
                    f"[{channel}|{user.username}]: {e}"
                )

        return notification

    @staticmethod
    def send_bulk(
        users,
        notification_type: str,
        title: str,
        message: str,
        data: dict = None,
    ) -> int:
        """Send the same notification to multiple users."""
        count = 0
        for user in users:
            try:
                NotificationService.send(
                    user=user,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    data=data,
                )
                count += 1
            except Exception as e:
                logger.error(
                    f"NotificationService bulk error [{user.username}]: {e}"
                )
        return count

    # ------------------------------------------------------------------
    # Read / Management
    # ------------------------------------------------------------------

    @staticmethod
    def get_notifications(
        user,
        unread_only: bool = False,
        limit: int = 50,
    ):
        """Return notifications for a user."""
        return NotificationRepository.get_for_user(
            user=user,
            unread_only=unread_only,
            limit=limit,
        )

    @staticmethod
    def get_unread_count(user) -> int:
        """Return unread notification count."""
        return NotificationRepository.get_unread_count(user)

    @staticmethod
    def mark_read(notification_id: int, user) -> dict:
        """Mark a notification as read."""
        notification = NotificationRepository.first(
            id=notification_id,
            user=user,
        )
        if not notification:
            return {"success": False, "message": "Notification not found."}

        NotificationRepository.mark_read(notification)
        return {"success": True}

    @staticmethod
    def mark_all_read(user) -> int:
        """Mark all notifications as read."""
        return NotificationRepository.mark_all_read(user)

    # ------------------------------------------------------------------
    # Preferences
    # ------------------------------------------------------------------

    @staticmethod
    def get_preferences(user) -> NotificationPreference:
        """Get or create notification preferences for a user."""
        prefs, _ = NotificationPreferenceRepository.get_or_create_for_user(user)
        return prefs

    @staticmethod
    def update_preferences(user, data: dict) -> NotificationPreference:
        """Update notification preferences."""
        prefs, _ = NotificationPreferenceRepository.get_or_create_for_user(user)
        return NotificationPreferenceRepository.update(prefs, **data)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_channels(
        prefs: NotificationPreference,
        notification_type: str,
    ) -> list[str]:
        """Determine which external channels to dispatch to."""
        channels = []

        event_map = {
            "AI_SIGNAL": prefs.notify_ai_signals,
            "STRATEGY_SIGNAL": prefs.notify_strategy_signals,
            "PRICE_ALERT": prefs.notify_price_alerts,
            "TRADE_EXECUTION": prefs.notify_trade_execution,
            "MARKET_OPEN": prefs.notify_market_open,
            "MARKET_CLOSE": prefs.notify_market_close,
            "DAILY_SUMMARY": prefs.notify_daily_summary,
        }

        if not event_map.get(notification_type, True):
            return []

        if prefs.email_enabled and prefs.email_address:
            channels.append("EMAIL")

        if prefs.telegram_enabled and prefs.telegram_chat_id:
            channels.append("TELEGRAM")

        return channels

    @staticmethod
    def _is_quiet_hours(prefs: NotificationPreference) -> bool:
        """Check if current time is within quiet hours."""
        if not prefs.quiet_hours_enabled:
            return False

        from zoneinfo import ZoneInfo
        from datetime import datetime

        now = datetime.now(tz=ZoneInfo("Asia/Kolkata")).time()
        quiet_from = prefs.quiet_from
        quiet_until = prefs.quiet_until

        if quiet_from <= quiet_until:
            return quiet_from <= now <= quiet_until
        else:
            return now >= quiet_from or now <= quiet_until

    @staticmethod
    def _dispatch(
        user,
        prefs: NotificationPreference,
        channel: str,
        notification_type: str,
        title: str,
        message: str,
        data: dict,
    ) -> None:
        """Dispatch to a specific external channel."""

        if channel == "EMAIL":
            from .email_service import EmailService
            EmailService.send(
                to_email=prefs.email_address or user.email,
                subject=title,
                message=message,
            )

        elif channel == "TELEGRAM":
            from .telegram_service import TelegramService
            service = TelegramService()
            service.send(
                chat_id=prefs.telegram_chat_id,
                message=f"*{title}*\n\n{message}",
            )