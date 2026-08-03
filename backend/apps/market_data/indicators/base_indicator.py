from abc import ABC, abstractmethod

import pandas as pd


class BaseIndicator(ABC):
    """
    Abstract base class for all technical indicators.

    All indicators:
    - Accept a pandas Series or DataFrame
    - Return a pandas Series or DataFrame
    - Never modify input data in place
    - Handle edge cases (insufficient data) gracefully
    """

    @abstractmethod
    def calculate(self, data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
        """
        Calculate the indicator.

        Args:
            data: Input price series or OHLCV DataFrame

        Returns:
            Calculated indicator as Series or DataFrame
        """
        pass

    @staticmethod
    def to_series(data: list[float] | pd.Series) -> pd.Series:
        """Convert list or Series to pandas Series."""
        if isinstance(data, pd.Series):
            return data
        return pd.Series(data)

    @staticmethod
    def ohlcv_dataframe(candles: list[dict]) -> pd.DataFrame:
        """
        Convert list of candle dicts to OHLCV DataFrame.

        Expected candle dict keys:
            candle_time, open, high, low, close, volume
        """
        df = pd.DataFrame(candles)
        df["candle_time"] = pd.to_datetime(df["candle_time"])
        df = df.set_index("candle_time")
        df = df[["open", "high", "low", "close", "volume"]].astype(float)
        df = df.sort_index()
        return df