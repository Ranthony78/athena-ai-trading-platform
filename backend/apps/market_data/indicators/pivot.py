import pandas as pd

from .base_indicator import BaseIndicator


class PivotPoints(BaseIndicator):
    """
    Classic Pivot Points.
    Calculated from previous session's high, low, close.
    Returns PP, R1, R2, R3, S1, S2, S3.
    """

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Pivot Points for each row based on previous candle.

        Args:
            data: OHLCV DataFrame

        Returns:
            DataFrame with pp, r1, r2, r3, s1, s2, s3 columns
        """
        high = data["high"].shift(1)
        low = data["low"].shift(1)
        close = data["close"].shift(1)

        pp = (high + low + close) / 3

        r1 = (2 * pp) - low
        r2 = pp + (high - low)
        r3 = high + 2 * (pp - low)

        s1 = (2 * pp) - high
        s2 = pp - (high - low)
        s3 = low - 2 * (high - pp)

        return pd.DataFrame({
            "pp": pp,
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "s1": s1,
            "s2": s2,
            "s3": s3,
        })

    @classmethod
    def compute(cls, candles: list[dict]) -> dict:
        """Convenience class method — returns dict of lists."""
        df = cls.ohlcv_dataframe(candles)
        result = cls().calculate(df)
        return {
            col: result[col].where(result[col].notna(), None).tolist()
            for col in result.columns
        }


class CPR(BaseIndicator):
    """
    Central Pivot Range.
    Three levels: BC (Bottom Central), PP (Pivot), TC (Top Central).
    Narrow CPR = trending day. Wide CPR = sideways day.
    """

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate CPR for each row based on previous candle.

        Args:
            data: OHLCV DataFrame

        Returns:
            DataFrame with tc, pp, bc, width columns
        """
        high = data["high"].shift(1)
        low = data["low"].shift(1)
        close = data["close"].shift(1)

        pp = (high + low + close) / 3
        bc = (high + low) / 2
        tc = (pp - bc) + pp
        width = (tc - bc).abs()

        return pd.DataFrame({
            "tc": tc,
            "pp": pp,
            "bc": bc,
            "width": width,
        })

    @classmethod
    def compute(cls, candles: list[dict]) -> dict:
        """Convenience class method — returns dict of lists."""
        df = cls.ohlcv_dataframe(candles)
        result = cls().calculate(df)
        return {
            col: result[col].where(result[col].notna(), None).tolist()
            for col in result.columns
        }