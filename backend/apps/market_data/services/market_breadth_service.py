"""
backend/apps/market_data/services/market_breadth_service.py

New file.

Computes real Nifty 50 market breadth (advances vs. declines) from live
quotes across the actual 50 constituent stocks — not scraped from any
website, just batch-quoting stocks Athena already has imported as
Instruments and counting green vs. red.

Constituent list: Nifty 50 is rebalanced semi-annually (cutoffs 31 Jan /
31 Jul) by NSE Indices. The list below is a snapshot as of the 8 Dec 2025
rebalance (source: NSE Indices' own published constituent list). This
WILL go stale over time — NSE publishes the live, always-current list at
https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv if you
want to replace this hardcoded snapshot with a periodic live fetch later.
Until then, review/update this list after each semi-annual rebalance.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Snapshot as of 8 Dec 2025 — see module docstring for staleness caveat.
NIFTY50_CONSTITUENTS = [
    "ADANIENT",
    "ADANIPORTS",
    "APOLLOHOSP",
    "ASIANPAINT",
    "AXISBANK",
    "BAJAJ-AUTO",
    "BAJFINANCE",
    "BAJAJFINSV",
    "BEL",
    "BHARTIARTL",
    "CIPLA",
    "COALINDIA",
    "DRREDDY",
    "EICHERMOT",
    "ETERNAL",
    "GRASIM",
    "HCLTECH",
    "HDFCBANK",
    "HDFCLIFE",
    "HINDALCO",
    "HINDUNILVR",
    "ICICIBANK",
    "INDIGO",
    "INFY",
    "ITC",
    "JIOFIN",
    "JSWSTEEL",
    "KOTAKBANK",
    "LT",
    "M&M",
    "MARUTI",
    "MAXHEALTH",
    "NESTLEIND",
    "NTPC",
    "ONGC",
    "POWERGRID",
    "RELIANCE",
    "SBILIFE",
    "SHRIRAMFIN",
    "SBIN",
    "SUNPHARMA",
    "TCS",
    "TATACONSUM",
    "TMPV",
    "TATASTEEL",
    "TECHM",
    "TITAN",
    "TRENT",
    "ULTRACEMCO",
    "WIPRO",
]

# Bank Nifty has 12 constituents. Snapshot only: NSE Indices rebalances it
# semi-annually, so verify against the published list
# (https://www.niftyindices.com/IndexConstituent/ind_niftybanklist.csv)
# before relying on it. Unresolvable symbols are skipped and reported via
# sample_size/of_total, never counted.
BANKNIFTY_CONSTITUENTS = [
    "AUBANK",
    "AXISBANK",
    "BANKBARODA",
    "FEDERALBNK",
    "HDFCBANK",
    "ICICIBANK",
    "IDFCFIRSTB",
    "INDUSINDBK",
    "KOTAKBANK",
    "PNB",
    "SBIN",
    "CANBK",
]

CONSTITUENTS = {
    "NIFTY": NIFTY50_CONSTITUENTS,
    "BANKNIFTY": BANKNIFTY_CONSTITUENTS,
}

# Minimum share of constituents that must return a quote for a clean reading.
MIN_SAMPLE_FRACTION = 0.8


class MarketBreadthService:
    """
    Computes Nifty 50 advance/decline breadth from live quotes. Never
    fabricates: if fewer than 80% of constituents
    resolve to real quotes, the result is flagged low-confidence rather
    than presented as a clean 50-stock reading.
    """

    @classmethod
    def get_breadth(cls, user, index: str = "NIFTY") -> Optional[dict]:
        constituents = CONSTITUENTS.get(str(index).upper())
        if not user or not constituents:
            return None

        try:
            from ..repositories.instrument_repository import InstrumentRepository
            from .market_service import MarketService

            # Pre-filter to symbols that actually resolve to a real
            # Instrument — a single unresolvable symbol would otherwise
            # raise inside get_quotes() and kill the whole batch.
            resolvable = [
                s
                for s in constituents
                if InstrumentRepository.get_by_symbol(s) is not None
            ]
            if not resolvable:
                return None

            market = MarketService(user=user)
            quotes = market.quotes(resolvable)

            advances = declines = unchanged = 0
            for q in quotes:
                if not q:
                    continue
                change_pct = q.get("change_percent")
                if change_pct is None:
                    continue
                change_pct = float(change_pct)
                if change_pct > 0:
                    advances += 1
                elif change_pct < 0:
                    declines += 1
                else:
                    unchanged += 1

            sample_size = advances + declines + unchanged
            if sample_size == 0:
                return None

            return {
                "advances": advances,
                "declines": declines,
                "unchanged": unchanged,
                "sample_size": sample_size,
                "of_total": len(constituents),
                "index": str(index).upper(),
                "low_confidence": sample_size < len(constituents) * MIN_SAMPLE_FRACTION,
            }
        except Exception as e:
            logger.error(f"MarketBreadthService error: {e}")
            return None
