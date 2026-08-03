from typing import Optional

from django.utils import timezone

from shared.repositories import BaseRepository

from ..models import ZerodhaConfig, ZerodhaSession


class ZerodhaConfigRepository(BaseRepository[ZerodhaConfig]):

    model = ZerodhaConfig

    @classmethod
    def get_for_user(cls, user) -> Optional[ZerodhaConfig]:
        """Return Zerodha config for a user."""
        return cls.model.objects.filter(user=user).first()

    @classmethod
    def get_or_create_for_user(
        cls,
        user,
    ) -> tuple[ZerodhaConfig, bool]:
        """Get or create config for a user."""
        return cls.model.objects.get_or_create(user=user)

    @classmethod
    def save_access_token(
        cls,
        config: ZerodhaConfig,
        access_token: str,
        expires_at=None,
    ) -> ZerodhaConfig:
        """Save access token and mark as connected."""
        config.access_token = access_token
        config.is_connected = True
        config.connected_at = timezone.now()
        if expires_at:
            config.token_expires_at = expires_at
        config.save()
        return config

    @classmethod
    def revoke_token(cls, config: ZerodhaConfig) -> ZerodhaConfig:
        """Revoke access token and disconnect."""
        config.access_token = ""
        config.is_connected = False
        config.save()
        return config


class ZerodhaSessionRepository(BaseRepository[ZerodhaSession]):

    model = ZerodhaSession

    @classmethod
    def get_active_for_user(cls, user) -> Optional[ZerodhaSession]:
        """Return active session for a user."""
        return cls.model.objects.filter(
            user=user,
            status="ACTIVE",
        ).order_by("-login_at").first()

    @classmethod
    def revoke_all_for_user(cls, user) -> int:
        """Revoke all active sessions for a user."""
        return cls.model.objects.filter(
            user=user,
            status="ACTIVE",
        ).update(
            status="REVOKED",
            revoked_at=timezone.now(),
        )