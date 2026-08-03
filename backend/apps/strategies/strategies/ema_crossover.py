import pandas as pd

from apps.market_data.indicators.moving_averages import EMA

from .base_strategy import BaseStrategy, SignalResult


class EMACrossoverStrategy(BaseStrategy):
    """
    EMA Crossover Strategy.

    Logic:
        - BUY  when fast EMA crosses ABOVE slow EMA
        - SELL when fast EMA crosses BELOW slow EMA
        - Strength = STRONG if crossover + price > slow EMA by margin

    Default: EMA 9 / EMA 21
    """

    name = "EMA Crossover"
    description = "Generates signals when fast EMA crosses slow EMA."

    def __init__(
        self,
        fast_period: int = 9,
        slow_period: int = 21,
    ) -> None:
        self.fast_period = fast_period
        self.slow_period = slow_period

    def evaluate(self, df: pd.DataFrame) -> SignalResult:
        close = df["close"]
        price = float(close.iloc[-1])

        if len(df) < self.slow_period + 2:
            return self.neutral(price, notes="Insufficient candles.")

        fast_ema = EMA(self.fast_period).calculate(close)
        slow_ema = EMA(self.slow_period).calculate(close)

        fast_now = float(fast_ema.iloc[-1])
        fast_prev = float(fast_ema.iloc[-2])
        slow_now = float(slow_ema.iloc[-1])
        slow_prev = float(slow_ema.iloc[-2])

        context = {
            f"ema_{self.fast_period}": round(fast_now, 2),
            f"ema_{self.slow_period}": round(slow_now, 2),
            "price": price,
        }

        # Bullish crossover — fast crosses above slow
        if fast_prev <= slow_prev and fast_now > slow_now:
            margin = abs(fast_now - slow_now) / slow_now * 100
            strength = "STRONG" if margin > 0.1 else "MODERATE"
            stop_loss = round(slow_now * 0.995, 2)
            target = round(price + (price - stop_loss) * 2, 2)

            return self.buy(
                price=price,
                strength=strength,
                target=target,
                stop_loss=stop_loss,
                notes=(
                    f"EMA{self.fast_period} crossed above "
                    f"EMA{self.slow_period}. "
                    f"Fast: {fast_now:.2f} | Slow: {slow_now:.2f}"
                ),
                context=context,
            )

        # Bearish crossover — fast crosses below slow
        if fast_prev >= slow_prev and fast_now < slow_now:
            margin = abs(fast_now - slow_now) / slow_now * 100
            strength = "STRONG" if margin > 0.1 else "MODERATE"
            stop_loss = round(slow_now * 1.005, 2)
            target = round(price - (stop_loss - price) * 2, 2)

            return self.sell(
                price=price,
                strength=strength,
                target=target,
                stop_loss=stop_loss,
                notes=(
                    f"EMA{self.fast_period} crossed below "
                    f"EMA{self.slow_period}. "
                    f"Fast: {fast_now:.2f} | Slow: {slow_now:.2f}"
                ),
                context=context,
            )

        return self.neutral(
            price=price,
            notes=f"No crossover. Fast: {fast_now:.2f} | Slow: {slow_now:.2f}",
            context=context,
        )

    def minimum_candles_required(self) -> int:
        return self.slow_period + 5