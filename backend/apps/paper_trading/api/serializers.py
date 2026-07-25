from rest_framework import serializers

from ..models import PaperAccount, PaperOrder, PaperPosition, PaperTrade


class PaperAccountSerializer(serializers.ModelSerializer):

    win_rate = serializers.FloatField(read_only=True)
    available_balance = serializers.FloatField(read_only=True)
    total_return_pct = serializers.FloatField(read_only=True)

    class Meta:
        model = PaperAccount
        fields = [
            "id",
            "balance",
            "initial_balance",
            "used_margin",
            "available_balance",
            "total_pnl",
            "today_pnl",
            "total_return_pct",
            "total_trades",
            "winning_trades",
            "losing_trades",
            "win_rate",
        ]


class PaperOrderSerializer(serializers.ModelSerializer):

    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )

    class Meta:
        model = PaperOrder
        fields = [
            "id",
            "symbol",
            "transaction_type",
            "order_type",
            "product",
            "status",
            "quantity",
            "price",
            "average_price",
            "filled_quantity",
            "pending_quantity",
            "order_time",
            "execution_time",
            "tag",
            "notes",
            "reject_reason",
        ]


class PlaceOrderSerializer(serializers.Serializer):
    """Request body for placing a paper order."""
    symbol = serializers.CharField()
    transaction_type = serializers.ChoiceField(choices=["BUY", "SELL"])
    quantity = serializers.IntegerField(min_value=1)
    order_type = serializers.ChoiceField(
        choices=["MARKET", "LIMIT"],
        default="MARKET",
    )
    price = serializers.FloatField(default=0)
    product = serializers.ChoiceField(
        choices=["MIS", "NRML", "CNC"],
        default="MIS",
    )
    tag = serializers.CharField(default="", allow_blank=True)


class PaperPositionSerializer(serializers.ModelSerializer):

    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )
    trading_symbol = serializers.CharField(
        source="instrument.trading_symbol",
        read_only=True,
    )
    current_value = serializers.FloatField(read_only=True)
    invested_value = serializers.FloatField(read_only=True)
    pnl_pct = serializers.FloatField(read_only=True)

    class Meta:
        model = PaperPosition
        fields = [
            "id",
            "symbol",
            "trading_symbol",
            "direction",
            "quantity",
            "average_price",
            "last_price",
            "current_value",
            "invested_value",
            "unrealized_pnl",
            "realized_pnl",
            "pnl_pct",
            "product",
            "tag",
            "open_time",
            "is_open",
        ]


class PaperTradeSerializer(serializers.ModelSerializer):

    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )

    class Meta:
        model = PaperTrade
        fields = [
            "id",
            "symbol",
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
            "product",
            "tag",
            "strategy_signal",
            "ai_signal",
        ]