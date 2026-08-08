import pandas as pd

from .base_indicator import BaseIndicator


class RSI(BaseIndicator):
    """
    Relative Strength Index.
    Measures momentum — overbought > 70, oversold < 30.
    """

    def __init__(self, period: int = 14) -> None:
        self.period = period

    def calculate(self, data: pd.Series) -> pd.Series:
        """
        Calculate RSI using Wilder's smoothing method.

        Args:
            data: Closing price series

        Returns:
            RSI series (0-100)
        """
        series = self.to_series(data)
        delta = series.diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(
            alpha=1 / self.period,
            min_periods=self.period,
            adjust=False,
        ).mean()

        avg_loss = loss.ewm(
            alpha=1 / self.period,
            min_periods=self.period,
            adjust=False,
        ).mean()

        rs = avg_gain / avg_loss.replace(0, float("inf"))
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @classmethod
    def compute(cls, data: list[float], period: int = 14) -> list[float | None]:
        """Convenience class method — returns list."""
        result = cls(period).calculate(pd.Series(data))
        return result.where(result.notna(), None).tolist()


class MACD(BaseIndicator):
    """
    Moving Average Convergence Divergence.
    Trend-following momentum indicator.

    Returns DataFrame with columns:
        macd, signal, histogram
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> None:
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def calculate(self, data: pd.Series) -> pd.DataFrame:
        """
        Calculate MACD, Signal, and Histogram.

        Args:
            data: Closing price series

        Returns:
            DataFrame with macd, signal, histogram columns
        """
        series = self.to_series(data)

        ema_fast = series.ewm(
            span=self.fast_period,
            adjust=False,
        ).mean()

        ema_slow = series.ewm(
            span=self.slow_period,
            adjust=False,
        ).mean()

        macd_line = ema_fast - ema_slow

        signal_line = macd_line.ewm(
            span=self.signal_period,
            adjust=False,
        ).mean()

        histogram = macd_line - signal_line

        return pd.DataFrame({
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram,
        })

    @classmethod
    def compute(
        cls,
        data: list[float],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> dict:
        """Convenience class method — returns dict of lists."""
        result = cls(fast, slow, signal).calculate(pd.Series(data))
        return {
            "macd": result["macd"].where(result["macd"].notna(), None).tolist(),
            "signal": result["signal"].where(result["signal"].notna(), None).tolist(),
            "histogram": result["histogram"].where(result["histogram"].notna(), None).tolist(),
        }


class Stochastic(BaseIndicator):
    """
    Stochastic Oscillator.
    Compares closing price to price range over N periods.
    Returns %K and %D lines.
    """

    def __init__(
        self,
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 3,
    ) -> None:
        self.k_period = k_period
        self.d_period = d_period
        self.smooth_k = smooth_k

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Stochastic %K and %D.

        Args:
            data: OHLCV DataFrame with high, low, close columns

        Returns:
            DataFrame with k, d columns
        """
        high = data["high"]
        low = data["low"]
        close = data["close"]

        lowest_low = low.rolling(window=self.k_period).min()
        highest_high = high.rolling(window=self.k_period).max()

        raw_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        k = raw_k.rolling(window=self.smooth_k).mean()
        d = k.rolling(window=self.d_period).mean()

        return pd.DataFrame({"k": k, "d": d})

    @classmethod
    def compute(
        cls,
        candles: list[dict],
        k_period: int = 14,
        d_period: int = 3,
    ) -> dict:
        """Convenience class method — returns dict of lists."""
        df = cls.ohlcv_dataframe(candles)
        result = cls(k_period, d_period).calculate(df)
        return {
            "k": result["k"].where(result["k"].notna(), None).tolist(),
            "d": result["d"].where(result["d"].notna(), None).tolist(),
        }