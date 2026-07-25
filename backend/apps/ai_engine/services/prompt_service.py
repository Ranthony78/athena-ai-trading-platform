import logging
from typing import Optional

from apps.market_data.repositories.candle_repository import CandleRepository
from apps.market_data.repositories.instrument_repository import InstrumentRepository
from apps.market_data.indicators.indicator_service import IndicatorService
from apps.strategies.repositories.signal_repository import SignalRepository

logger = logging.getLogger(__name__)


class PromptService:
    """
    Builds AI prompts from live market data.
    Assembles context from quotes, candles, indicators, and signals.
    """

    # ------------------------------------------------------------------
    # Default system prompt
    # ------------------------------------------------------------------

    DEFAULT_SYSTEM_PROMPT = """You are Athena, an AI trading analyst specializing in 
Nifty 50 and Bank Nifty options analysis.

Your role:
- Analyze market data objectively and produce structured assessments
- NO_SETUP is the default — a setup must be earned through evidence
- Never fabricate data — if data is missing, report it as NA
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
    ) -> tuple[str, dict]:
        """
        Build a market analysis prompt for a symbol.

        Returns:
            (user_prompt, market_context)
        """
        instrument = InstrumentRepository.get_by_symbol(symbol)
        context = {"symbol": symbol, "timeframe": timeframe}

        if not instrument:
            context["error"] = f"Instrument {symbol} not found."
            return PromptService._error_prompt(symbol), context

        # Fetch candles
        candles = CandleRepository.get_by_instrument_and_timeframe(
            instrument=instrument,
            timeframe=timeframe,
            limit=limit,
        )

        candle_list = list(
            candles.values(
                "candle_time", "open", "high", "low", "close", "volume"
            ).order_by("candle_time")
        )

        if not candle_list:
            context["error"] = "No candle data available."
            return PromptService._error_prompt(symbol), context

        # Latest candle
        latest = candle_list[-1]
        context["latest_candle"] = {
            "time": str(latest["candle_time"]),
            "open": float(latest["open"]),
            "high": float(latest["high"]),
            "low": float(latest["low"]),
            "close": float(latest["close"]),
            "volume": int(latest["volume"]),
        }

        # Calculate indicators
        try:
            indicators = IndicatorService.calculate(
                symbol=symbol,
                timeframe=timeframe,
                indicators=[
                    "EMA_9", "EMA_21", "EMA_50",
                    "RSI_14",
                    "MACD",
                    "BB_20",
                    "VWAP",
                    "ATR_14",
                    "CPR",
                ],
                limit=limit,
            )

            # Extract latest values only
            def latest_val(data):
                if isinstance(data, list):
                    vals = [v for v in data if v is not None]
                    return round(vals[-1], 2) if vals else None
                if isinstance(data, dict):
                    return {
                        k: round(latest_val(v), 2) if latest_val(v) else None
                        for k, v in data.items()
                    }
                return data

            context["indicators"] = {
                k: latest_val(v) for k, v in indicators.items()
            }

        except Exception as e:
            logger.error(f"PromptService indicator error: {e}")
            context["indicators"] = {}

        # Recent strategy signals
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

        # Build prompt
        user_prompt = PromptService._format_market_prompt(symbol, timeframe, context)
        return user_prompt, context

    # ------------------------------------------------------------------
    # Prompt formatters
    # ------------------------------------------------------------------

    @staticmethod
    def _format_market_prompt(
        symbol: str,
        timeframe: str,
        context: dict,
    ) -> str:
        """Format the market analysis user prompt."""

        latest = context.get("latest_candle", {})
        indicators = context.get("indicators", {})
        signals = context.get("recent_signals", [])

        macd = indicators.get("MACD", {}) or {}
        bb = indicators.get("BB_20", {}) or {}
        cpr = indicators.get("CPR", {}) or {}

        signals_text = "\n".join([
            f"  - {s['strategy']}: {s['signal']} ({s['strength']}) @ {s['price']}"
            for s in signals
        ]) or "  None"

        return f"""
## Market Analysis Request

**Symbol:** {symbol}
**Timeframe:** {timeframe}
**Time:** {latest.get('time', 'NA')}

---

## Price Data (Latest Candle)

| Field | Value |
|-------|-------|
| Open  | {latest.get('open', 'NA')} |
| High  | {latest.get('high', 'NA')} |
| Low   | {latest.get('low', 'NA')} |
| Close | {latest.get('close', 'NA')} |
| Volume | {latest.get('volume', 'NA')} |

---

## Technical Indicators

| Indicator | Value |
|-----------|-------|
| EMA 9     | {indicators.get('EMA_9', 'NA')} |
| EMA 21    | {indicators.get('EMA_21', 'NA')} |
| EMA 50    | {indicators.get('EMA_50', 'NA')} |
| RSI 14    | {indicators.get('RSI_14', 'NA')} |
| MACD      | {macd.get('macd', 'NA')} |
| Signal    | {macd.get('signal', 'NA')} |
| Histogram | {macd.get('histogram', 'NA')} |
| BB Upper  | {bb.get('upper', 'NA')} |
| BB Middle | {bb.get('middle', 'NA')} |
| BB Lower  | {bb.get('lower', 'NA')} |
| VWAP      | {indicators.get('VWAP', 'NA')} |
| ATR 14    | {indicators.get('ATR_14', 'NA')} |
| CPR TC    | {cpr.get('tc', 'NA')} |
| CPR PP    | {cpr.get('pp', 'NA')} |
| CPR BC    | {cpr.get('bc', 'NA')} |

---

## Recent Strategy Signals

{signals_text}

---

## Instructions

1. Analyze the market structure and trend
2. Assess setup quality using the data above
3. Provide a clear signal: BUY / SELL / NEUTRAL / NO_SETUP / WATCH
4. Give a confidence score (0-100)
5. List key levels and risk factors
6. End with a JSON block in this exact format:

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