import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class TelegramService:
    """
    Sends notifications via Telegram Bot API.
    Requires TELEGRAM_BOT_TOKEN in settings.
    """

    API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self) -> None:
        self.token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        if not self.token:
            logger.warning("TelegramService: TELEGRAM_BOT_TOKEN not set.")

    def send(
        self,
        chat_id: str,
        message: str,
        parse_mode: str = "Markdown",
    ) -> bool:
        """
        Send a Telegram message to a chat ID.

        Returns True if sent successfully.
        """
        if not self.token:
            logger.warning("TelegramService: no token configured.")
            return False

        if not chat_id:
            logger.warning("TelegramService: no chat_id provided.")
            return False

        url = self.API_URL.format(token=self.token)

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    url,
                    json={
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": parse_mode,
                    },
                )
                response.raise_for_status()
                logger.info(f"TelegramService: sent to {chat_id}")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(
                f"TelegramService HTTP error: "
                f"{e.response.status_code} — {e.response.text}"
            )
            return False
        except Exception as e:
            logger.error(f"TelegramService error: {e}")
            return False

    def send_signal(
        self,
        chat_id: str,
        symbol: str,
        signal: str,
        confidence: int,
        price: float,
        notes: str = "",
    ) -> bool:
        """Send a formatted signal notification."""
        emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "⚪"
        message = (
            f"{emoji} *Athena AI Signal*\n\n"
            f"*Symbol:* {symbol}\n"
            f"*Signal:* {signal}\n"
            f"*Confidence:* {confidence}%\n"
            f"*Price:* ₹{price}\n"
            f"*Notes:* {notes[:200] if notes else 'N/A'}\n\n"
            f"_This is a research notification — not financial advice._"
        )
        return self.send(chat_id, message)

    def send_price_alert(
        self,
        chat_id: str,
        symbol: str,
        alert_type: str,
        target: float,
        current: float,
    ) -> bool:
        """Send a price alert notification."""
        message = (
            f"🔔 *Price Alert Triggered*\n\n"
            f"*Symbol:* {symbol}\n"
            f"*Type:* {alert_type}\n"
            f"*Target:* ₹{target}\n"
            f"*Current:* ₹{current}"
        )
        return self.send(chat_id, message)

    def send_daily_summary(
        self,
        chat_id: str,
        summary: dict,
    ) -> bool:
        """Send daily trading summary."""
        pnl = summary.get("today_pnl", 0)
        pnl_emoji = "📈" if float(pnl) >= 0 else "📉"
        message = (
            f"{pnl_emoji} *Athena Daily Summary*\n\n"
            f"*Date:* {summary.get('date', 'Today')}\n"
            f"*Today PnL:* ₹{pnl}\n"
            f"*Trades:* {summary.get('trades', 0)}\n"
            f"*AI Signals:* {summary.get('ai_signals', 0)}\n"
            f"*Strategy Signals:* {summary.get('strategy_signals', 0)}"
        )
        return self.send(chat_id, message)