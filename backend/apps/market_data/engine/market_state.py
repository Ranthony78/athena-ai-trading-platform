import logging
from datetime import datetime, time
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")

# NSE/BSE regular market session times (IST)
PRE_OPEN_START = time(9, 0)
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)


class MarketState:
    """
    Determines the current market session state based on IST clock time.

    This is intentionally clock-based only (no live feed dependency).
    It does NOT account for exchange holidays — there is no holiday
    calendar wired up yet, so a weekday during market hours is always
    reported as LIVE even on a declared trading holiday. Revisit once
    a holiday calendar/provider exists.
    """

    SESSION_PRE_OPEN = "PRE_OPEN"
    SESSION_LIVE = "LIVE"
    SESSION_CLOSED = "CLOSED"

    @staticmethod
    def now_ist() -> datetime:
        """Return current datetime in IST."""
        return datetime.now(IST)

    @classmethod
    def current_session(cls, now: datetime = None) -> str:
        """Return the current session name."""
        now = now or cls.now_ist()

        # Weekend — markets closed
        if now.weekday() >= 5:  # 5=Saturday, 6=Sunday
            return cls.SESSION_CLOSED

        current_time = now.time()

        if PRE_OPEN_START <= current_time < MARKET_OPEN:
            return cls.SESSION_PRE_OPEN
        if MARKET_OPEN <= current_time < MARKET_CLOSE:
            return cls.SESSION_LIVE
        return cls.SESSION_CLOSED

    @classmethod
    def session_info(cls) -> dict:
        """
        Return current session state for the /market/session/ endpoint.

        NOTE: is_live here reflects the clock-based market session only.
        It does NOT reflect whether a live data/WebSocket feed is
        connected — that engine (Django Channels consumers) has not
        been built yet. Treat is_live as "market is open", not as
        "we have a live data connection."
        """
        now = cls.now_ist()
        session = cls.current_session(now)

        return {
            "session": session,
            "is_live": session == cls.SESSION_LIVE,
            "time": now.strftime("%H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "weekday": now.strftime("%A"),
        }
