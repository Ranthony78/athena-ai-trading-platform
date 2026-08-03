import pandas as pd

from .base_indicator import BaseIndicator


class BollingerBands(BaseIndicator):
    """
    Bollinger Bands.
    SMA ± (std_dev * multiplier).
    Returns upper, middle, lower bands.
    """

    def __init__(
        self,
        period: int = 20,
        std_dev: float = 2.0,
    ) -> None:
        self.period = period
        self.std_dev = std_dev

    def calculate(self, data: pd.Series) -> pd.DataFrame:
        """
        Calculate Bollinger Bands.

        Args:
            data: Closing price series

        Returns:
            DataFrame with upper, middle, lower columns
        """
        series = self.to_series(data)
        middle = series.rolling(window=self.period).mean()
        std = series.rolling(window=self.period).std()

        upper = middle + (std * self.std_dev)
        lower = middle - (std * self.std_dev)

        bandwidth = (upper - lower) / middle * 100
        percent_b = (series - lower) / (upper - lower) * 100

        return pd.DataFrame({
            "upper": upper,
            "middle": middle,
            "lower": lower,
            "bandwidth": bandwidth,
            "percent_b": percent_b,
        })

    @classmethod
    def compute(
        cls,
        data: list[float],
        period: int = 20,
        std_dev: float = 2.0,
    ) -> dict:
        """Convenience class method — returns dict of lists."""
        result = cls(period, std_dev).calculate(pd.Series(data))
        return {
            col: result[col].where(result[col].notna(), None).tolist()
            for col in result.columns
        }


class ATR(BaseIndicator):
    """
    Average True Range.
    Measures market volatility.
    """

    def __init__(self, period: int = 14) -> None:
        self.period = period

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate ATR.

        Args:
            data: OHLCV DataFrame with high, low, close columns

        Returns:
            ATR series
        """
        high = data["high"]
        low = data["low"]
        close = data["close"]
        prev_close = close.shift(1)

        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ], axis=1).max(axis=1)

        atr = tr.ewm(
            alpha=1 / self.period,
            min_periods=self.period,
            adjust=False,
        ).mean()

        return atr

    @classmethod
    def compute(
        cls,
        candles: list[dict],
        period: int = 14,
    ) -> list[float | None]:
        """Convenience class method — returns list."""
        df = cls.ohlcv_dataframe(candles)
        result = cls(period).calculate(df)
        return result.where(result.notna(), None).tolist()