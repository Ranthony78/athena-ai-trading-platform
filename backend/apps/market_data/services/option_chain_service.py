"""
Real option chain analysis: implied volatility and Greeks via
Black-Scholes, plus chain-level analytics (PCR, max pain, ATM strike).

Built on top of MarketService.option_chain(), which already resolves
real strikes/OI/volume/LTP from the active provider (mock returns an
empty chain by design — this service needs real, seeded NFO
instruments and a working quote provider to produce anything).

Simplifying assumptions used throughout — documented here rather than
buried in the math, since they materially affect the numbers this
service produces:

- Risk-free rate is a fixed constant (see DEFAULT_RISK_FREE_RATE),
  not fetched from a live source.
- Time to expiry is calendar time in seconds until 15:30 IST on the
  expiry day, measured from when the quoted prices were current (see
  snapshot_signals_service.valuation_time). Whole-day counting made
  expiry-day IV and theta several times too large.
- European-style Black-Scholes pricing is used, the standard accepted
  approximation for NSE index options (they're European-exercise
  anyway for indices).
- Implied volatility is solved numerically per option via bisection.
  If a quote is missing, zero, or below intrinsic value (a bad/stale
  quote), IV and Greeks for that row are returned as None rather than
  a fabricated number — this matters more than it might seem, since
  a plausible-looking wrong Greek is worse than an honest gap.
"""

import logging
import math
from datetime import date
from typing import Optional

from . import black76
from .snapshot_signals_service import _years_to_expiry, valuation_time

logger = logging.getLogger(__name__)

DEFAULT_RISK_FREE_RATE = 0.06
MIN_TIME_TO_EXPIRY_YEARS = 1 / (365 * 24)  # floor ~1 hour, avoids /0 at expiry
IV_LOWER_BOUND = 0.001  # 0.1%
IV_UPPER_BOUND = 5.0  # 500%
IV_TOLERANCE = 1e-4
IV_MAX_ITERATIONS = 100


class OptionChainService:
    """
    Builds an analyzed option chain: real Greeks + implied volatility
    per strike, plus chain-level PCR / max pain / ATM strike.
    """

    def __init__(self, user=None) -> None:
        self.user = user
        self.status_message = "Success"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_chain(
        self,
        symbol: str,
        expiry: Optional[str] = None,
        risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
    ) -> list[dict]:
        """
        Return a flat list of option rows for one expiry, enriched with
        real IV/delta/gamma/theta/vega. Same core shape as the existing
        raw provider chain (strike, option_type, trading_symbol, expiry,
        ltp, oi, volume) — iv/delta/theta are now real values instead
        of hardcoded 0, and gamma/vega are new additive fields.

        If `expiry` isn't given, the nearest available expiry is used
        (the raw provider chain mixes all expiries together, which
        isn't meaningful to show as one table — this filters to one).
        """
        from django.conf import settings

        from ..services.market_service import MarketService

        market = MarketService(user=self.user)

        if settings.MARKET_PROVIDER == "mock":
            self.status_message = (
                "The mock provider does not supply option-chain quotes."
            )
            return []

        available_expiries = self._get_available_expiries(symbol)
        target_expiry = expiry or (
            str(available_expiries[0]) if available_expiries else None
        )

        if not target_expiry or target_expiry not in [
            str(e) for e in available_expiries
        ]:
            self.status_message = "No current NFO contracts found for this expiry. Refresh the instrument catalog."
            return []

        spot_quote = market.quote(symbol)
        spot_price = spot_quote.get("ltp") if spot_quote else None
        if spot_price is None or spot_price <= 0:
            self.status_message = "The provider returned no usable underlying quote. Check the Zerodha connection and quote access."
            return []

        raw_chain = market.option_chain(symbol, expiry=target_expiry)

        if target_expiry:
            raw_chain = [
                row for row in raw_chain if str(row.get("expiry")) == str(target_expiry)
            ]

        if not raw_chain:
            self.status_message = "NFO contracts exist, but the provider returned no option quotes. Check the Zerodha connection and quote access."
            return []

        self.valuation_time = valuation_time(spot_quote.get("timestamp"))
        time_to_expiry = self._time_to_expiry_years(
            target_expiry, at=self.valuation_time
        )

        # Black-76 prices off a forward implied by the chain itself; if the
        # chain has no usable call/put pair the rows fall back to
        # Black-Scholes and say so in "iv_model".
        forward = None
        if getattr(settings, "OPTION_IV_MODEL", "black_scholes") == "black76":
            forward = black76.parity_forward(
                raw_chain, spot_price, time_to_expiry, risk_free_rate
            )

        return [
            self._enrich_row(row, spot_price, time_to_expiry, risk_free_rate, forward)
            for row in raw_chain
        ]

    def get_chain_summary(
        self,
        symbol: str,
        expiry: Optional[str] = None,
        risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
    ) -> dict:
        """
        Return chain-level analytics on top of get_chain(): PCR (OI and
        volume based), max pain strike, ATM strike, and spot price.
        """
        from ..services.market_service import MarketService

        market = MarketService(user=self.user)
        spot_quote = market.quote(symbol)
        spot_price = spot_quote.get("ltp") if spot_quote else None

        available_expiries = self._get_available_expiries(symbol)
        target_expiry = expiry or (
            str(available_expiries[0]) if available_expiries else None
        )

        rows = self.get_chain(
            symbol, expiry=target_expiry, risk_free_rate=risk_free_rate
        )

        atm_strike = (
            self._find_atm_strike(rows, spot_price) if rows and spot_price else None
        )
        pcr_oi, pcr_volume = self._calculate_pcr(rows)
        max_pain = self._calculate_max_pain(rows)

        return {
            "symbol": symbol,
            "spot_price": spot_price,
            "expiry": target_expiry,
            "available_expiries": [str(e) for e in available_expiries],
            "atm_strike": atm_strike,
            "pcr_oi": pcr_oi,
            "pcr_volume": pcr_volume,
            "max_pain": max_pain,
        }

    # ------------------------------------------------------------------
    # Expiry handling
    # ------------------------------------------------------------------

    @staticmethod
    def _get_available_expiries(symbol: str) -> list[date]:
        from ..engine.market_state import MarketState
        from ..repositories.instrument_repository import InstrumentRepository

        expiries = (
            InstrumentRepository.get_options(symbol)
            .filter(expiry__gte=MarketState.now_ist().date())
            .exclude(expiry__isnull=True)
            .values_list("expiry", flat=True)
            .distinct()
            .order_by("expiry")
        )
        return list(expiries)

    @staticmethod
    def _time_to_expiry_years(expiry_str: str, at=None) -> float:
        """Years from `at` (default now) to 15:30 IST on the expiry date, floored at 1 hour."""
        from django.utils import timezone

        expiry_date = date.fromisoformat(str(expiry_str))
        return max(
            _years_to_expiry(expiry_date, at or timezone.now()),
            MIN_TIME_TO_EXPIRY_YEARS,
        )

    # ------------------------------------------------------------------
    # Per-row enrichment (real Greeks + IV, replacing provider's 0s)
    # ------------------------------------------------------------------

    def _enrich_row(
        self,
        row: dict,
        spot: float,
        time_to_expiry: float,
        risk_free_rate: float,
        forward: Optional[float] = None,
    ) -> dict:
        strike = row.get("strike", 0)
        option_type = row.get("option_type")
        ltp = row.get("ltp", 0)

        iv = None
        greeks = {"delta": None, "gamma": None, "theta": None, "vega": None}

        if strike and ltp and ltp > 0 and forward:
            iv = black76.implied_vol(
                ltp, forward, strike, time_to_expiry, risk_free_rate, option_type
            )
            if iv is not None:
                greeks = (
                    black76.greeks(
                        forward, strike, time_to_expiry, risk_free_rate, iv, option_type
                    )
                    or greeks
                )
        elif strike and ltp and ltp > 0:
            iv = self._implied_volatility(
                option_price=ltp,
                spot=spot,
                strike=strike,
                time_to_expiry=time_to_expiry,
                risk_free_rate=risk_free_rate,
                option_type=option_type,
            )
            if iv is not None:
                greeks = self._black_scholes_greeks(
                    spot=spot,
                    strike=strike,
                    time_to_expiry=time_to_expiry,
                    risk_free_rate=risk_free_rate,
                    volatility=iv,
                    option_type=option_type,
                )

        return {
            **row,
            "iv_model": "black76" if forward else "black_scholes",
            "iv": round(iv * 100, 2) if iv is not None else 0,
            "delta": round(greeks["delta"], 4) if greeks["delta"] is not None else 0,
            "gamma": round(greeks["gamma"], 6) if greeks["gamma"] is not None else 0,
            "theta": round(greeks["theta"], 4) if greeks["theta"] is not None else 0,
            "vega": round(greeks["vega"], 4) if greeks["vega"] is not None else 0,
        }

    # ------------------------------------------------------------------
    # Black-Scholes pricing, Greeks, and implied volatility
    # ------------------------------------------------------------------

    @staticmethod
    def _norm_cdf(x: float) -> float:
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    @staticmethod
    def _norm_pdf(x: float) -> float:
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

    def _bs_price(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
        option_type: str,
    ) -> float:
        if volatility <= 0 or time_to_expiry <= 0:
            return (
                max(spot - strike, 0) if option_type == "CE" else max(strike - spot, 0)
            )

        d1 = (
            math.log(spot / strike)
            + (risk_free_rate + 0.5 * volatility**2) * time_to_expiry
        ) / (volatility * math.sqrt(time_to_expiry))
        d2 = d1 - volatility * math.sqrt(time_to_expiry)

        if option_type == "CE":
            return spot * self._norm_cdf(d1) - strike * math.exp(
                -risk_free_rate * time_to_expiry
            ) * self._norm_cdf(d2)
        else:
            return strike * math.exp(-risk_free_rate * time_to_expiry) * self._norm_cdf(
                -d2
            ) - spot * self._norm_cdf(-d1)

    def _black_scholes_greeks(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
        option_type: str,
    ) -> dict:
        d1 = (
            math.log(spot / strike)
            + (risk_free_rate + 0.5 * volatility**2) * time_to_expiry
        ) / (volatility * math.sqrt(time_to_expiry))
        d2 = d1 - volatility * math.sqrt(time_to_expiry)

        pdf_d1 = self._norm_pdf(d1)

        gamma = pdf_d1 / (spot * volatility * math.sqrt(time_to_expiry))
        vega = spot * pdf_d1 * math.sqrt(time_to_expiry) / 100  # per 1% vol move

        if option_type == "CE":
            delta = self._norm_cdf(d1)
            theta = (
                -(spot * pdf_d1 * volatility) / (2 * math.sqrt(time_to_expiry))
                - risk_free_rate
                * strike
                * math.exp(-risk_free_rate * time_to_expiry)
                * self._norm_cdf(d2)
            ) / 365
        else:
            delta = self._norm_cdf(d1) - 1
            theta = (
                -(spot * pdf_d1 * volatility) / (2 * math.sqrt(time_to_expiry))
                + risk_free_rate
                * strike
                * math.exp(-risk_free_rate * time_to_expiry)
                * self._norm_cdf(-d2)
            ) / 365

        return {"delta": delta, "gamma": gamma, "theta": theta, "vega": vega}

    def _implied_volatility(
        self,
        option_price: float,
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        option_type: str,
    ) -> Optional[float]:
        """Solve for IV via bisection. Returns None if it can't converge
        (e.g. price below intrinsic value — a bad/stale quote)."""
        intrinsic = (
            max(spot - strike, 0) if option_type == "CE" else max(strike - spot, 0)
        )
        if option_price < intrinsic:
            return None

        low, high = IV_LOWER_BOUND, IV_UPPER_BOUND
        price_at_low = self._bs_price(
            spot, strike, time_to_expiry, risk_free_rate, low, option_type
        )
        price_at_high = self._bs_price(
            spot, strike, time_to_expiry, risk_free_rate, high, option_type
        )

        if not (price_at_low <= option_price <= price_at_high):
            return None

        mid = low
        for _ in range(IV_MAX_ITERATIONS):
            mid = (low + high) / 2
            price = self._bs_price(
                spot, strike, time_to_expiry, risk_free_rate, mid, option_type
            )

            if abs(price - option_price) < IV_TOLERANCE:
                return mid

            if price < option_price:
                low = mid
            else:
                high = mid

        return mid

    # ------------------------------------------------------------------
    # Chain-level analytics
    # ------------------------------------------------------------------

    @staticmethod
    def _find_atm_strike(rows: list[dict], spot: float) -> Optional[float]:
        strikes = {r["strike"] for r in rows if r.get("strike")}
        if not strikes:
            return None
        return min(strikes, key=lambda s: abs(s - spot))

    @staticmethod
    def _calculate_pcr(rows: list[dict]) -> tuple:
        calls = [r for r in rows if r.get("option_type") == "CE"]
        puts = [r for r in rows if r.get("option_type") == "PE"]

        total_call_oi = sum(r.get("oi", 0) or 0 for r in calls)
        total_put_oi = sum(r.get("oi", 0) or 0 for r in puts)
        total_call_vol = sum(r.get("volume", 0) or 0 for r in calls)
        total_put_vol = sum(r.get("volume", 0) or 0 for r in puts)

        pcr_oi = round(total_put_oi / total_call_oi, 2) if total_call_oi else None
        pcr_volume = (
            round(total_put_vol / total_call_vol, 2) if total_call_vol else None
        )

        return pcr_oi, pcr_volume

    @staticmethod
    def _calculate_max_pain(rows: list[dict]) -> Optional[float]:
        """
        Max pain = the strike at which option WRITERS collectively lose
        the least (equivalently, buyers gain the least) if the
        underlying settles there at expiry.
        """
        strikes = sorted({r["strike"] for r in rows if r.get("strike")})
        if not strikes:
            return None

        call_oi = {
            r["strike"]: r.get("oi", 0) or 0
            for r in rows
            if r.get("option_type") == "CE"
        }
        put_oi = {
            r["strike"]: r.get("oi", 0) or 0
            for r in rows
            if r.get("option_type") == "PE"
        }

        best_strike = None
        best_payout = None

        for settle in strikes:
            payout = sum(call_oi.get(k, 0) * max(settle - k, 0) for k in strikes) + sum(
                put_oi.get(k, 0) * max(k - settle, 0) for k in strikes
            )
            if best_payout is None or payout < best_payout:
                best_payout = payout
                best_strike = settle

        return best_strike
