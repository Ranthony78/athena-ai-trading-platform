import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..constants import INDICES
from ..services.analysis_report_service import AnalysisReportService
from ..services.candle_service import CandleService
from ..services.instrument_service import InstrumentService
from ..services.market_service import MarketService
from ..services.option_chain_service import OptionChainService
from ..services.outcome_stats_service import OutcomeStatsService
from ..services.quote_service import QuoteService
from .serializers import (
    BulkQuoteRequestSerializer,
    CandleSerializer,
    ExpirySerializer,
    InstrumentSerializer,
    OptionChainSerializer,
    OptionChainSummarySerializer,
    QuoteSerializer,
)

logger = logging.getLogger(__name__)


class InstrumentListAPIView(APIView):
    """
    GET /api/market/instruments/
    Return paginated list of all active instruments.
    Supports filtering by exchange and instrument_type.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        exchange = request.query_params.get("exchange")
        instrument_type = request.query_params.get("instrument_type")

        if exchange:
            instruments = InstrumentService.get_by_exchange(exchange.upper())
        elif instrument_type:
            from ..repositories.instrument_repository import InstrumentRepository

            instruments = InstrumentRepository.filter(
                instrument_type=instrument_type.upper(),
                is_active=True,
            )
        else:
            instruments = InstrumentService.get_all()

        serializer = InstrumentSerializer(instruments, many=True)
        return ApiResponse.success(
            data=serializer.data,
            message=f"{instruments.count()} instruments found.",
        )


class InstrumentSearchAPIView(APIView):
    """
    GET /api/market/instruments/search/?q=NIFTY
    Search instruments by symbol or trading symbol.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()

        if not query or len(query) < 2:
            return ApiResponse.error(
                message="Query parameter 'q' must be at least 2 characters.",
            )

        instruments = InstrumentService.search(query)
        serializer = InstrumentSerializer(instruments, many=True)
        return ApiResponse.success(
            data=serializer.data,
            message=f"{instruments.count()} instruments found.",
        )


class InstrumentDetailAPIView(APIView):
    """
    GET /api/market/instruments/<symbol>/
    Return a single instrument by symbol.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol: str):
        instrument = InstrumentService.get_by_symbol(symbol.upper())

        if not instrument:
            return ApiResponse.error(
                message=f"Instrument not found: {symbol}",
            )

        serializer = InstrumentSerializer(instrument)
        return ApiResponse.success(serializer.data)


class IndexListAPIView(APIView):
    """
    GET /api/market/indices/
    Return all index instruments.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        instruments = InstrumentService.get_indices()
        serializer = InstrumentSerializer(instruments, many=True)
        return ApiResponse.success(serializer.data)


class QuoteListAPIView(APIView):
    """
    GET /api/market/quotes/
    Return live quotes for all major indices.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = QuoteService(user=request.user)
            quotes = service.get_quotes(list(INDICES))
            serializer = QuoteSerializer(quotes, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"QuoteListAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch quotes.")


class QuoteDetailAPIView(APIView):
    """
    GET /api/market/quotes/<symbol>/
    Return live quote for a single symbol.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol: str):
        try:
            service = QuoteService(user=request.user)
            quote = service.get_quote(symbol.upper())

            if not quote:
                return ApiResponse.error(
                    message=f"Quote not found for: {symbol}",
                )

            serializer = QuoteSerializer(quote)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"QuoteDetailAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch quote.")


class BulkQuoteAPIView(APIView):
    """
    POST /api/market/quotes/bulk/
    Return live quotes for a list of symbols.

    Request body:
        { "symbols": ["NIFTY", "BANKNIFTY", "RELIANCE"] }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BulkQuoteRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid request.",
                errors=serializer.errors,
            )

        try:
            symbols = serializer.validated_data["symbols"]
            service = QuoteService(user=request.user)
            quotes = service.get_quotes([s.upper() for s in symbols])
            response_serializer = QuoteSerializer(quotes, many=True)
            return ApiResponse.success(response_serializer.data)
        except Exception as e:
            logger.error(f"BulkQuoteAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch quotes.")


class HistoricalDataAPIView(APIView):
    """
    GET /api/market/historical/<symbol>/
    Return historical OHLCV candles for a symbol.

    Query params:
        timeframe: 1m | 3m | 5m | 15m | 30m | 1h | 1d (default: 1d)
        limit: number of candles to return (default: 100)
    """

    permission_classes = [IsAuthenticated]

    VALID_TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "1d"]

    def get(self, request, symbol: str):
        timeframe = request.query_params.get("timeframe", "1d").strip()
        limit = request.query_params.get("limit", 100)

        if timeframe not in self.VALID_TIMEFRAMES:
            return ApiResponse.error(
                message=f"Invalid timeframe. Choose from: {', '.join(self.VALID_TIMEFRAMES)}",
            )

        try:
            limit = int(limit)
            if limit < 1 or limit > 500:
                return ApiResponse.error(
                    message="Limit must be between 1 and 500.",
                )
        except ValueError:
            return ApiResponse.error(message="Invalid limit value.")

        try:
            # During the regular session, prefer a read-only same-day
            # backfill from Zerodha so the chart has the morning's candles
            # after a page load. The browser aggregates refreshed quotes
            # into the still-forming bar between these history snapshots.
            current_session_requested = request.query_params.get("current_session") in {
                "1",
                "true",
            }
            if current_session_requested and timeframe not in {"1h", "1d"}:
                from django.conf import settings

                from ..engine.market_state import MarketState

                if (
                    getattr(settings, "MARKET_PROVIDER", "mock") == "zerodha"
                    and MarketState.current_session() == MarketState.SESSION_LIVE
                ):
                    current_date = MarketState.now_ist().date()
                    try:
                        current_candles = CandleService(
                            user=request.user
                        ).fetch_historical(
                            symbol=symbol.upper(),
                            interval=timeframe,
                            from_date=str(current_date),
                            to_date=str(current_date),
                        )
                        if current_candles:
                            # Keep the canonical candle store in sync with the
                            # same Zerodha snapshot served to the live chart.
                            # Market Read and indicator calculations consume
                            # stored candles, so returning these without saving
                            # them leaves those panels one session behind.
                            try:
                                from ..repositories.candle_repository import (
                                    CandleRepository,
                                )
                                from ..repositories.instrument_repository import (
                                    InstrumentRepository,
                                )

                                instrument = InstrumentRepository.get_by_symbol(
                                    symbol.upper()
                                )
                                if instrument:
                                    provider = CandleService(user=request.user).provider
                                    CandleRepository.bulk_upsert(
                                        instrument=instrument,
                                        timeframe=timeframe,
                                        candles=current_candles,
                                        source=getattr(
                                            provider, "data_source", "UNKNOWN"
                                        ),
                                    )
                            except Exception as storage_error:
                                logger.warning(
                                    "Could not store current-session candles for %s %s: %s",
                                    symbol.upper(),
                                    timeframe,
                                    storage_error,
                                )
                            return ApiResponse.success(
                                data=current_candles,
                                message="Current-session candles fetched from Zerodha.",
                            )
                    except Exception as provider_error:
                        # Keep the existing stored-history path available if
                        # the broker history endpoint is temporarily down.
                        logger.warning(
                            "Current-session candle backfill failed for %s (%s): %s",
                            symbol.upper(),
                            timeframe,
                            provider_error,
                        )

            candles = CandleService.get_candles(
                symbol=symbol.upper(),
                timeframe=timeframe,
                limit=limit,
            )
            serializer = CandleSerializer(candles, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"HistoricalDataAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch historical data.")


class FuturesActivityAPIView(APIView):
    """Read-only nearest active futures quote and session VWAP context."""

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol: str):
        from django.conf import settings

        from ..engine.market_state import MARKET_CLOSE, MarketState
        from ..repositories.instrument_repository import InstrumentRepository

        symbol = symbol.strip().upper()
        if symbol != "NIFTY":
            return ApiResponse.error(
                message="Futures activity is currently available for NIFTY only."
            )

        unavailable = {
            "available": False,
            "symbol": symbol,
            "trading_symbol": None,
            "expiry": None,
            "ltp": None,
            "volume": None,
            "vwap": None,
            "quote_timestamp": None,
            "last_trade_time": None,
            "source": "ZERODHA",
        }
        if getattr(settings, "MARKET_PROVIDER", "mock") != "zerodha":
            unavailable["reason"] = (
                "The configured provider does not supply live NIFTY futures data."
            )
            return ApiResponse.success(data=unavailable)

        now_ist = MarketState.now_ist()
        today = now_ist.date()
        futures = InstrumentRepository.get_futures(symbol)
        # A contract expiring today remains the front contract before and
        # during the regular session. After the close, roll to the next expiry.
        if now_ist.weekday() >= 5 or now_ist.time() >= MARKET_CLOSE:
            futures = futures.filter(expiry__gt=today)
        else:
            futures = futures.filter(expiry__gte=today)
        future = futures.order_by("expiry", "trading_symbol").first()
        if not future:
            unavailable["reason"] = (
                "No active NIFTY futures contract was found. Refresh the Zerodha instrument catalog."
            )
            return ApiResponse.success(data=unavailable)

        try:
            quote = MarketService(user=request.user).quote(future.trading_symbol)
        except Exception:
            logger.warning(
                "Unable to retrieve read-only NIFTY futures quote.", exc_info=True
            )
            return ApiResponse.error(
                message="Could not retrieve the NIFTY futures quote from Zerodha."
            )

        if not quote or not quote.get("ltp"):
            unavailable.update(
                {
                    "trading_symbol": future.trading_symbol,
                    "expiry": str(future.expiry),
                    "reason": "Zerodha has not returned a usable quote for the active futures contract.",
                }
            )
            return ApiResponse.success(data=unavailable)

        vwap = quote.get("average_price")
        return ApiResponse.success(
            data={
                "available": True,
                "symbol": symbol,
                "trading_symbol": future.trading_symbol,
                "expiry": str(future.expiry),
                "ltp": quote.get("ltp"),
                "volume": quote.get("volume"),
                "vwap": vwap if vwap is not None and float(vwap) > 0 else None,
                "quote_timestamp": quote.get("quote_timestamp")
                or quote.get("timestamp"),
                "last_trade_time": quote.get("last_trade_time"),
                "source": "ZERODHA KITE QUOTE",
                "reason": (
                    None
                    if vwap is not None and float(vwap) > 0
                    else "Zerodha has not supplied a usable session average price for this contract."
                ),
            }
        )


class ExpiryListAPIView(APIView):
    """
    GET /api/market/expiry/<symbol>/
    Return list of available expiry dates for a symbol.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol: str):
        try:
            from ..repositories.instrument_repository import InstrumentRepository

            expiries = (
                InstrumentRepository.filter(
                    symbol__iexact=symbol,
                    expiry__isnull=False,
                    is_active=True,
                )
                .values("expiry")
                .distinct()
                .order_by("expiry")
            )

            data = [{"expiry": e["expiry"]} for e in expiries]
            serializer = ExpirySerializer(data, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"ExpiryListAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch expiry dates.")


class OptionChainAPIView(APIView):
    """
    GET /api/market/option-chain/<symbol>/
    GET /api/market/option-chain/<symbol>/?expiry=YYYY-MM-DD
    Return the analyzed option chain (real Greeks + IV) for one
    expiry — nearest available if not specified.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol: str):
        try:
            service = OptionChainService(user=request.user)
            expiry = request.query_params.get("expiry")
            chain = service.get_chain(symbol.upper(), expiry=expiry)
            serializer = OptionChainSerializer(chain, many=True)
            return ApiResponse.success(serializer.data, message=service.status_message)
        except Exception as e:
            logger.error(f"OptionChainAPIView error: {e}")
            return ApiResponse.error(
                message="Unable to fetch option quotes. Check your Zerodha connection, token validity, and market-data access."
            )


class OptionChainSummaryAPIView(APIView):
    """
    GET /api/market/option-chain/<symbol>/summary/
    GET /api/market/option-chain/<symbol>/summary/?expiry=YYYY-MM-DD
    Return chain-level analytics: PCR, max pain, ATM strike, spot price.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol: str):
        try:
            service = OptionChainService(user=request.user)
            expiry = request.query_params.get("expiry")
            summary = service.get_chain_summary(symbol.upper(), expiry=expiry)
            serializer = OptionChainSummarySerializer(summary)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"OptionChainSummaryAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch option chain summary.")


class MarketReadAPIView(APIView):
    """GET /api/market/read/<symbol>/ — read-only evidence snapshot."""

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol: str):
        try:
            from ..services.market_read_service import MarketReadService

            data = MarketReadService.get_snapshot(symbol, user=request.user)
            return ApiResponse.success(data=data)
        except Exception as e:
            logger.error("MarketReadAPIView error: %s", e)
            return ApiResponse.error(
                message="Unable to build the read-only market snapshot."
            )


# ----------------------------------------------------------------------
# Sprint 11 — Market Engine
# ----------------------------------------------------------------------


class MarketSessionAPIView(APIView):
    """
    GET /api/market/session/
    Return current market session state.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from ..engine.market_state import MarketState

            return ApiResponse.success(MarketState.session_info())
        except Exception as e:
            logger.error(f"MarketSessionAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch session info.")


class MarketEngineStatusAPIView(APIView):
    """
    GET /api/market/engine/status/
    Return current market engine status.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from django.conf import settings

            from ..engine.market_state import MarketState

            provider = getattr(settings, "MARKET_PROVIDER", "mock")
            session_info = MarketState.session_info()

            data = {
                "engine": "MarketEngine",
                "provider": provider,
                "session": session_info["session"],
                # Clock-based session status, not broker connectivity.
                "is_live": session_info["is_live"],
                "websocket_endpoint": "ws://host/ws/market/quotes/",
            }

            return ApiResponse.success(data)
        except Exception as e:
            logger.error(f"MarketEngineStatusAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch engine status.")


# ----------------------------------------------------------------------
# Sprint 12 — Technical Indicators
# ----------------------------------------------------------------------


class IndicatorListAPIView(APIView):
    """
    GET /api/market/indicators/
    Return list of all supported indicators.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        indicators = {
            "moving_averages": [
                {"name": "SMA", "params": ["period"], "example": "SMA_20"},
                {"name": "EMA", "params": ["period"], "example": "EMA_9"},
                {"name": "WMA", "params": ["period"], "example": "WMA_20"},
            ],
            "momentum": [
                {"name": "RSI", "params": ["period"], "example": "RSI_14"},
                {
                    "name": "MACD",
                    "params": ["fast", "slow", "signal"],
                    "example": "MACD_12_26_9",
                },
                {
                    "name": "STOCH",
                    "params": ["k_period", "d_period"],
                    "example": "STOCH_14_3",
                },
            ],
            "volatility": [
                {"name": "BB", "params": ["period", "std_dev"], "example": "BB_20_2"},
                {"name": "ATR", "params": ["period"], "example": "ATR_14"},
            ],
            "volume": [
                {"name": "VWAP", "params": [], "example": "VWAP"},
                {"name": "OBV", "params": [], "example": "OBV"},
            ],
            "pivot": [
                {"name": "PIVOT", "params": [], "example": "PIVOT"},
                {"name": "CPR", "params": [], "example": "CPR"},
            ],
        }
        return ApiResponse.success(data=indicators)


class IndicatorAPIView(APIView):
    """
    POST /api/market/indicators/calculate/
    Calculate technical indicators for a symbol.

    Request body:
    {
        "symbol": "NIFTY",
        "timeframe": "15m",
        "indicators": ["EMA_9", "EMA_21", "RSI_14", "MACD", "BB_20"],
        "limit": 200
    }
    """

    permission_classes = [IsAuthenticated]

    VALID_TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "1d"]

    def post(self, request):
        symbol = request.data.get("symbol", "").strip().upper()
        timeframe = request.data.get("timeframe", "1d").strip()
        indicators = request.data.get("indicators", [])
        limit = request.data.get("limit", 200)

        if not symbol:
            return ApiResponse.error(message="symbol is required.")

        if not indicators:
            return ApiResponse.error(message="indicators list is required.")

        if timeframe not in self.VALID_TIMEFRAMES:
            return ApiResponse.error(
                message=f"Invalid timeframe. Choose from: {', '.join(self.VALID_TIMEFRAMES)}"
            )

        try:
            limit = int(limit)
            limit = max(50, min(limit, 500))
        except (ValueError, TypeError):
            limit = 200

        try:
            from ..indicators.indicator_service import IndicatorService

            result = IndicatorService.calculate(
                symbol=symbol,
                timeframe=timeframe,
                indicators=indicators,
                limit=limit,
            )
            return ApiResponse.success(data=result)
        except ValueError as e:
            return ApiResponse.error(message=str(e))
        except Exception as e:
            logger.error(f"IndicatorAPIView error: {e}")
            return ApiResponse.error(message="Failed to calculate indicators.")


class AnalysisReportAPIView(APIView):
    """
    GET /api/market/report/<symbol>/
    Return the full Analysis Report payload: real price history + EMA
    overlay, stats, support/resistance, multi-timeframe trend, ATM
    options, and the last AI Analysis run — the "fixed block" report
    view, symbol-only, no timeframe picker.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol: str):
        try:
            data = AnalysisReportService.get_report(symbol.upper(), user=request.user)
            return ApiResponse.success(data=data)
        except Exception as e:
            logger.error(f"AnalysisReportAPIView error: {e}")
            return ApiResponse.error(message="Failed to generate analysis report.")


# ----------------------------------------------------------------------
# Step 6 — Outcome Tracking Stats
# ----------------------------------------------------------------------


class OutcomeStatsSummaryAPIView(APIView):
    """
    GET /api/market/outcomes/summary/
    Overall win-rate summary for AI and Strategy signals — open count,
    resolved wins/losses/win_rate, breakdowns by outcome_status and
    product (MIS/NRML). Scoped to the requesting user's own signals.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            data = OutcomeStatsService.get_summary(user=request.user)
            return ApiResponse.success(data=data)
        except Exception as e:
            logger.error(f"OutcomeStatsSummaryAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch outcome stats.")


class OutcomeStatsByStrategyAPIView(APIView):
    """
    GET /api/market/outcomes/by-strategy/
    Win rate per strategy (StrategySignal only).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            data = OutcomeStatsService.get_by_strategy(user=request.user)
            return ApiResponse.success(data=data)
        except Exception as e:
            logger.error(f"OutcomeStatsByStrategyAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch strategy outcome stats.")


class OutcomeStatsBySymbolAPIView(APIView):
    """
    GET /api/market/outcomes/by-symbol/
    Win rate per underlying symbol, combining AI and Strategy signals.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            data = OutcomeStatsService.get_by_symbol(user=request.user)
            return ApiResponse.success(data=data)
        except Exception as e:
            logger.error(f"OutcomeStatsBySymbolAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch symbol outcome stats.")
