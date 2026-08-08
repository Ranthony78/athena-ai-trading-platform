from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd


@dataclass
class SignalResult:
    """
    Represents the result of a strategy evaluation.
    Returned by every strategy's evaluate() method.
    """

    signal: str                          # BUY | SELL | NEUTRAL
    strength: str                        # STRONG | MODERATE | WEAK
    price: float                         # price at signal
    target: Optional[float] = None       # target price
    stop_loss: Optional[float] = None    # stop loss price
    notes: str = ""                      # human readable reason
    context: dict = field(default_factory=dict)  # indicator snapshot
    timestamp: datetime = field(default_factory=datetime.now)


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.

    Every strategy must implement:
        - evaluate(df): analyze candles and return SignalResult
        - name: strategy name
        - description: what the strategy does

    Convention:
        - df is always a sorted OHLCV DataFrame (oldest first)
        - Always return a SignalResult — never raise for neutral
        - Log reasoning in SignalResult.notes
    """

    name: str = "BaseStrategy"
    description: str = ""

    @abstractmethod
    def evaluate(self, df: pd.DataFrame) -> SignalResult:
        """
        Analyze OHLCV data and return a trading signal.

        Args:
            df: OHLCV DataFrame sorted oldest → newest
                Columns: open, high, low, close, volume

        Returns:
            SignalResult with signal, strength, price, context
        """
        pass

    @staticmethod
    def neutral(price: float, notes: str = "", context: dict = None) -> SignalResult:
        """Convenience method to return a NEUTRAL signal."""
        return SignalResult(
            signal="NEUTRAL",
            strength="WEAK",
            price=price,
            notes=notes,
            context=context or {},
        )

    @staticmethod
    def buy(
        price: float,
        strength: str = "MODERATE",
        target: float = None,
        stop_loss: float = None,
        notes: str = "",
        context: dict = None,
    ) -> SignalResult:
        """Convenience method to return a BUY signal."""
        return SignalResult(
            signal="BUY",
            strength=strength,
            price=price,
            target=target,
            stop_loss=stop_loss,
            notes=notes,
            context=context or {},
        )

    @staticmethod
    def sell(
        price: float,
        strength: str = "MODERATE",
        target: float = None,
        stop_loss: float = None,
        notes: str = "",
        context: dict = None,
    ) -> SignalResult:
        """Convenience method to return a SELL signal."""
        return SignalResult(
            signal="SELL",
            strength=strength,
            price=price,
            target=target,
            stop_loss=stop_loss,
            notes=notes,
            context=context or {},
        )

    def minimum_candles_required(self) -> int:
        """
        Minimum number of candles needed for this strategy.
        Override in subclass if different.
        """
        return 50