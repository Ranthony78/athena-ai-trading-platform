from django.db import models
from django.contrib.auth import get_user_model

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
        return (
            f"{self.user.username} | "
            f"{self.zerodha_user_id} | "
            f"{self.status}"
        )