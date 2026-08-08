import pandas as pd

from .base_indicator import BaseIndicator


class SMA(BaseIndicator):
    """
    Simple Moving Average.
    Average of closing prices over N periods.
    """

    def __init__(self, period: int = 20) -> None:
        self.period = period

    def calculate(self, data: pd.Series) -> pd.Series:
        """
        Calculate SMA.

        Args:
            data: Closing price series

        Returns:
            SMA series (NaN for first period-1 values)
        """
        series = self.to_series(data)
        return series.rolling(window=self.period).mean()

    @classmethod
    def compute(cls, data: list[float], period: int = 20) -> list[float | None]:
        """Convenience class method — returns list."""
        result = cls(period).calculate(pd.Series(data))
        return result.where(result.notna(), None).tolist()


class EMA(BaseIndicator):
    """
    Exponential Moving Average.
    Gives more weight to recent prices.
    """

    def __init__(self, period: int = 20) -> None:
        self.period = period

    def calculate(self, data: pd.Series) -> pd.Series:
        """
        Calculate EMA.

        Args:
            data: Closing price series

        Returns:
            EMA series
        """
        series = self.to_series(data)
        return series.ewm(span=self.period, adjust=False).mean()

    @classmethod
    def compute(cls, data: list[float], period: int = 20) -> list[float | None]:
        """Convenience class method — returns list."""
        result = cls(period).calculate(pd.Series(data))
        return result.where(result.notna(), None).tolist()


class WMA(BaseIndicator):
    """
    Weighted Moving Average.
    Linearly weighted — most recent price has highest weight.
    """

    def __init__(self, period: int = 20) -> None:
        self.period = period

    def calculate(self, data: pd.Series) -> pd.Series:
        """
        Calculate WMA.

        Args:
            data: Closing price series

        Returns:
            WMA series
        """
        series = self.to_series(data)
        weights = pd.Series(range(1, self.period + 1))

        def _wma(window):
            if len(window) < self.period:
                return None
            return (window.values * weights.values).sum() / weights.sum()

        return series.rolling(window=self.period).apply(_wma, raw=False)

    @classmethod
    def compute(cls, data: list[float], period: int = 20) -> list[float | None]:
        """Convenience class method — returns list."""
        result = cls(period).calculate(pd.Series(data))
        return result.where(result.notna(), None).tolist()