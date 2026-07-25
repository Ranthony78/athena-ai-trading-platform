import pandas as pd

from .base_indicator import BaseIndicator


class VWAP(BaseIndicator):
    """
    Volume Weighted Average Price.
    Average price weighted by volume — resets each session.
    Used as intraday support/resistance.
    """

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate VWAP.

        Args:
            data: OHLCV DataFrame with high, low, close, volume columns

        Returns:
            VWAP series
        """
        typical_price = (data["high"] + data["low"] + data["close"]) / 3
        vwap = (typical_price * data["volume"]).cumsum() / data["volume"].cumsum()
        return vwap

    @classmethod
    def compute(cls, candles: list[dict]) -> list[float | None]:
        """Convenience class method — returns list."""
        df = cls.ohlcv_dataframe(candles)
        result = cls().calculate(df)
        return result.where(result.notna(), None).tolist()


class OBV(BaseIndicator):
    """
    On Balance Volume.
    Cumulative volume indicator — confirms price trends.
    """

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate OBV.

        Args:
            data: OHLCV DataFrame with close, volume columns

        Returns:
            OBV series
        """
        close = data["close"]
        volume = data["volume"]

        direction = close.diff().apply(
            lambda x: 1 if x > 0 else (-1 if x < 0 else 0)
        )

        obv = (volume * direction).cumsum()
        return obv

    @classmethod
    def compute(cls, candles: list[dict]) -> list[float | None]:
        """Convenience class method — returns list."""
        df = cls.ohlcv_dataframe(candles)
        result = cls().calculate(df)
        return result.where(result.notna(), None).tolist()