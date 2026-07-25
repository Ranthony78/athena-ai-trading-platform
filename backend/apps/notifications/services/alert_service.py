import logging
from decimal import Decimal

from django.utils import timezone

from apps.market_data.providers.provider_factory import ProviderFactory

from ..models import Alert, Notification
from ..repositories.notification_repository import (
    AlertRepository,
    NotificationRepository,
)
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class AlertService:
    """
    Manages price and signal alerts.
    Checks alert conditions against live market data.
    """

    def __init__(self) -> None:
        self.provider = ProviderFactory.get_provider()

    # ------------------------------------------------------------------
    # Alert CRUD
    # ------------------------------------------------------------------

    @staticmethod
    def get_alerts(user):
        """Return active alerts for a user."""
        return AlertRepository.get_active(user)

    @staticmethod
    def create_alert(user, data: dict) -> Alert:
        """Create a new price alert."""
        data["user"] = user
        data["symbol"] = data["symbol"].upper()
        return AlertRepository.create(**data)

    @staticmethod
    def cancel_alert(user, alert_id: int) -> dict:
        """Cancel an active alert."""
        alert = AlertRepository.first(id=alert_id, user=user)
        if not alert:
            return {"success": False, "message": "Alert not found."}

        alert.status = "CANCELLED"
        alert.save()
        return {"success": True, "message": "Alert cancelled."}

    # ------------------------------------------------------------------
    # Alert Checking
    # ------------------------------------------------------------------

    def check_all_alerts(self) -> int:
        """
        Check all active alerts against current prices.
        Called periodically by the market engine.
        Returns count of triggered alerts.
        """
        alerts = AlertRepository.get_all_active()
        triggered = 0

        for alert in alerts:
            try:
                if self._check_alert(alert):
                    triggered += 1
            except Exception as e:
                logger.error(
                    f"AlertService: error checking alert {alert.id}: {e}"
                )

        return triggered

    def _check_alert(self, alert: Alert) -> bool:
        """
        Check if a single alert condition is met.
        Returns True if triggered.
        """
        try:
            quote = self.provider.get_quote(alert.symbol)
            if not quote:
                return False

            current_price = float(quote.get("ltp", 0))
            target = float(alert.target_value)

            # Update current value
            Alert.objects.filter(pk=alert.pk).update(
                current_value=Decimal(str(current_price))
            )

            triggered = False

            if alert.alert_type == "PRICE_ABOVE" and current_price >= target:
                triggered = True
            elif alert.alert_type == "PRICE_BELOW" and current_price <= target:
                triggered = True
            elif alert.alert_type == "PRICE_CROSS":
                prev = float(alert.current_value)
                triggered = (
                    (prev < target <= current_price) or
                    (prev > target >= current_price)
                )

            if triggered:
                AlertRepository.trigger(alert, current_price)
                self._send_alert_notification(alert, current_price)
                return True

            return False

        except Exception as e:
            logger.error(f"Alert check error [{alert.id}]: {e}")
            return False

    def _send_alert_notification(
        self,
        alert: Alert,
        current_price: float,
    ) -> None:
        """Send notification when alert is triggered."""
        user = alert.user
        title = f"Alert: {alert.symbol} {alert.alert_type}"
        message = (
            alert.message or
            f"{alert.symbol} hit {alert.alert_type} target "
            f"₹{alert.target_value} | Current: ₹{current_price}"
        )

        NotificationService.send(
            user=user,
            notification_type="PRICE_ALERT",
            title=title,
            message=message,
            data={
                "symbol": alert.symbol,
                "alert_type": alert.alert_type,
                "target": float(alert.target_value),
                "current": current_price,
            },
        )