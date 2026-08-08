import logging
from datetime import datetime

from django.utils import timezone

from apps.market_data.repositories.candle_repository import CandleRepository
from apps.market_data.repositories.instrument_repository import InstrumentRepository

from ..models import Strategy, StrategySignal
from ..repositories.signal_repository import SignalRepository
from ..strategies.base_strategy import BaseStrategy, SignalResult
from ..strategies.ema_crossover import EMACrossoverStrategy
from ..strategies.orb_strategy import ORBStrategy
from ..strategies.rsi_strategy import RSIStrategy
from ..strategies.vwap_strategy import VWAPStrategy

import pandas as pd

logger = logging.getLogger(__name__)


class StrategyEngine:
    """
    Runs strategies against market data and persists signals.
    Orchestrates the full strategy evaluation pipeline.
    """

    # Map strategy_type to implementation class
    STRATEGY_MAP: dict[str, type[BaseStrategy]] = {
        "EMA_CROSSOVER": EMACrossoverStrategy,
        "RSI": RSIStrategy,
        "VWAP": VWAPStrategy,
        "ORB": ORBStrategy,
    }

    # ------------------------------------------------------------------
    # Run a single strategy against a symbol
    # ------------------------------------------------------------------

    @classmethod
    def run(
        cls,
        strategy: Strategy,
        symbol: str,
        persist: bool = True,
        user=None,
    ) -> SignalResult | None:
        """
        Evaluate a strategy against the latest candle data for a symbol.

        Args:
            strategy: Strategy model instance
            symbol:   Instrument symbol
            persist:  If True, save signal to DB
            user:     Required to attach a real option contract to a
                persisted signal (Step 3). If omitted, the signal is
                still saved, just without a contract — same graceful
                degradation as everywhere else this pattern is used.

        Returns:
            SignalResult or None if evaluation failed
        """
        instrument = InstrumentRepository.get_by_symbol(symbol)

        if not instrument:
            logger.warning(f"StrategyEngine: instrument not found: {symbol}")
            return None

        strategy_class = cls.STRATEGY_MAP.get(strategy.strategy_type)

        if not strategy_class:
            logger.warning(
                f"StrategyEngine: no implementation for {strategy.strategy_type}"
            )
            return None

        # Instantiate with parameters from DB
        params = strategy.parameters or {}
        impl: BaseStrategy = strategy_class(**params)

        # Fetch candles
        candles = CandleRepository.get_by_instrument_and_timeframe(
            instrument=instrument,
            timeframe=strategy.timeframe,
            limit=max(200, impl.minimum_candles_required() + 10),
        )

        if not candles.exists():
            logger.warning(
                f"StrategyEngine: no candles for {symbol} {strategy.timeframe}"
            )
            return None

        # Build DataFrame
        candle_list = list(
            candles.values(
                "candle_time", "open", "high", "low", "close", "volume"
            )
        )
        candle_list.reverse()

        df = pd.DataFrame(candle_list)
        df["candle_time"] = pd.to_datetime(df["candle_time"])
        df = df.set_index("candle_time")
        df = df[["open", "high", "low", "close", "volume"]].astype(float)

        if len(df) < impl.minimum_candles_required():
            logger.warning(
                f"StrategyEngine: not enough candles for {symbol}. "
                f"Need {impl.minimum_candles_required()}, got {len(df)}"
            )
            return None

        # Evaluate
        try:
            result = impl.evaluate(df)
        except Exception as e:
            logger.error(
                f"StrategyEngine evaluation error [{strategy.name}|{symbol}]: {e}"
            )
            return None

        logger.info(
            f"Strategy [{strategy.name}] | {symbol} | "
            f"{result.signal} ({result.strength}) @ {result.price}"
        )

        # Persist signal
        if persist and result.signal != "NEUTRAL":
            cls._persist_signal(
                strategy=strategy,
                instrument=instrument,
                result=result,
                timeframe=strategy.timeframe,
                user=user,
            )

        return result

    # ------------------------------------------------------------------
    # Run all enabled strategies against all symbols
    # ------------------------------------------------------------------

    @classmethod
    def run_all(
        cls,
        symbols: list[str],
        persist: bool = True,
        user=None,
    ) -> dict[str, list[dict]]:
        """
        Run all enabled strategies against a list of symbols.

        Returns:
            Dict keyed by symbol, each value is a list of signal dicts
        """
        from ..repositories.strategy_repository import StrategyRepository

        strategies = StrategyRepository.get_enabled()
        results = {symbol: [] for symbol in symbols}

        for strategy in strategies:
            for symbol in symbols:
                result = cls.run(
                    strategy=strategy,
                    symbol=symbol,
                    persist=persist,
                    user=user,
                )
                if result:
                    results[symbol].append({
                        "strategy": strategy.name,
                        "strategy_type": strategy.strategy_type,
                        "signal": result.signal,
                        "strength": result.strength,
                        "price": result.price,
                        "target": result.target,
                        "stop_loss": result.stop_loss,
                        "notes": result.notes,
                        "context": result.context,
                        "timestamp": result.timestamp.isoformat(),
                    })

        return results

    # ------------------------------------------------------------------
    # Persist signal to DB
    # ------------------------------------------------------------------

    @classmethod
    def _persist_signal(
        cls,
        strategy: Strategy,
        instrument,
        result: SignalResult,
        timeframe: str,
        user=None,
    ) -> StrategySignal:
        """Save a SignalResult to the database."""

        # Step 3: attach a real option contract for directional signals.
        option_data = None
        try:
            from apps.market_data.services.strike_selection_service import (
                StrikeSelectionService,
            )
            option_data = StrikeSelectionService.select_for_signal(
                symbol=instrument.symbol,
                direction=result.signal,
                user=user,
            )
        except Exception as e:
            logger.error(f"StrategyEngine strike selection error: {e}")

        signal_kwargs = dict(
            strategy=strategy,
            instrument=instrument,
            user=user,
            signal=result.signal,
            strength=result.strength,
            status="ACTIVE",
            price_at_signal=result.price,
            target_price=result.target,
            stop_loss=result.stop_loss,
            timeframe=timeframe,
            signal_time=result.timestamp or timezone.now(),
            context=result.context,
            notes=result.notes,
        )

        if option_data:
            from apps.market_data.models import Instrument
            signal_kwargs["option_instrument"] = Instrument.objects.filter(
                id=option_data["instrument_id"]
            ).first()
            signal_kwargs["entry_premium"] = option_data["entry_premium"]

        return StrategySignal.objects.create(**signal_kwargs)