import pandas as pd

from .base_strategy import BaseStrategy, SignalResult


class ORBStrategy(BaseStrategy):
    """
    Opening Range Breakout (ORB) Strategy.

    Logic:
        - Define opening range as high/low of first N candles (default 15min)
        - BUY  when price breaks above opening range high
        - SELL when price breaks below opening range low
        - Only valid during market hours (intraday)
    """

    name = "Opening Range Breakout"
    description = "Generates signals when price breaks the opening range."

    def __init__(self, orb_candles: int = 3) -> None:
        """
        Args:
            orb_candles: Number of opening candles to define the range.
                         Default 3 = first 15 mins on 5m timeframe.
        """
        self.orb_candles = orb_candles

    def evaluate(self, df: pd.DataFrame) -> SignalResult:
        price = float(df["close"].iloc[-1])

        if len(df) < self.orb_candles + 2:
            return self.neutral(price, notes="Insufficient candles.")

        # Opening range
        orb_df = df.iloc[:self.orb_candles]
        orb_high = float(orb_df["high"].max())
        orb_low = float(orb_df["low"].min())
        orb_range = orb_high - orb_low

        prev_close = float(df["close"].iloc[-2])

        context = {
            "orb_high": round(orb_high, 2),
            "orb_low": round(orb_low, 2),
            "orb_range": round(orb_range, 2),
            "price": price,
        }

        # Breakout above ORB high — BUY
        if prev_close <= orb_high and price > orb_high:
            stop_loss = round(orb_high - (orb_range * 0.5), 2)
            target = round(orb_high + orb_range, 2)
            strength = "STRONG" if orb_range > 0 else "MODERATE"

            return self.buy(
                price=price,
                strength=strength,
                target=target,
                stop_loss=stop_loss,
                notes=(
                    f"ORB breakout above {orb_high:.2f}. "
                    f"Range: {orb_range:.2f}"
                ),
                context=context,
            )

        # Breakdown below ORB low — SELL
        if prev_close >= orb_low and price < orb_low:
            stop_loss = round(orb_low + (orb_range * 0.5), 2)
            target = round(orb_low - orb_range, 2)
            strength = "STRONG" if orb_range > 0 else "MODERATE"

            return self.sell(
                price=price,
                strength=strength,
                target=target,
                stop_loss=stop_loss,
                notes=(
                    f"ORB breakdown below {orb_low:.2f}. "
                    f"Range: {orb_range:.2f}"
                ),
                context=context,
            )

        return self.neutral(
            price=price,
            notes=(
                f"Within ORB range. "
                f"High: {orb_high:.2f} | Low: {orb_low:.2f}"
            ),
            context=context,
        )

    def minimum_candles_required(self) -> int:
        return self.orb_candles + 5