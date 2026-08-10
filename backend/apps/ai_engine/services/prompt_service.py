import logging
from typing import Optional

from apps.market_data.repositories.candle_repository import CandleRepository
from apps.market_data.repositories.instrument_repository import InstrumentRepository
from apps.market_data.indicators.indicator_service import IndicatorService
from apps.market_data.engine.market_state import MarketState
from apps.market_data.services.historical_distribution_service import HistoricalDistributionService
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

    Phase 2 enrichment: a real 5-year historical base rate (gap
    frequency distribution, intraday range percentiles) computed from
    stored daily candles via HistoricalDistributionService. This gives
    the model an actual empirical anchor to adjust from instead of
    estimating a probability purely from qualitative judgment. Degrades
    to NA (with the underlying sample_size reported) if there isn't
    enough backfilled daily history yet — see backfill_candles command.

    Phase 3 enrichment: India VIX and market breadth, now that both are
    confirmed feasible from what Athena already has — VIX via the same
    quote pathway as NIFTY/BANKNIFTY, breadth via batch-quoting the real
    Nifty 50 constituent stocks and counting advances/declines. Neither
    needs external scraping. Both degrade to NA if the underlying calls
    fail, same as every other live-data field here.

    Phase 4 enrichment: real news sentiment for India-macro keywords
    (RBI, rates, inflation, budget, Fed) via Marketaux's structured news
    API (real per-article sentiment scores, not scraped, not an LLM
    guessing). Requires MARKETAUX_API_KEY — degrades to NA if unset or
    the request fails. Honest limitation: RBI isn't a trackable entity
    in Marketaux's system, so this matches via free-text keyword search
    rather than a dedicated entity sentiment score — see
    NewsSentimentService's docstring for the full caveat.

    Phase 5 enrichment: today's REALIZED (not predicted) intraday
    session structure via SessionStructureService — actual range/
    direction per standard time block, from real candles, for blocks
    that have actually happened. Blocks that haven't started yet report
    NA rather than a forward guess: Athena doesn't have the backfilled
    intraday history to compute a real time-of-day base rate, and
    guessing one via AI judgment alone would reintroduce the exact
    fabrication risk this pipeline exists to remove. Also in this phase:
    per-timeframe trend confidence is now a real, deterministic score
    (RSI distance from 50, not an AI estimate).

    Phase 6 enrichment: real IV vs. realized-volatility comparison via
    IVRealizedVolatilityService — the honest substitute for an "IV
    percentile" (no historical IV time series is stored yet, so a real
    percentile isn't computable; this compares current IV against real
    realized volatility computed from actual backfilled price history
    instead, a standard professional concept). Degrades to NA if the
    ATM option analysis (Section 10) isn't available.

    NOT included (see project scope): FII/DII flow data — needs a
    scheduled fetch of NSE's daily published report, since it isn't
    available via Kite Connect at all. Also not included: ADX and
    Stochastic RSI — not yet implemented as indicators.
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
- If the Session is CLOSED, this is pre-market/after-hours planning, not
  a reason to withhold analysis. Frame your assessment as an outlook for
  the NEXT trading session: what the prior session's data suggests, what
  levels to watch at the next open, and what would need to happen for a
  BUY/SELL setup to qualify once trading resumes. Still use NO_SETUP if
  the data genuinely doesn't support a directional view — closed-market
  status is context for your framing, not an automatic NO_SETUP trigger.
- Always provide reasoning for your signals
- Output must include a JSON block for structured parsing

Rules:
- Maximum 2 setup candidates per session
- No new setups after 14:00 IST (does not apply to next-session planning
  during closed-market hours — that 14:00 cutoff is about the *current*
  live session, not about whether you can plan ahead for tomorrow)
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
        context["historical_stats"] = PromptService._safe_historical_stats(symbol)
        context["conditional_probability"] = PromptService._safe_conditional_probability(
            symbol, context["gap"]
        )
        context["vix"] = PromptService._safe_get_vix(user)
        context["breadth"] = PromptService._safe_get_breadth(user)
        context["news_sentiment"] = PromptService._safe_get_news_sentiment()
        context["session_structure"] = PromptService._safe_get_session_structure(symbol)

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
        context["iv_vs_hv"] = PromptService._safe_iv_vs_hv(symbol, context["options"])

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
    def _safe_get_vix(user) -> Optional[dict]:
        """
        India VIX quote — same pathway as any other index (real
        Instrument row, real Kite quote), not a scrape or separate
        integration. None if the user isn't connected or the quote
        call fails for any reason; never fabricated.
        """
        if not user:
            return None
        try:
            from apps.market_data.services.market_service import MarketService
            return MarketService(user=user).quote("VIX")
        except Exception as e:
            logger.error(f"PromptService VIX quote error: {e}")
            return None

    @staticmethod
    def _safe_get_breadth(user) -> Optional[dict]:
        """
        Real Nifty 50 advance/decline breadth from live constituent
        quotes. See MarketBreadthService for the constituent list and
        staleness caveat. None if unavailable; never fabricated.
        """
        try:
            from apps.market_data.services.market_breadth_service import (
                MarketBreadthService,
            )
            return MarketBreadthService.get_breadth(user)
        except Exception as e:
            logger.error(f"PromptService breadth error: {e}")
            return None

    @staticmethod
    def _safe_get_news_sentiment() -> Optional[dict]:
        """
        Real India-macro news sentiment via Marketaux. None if
        MARKETAUX_API_KEY isn't configured or the call fails — see
        NewsSentimentService for the RBI-entity-matching caveat.
        """
        try:
            from apps.market_data.services.news_sentiment_service import (
                NewsSentimentService,
            )
            return NewsSentimentService.get_macro_sentiment()
        except Exception as e:
            logger.error(f"PromptService news sentiment error: {e}")
            return None

    @staticmethod
    def _safe_get_session_structure(symbol: str) -> Optional[list]:
        """
        Today's REALIZED (not predicted) time-block structure. See
        SessionStructureService — blocks that haven't started yet come
        back with status NOT_STARTED, never a forward guess.
        """
        try:
            from apps.market_data.services.session_structure_service import (
                SessionStructureService,
            )
            return SessionStructureService.get_today_structure(symbol)
        except Exception as e:
            logger.error(f"PromptService session structure error [{symbol}]: {e}")
            return None

    @staticmethod
    def _safe_historical_stats(symbol: str) -> Optional[dict]:
        """
        Real 5-year empirical base rate — gap frequency distribution and
        intraday range percentiles — computed from stored daily candles.
        Returns None (renders as NA) if there isn't enough backfilled
        history yet; never returns a stat built on a thin sample without
        flagging it, since a confident-looking base rate from too few
        days is worse than no base rate at all.
        """
        try:
            gap_stats = HistoricalDistributionService.gap_stats(symbol)
            range_stats = HistoricalDistributionService.intraday_range_stats(symbol)

            if gap_stats.get("error") or range_stats.get("error"):
                return None

            return {"gap": gap_stats, "range": range_stats}
        except Exception as e:
            logger.error(f"PromptService historical stats error [{symbol}]: {e}")
            return None

    @staticmethod
    def _gap_bucket_key(gap: Optional[dict]) -> Optional[str]:
        """
        Maps today's already-computed gap classification (gap_type,
        direction — human-readable strings) to the bucket key format
        HistoricalDistributionService uses internally (e.g.
        "gap_down_mild"). Returns None if gap is unavailable or
        genuinely flat (no up/down bucket applies).
        """
        if not gap:
            return None
        type_map = {
            "Normal Open": "normal",
            "Mild Gap": "mild",
            "Large Gap": "large",
            "Extreme Gap": "extreme",
        }
        size = type_map.get(gap.get("gap_type"))
        direction = gap.get("direction")
        if not size or direction not in ("Gap Up", "Gap Down"):
            return None
        return f"gap_{'up' if direction == 'Gap Up' else 'down'}_{size}"

    @staticmethod
    def _safe_conditional_probability(symbol: str, gap: Optional[dict]) -> Optional[dict]:
        """
        Real, pre-computed answer to "given today's specific gap type,
        how did the rest of the day historically close" — a genuinely
        different (and more directly useful) statistic than the raw
        gap-frequency distribution in _safe_historical_stats. Computed
        here in Python, handed to the model as a fact, so it never has
        to derive this itself from the raw distribution table.
        """
        bucket = PromptService._gap_bucket_key(gap)
        if not bucket:
            return None
        try:
            result = HistoricalDistributionService.close_direction_given_gap(symbol, bucket)
            return None if result.get("error") else result
        except Exception as e:
            logger.error(f"PromptService conditional probability error [{symbol}]: {e}")
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
                    # Real, deterministic — distance of RSI from neutral
                    # 50, scaled to 0-100. Not an AI estimate: same input
                    # always produces the same output. Capped at 100.
                    "confidence": min(100, round(abs(latest_rsi - 50) * 2)),
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

    @staticmethod
    def _safe_iv_vs_hv(symbol: str, options: Optional[dict]) -> Optional[dict]:
        """
        Real IV-vs-realized-volatility comparison. Uses the ATM call/put
        IV already fetched in `options` — averages both sides when
        available, since ATM call and put IV are normally close. None if
        options data (or the IV within it) wasn't available.
        """
        if not options:
            return None
        try:
            call_iv = (options.get("atm_call") or {}).get("iv")
            put_iv = (options.get("atm_put") or {}).get("iv")
            ivs = [float(v) for v in (call_iv, put_iv) if v is not None]
            if not ivs:
                return None
            avg_iv = sum(ivs) / len(ivs)

            from apps.market_data.services.iv_realized_vol_service import (
                IVRealizedVolatilityService,
            )
            return IVRealizedVolatilityService.get_iv_vs_realized(symbol, avg_iv)
        except Exception as e:
            logger.error(f"PromptService IV-vs-HV error [{symbol}]: {e}")
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
        conditional_probability = context.get("conditional_probability")
        vix = context.get("vix")
        breadth = context.get("breadth")
        news_sentiment = context.get("news_sentiment")
        session_structure = context.get("session_structure")
        iv_vs_hv = context.get("iv_vs_hv")
        mtf = context.get("multi_timeframe", {})
        options = context.get("options")
        historical = context.get("historical_stats")

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
| Volume | {quote.get('volume', 'NA')} |
| India VIX | {vix.get('ltp', 'NA') if vix else 'NA'} |"""
        else:
            market_data_text = "NA — live quote unavailable for this request."

        if gap:
            gap_text = f"""**Gap Type:** {gap['gap_type']} ({gap['direction']})
**Gap %:** {gap['gap_pct']}%
**Previous Close:** {gap['previous_close']} → **Today's Open:** {gap['today_open']}

Note: gap direction does not guarantee trend direction. Evaluate continuation vs. reversal probability using the data below rather than assuming the gap will hold."""
        else:
            gap_text = "NA — gap analysis unavailable (needs a live quote)."

        if historical:
            g = historical["gap"]["distribution_pct"]
            r = historical["range"]
            historical_text = f"""**Sample size:** {historical['gap']['sample_size']} trading days

| Gap type | Up | Down |
|----------|----|----|
| Normal (≤0.3%) | {g['gap_up_normal']}% | {g['gap_down_normal']}% |
| Mild (0.3-0.8%) | {g['gap_up_mild']}% | {g['gap_down_mild']}% |
| Large (0.8-1.5%) | {g['gap_up_large']}% | {g['gap_down_large']}% |
| Extreme (>1.5%) | {g['gap_up_extreme']}% | {g['gap_down_extreme']}% |

**Intraday range (points):** median {r['range_points']['median']}, P95 {r['range_points']['p95']}, P5 {r['range_points']['p5']}
**Upside from open (points):** median {r['upside_from_open_points']['median']}, P95 {r['upside_from_open_points']['p95']}
**Downside from open (points):** median {r['downside_from_open_points']['median']}, P95 {r['downside_from_open_points']['p95']}

This is a real 5-year empirical base rate, not an estimate. Use it as your anchor — adjust from these percentages based on today's specific signals (technicals, options, news) rather than inventing a probability independently of this data."""
        else:
            historical_text = "NA — insufficient backfilled daily history for a reliable base rate."

        if conditional_probability:
            cp = conditional_probability
            historical_text += f"""

**Today's Applicable Base Rate** — of the {cp['sample_size']} historical days that opened with the SAME gap type as today ({cp['gap_bucket']}), here's how the rest of that day closed relative to its own open:
- Closed UP: {cp['up_pct']}%
- Closed DOWN: {cp['down_pct']}%
- Closed FLAT (within {cp['flat_threshold_pct']}% of open): {cp['flat_pct']}%
{"(Low confidence — sample size under 20)" if cp['low_confidence'] else ""}

This is the direct, pre-computed answer for probability.upside_pct / downside_pct / sideways_pct below — use these numbers as-is rather than deriving your own from the raw distribution table above."""

        if breadth:
            confidence_note = (
                " (fewer than 40/50 constituents resolved — treat as directional only)"
                if breadth["low_confidence"] else ""
            )
            breadth_text = (
                f"**Advances:** {breadth['advances']} · "
                f"**Declines:** {breadth['declines']} · "
                f"**Unchanged:** {breadth['unchanged']} "
                f"(of {breadth['sample_size']}/{breadth['of_total']} Nifty 50 "
                f"constituents live-quoted{confidence_note})"
            )
        else:
            breadth_text = "NA — market breadth unavailable for this request."

        if news_sentiment:
            avg = news_sentiment.get("avg_sentiment")
            headline_rows = "\n".join(
                f"  - [{h['sentiment']:+.2f}] {h['title']} ({h['source']})"
                if h.get("sentiment") is not None
                else f"  - [n/a] {h['title']} ({h['source']})"
                for h in news_sentiment["headlines"]
            )
            sentiment_text = f"""**Articles matched:** {news_sentiment['article_count']} (India sources, RBI/rates/inflation/budget/Fed keywords, recent)
**Average sentiment:** {avg if avg is not None else 'NA'} (-1 very negative to +1 very positive)

{headline_rows}

Note: this is keyword-matched sentiment, not a dedicated RBI entity score — treat as a coarser signal than the numeric data above, and weight it accordingly rather than as a precise probability input."""
        else:
            sentiment_text = "NA — news sentiment unavailable (API key not configured or request failed)."

        mtf_rows = []
        for tf in PromptService.MULTI_TIMEFRAME_SET:
            data = mtf.get(tf)
            if data:
                mtf_rows.append(
                    f"| {tf} | {data['trend']} | {data['ema_20']} | {data['rsi_14']} | {data['confidence']}% |"
                )
            else:
                mtf_rows.append(f"| {tf} | NA | NA | NA | NA |")
        mtf_text = (
            "| Timeframe | Trend | EMA 20 | RSI 14 | Confidence* |\n"
            "|-----------|-------|--------|--------|-------------|\n"
            + "\n".join(mtf_rows) +
            "\n\n*Confidence is a real, deterministic score (RSI distance from neutral 50), not an estimate."
        )

        if session_structure:
            # If any block carries a reference_date, this is the
            # most-recent-day fallback (today hasn't started yet) rather
            # than today's own data — label the whole block clearly so
            # the model doesn't present it as today's session.
            reference_date = next(
                (b.get("reference_date") for b in session_structure if b.get("reference_date")),
                None,
            )
            block_rows = []
            for b in session_structure:
                if b["status"] == "NOT_STARTED":
                    block_rows.append(f"| {b['window']} | Not started yet | — | — |")
                elif b["status"] == "NO_DATA":
                    block_rows.append(f"| {b['window']} | No candle data | — | — |")
                else:
                    status_label = "Complete" if b["status"] in ("COMPLETE", "REFERENCE") else "In progress"
                    block_rows.append(
                        f"| {b['window']} | {status_label} | {b['direction']} "
                        f"({b['move_pts']:+.1f} pts) | {b['range_pts']} pts |"
                    )
            if reference_date:
                session_structure_text = (
                    f"NOTE: Today's session hasn't started yet — this is the MOST RECENT "
                    f"completed trading day ({reference_date}), shown for reference only. "
                    f"Do not present this as today's session.\n\n"
                    "| Window | Status | Direction | Range |\n"
                    "|--------|--------|-----------|-------|\n"
                    + "\n".join(block_rows)
                )
            else:
                session_structure_text = (
                    "| Window | Status | Direction | Range |\n"
                    "|--------|--------|-----------|-------|\n"
                    + "\n".join(block_rows) +
                    "\n\nThis is what ACTUALLY happened today in each window, not a prediction. "
                    "'Not started yet' blocks are in the future — there is nothing real to report "
                    "for them; do not guess their bias."
                )
        else:
            session_structure_text = "NA — today's session structure unavailable (needs live intraday candle data)."

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

            if iv_vs_hv:
                w20 = iv_vs_hv["windows"].get("20d") or {}
                w60 = iv_vs_hv["windows"].get("60d") or {}
                options_text += f"""

**IV vs. Realized Volatility:** {iv_vs_hv['classification'] or 'NA'}
- 20-day realized vol: {w20.get('realized_vol_pct', 'NA')}% (IV/RV ratio: {w20.get('iv_hv_ratio', 'NA')})
- 60-day realized vol: {w60.get('realized_vol_pct', 'NA')}% (IV/RV ratio: {w60.get('iv_hv_ratio', 'NA')})
- {iv_vs_hv['note']}"""
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

## 3. Historical Base Rate (5-Year)

{historical_text}

---

## 4. Market Breadth (Nifty 50)

{breadth_text}

---

## 5. News Sentiment (India Macro)

{sentiment_text}

---

## 6. Multi-Timeframe Trend

{mtf_text}

---

## 7. Today's Realized Session Structure

{session_structure_text}

---

## 8. Primary Timeframe — Price & Indicators ({timeframe})

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

## 9. Support & Resistance

**CPR:** TC {cpr.get('tc', 'NA')} / PP {cpr.get('pp', 'NA')} / BC {cpr.get('bc', 'NA')}

**Pivot Points:**
| R3 | R2 | R1 | PP | S1 | S2 | S3 |
|----|----|----|----|----|----|----|
| {pivot.get('r3', 'NA')} | {pivot.get('r2', 'NA')} | {pivot.get('r1', 'NA')} | {pivot.get('pp', 'NA')} | {pivot.get('s1', 'NA')} | {pivot.get('s2', 'NA')} | {pivot.get('s3', 'NA')} |

---

## 10. ATM Option Analysis

{options_text}

---

## 11. Recent Strategy Signals

{signals_text}

---

## Instructions

1. Synthesize the sections above into a market structure and trend assessment
2. Assess setup quality using the data above — do not treat gap direction as guaranteed trend direction
3. Section 3 includes a "Today's Applicable Base Rate" line when available — a pre-computed real statistic for exactly today's gap type. Use those numbers directly for your probability assessment rather than deriving your own from the raw distribution table above it. If that line is absent, the raw distribution table is still useful context but do not attempt to convert it into an upside/downside/sideways split yourself — say the applicable base rate wasn't available instead.
4. If Market Breadth (Section 4) is available, factor it into conviction — narrow breadth (few advancing stocks driving the move) should lower confidence even if the index itself looks bullish; if it says NA, do not speculate about it.
5. If News Sentiment (Section 5) is available, treat it as a coarser, secondary signal — it's keyword-matched, not a precise entity score. Do not let it override the technical/historical data; use it only to flag event risk (e.g. an imminent RBI decision) or to note when sentiment and technicals conflict. If it says NA, do not speculate about news you don't have.
6. Section 7 (Today's Realized Session Structure) reports what ACTUALLY happened, never a forecast. Do not describe a "Not started yet" block as if you know its bias — that block is in the future.
7. Provide a clear signal: BUY / SELL / NEUTRAL / NO_SETUP / WATCH
8. Give a confidence score (0-100)
9. List key levels (using the CPR/Pivot data above) and risk factors
10. If option data is available, factor ATM call/put positioning and PCR into your reasoning; if it says NA, do not speculate about it
11. Report the Session value exactly as given above — do not restate it differently or infer a different session status
12. MANDATORY — write out each of these four prose subsections before the JSON block, in this exact order, matching the same level of effort as your Key Levels section. Do not skip any of them because the signal is NO_SETUP or low-confidence — a quiet/consolidating market still has a real probability split, real sentiment, and a real expected range; "nothing to trade" is not the same as "nothing to report":
   - `### Probability Assessment` — state the real upside/downside/sideways split from Section 3 in words, then the matching numbers.
   - `### Sentiment Assessment` — state the sentiment read from Sections 1/4/5 in words (VIX level, breadth, news tone), then classify it.
   - `### Price Expectation` — state the expected range using CPR/Pivot/ATR, same source as your Key Levels section — if you can fill Key Levels from this data, you can fill this too.
   - `### Option Comparison` — only if Section 10 has real delta values; state which side (call/put) has the higher ITM probability and why, using the real delta numbers.
   If, after actually attempting a subsection, its underlying section genuinely was NA, write "NA — [section] unavailable" for that subsection instead of the analysis, and its JSON field must be null. Leaving a field null WITHOUT first writing the corresponding prose subsection is not acceptable — that's how fields get skipped instead of genuinely assessed.
13. For the new structured JSON fields below (probability, sentiment, option_comparison, price_expectation): every non-null value must trace to a specific section above and match what you wrote in the corresponding prose subsection above. The "basis" field in each object must name which section(s) you used.
14. For option_comparison specifically: use option delta as the probability-of-expiring-ITM proxy (standard options theory — delta approximates this), not a separately invented percentage. If Section 10 is NA, option_comparison must be null.
15. Keep prose reasoning concise otherwise. Completing the JSON block below is mandatory — prioritize finishing it over adding more unrelated prose if you're running low on space
16. End with a JSON block in this exact format:

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
    "risks": [],
    "probability": {{
        "upside_pct": null,
        "downside_pct": null,
        "sideways_pct": null,
        "basis": null
    }},
    "sentiment": {{
        "classification": null,
        "confidence_pct": null,
        "key_reasons": [],
        "basis": null
    }},
    "option_comparison": {{
        "stronger_side": null,
        "call_itm_probability_pct": null,
        "put_itm_probability_pct": null,
        "basis": null
    }},
    "price_expectation": {{
        "nearest_support": null,
        "nearest_resistance": null,
        "expected_range_low": null,
        "expected_range_high": null,
        "basis": null
    }}
}}
```
""".strip()

    @staticmethod
    def _error_prompt(symbol: str) -> str:
        return f"LIVE DATA NOT AVAILABLE FOR {symbol} — NO SETUP"