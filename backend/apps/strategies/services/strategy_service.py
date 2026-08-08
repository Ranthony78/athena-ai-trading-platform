from typing import Optional

from django.db.models import QuerySet

from ..models import Strategy, StrategySignal
from ..repositories.signal_repository import SignalRepository
from ..repositories.strategy_repository import StrategyRepository
from .strategy_engine import StrategyEngine


class StrategyService:
    """
    Business logic for strategy management and signal retrieval.
    """

    # ------------------------------------------------------------------
    # Strategy CRUD
    # ------------------------------------------------------------------

    @staticmethod
    def get_all() -> QuerySet[Strategy]:
        return StrategyRepository.active()

    @staticmethod
    def get_enabled() -> QuerySet[Strategy]:
        return StrategyRepository.get_enabled()

    @staticmethod
    def get_by_id(id: int) -> Optional[Strategy]:
        return StrategyRepository.get_by_id(id)

    @staticmethod
    def create(data: dict) -> Strategy:
        return StrategyRepository.create(**data)

    @staticmethod
    def update(strategy: Strategy, data: dict) -> Strategy:
        return StrategyRepository.update(strategy, **data)

    @staticmethod
    def delete(strategy: Strategy) -> None:
        StrategyRepository.soft_delete(strategy)

    # ------------------------------------------------------------------
    # Signal Retrieval
    # ------------------------------------------------------------------

    @staticmethod
    def get_active_signals() -> QuerySet[StrategySignal]:
        return SignalRepository.get_active_signals()

    @staticmethod
    def get_today_signals() -> QuerySet[StrategySignal]:
        return SignalRepository.get_today()

    @staticmethod
    def get_signals_for_instrument(
        symbol: str,
        limit: int = 50,
    ) -> QuerySet[StrategySignal]:
        from apps.market_data.repositories.instrument_repository import (
            InstrumentRepository,
        )
        instrument = InstrumentRepository.get_by_symbol(symbol)
        if not instrument:
            return StrategySignal.objects.none()
        return SignalRepository.get_by_instrument(instrument, limit)

    # ------------------------------------------------------------------
    # Engine
    # ------------------------------------------------------------------

    @staticmethod
    def run_strategy(
        strategy_id: int,
        symbol: str,
        user=None,
    ) -> Optional[dict]:
        """Run a single strategy against a symbol."""
        strategy = StrategyRepository.get_by_id(strategy_id)
        if not strategy:
            raise ValueError(f"Strategy not found: {strategy_id}")

        result = StrategyEngine.run(
            strategy=strategy,
            symbol=symbol,
            persist=True,
            user=user,
        )

        if not result:
            return None

        return {
            "strategy": strategy.name,
            "signal": result.signal,
            "strength": result.strength,
            "price": result.price,
            "target": result.target,
            "stop_loss": result.stop_loss,
            "notes": result.notes,
            "context": result.context,
            "timestamp": result.timestamp.isoformat(),
        }

    @staticmethod
    def run_all(symbols: list[str], user=None) -> dict:
        """Run all enabled strategies against symbols."""
        return StrategyEngine.run_all(symbols=symbols, persist=True, user=user)