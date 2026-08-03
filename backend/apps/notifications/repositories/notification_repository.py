from django.db import models
from typing import Optional
from django.db.models import QuerySet
from django.utils import timezone
from shared.repositories import BaseRepository
from ..models import Alert, Notification, NotificationPreference


class NotificationPreferenceRepository(BaseRepository[NotificationPreference]):

    model = NotificationPreference

    @classmethod
    def get_for_user(cls, user) -> Optional[NotificationPreference]:
        """Return preferences for a user."""
        return cls.model.objects.filter(user=user).first()

    @classmethod
    def get_or_create_for_user(
        cls,
        user,
    ) -> tuple[NotificationPreference, bool]:
        """Get or create preferences for a user."""
        return cls.model.objects.get_or_create(
            user=user,
            defaults={
                "email_address": user.email,
            },
        )


class NotificationRepository(BaseRepository[Notification]):

    model = Notification

    @classmethod
    def get_for_user(
        cls,
        user,
        unread_only: bool = False,
        limit: int = 50,
    ) -> QuerySet[Notification]:
        """Return notifications for a user."""
        qs = cls.model.objects.filter(user=user)
        if unread_only:
            qs = qs.exclude(status="READ")
        return qs.order_by("-created_at")[:limit]

    @classmethod
    def get_unread_count(cls, user) -> int:
        """Return unread notification count."""
        return cls.model.objects.filter(
            user=user,
        ).exclude(status="READ").count()

    @classmethod
    def mark_read(cls, notification: Notification) -> Notification:
        """Mark a notification as read."""
        notification.status = "READ"
        notification.read_at = timezone.now()
        notification.save()
        return notification

    @classmethod
    def mark_all_read(cls, user) -> int:
        """Mark all notifications as read for a user."""
        return cls.model.objects.filter(
            user=user,
        ).exclude(status="READ").update(
            status="READ",
            read_at=timezone.now(),
        )

    @classmethod
    def get_by_type(
        cls,
        user,
        notification_type: str,
        limit: int = 20,
    ) -> QuerySet[Notification]:
        """Return notifications by type."""
        return cls.model.objects.filter(
            user=user,
            notification_type=notification_type,
        ).order_by("-created_at")[:limit]


class AlertRepository(BaseRepository[Alert]):

    model = Alert

    @classmethod
    def get_active(cls, user) -> QuerySet[Alert]:
        """Return active alerts for a user."""
        return cls.model.objects.filter(
            user=user,
            status="ACTIVE",
            is_active=True,
        ).order_by("-created_at")

    @classmethod
    def get_active_by_symbol(cls, symbol: str) -> QuerySet[Alert]:
        """Return all active alerts for a symbol."""
        return cls.model.objects.filter(
            symbol=symbol.upper(),
            status="ACTIVE",
            is_active=True,
        ).select_related("user")

    @classmethod
    def get_all_active(cls) -> QuerySet[Alert]:
        """Return all active alerts across all users."""
        now = timezone.now()
        return cls.model.objects.filter(
            status="ACTIVE",
            is_active=True,
        ).filter(
            models.Q(expires_at__isnull=True) |
            models.Q(expires_at__gt=now)
        ).select_related("user")

    @classmethod
    def trigger(
        cls,
        alert: Alert,
        triggered_value: float,
    ) -> Alert:
        """Mark an alert as triggered."""
        alert.status = "TRIGGERED" if not alert.repeat else "ACTIVE"
        alert.triggered_at = timezone.now()
        alert.triggered_value = triggered_value
        alert.current_value = triggered_value
        alert.save()
        return alert