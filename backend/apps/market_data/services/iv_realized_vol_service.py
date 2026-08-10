"""
backend/apps/market_data/services/iv_realized_vol_service.py

New file.

The honest, immediately-buildable alternative to "IV percentile" (see
this file's design discussion): Athena has never persisted historical IV
snapshots — IV is computed live via Black-Scholes on each call, never
stored over time — so there is no real history to rank current IV
against yet. Faking a percentile from data that doesn't exist would be
exactly the fabrication pattern this project has spent significant
effort removing.

Instead, this computes the standard professional alternative: current
ATM IV vs. REALIZED volatility, calculated from the real 5-year daily
candle history Athena already has (same data HistoricalDistributionService
uses). This is a genuine, well-established options concept — IV richer
than realized vol suggests options are relatively expensive; IV below
realized vol suggests they're relatively cheap. Not a percentile, but
real, computable today, zero invention.

Once Athena starts persisting IV snapshots going forward (a natural
follow-up — snapshot ATM IV on each analysis run into a new model), a
genuine percentile becomes possible after enough history accumulates.
Until then, this is the correct honest substitute.
"""

import logging
import math
from typing import Optional

logger = logging.getLogger(__name__)

# Windows over which realized volatility is computed, in trading days.
RV_WINDOWS = {"20d": 20, "60d": 60}

# Heuristic thresholds for the rich/cheap/fair classification. These are
# a commonly-used rule of thumb (IV/HV ratio), not a statistically
# derived cutoff — documented as a heuristic, not presented as a
# calculated probability.
RICH_THRESHOLD = 1.2
CHEAP_THRESHOLD = 0.8


class IVRealizedVolatilityService:
    """
    Compares real current ATM IV against real realized volatility
    computed from actual historical daily candles. Never fabricates —
    returns None for any window where there isn't enough price history.
    """

    @classmethod
    def get_iv_vs_realized(cls, symbol: str, current_atm_iv: Optional[float]) -> Optional[dict]:
        if current_atm_iv is None:
            return None

        try:
            from .historical_distribution_service import HistoricalDistributionService

            candles = HistoricalDistributionService._daily_candles(symbol, lookback=90)
            if len(candles) < 21:
                return None

            closes = [float(c.close) for c in candles if c.close]

            windows_out = {}
            for label, window in RV_WINDOWS.items():
                if len(closes) < window + 1:
                    windows_out[label] = None
                    continue

                recent = closes[-(window + 1):]
                log_returns = [
                    math.log(recent[i] / recent[i - 1])
                    for i in range(1, len(recent))
                    if recent[i - 1] > 0
                ]
                if len(log_returns) < 2:
                    windows_out[label] = None
                    continue

                mean_ret = sum(log_returns) / len(log_returns)
                variance = sum((r - mean_ret) ** 2 for r in log_returns) / (len(log_returns) - 1)
                daily_std = math.sqrt(variance)
                annualized_rv_pct = round(daily_std * math.sqrt(252) * 100, 2)

                windows_out[label] = {
                    "realized_vol_pct": annualized_rv_pct,
                    "iv_hv_ratio": round(current_atm_iv / annualized_rv_pct, 2) if annualized_rv_pct else None,
                }

            primary = windows_out.get("20d")
            classification = None
            if primary and primary.get("iv_hv_ratio") is not None:
                ratio = primary["iv_hv_ratio"]
                if ratio >= RICH_THRESHOLD:
                    classification = "IV rich vs. realized vol"
                elif ratio <= CHEAP_THRESHOLD:
                    classification = "IV cheap vs. realized vol"
                else:
                    classification = "IV roughly fair vs. realized vol"

            return {
                "current_atm_iv_pct": current_atm_iv,
                "windows": windows_out,
                "classification": classification,
                "note": (
                    "Real IV vs. realized-volatility comparison, not a percentile "
                    "(no historical IV time series is stored yet). Ratio thresholds "
                    "are a standard heuristic, not a calculated probability."
                ),
            }
        except Exception as e:
            logger.error(f"IVRealizedVolatilityService error [{symbol}]: {e}")
            return None