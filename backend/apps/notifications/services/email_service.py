import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class EmailService:
    """
    Handles email notifications.
    Uses Django's built-in email backend.
    """

    @staticmethod
    def send(
        to_email: str,
        subject: str,
        message: str,
        html_message: str = None,
    ) -> bool:
        """
        Send an email notification.

        Returns True if sent successfully.
        """
        if not to_email:
            logger.warning("EmailService: no recipient email.")
            return False

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(
                    settings,
                    "DEFAULT_FROM_EMAIL",
                    "noreply@athena.ai",
                ),
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"EmailService: sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"EmailService error: {e}")
            return False

    @staticmethod
    def send_signal_notification(
        to_email: str,
        symbol: str,
        signal: str,
        confidence: int,
        price: float,
        notes: str = "",
    ) -> bool:
        """Send an AI signal notification email."""
        subject = f"Athena AI Signal: {signal} {symbol}"
        message = (
            f"Signal: {signal}\n"
            f"Symbol: {symbol}\n"
            f"Confidence: {confidence}%\n"
            f"Price: ₹{price}\n"
            f"Notes: {notes}\n\n"
            f"This is an automated research notification from Athena AI."
        )
        return EmailService.send(to_email, subject, message)

    @staticmethod
    def send_price_alert(
        to_email: str,
        symbol: str,
        alert_type: str,
        target: float,
        current: float,
    ) -> bool:
        """Send a price alert email."""
        subject = f"Athena Alert: {symbol} {alert_type}"
        message = (
            f"Price Alert Triggered!\n\n"
            f"Symbol: {symbol}\n"
            f"Alert Type: {alert_type}\n"
            f"Target: ₹{target}\n"
            f"Current Price: ₹{current}\n\n"
            f"This is an automated alert from Athena AI."
        )
        return EmailService.send(to_email, subject, message)

    @staticmethod
    def send_daily_summary(
        to_email: str,
        user_name: str,
        summary: dict,
    ) -> bool:
        """Send daily trading summary email."""
        subject = f"Athena Daily Summary — {summary.get('date', '')}"
        message = (
            f"Hi {user_name},\n\n"
            f"Here's your daily trading summary:\n\n"
            f"Today's PnL: ₹{summary.get('today_pnl', 0)}\n"
            f"Trades Taken: {summary.get('trades', 0)}\n"
            f"AI Signals: {summary.get('ai_signals', 0)}\n"
            f"Strategy Signals: {summary.get('strategy_signals', 0)}\n\n"
            f"Keep trading with discipline!\n"
            f"— Athena AI"
        )
        return EmailService.send(to_email, subject, message)