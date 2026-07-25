import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..constants import INDICES
from ..services.candle_service import CandleService
from ..services.instrument_service import InstrumentService
from ..services.market_service import MarketService
from ..services.quote_service import QuoteService
from .serializers import (
    BulkQuoteRequestSerializer,
    CandleSerializer,
    ExpirySerializer,
    InstrumentSerializer,
    OptionChainSerializer,
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
            service = QuoteService()
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
            service = QuoteService()
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
            service = QuoteService()
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
    Return option chain for a given underlying symbol.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol: str):
        try:
            service = MarketService()
            chain = service.option_chain(symbol.upper())
            serializer = OptionChainSerializer(chain, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"OptionChainAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch option chain.")


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
            from ..engine.market_state import MarketState
            from django.conf import settings

            provider = getattr(settings, "MARKET_PROVIDER", "mock")

            data = {
                "engine": "MarketEngine",
                "provider": provider,
                "session": MarketState.current_session(),
                "is_live": MarketState.is_live(),
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
                {"name": "MACD", "params": ["fast", "slow", "signal"], "example": "MACD_12_26_9"},
                {"name": "STOCH", "params": ["k_period", "d_period"], "example": "STOCH_14_3"},
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