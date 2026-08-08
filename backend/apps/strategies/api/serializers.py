from rest_framework import serializers

from ..models import Strategy, StrategySignal


class StrategySerializer(serializers.ModelSerializer):

    class Meta:
        model = Strategy
        fields = [
            "id",
            "name",
            "description",
            "strategy_type",
            "timeframe",
            "parameters",
            "is_enabled",
            "is_active",
            "created_at",
            "updated_at",
        ]


class StrategyCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Strategy
        fields = [
            "name",
            "description",
            "strategy_type",
            "timeframe",
            "parameters",
            "is_enabled",
        ]


class StrategySignalSerializer(serializers.ModelSerializer):

    strategy_name = serializers.CharField(
        source="strategy.name",
        read_only=True,
    )
    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )
    trading_symbol = serializers.CharField(
        source="instrument.trading_symbol",
        read_only=True,
    )

    class Meta:
        model = StrategySignal
        fields = [
            "id",
            "strategy_name",
            "symbol",
            "trading_symbol",
            "signal",
            "strength",
            "status",
            "price_at_signal",
            "target_price",
            "stop_loss",
            "timeframe",
            "signal_time",
            "context",
            "notes",
            "created_at",
        ]


class RunStrategySerializer(serializers.Serializer):
    """Request body for running a strategy."""
    symbol = serializers.CharField()
    strategy_id = serializers.IntegerField()


class RunAllSerializer(serializers.Serializer):
    """Request body for running all strategies."""
    symbols = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        max_length=20,
    )