import logging
from typing import Any

import pandas as pd

from ..repositories.candle_repository import CandleRepository
from ..repositories.instrument_repository import InstrumentRepository
from .moving_averages import EMA, SMA, WMA
from .momentum import MACD, RSI, Stochastic
from .pivot import CPR, PivotPoints
from .volatility import ATR, BollingerBands
from .volume import OBV, VWAP

logger = logging.getLogger(__name__)


class IndicatorService:
    """
    Orchestrates technical indicator calculations.
    Fetches candle data from DB and runs requested indicators.
    """

    # ------------------------------------------------------------------
    # Core entry point
    # ------------------------------------------------------------------

    @staticmethod
    def calculate(
        symbol: str,
        timeframe: str,
        indicators: list[str],
        limit: int = 200,
    ) -> dict[str, Any]:
        """
        Calculate multiple indicators for a symbol.

        Args:
            symbol:     Instrument symbol e.g. 'NIFTY'
            timeframe:  Candle timeframe e.g. '15m', '1h', '1d'
            indicators: List of indicator names e.g. ['EMA_20', 'RSI_14', 'MACD']
            limit:      Number of candles to fetch (default 200)

        Returns:
            Dict with indicator name as key, values as list
        """
        instrument = InstrumentRepository.get_by_symbol(symbol)

        if not instrument:
            raise ValueError(f"Instrument not found: {symbol}")

        candles = CandleRepository.get_by_instrument_and_timeframe(
            instrument=instrument,
            timeframe=timeframe,
            limit=limit,
        )

        if not candles.exists():
            return {"error": f"No candle data for {symbol} {timeframe}"}

        candle_list = list(
            candles.values(
                "candle_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ).order_by("candle_time")
        )

        df = pd.DataFrame(candle_list)
        df["candle_time"] = pd.to_datetime(df["candle_time"])
        df = df.set_index("candle_time")
        df = df[["open", "high", "low", "close", "volume"]].astype(float)

        close = df["close"]
        results = {}

        for indicator in indicators:
            try:
                results[indicator] = IndicatorService._compute_one(
                    name=indicator,
                    close=close,
                    df=df,
                )
            except Exception as e:
                logger.error(f"Indicator error [{indicator}]: {e}")
                results[indicator] = None

        return results

    # ------------------------------------------------------------------
    # Individual indicator dispatch
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_one(
        name: str,
        close: pd.Series,
        df: pd.DataFrame,
    ) -> Any:
        """
        Dispatch indicator calculation by name.

        Supported formats:
            SMA_20, EMA_9, EMA_21, WMA_20
            RSI_14
            MACD, MACD_12_26_9
            BB_20, BB_20_2
            ATR_14
            VWAP
            OBV
            STOCH_14_3
            PIVOT
            CPR
        """
        parts = name.upper().split("_")
        base = parts[0]

        # Moving Averages
        if base == "SMA":
            period = int(parts[1]) if len(parts) > 1 else 20
            return SMA(period).calculate(close).tolist()

        if base == "EMA":
            period = int(parts[1]) if len(parts) > 1 else 20
            return EMA(period).calculate(close).tolist()

        if base == "WMA":
            period = int(parts[1]) if len(parts) > 1 else 20
            return WMA(period).calculate(close).tolist()

        # Momentum
        if base == "RSI":
            period = int(parts[1]) if len(parts) > 1 else 14
            return RSI(period).calculate(close).tolist()

        if base == "MACD":
            fast = int(parts[1]) if len(parts) > 1 else 12
            slow = int(parts[2]) if len(parts) > 2 else 26
            signal = int(parts[3]) if len(parts) > 3 else 9
            result = MACD(fast, slow, signal).calculate(close)
            return {
                "macd": result["macd"].tolist(),
                "signal": result["signal"].tolist(),
                "histogram": result["histogram"].tolist(),
            }

        if base == "STOCH":
            k = int(parts[1]) if len(parts) > 1 else 14
            d = int(parts[2]) if len(parts) > 2 else 3
            result = Stochastic(k, d).calculate(df)
            return {
                "k": result["k"].tolist(),
                "d": result["d"].tolist(),
            }

        # Volatility
        if base == "BB":
            period = int(parts[1]) if len(parts) > 1 else 20
            std = float(parts[2]) if len(parts) > 2 else 2.0
            result = BollingerBands(period, std).calculate(close)
            return {col: result[col].tolist() for col in result.columns}

        if base == "ATR":
            period = int(parts[1]) if len(parts) > 1 else 14
            return ATR(period).calculate(df).tolist()

        # Volume
        if base == "VWAP":
            return VWAP().calculate(df).tolist()

        if base == "OBV":
            return OBV().calculate(df).tolist()

        # Pivot
        if base == "PIVOT":
            result = PivotPoints().calculate(df)
            return {col: result[col].tolist() for col in result.columns}

        if base == "CPR":
            result = CPR().calculate(df)
            return {col: result[col].tolist() for col in result.columns}

        raise ValueError(f"Unknown indicator: {name}")