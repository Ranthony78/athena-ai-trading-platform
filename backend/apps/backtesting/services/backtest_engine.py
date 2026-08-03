import logging
from decimal import Decimal
from typing import Optional

import pandas as pd

from apps.market_data.repositories.candle_repository import CandleRepository
from apps.market_data.repositories.instrument_repository import InstrumentRepository
from apps.strategies.strategies.base_strategy import BaseStrategy, SignalResult
from apps.strategies.services.strategy_engine import StrategyEngine

from ..models import BacktestRun, BacktestTrade

logger = logging.getLogger(__name__)

BROKERAGE = Decimal("20.00")


class BacktestEngine:
    """
    Core backtesting engine.
    Replays historical candle data through a strategy
    and records simulated trades.

    Walk-forward approach:
    - For each candle, feed all candles up to that point
    - Run strategy evaluation
    - Open/close positions based on signals
    """

    def __init__(self, run: BacktestRun) -> None:
        self.run = run
        self.strategy = run.strategy
        self.instrument = run.instrument
        self.timeframe = run.timeframe
        self.initial_capital = float(run.initial_capital)
        self.position_size_pct = float(run.position_size_pct) / 100
        self.brokerage = float(run.brokerage_per_trade)

        self.capital = self.initial_capital
        self.current_position: Optional[dict] = None
        self.trades: list[dict] = []
        self.equity_curve: list[dict] = []
        self.candles_processed = 0

    def run_backtest(self) -> list[dict]:
        """
        Execute the backtest.
        Returns list of trade dicts.
        """
        # Fetch all candles in range
        all_candles = list(
            CandleRepository.get_range(
                instrument=self.instrument,
                timeframe=self.timeframe,
                from_time=self.run.from_date,
                to_time=self.run.to_date,
            ).values(
                "candle_time", "open",
                "high", "low", "close", "volume",
            )
        )

        if not all_candles:
            logger.warning(
                f"BacktestEngine: no candles for "
                f"{self.instrument.symbol} {self.timeframe} "
                f"{self.run.from_date} → {self.run.to_date}"
            )
            return []

        logger.info(
            f"BacktestEngine: processing {len(all_candles)} candles "
            f"for {self.instrument.symbol}"
        )

        # Get strategy implementation
        strategy_class = StrategyEngine.STRATEGY_MAP.get(
            self.strategy.strategy_type
        )

        if not strategy_class:
            raise ValueError(
                f"No implementation for strategy: {self.strategy.strategy_type}"
            )

        params = self.strategy.parameters or {}
        impl: BaseStrategy = strategy_class(**params)
        min_candles = impl.minimum_candles_required()

        # Walk forward through candles
        for i in range(min_candles, len(all_candles)):
            window = all_candles[:i + 1]
            current_candle = all_candles[i]

            df = self._to_dataframe(window)

            try:
                result = impl.evaluate(df)
            except Exception as e:
                logger.error(f"Strategy eval error at candle {i}: {e}")
                continue

            self.candles_processed += 1
            current_price = float(current_candle["close"])
            current_time = current_candle["candle_time"]

            # Handle signal
            self._process_signal(
                result=result,
                price=current_price,
                time=current_time,
            )

            # Update equity curve
            unrealized = self._get_unrealized_pnl(current_price)
            self.equity_curve.append({
                "time": str(current_time),
                "capital": round(self.capital + unrealized, 2),
            })

        # Close any open position at end of data
        if self.current_position:
            last_candle = all_candles[-1]
            self._close_position(
                price=float(last_candle["close"]),
                time=last_candle["candle_time"],
                exit_reason="END_OF_DATA",
            )

        return self.trades

    # ------------------------------------------------------------------
    # Signal Processing
    # ------------------------------------------------------------------

    def _process_signal(
        self,
        result: SignalResult,
        price: float,
        time,
    ) -> None:
        """Process a strategy signal — open or close positions."""

        if result.signal == "NEUTRAL" or result.signal == "NO_SETUP":
            return

        if not self.current_position:
            # No open position — open one
            if result.signal in ("BUY", "SELL"):
                self._open_position(
                    signal=result.signal,
                    price=price,
                    time=time,
                    result=result,
                )

        else:
            # Position is open
            current_direction = self.current_position["direction"]

            # Opposite signal — close and reverse
            if (
                current_direction == "LONG" and result.signal == "SELL"
            ) or (
                current_direction == "SHORT" and result.signal == "BUY"
            ):
                self._close_position(
                    price=price,
                    time=time,
                    exit_reason="SIGNAL",
                )
                # Open new position in opposite direction
                self._open_position(
                    signal=result.signal,
                    price=price,
                    time=time,
                    result=result,
                )

            # Check stop loss
            elif result.stop_loss and self._is_stopped_out(price):
                self._close_position(
                    price=price,
                    time=time,
                    exit_reason="STOP_LOSS",
                )

    def _open_position(
        self,
        signal: str,
        price: float,
        time,
        result: SignalResult,
    ) -> None:
        """Open a new simulated position."""
        direction = "LONG" if signal == "BUY" else "SHORT"

        # Calculate position size
        trade_capital = self.capital * self.position_size_pct
        quantity = max(1, int(trade_capital / price))

        self.current_position = {
            "direction": direction,
            "quantity": quantity,
            "entry_price": price,
            "entry_time": time,
            "stop_loss": result.stop_loss,
            "target": result.target,
            "signal": signal,
            "strength": result.strength,
            "notes": result.notes,
            "context": result.context,
        }

    def _close_position(
        self,
        price: float,
        time,
        exit_reason: str = "SIGNAL",
    ) -> None:
        """Close the current position and record the trade."""
        if not self.current_position:
            return

        pos = self.current_position
        direction = pos["direction"]
        quantity = pos["quantity"]
        entry_price = pos["entry_price"]

        # Calculate PnL
        if direction == "LONG":
            pnl = (price - entry_price) * quantity
        else:
            pnl = (entry_price - price) * quantity

        net_pnl = pnl - self.brokerage
        pnl_pct = (pnl / (entry_price * quantity)) * 100

        # Update capital
        self.capital += net_pnl

        trade = {
            "direction": direction,
            "quantity": quantity,
            "entry_price": Decimal(str(entry_price)),
            "exit_price": Decimal(str(price)),
            "entry_time": pos["entry_time"],
            "exit_time": time,
            "pnl": Decimal(str(round(pnl, 2))),
            "pnl_pct": Decimal(str(round(pnl_pct, 4))),
            "brokerage": Decimal(str(self.brokerage)),
            "net_pnl": Decimal(str(round(net_pnl, 2))),
            "signal": pos["signal"],
            "signal_strength": pos["strength"],
            "signal_notes": pos["notes"],
            "signal_context": pos["context"],
            "exit_reason": exit_reason,
            "capital_after": Decimal(str(round(self.capital, 2))),
        }

        self.trades.append(trade)
        self.current_position = None

    def _is_stopped_out(self, price: float) -> bool:
        """Check if current price has hit stop loss."""
        if not self.current_position:
            return False

        sl = self.current_position.get("stop_loss")
        if not sl:
            return False

        direction = self.current_position["direction"]

        if direction == "LONG" and price <= float(sl):
            return True
        if direction == "SHORT" and price >= float(sl):
            return True

        return False

    def _get_unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized PnL for current open position."""
        if not self.current_position:
            return 0.0

        pos = self.current_position
        qty = pos["quantity"]
        entry = pos["entry_price"]

        if pos["direction"] == "LONG":
            return (current_price - entry) * qty
        return (entry - current_price) * qty

    @staticmethod
    def _to_dataframe(candles: list[dict]) -> pd.DataFrame:
        """Convert candle list to OHLCV DataFrame."""
        df = pd.DataFrame(candles)
        df["candle_time"] = pd.to_datetime(df["candle_time"])
        df = df.set_index("candle_time")
        df = df[["open", "high", "low", "close", "volume"]].astype(float)
        return df.sort_index()