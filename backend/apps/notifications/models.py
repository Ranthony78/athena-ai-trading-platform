from django.db import models
from django.contrib.auth import get_user_model

from shared.models import BaseModel

User = get_user_model()


class NotificationPreference(BaseModel):
    """
    User notification preferences.
    Controls which channels and events trigger notifications.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )

    # Channels
    email_enabled = models.BooleanField(default=True)
    telegram_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=False)

    # Telegram
    telegram_chat_id = models.CharField(max_length=50, blank=True)
    telegram_username = models.CharField(max_length=100, blank=True)

    # Email
    email_address = models.EmailField(blank=True)

    # Events
    notify_ai_signals = models.BooleanField(default=True)
    notify_strategy_signals = models.BooleanField(default=True)
    notify_price_alerts = models.BooleanField(default=True)
    notify_trade_execution = models.BooleanField(default=True)
    notify_market_open = models.BooleanField(default=False)
    notify_market_close = models.BooleanField(default=False)
    notify_daily_summary = models.BooleanField(default=True)

    # Quiet hours (IST)
    quiet_hours_enabled = models.BooleanField(default=True)
    quiet_from = models.TimeField(default="22:00")
    quiet_until = models.TimeField(default="08:00")

    class Meta:
        db_table = "notification_preferences"

    def __str__(self) -> str:
        return f"{self.user.username} — Notification Preferences"


class Notification(BaseModel):
    """
    A notification record.
    Tracks every notification sent to a user.
    """

    TYPE_CHOICES = [
        ("AI_SIGNAL", "AI Signal"),
        ("STRATEGY_SIGNAL", "Strategy Signal"),
        ("PRICE_ALERT", "Price Alert"),
        ("TRADE_EXECUTION", "Trade Execution"),
        ("MARKET_OPEN", "Market Open"),
        ("MARKET_CLOSE", "Market Close"),
        ("DAILY_SUMMARY", "Daily Summary"),
        ("SYSTEM", "System"),
        ("INFO", "Info"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
    ]

    CHANNEL_CHOICES = [
        ("IN_APP", "In App"),
        ("EMAIL", "Email"),
        ("TELEGRAM", "Telegram"),
        ("PUSH", "Push"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SENT", "Sent"),
        ("READ", "Read"),
        ("FAILED", "Failed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        db_index=True,
    )
    channel = models.CharField(
        max_length=10,
        choices=CHANNEL_CHOICES,
        default="IN_APP",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
    )

    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(
        default=dict,
        help_text="Additional structured data for the notification.",
    )

    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    failed_reason = models.TextField(blank=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "notification_type"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} | {self.notification_type} | {self.status}"

    @property
    def is_read(self) -> bool:
        return self.status == "READ"


class Alert(BaseModel):
    """
    A price or signal alert set by the user.
    Triggers a notification when the condition is met.
    """

    ALERT_TYPE_CHOICES = [
        ("PRICE_ABOVE", "Price Above"),
        ("PRICE_BELOW", "Price Below"),
        ("PRICE_CROSS", "Price Crossover"),
        ("RSI_ABOVE", "RSI Above"),
        ("RSI_BELOW", "RSI Below"),
        ("VOLUME_SPIKE", "Volume Spike"),
        ("SIGNAL_BUY", "Buy Signal"),
        ("SIGNAL_SELL", "Sell Signal"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("TRIGGERED", "Triggered"),
        ("EXPIRED", "Expired"),
        ("CANCELLED", "Cancelled"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="alerts",
    )

    symbol = models.CharField(max_length=50, db_index=True)
    alert_type = models.CharField(
        max_length=15,
        choices=ALERT_TYPE_CHOICES,
        db_index=True,
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE",
        db_index=True,
    )

    # Condition
    target_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Price or indicator value to trigger alert.",
    )
    current_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Last checked value.",
    )

    # Notification
    message = models.CharField(
        max_length=300,
        blank=True,
        help_text="Custom alert message.",
    )
    notify_email = models.BooleanField(default=True)
    notify_telegram = models.BooleanField(default=False)

    # Trigger info
    triggered_at = models.DateTimeField(null=True, blank=True)
    triggered_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # Repeat
    repeat = models.BooleanField(
        default=False,
        help_text="Re-arm alert after triggering.",
    )
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "alerts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["symbol", "status"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.symbol} | {self.alert_type} @ "
            f"{self.target_value} [{self.status}]"
        )