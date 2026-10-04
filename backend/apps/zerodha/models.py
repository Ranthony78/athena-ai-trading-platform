from django.contrib.auth import get_user_model
from django.db import models

from shared.models import BaseModel

User = get_user_model()


class ZerodhaConfig(BaseModel):
    """
    Zerodha API configuration per user.
    Stores API key and access token for Kite Connect.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="zerodha_config",
    )

    api_key = models.CharField(
        max_length=100,
        blank=True,
        help_text="Zerodha Kite Connect API key.",
    )
    api_secret = models.CharField(
        max_length=100,
        blank=True,
        help_text="Zerodha Kite Connect API secret.",
    )
    access_token = models.CharField(
        max_length=500,
        blank=True,
        help_text="Current active access token.",
    )
    request_token = models.CharField(
        max_length=500,
        blank=True,
        help_text="Request token from login redirect.",
    )

    is_connected = models.BooleanField(default=False)
    connected_at = models.DateTimeField(null=True, blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)

    # MCP endpoint
    mcp_url = models.URLField(
        default="https://mcp.kite.trade/mcp",
        help_text="Zerodha MCP server URL.",
    )

    class Meta:
        db_table = "zerodha_configs"

    def __str__(self) -> str:
        return f"{self.user.username} — Zerodha Config"

    @property
    def is_token_valid(self) -> bool:
        """Check if access token is still valid."""
        if not self.access_token or not self.is_connected:
            return False
        if not self.token_expires_at:
            return True
        from django.utils import timezone

        return timezone.now() < self.token_expires_at


class ZerodhaSession(BaseModel):
    """
    Tracks Zerodha login sessions.
    Records each authentication event.
    """

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("EXPIRED", "Expired"),
        ("REVOKED", "Revoked"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="zerodha_sessions",
    )
    config = models.ForeignKey(
        ZerodhaConfig,
        on_delete=models.CASCADE,
        related_name="sessions",
    )

    access_token = models.CharField(max_length=500)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE",
        db_index=True,
    )

    login_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    # Profile snapshot at login
    zerodha_user_id = models.CharField(max_length=20, blank=True)
    zerodha_username = models.CharField(max_length=100, blank=True)
    broker = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    user_type = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "zerodha_sessions"
        ordering = ["-login_at"]

    def __str__(self) -> str:
        return f"{self.user.username} | " f"{self.zerodha_user_id} | " f"{self.status}"


class LiveTradingControl(BaseModel):
    """
    Installation-wide master switch for real broker orders. One row; only
    staff can change it from the app. Off by default.
    """

    enabled = models.BooleanField(default=False)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        db_table = "zerodha_live_trading_control"

    def __str__(self) -> str:
        return f"Live trading master switch: {'ON' if self.enabled else 'OFF'}"


class LiveTradingArming(BaseModel):
    """
    A user's own, time-limited permission to send real orders. It lapses at
    the end of the trading day and is cancelled when the master switch goes
    off.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="live_trading_armings",
    )
    armed_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    disarmed_at = models.DateTimeField(null=True, blank=True)
    disclaimer_version = models.CharField(max_length=40)

    class Meta:
        db_table = "zerodha_live_trading_armings"
        ordering = ["-armed_at"]
        indexes = [models.Index(fields=["user", "expires_at"])]

    def __str__(self) -> str:
        return f"{self.user.username} armed until {self.expires_at}"


class LiveTradingAuditEvent(BaseModel):
    """Who changed live-trading permissions, and when."""

    ACTION_CHOICES = [
        ("MASTER_ON", "Master switch turned on"),
        ("MASTER_OFF", "Master switch turned off"),
        ("ARM", "User armed live orders"),
        ("DISARM", "User disarmed live orders"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
    )
    action = models.CharField(max_length=12, choices=ACTION_CHOICES)
    detail = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "zerodha_live_trading_audit"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.action} by {self.user} at {self.created_at}"
