import pandas as pd

from apps.market_data.indicators.momentum import RSI

from .base_strategy import BaseStrategy, SignalResult


class RSIStrategy(BaseStrategy):
    """
    RSI Overbought/Oversold Strategy.

    Logic:
        - BUY  when RSI crosses above oversold level (default 30)
        - SELL when RSI crosses below overbought level (default 70)
        - STRONG signal when RSI is extreme (< 25 or > 75)
    """

    name = "RSI Strategy"
    description = "Generates signals based on RSI overbought/oversold levels."

    def __init__(
        self,
        period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
    ) -> None:
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def evaluate(self, df: pd.DataFrame) -> SignalResult:
        close = df["close"]
        price = float(close.iloc[-1])

        if len(df) < self.period + 2:
            return self.neutral(price, notes="Insufficient candles.")

        rsi_series = RSI(self.period).calculate(close)
        rsi_now = float(rsi_series.iloc[-1])
        rsi_prev = float(rsi_series.iloc[-2])

        context = {
            "rsi": round(rsi_now, 2),
            "rsi_prev": round(rsi_prev, 2),
            "oversold": self.oversold,
            "overbought": self.overbought,
            "price": price,
        }

        # RSI crossing up from oversold — BUY
        if rsi_prev <= self.oversold and rsi_now > self.oversold:
            strength = "STRONG" if rsi_prev < 25 else "MODERATE"
            stop_loss = round(price * 0.99, 2)
            target = round(price * 1.02, 2)

            return self.buy(
                price=price,
                strength=strength,
                target=target,
                stop_loss=stop_loss,
                notes=(
                    f"RSI crossed above oversold ({self.oversold}). "
                    f"RSI: {rsi_now:.2f}"
                ),
                context=context,
            )

        # RSI crossing down from overbought — SELL
        if rsi_prev >= self.overbought and rsi_now < self.overbought:
            strength = "STRONG" if rsi_prev > 75 else "MODERATE"
            stop_loss = round(price * 1.01, 2)
            target = round(price * 0.98, 2)

            return self.sell(
                price=price,
                strength=strength,
                target=target,
                stop_loss=stop_loss,
                notes=(
                    f"RSI crossed below overbought ({self.overbought}). "
                    f"RSI: {rsi_now:.2f}"
                ),
                context=context,
            )

        return self.neutral(
            price=price,
            notes=f"RSI neutral at {rsi_now:.2f}",
            context=context,
        )

    def minimum_candles_required(self) -> int:
        return self.period + 5