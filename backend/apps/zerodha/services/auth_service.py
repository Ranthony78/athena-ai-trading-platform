import logging
from datetime import timedelta

from django.utils import timezone

from ..models import ZerodhaConfig, ZerodhaSession
from ..repositories.zerodha_repository import (
    ZerodhaConfigRepository,
    ZerodhaSessionRepository,
)

logger = logging.getLogger(__name__)


class ZerodhaAuthService:
    """
    Manages Zerodha authentication via Kite Connect.
    Handles login URL generation, token exchange, and logout.
    """

    KITE_LOGIN_URL = "https://kite.zerodha.com/connect/login"
    KITE_TOKEN_URL = "https://api.kite.trade/session/token"

    def __init__(self, user) -> None:
        self.user = user
        self.config, _ = ZerodhaConfigRepository.get_or_create_for_user(user)

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def get_login_url(self) -> str:
        """
        Generate the Kite Connect login URL.
        User visits this URL to authenticate with Zerodha.
        """
        if not self.config.api_key:
            raise ValueError("Zerodha API key not configured.")

        return (
            f"{self.KITE_LOGIN_URL}"
            f"?api_key={self.config.api_key}"
            f"&v=3"
        )

    def exchange_token(self, request_token: str) -> dict:
        """
        Exchange request token for access token.
        Called after user completes Zerodha login.

        Args:
            request_token: Token received from Kite Connect redirect

        Returns:
            Session data dict
        """
        if not self.config.api_key or not self.config.api_secret:
            raise ValueError("Zerodha API key/secret not configured.")

        try:
            import hashlib
            import httpx

            # Generate checksum
            checksum_input = (
                self.config.api_key +
                request_token +
                self.config.api_secret
            )
            checksum = hashlib.sha256(
                checksum_input.encode()
            ).hexdigest()

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.KITE_TOKEN_URL,
                    data={
                        "api_key": self.config.api_key,
                        "request_token": request_token,
                        "checksum": checksum,
                    },
                )
                response.raise_for_status()
                data = response.json()

            if data.get("status") != "success":
                raise ValueError(
                    f"Token exchange failed: {data.get('message', 'Unknown error')}"
                )

            session_data = data["data"]
            access_token = session_data["access_token"]

            # Token expires at midnight IST
            expires_at = (
                timezone.now().replace(
                    hour=23, minute=59, second=59
                )
            )

            # Save config
            ZerodhaConfigRepository.save_access_token(
                config=self.config,
                access_token=access_token,
                expires_at=expires_at,
            )

            # Revoke old sessions
            ZerodhaSessionRepository.revoke_all_for_user(self.user)

            # Create new session
            ZerodhaSession.objects.create(
                user=self.user,
                config=self.config,
                access_token=access_token,
                status="ACTIVE",
                expires_at=expires_at,
                zerodha_user_id=session_data.get("user_id", ""),
                zerodha_username=session_data.get("user_name", ""),
                broker=session_data.get("broker", "ZERODHA"),
                email=session_data.get("email", ""),
                user_type=session_data.get("user_type", ""),
            )

            logger.info(
                f"ZerodhaAuthService: login successful for "
                f"{self.user.username} "
                f"({session_data.get('user_id', '')})"
            )

            return {
                "success": True,
                "user_id": session_data.get("user_id"),
                "user_name": session_data.get("user_name"),
                "email": session_data.get("email"),
                "broker": session_data.get("broker"),
                "connected_at": timezone.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"ZerodhaAuthService token exchange error: {e}")
            raise

    def logout(self) -> dict:
        """Logout and revoke access token."""
        try:
            ZerodhaConfigRepository.revoke_token(self.config)
            ZerodhaSessionRepository.revoke_all_for_user(self.user)

            logger.info(
                f"ZerodhaAuthService: logout for {self.user.username}"
            )

            return {"success": True, "message": "Logged out from Zerodha."}

        except Exception as e:
            logger.error(f"ZerodhaAuthService logout error: {e}")
            return {"success": False, "message": str(e)}

    def get_status(self) -> dict:
        """Return current connection status."""
        config = self.config
        session = ZerodhaSessionRepository.get_active_for_user(self.user)

        return {
            "is_connected": config.is_connected,
            "is_token_valid": config.is_token_valid,
            "connected_at": (
                config.connected_at.isoformat()
                if config.connected_at else None
            ),
            "token_expires_at": (
                config.token_expires_at.isoformat()
                if config.token_expires_at else None
            ),
            "zerodha_user_id": (
                session.zerodha_user_id if session else None
            ),
            "zerodha_username": (
                session.zerodha_username if session else None
            ),
            "mcp_url": config.mcp_url,
        }

    def save_config(self, data: dict) -> ZerodhaConfig:
        """Save API key and secret."""
        if "api_key" in data:
            self.config.api_key = data["api_key"]
        if "api_secret" in data:
            self.config.api_secret = data["api_secret"]
        if "mcp_url" in data:
            self.config.mcp_url = data["mcp_url"]
        self.config.save()
        return self.config