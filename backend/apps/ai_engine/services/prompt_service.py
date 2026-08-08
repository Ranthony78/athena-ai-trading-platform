import logging
from typing import Optional

from apps.market_data.repositories.candle_repository import CandleRepository
from apps.market_data.repositories.instrument_repository import InstrumentRepository
from apps.market_data.indicators.indicator_service import IndicatorService
from apps.market_data.engine.market_state import MarketState
from apps.strategies.repositories.signal_repository import SignalRepository

logger = logging.getLogger(__name__)


class PromptService:
    """
    Builds AI prompts from live market data.

    Phase 1 enrichment: current market data, gap analysis, multi-
    timeframe trend, ATM option analysis, and pivot-based support/
    resistance — all from real data sources (quotes, candles,
    indicators, option chain). Every new section degrades gracefully
    to "NA" if its underlying data isn't available (e.g. option chain
    needs a real NFO instrument import), rather than fabricating a
    value or crashing the whole prompt.

    NOT included (see project scope): India VIX, market breadth, and
    FII/DII flow data — these need data sources beyond what's wired up
    yet (VIX/breadth need additional NSE instrument imports; FII/DII
    isn't available via Kite Connect at all). Also not included:
    ADX and Stochastic RSI — not yet implemented as indicators.
    """

    MULTI_TIMEFRAME_SET = ["5m", "15m", "30m"]

    # ------------------------------------------------------------------
    # Default system prompt
    # ------------------------------------------------------------------

    DEFAULT_SYSTEM_PROMPT = """You are Athena, an AI trading analyst specializing in 
Nifty 50 and Bank Nifty options analysis.

Your role:
- Analyze market data objectively and produce structured assessments
- NO_SETUP is the default — a setup must be earned through evidence
- Never fabricate data — if data is missing, report it as NA
- Only report fields that are explicitly present in the data provided to
  you below (including market session status). Do not add a "Session"
  line, a bias statement, or any other field unless the value for it was
  given to you in this prompt — guessing or inferring it from context is
  fabrication, even if it seems like a reasonable default.
- Always provide reasoning for your signals
- Output must include a JSON block for structured parsing

Rules:
- Maximum 2 setup candidates per session
- No new setups after 14:00 IST
- High event risk = NO_SETUP
- All percentages are estimates, not calculated probabilities
"""

    # ------------------------------------------------------------------
    # Market Analysis Prompt
    # ------------------------------------------------------------------

    @staticmethod
    def build_market_analysis_prompt(
        symbol: str,
        timeframe: str = "15m",
        limit: int = 100,
        user=None,
    ) -> tuple[str, dict]:
        """
        Build a market analysis prompt for a symbol.

        Args:
            user: required for live quote and option chain data
                (real Zerodha calls need a user context). If omitted,
                those sections degrade to "NA" rather than failing
                the whole prompt.

        Returns:
            (user_prompt, market_context)
        """
        instrument = InstrumentRepository.get_by_symbol(symbol)
        context = {"symbol": symbol, "timeframe": timeframe}

        try:
            context["session"] = MarketState.session_info()
        except Exception as e:
            logger.error(f"PromptService session error: {e}")
            context["session"] = None

        if not instrument:
            context["error"] = f"Instrument {symbol} not found."
            return PromptService._error_prompt(symbol), context

        context["quote"] = PromptService._safe_get_quote(symbol, user)
        context["gap"] = PromptService._calculate_gap(context["quote"])

        candles = CandleRepository.get_by_instrument_and_timeframe(
            instrument=instrument,
            timeframe=timeframe,
            limit=limit,
        )

        candle_list = list(
            candles.values(
                "candle_time", "open", "high", "low", "close", "volume"
            )
        )
        candle_list.reverse()

        if not candle_list:
            context["error"] = "No candle data available."
            return PromptService._error_prompt(symbol), context

        latest = candle_list[-1]
        context["latest_candle"] = {
            "time": str(latest["candle_time"]),
            "open": float(latest["open"]),
            "high": float(latest["high"]),
            "low": float(latest["low"]),
            "close": float(latest["close"]),
            "volume": int(latest["volume"]),
        }

        context["indicators"] = PromptService._safe_indicators(
            symbol, timeframe,
            ["EMA_9", "EMA_21", "EMA_50", "RSI_14", "MACD", "BB_20",
             "VWAP", "ATR_14", "CPR", "PIVOT"],
            limit,
        )

        context["multi_timeframe"] = PromptService._safe_multi_timeframe(symbol)

        context["options"] = PromptService._safe_option_analysis(symbol, user)

        try:
            signals = SignalRepository.get_by_instrument(instrument, limit=5)
            context["recent_signals"] = [
                {
                    "strategy": s.strategy.name,
                    "signal": s.signal,
                    "strength": s.strength,
                    "price": float(s.price_at_signal),
                    "time": str(s.signal_time),
                }
                for s in signals
            ]
        except Exception:
            context["recent_signals"] = []

        user_prompt = PromptService._format_market_prompt(symbol, timeframe, context)
        return user_prompt, context

    # ------------------------------------------------------------------
    # New data-gathering helpers — each fails gracefully to None/{}
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_get_quote(symbol: str, user) -> Optional[dict]:
        if not user:
            return None
        try:
            from apps.market_data.services.market_service import MarketService
            return MarketService(user=user).quote(symbol)
        except Exception as e:
            logger.error(f"PromptService quote error [{symbol}]: {e}")
            return None

    @staticmethod
    def _calculate_gap(quote: Optional[dict]) -> Optional[dict]:
        """
        Gap % = (today's open - previous close) / previous close * 100.
        Kite convention: quote['open'] = today's open,
        quote['close'] = PREVIOUS day's close.
        """
        if not quote:
            return None
        try:
            today_open = quote.get("open")
            prev_close = quote.get("close")
            if not today_open or not prev_close:
                return None

            gap_pct = round((today_open - prev_close) / prev_close * 100, 2)
            abs_gap = abs(gap_pct)

            if abs_gap <= 0.3:
                gap_type = "Normal Open"
            elif abs_gap <= 0.8:
                gap_type = "Mild Gap"
            elif abs_gap <= 1.5:
                gap_type = "Large Gap"
            else:
                gap_type = "Extreme Gap"

            direction = "Gap Up" if gap_pct > 0 else ("Gap Down" if gap_pct < 0 else "Flat")

            return {
                "previous_close": prev_close,
                "today_open": today_open,
                "gap_pct": gap_pct,
                "gap_type": gap_type,
                "direction": direction,
            }
        except Exception as e:
            logger.error(f"PromptService gap calc error: {e}")
            return None

    @staticmethod
    def _latest_val(data):
        """Reduce a full indicator time series down to its latest
        value. Without this, every indicator embeds its entire ~100-
        value history as raw text in the prompt — this is what was
        blowing up token usage, not the new Phase 1 sections."""
        if isinstance(data, list):
            vals = [v for v in data if v is not None]
            return round(vals[-1], 2) if vals else None
        if isinstance(data, dict):
            return {
                k: PromptService._latest_val(v) for k, v in data.items()
            }
        return data

    @staticmethod
    def _safe_indicators(symbol: str, timeframe: str, names: list[str], limit: int) -> dict:
        try:
            raw = IndicatorService.calculate(
                symbol=symbol, timeframe=timeframe, indicators=names, limit=limit,
            )
            return {k: PromptService._latest_val(v) for k, v in raw.items()}
        except Exception as e:
            logger.error(f"PromptService indicator error: {e}")
            return {}

    @staticmethod
    def _safe_multi_timeframe(symbol: str) -> dict:
        """
        Lightweight trend read per timeframe: latest close vs EMA_20,
        plus latest RSI_14. Each timeframe fails independently.
        """
        results = {}
        for tf in PromptService.MULTI_TIMEFRAME_SET:
            try:
                data = IndicatorService.calculate(
                    symbol=symbol, timeframe=tf,
                    indicators=["EMA_20", "RSI_14"], limit=60,
                )
                ema_series = data.get("EMA_20") or []
                rsi_series = data.get("RSI_14") or []
                ema_vals = [v for v in ema_series if v is not None]
                rsi_vals = [v for v in rsi_series if v is not None]

                if not ema_vals or not rsi_vals:
                    results[tf] = None
                    continue

                instrument = InstrumentRepository.get_by_symbol(symbol)
                candles = list(
                    CandleRepository.get_by_instrument_and_timeframe(
                        instrument=instrument, timeframe=tf, limit=1,
                    ).values("close")
                )
                latest_close = float(candles[0]["close"]) if candles else None
                latest_ema = round(ema_vals[-1], 2)
                latest_rsi = round(rsi_vals[-1], 2)

                if latest_close is None:
                    trend = "NA"
                elif latest_close > latest_ema:
                    trend = "Bullish"
                elif latest_close < latest_ema:
                    trend = "Bearish"
                else:
                    trend = "Neutral"

                results[tf] = {
                    "trend": trend,
                    "ema_20": latest_ema,
                    "rsi_14": latest_rsi,
                }
            except Exception as e:
                logger.error(f"PromptService multi-timeframe error [{tf}]: {e}")
                results[tf] = None
        return results

    @staticmethod
    def _safe_option_analysis(symbol: str, user) -> Optional[dict]:
        if not user:
            return None
        try:
            from apps.market_data.services.option_chain_service import OptionChainService
            service = OptionChainService(user=user)
            summary = service.get_chain_summary(symbol)

            if not summary.get("atm_strike"):
                return None

            chain = service.get_chain(symbol, expiry=summary.get("expiry"))
            atm_call = next(
                (r for r in chain if r.get("strike") == summary["atm_strike"] and r.get("option_type") == "CE"),
                None,
            )
            atm_put = next(
                (r for r in chain if r.get("strike") == summary["atm_strike"] and r.get("option_type") == "PE"),
                None,
            )

            return {
                "spot_price": summary.get("spot_price"),
                "expiry": summary.get("expiry"),
                "atm_strike": summary.get("atm_strike"),
                "pcr_oi": summary.get("pcr_oi"),
                "pcr_volume": summary.get("pcr_volume"),
                "max_pain": summary.get("max_pain"),
                "atm_call": atm_call,
                "atm_put": atm_put,
            }
        except Exception as e:
            logger.error(f"PromptService option analysis error [{symbol}]: {e}")
            return None

    # ------------------------------------------------------------------
    # Prompt formatter
    # ------------------------------------------------------------------

    @staticmethod
    def _format_market_prompt(symbol: str, timeframe: str, context: dict) -> str:
        """Format the full, enriched market analysis user prompt."""

        latest = context.get("latest_candle", {})
        indicators = context.get("indicators", {})
        signals = context.get("recent_signals", [])
        session = context.get("session")
        quote = context.get("quote")
        gap = context.get("gap")
        mtf = context.get("multi_timeframe", {})
        options = context.get("options")

        macd = indicators.get("MACD", {}) or {}
        bb = indicators.get("BB_20", {}) or {}
        cpr = indicators.get("CPR", {}) or {}
        pivot = indicators.get("PIVOT", {}) or {}

        signals_text = "\n".join([
            f"  - {s['strategy']}: {s['signal']} ({s['strength']}) @ {s['price']}"
            for s in signals
        ]) or "  None"

        if session:
            session_text = (
                f"**Session:** {session['session']}  "
                f"**Time (IST):** {session['time']}  "
                f"**Market Open:** {'Yes' if session['is_live'] else 'No'}"
            )
        else:
            session_text = "**Session:** NA (session state unavailable)"

        if quote:
            market_data_text = f"""| Field | Value |
|-------|-------|
| LTP | {quote.get('ltp', 'NA')} |
| Open | {quote.get('open', 'NA')} |
| High | {quote.get('high', 'NA')} |
| Low | {quote.get('low', 'NA')} |
| Previous Close | {quote.get('close', 'NA')} |
| Change | {quote.get('change', 'NA')} |
| Change % | {quote.get('change_percent', 'NA')} |
| Volume | {quote.get('volume', 'NA')} |"""
        else:
            market_data_text = "NA — live quote unavailable for this request."

        if gap:
            gap_text = f"""**Gap Type:** {gap['gap_type']} ({gap['direction']})
**Gap %:** {gap['gap_pct']}%
**Previous Close:** {gap['previous_close']} → **Today's Open:** {gap['today_open']}

Note: gap direction does not guarantee trend direction. Evaluate continuation vs. reversal probability using the data below rather than assuming the gap will hold."""
        else:
            gap_text = "NA — gap analysis unavailable (needs a live quote)."

        mtf_rows = []
        for tf in PromptService.MULTI_TIMEFRAME_SET:
            data = mtf.get(tf)
            if data:
                mtf_rows.append(
                    f"| {tf} | {data['trend']} | {data['ema_20']} | {data['rsi_14']} |"
                )
            else:
                mtf_rows.append(f"| {tf} | NA | NA | NA |")
        mtf_text = (
            "| Timeframe | Trend | EMA 20 | RSI 14 |\n"
            "|-----------|-------|--------|--------|\n" + "\n".join(mtf_rows)
        )

        if options:
            call = options.get("atm_call") or {}
            put = options.get("atm_put") or {}
            options_text = f"""**Spot Price:** {options.get('spot_price', 'NA')}
**Expiry:** {options.get('expiry', 'NA')}
**ATM Strike:** {options.get('atm_strike', 'NA')}
**PCR (OI):** {options.get('pcr_oi', 'NA')}
**PCR (Volume):** {options.get('pcr_volume', 'NA')}
**Max Pain:** {options.get('max_pain', 'NA')}

| Side | LTP | OI | Volume | IV % | Delta | Theta |
|------|-----|----|----|------|-------|-------|
| ATM CALL | {call.get('ltp', 'NA')} | {call.get('oi', 'NA')} | {call.get('volume', 'NA')} | {call.get('iv', 'NA')} | {call.get('delta', 'NA')} | {call.get('theta', 'NA')} |
| ATM PUT | {put.get('ltp', 'NA')} | {put.get('oi', 'NA')} | {put.get('volume', 'NA')} | {put.get('iv', 'NA')} | {put.get('delta', 'NA')} | {put.get('theta', 'NA')} |"""
        else:
            options_text = "NA — option chain unavailable (needs a real NFO instrument import and a working live connection)."

        return f"""
## Market Analysis Request

**Symbol:** {symbol}
**Timeframe:** {timeframe}
**Time:** {latest.get('time', 'NA')}

{session_text}

---

## 1. Current Market Data

{market_data_text}

---

## 2. Gap Analysis

{gap_text}

---

## 3. Multi-Timeframe Trend

{mtf_text}

---

## 4. Primary Timeframe — Price & Indicators ({timeframe})

| Field | Value |
|-------|-------|
| Open  | {latest.get('open', 'NA')} |
| High  | {latest.get('high', 'NA')} |
| Low   | {latest.get('low', 'NA')} |
| Close | {latest.get('close', 'NA')} |
| Volume | {latest.get('volume', 'NA')} |
| EMA 9     | {indicators.get('EMA_9', 'NA')} |
| EMA 21    | {indicators.get('EMA_21', 'NA')} |
| EMA 50    | {indicators.get('EMA_50', 'NA')} |
| RSI 14    | {indicators.get('RSI_14', 'NA')} |
| MACD      | {macd.get('macd', 'NA')} |
| MACD Signal | {macd.get('signal', 'NA')} |
| MACD Histogram | {macd.get('histogram', 'NA')} |
| BB Upper  | {bb.get('upper', 'NA')} |
| BB Middle | {bb.get('middle', 'NA')} |
| BB Lower  | {bb.get('lower', 'NA')} |
| VWAP      | {indicators.get('VWAP', 'NA')} |
| ATR 14    | {indicators.get('ATR_14', 'NA')} |

---

## 5. Support & Resistance

**CPR:** TC {cpr.get('tc', 'NA')} / PP {cpr.get('pp', 'NA')} / BC {cpr.get('bc', 'NA')}

**Pivot Points:**
| R3 | R2 | R1 | PP | S1 | S2 | S3 |
|----|----|----|----|----|----|----|
| {pivot.get('r3', 'NA')} | {pivot.get('r2', 'NA')} | {pivot.get('r1', 'NA')} | {pivot.get('pp', 'NA')} | {pivot.get('s1', 'NA')} | {pivot.get('s2', 'NA')} | {pivot.get('s3', 'NA')} |

---

## 6. ATM Option Analysis

{options_text}

---

## 7. Recent Strategy Signals

{signals_text}

---

## Instructions

1. Synthesize the sections above into a market structure and trend assessment
2. Assess setup quality using the data above — do not treat gap direction as guaranteed trend direction
3. Provide a clear signal: BUY / SELL / NEUTRAL / NO_SETUP / WATCH
4. Give a confidence score (0-100)
5. List key levels (using the CPR/Pivot data above) and risk factors
6. If option data is available, factor ATM call/put positioning and PCR into your reasoning; if it says NA, do not speculate about it
7. Report the Session value exactly as given above — do not restate it differently or infer a different session status
8. Keep prose reasoning concise. Completing the JSON block below is mandatory — prioritize finishing it over adding more prose if you're running low on space
9. End with a JSON block in this exact format:

```json
{{
    "signal": "NO_SETUP",
    "confidence": 45,
    "confidence_level": "LOW",
    "target": null,
    "stop_loss": null,
    "key_levels": {{
        "resistance": null,
        "support": null,
        "vwap": null
    }},
    "risks": []
}}
```
""".strip()

    @staticmethod
    def _error_prompt(symbol: str) -> str:
        return f"LIVE DATA NOT AVAILABLE FOR {symbol} — NO SETUP"