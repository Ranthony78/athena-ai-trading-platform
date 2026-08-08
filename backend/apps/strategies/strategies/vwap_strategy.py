import pandas as pd

from apps.market_data.indicators.volume import VWAP

from .base_strategy import BaseStrategy, SignalResult


class VWAPStrategy(BaseStrategy):
    """
    VWAP Reversal Strategy.

    Logic:
        - BUY  when price crosses above VWAP from below
        - SELL when price crosses below VWAP from above
        - Used as intraday support/resistance
    """

    name = "VWAP Strategy"
    description = "Generates signals based on price crossing VWAP."

    def evaluate(self, df: pd.DataFrame) -> SignalResult:
        price = float(df["close"].iloc[-1])
        prev_price = float(df["close"].iloc[-2])

        if len(df) < 10:
            return self.neutral(price, notes="Insufficient candles.")

        vwap_series = VWAP().calculate(df)
        vwap_now = float(vwap_series.iloc[-1])
        vwap_prev = float(vwap_series.iloc[-2])

        context = {
            "vwap": round(vwap_now, 2),
            "price": price,
            "price_vs_vwap_pct": round(
                (price - vwap_now) / vwap_now * 100, 3
            ),
        }

        # Price crosses above VWAP — BUY
        if prev_price <= vwap_prev and price > vwap_now:
            stop_loss = round(vwap_now * 0.998, 2)
            target = round(price + (price - stop_loss) * 2, 2)

            return self.buy(
                price=price,
                strength="MODERATE",
                target=target,
                stop_loss=stop_loss,
                notes=f"Price crossed above VWAP ({vwap_now:.2f}).",
                context=context,
            )

        # Price crosses below VWAP — SELL
        if prev_price >= vwap_prev and price < vwap_now:
            stop_loss = round(vwap_now * 1.002, 2)
            target = round(price - (stop_loss - price) * 2, 2)

            return self.sell(
                price=price,
                strength="MODERATE",
                target=target,
                stop_loss=stop_loss,
                notes=f"Price crossed below VWAP ({vwap_now:.2f}).",
                context=context,
            )

        return self.neutral(
            price=price,
            notes=f"Price {price:.2f} vs VWAP {vwap_now:.2f}",
            context=context,
        )

    def minimum_candles_required(self) -> int:
        return 10