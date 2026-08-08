from rest_framework import serializers

from ..models import BacktestResult, BacktestRun, BacktestTrade


class BacktestRunSerializer(serializers.ModelSerializer):

    strategy_name = serializers.CharField(
        source="strategy.name",
        read_only=True,
    )
    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )

    class Meta:
        model = BacktestRun
        fields = [
            "id",
            "strategy_name",
            "symbol",
            "timeframe",
            "from_date",
            "to_date",
            "initial_capital",
            "position_size_pct",
            "brokerage_per_trade",
            "status",
            "candles_processed",
            "duration_seconds",
            "started_at",
            "completed_at",
            "error_message",
            "created_at",
        ]


class BacktestCreateSerializer(serializers.Serializer):
    """Request body for creating a backtest run."""
    strategy_id = serializers.IntegerField()
    symbol = serializers.CharField()
    timeframe = serializers.ChoiceField(
        choices=["1m", "3m", "5m", "15m", "30m", "1h", "1d"],
    )
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    initial_capital = serializers.FloatField(default=100000)
    position_size_pct = serializers.FloatField(default=10)
    brokerage_per_trade = serializers.FloatField(default=20)

    def validate(self, attrs):
        if attrs["from_date"] >= attrs["to_date"]:
            raise serializers.ValidationError(
                "from_date must be before to_date."
            )
        return attrs


class BacktestTradeSerializer(serializers.ModelSerializer):

    class Meta:
        model = BacktestTrade
        fields = [
            "id",
            "direction",
            "quantity",
            "entry_price",
            "exit_price",
            "entry_time",
            "exit_time",
            "pnl",
            "pnl_pct",
            "brokerage",
            "net_pnl",
            "signal",
            "signal_strength",
            "exit_reason",
            "capital_after",
        ]


class BacktestResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = BacktestResult
        fields = [
            "id",
            "total_trades",
            "winning_trades",
            "losing_trades",
            "win_rate",
            "total_pnl",
            "total_net_pnl",
            "avg_pnl_per_trade",
            "avg_win",
            "avg_loss",
            "largest_win",
            "largest_loss",
            "profit_factor",
            "initial_capital",
            "final_capital",
            "total_return_pct",
            "max_drawdown",
            "max_drawdown_pct",
            "sharpe_ratio",
            "expectancy",
            "risk_reward_ratio",
            "consecutive_wins",
            "consecutive_losses",
            "equity_curve",
        ]


class BacktestRunDetailSerializer(serializers.ModelSerializer):
    """Full detail including result."""

    strategy_name = serializers.CharField(
        source="strategy.name",
        read_only=True,
    )
    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )
    result = BacktestResultSerializer(read_only=True)

    class Meta:
        model = BacktestRun
        fields = [
            "id",
            "strategy_name",
            "symbol",
            "timeframe",
            "from_date",
            "to_date",
            "initial_capital",
            "position_size_pct",
            "status",
            "candles_processed",
            "duration_seconds",
            "result",
            "created_at",
        ]