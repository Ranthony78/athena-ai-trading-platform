from rest_framework import serializers

from ..models import ZerodhaConfig, ZerodhaSession


class ZerodhaConfigSerializer(serializers.ModelSerializer):

    class Meta:
        model = ZerodhaConfig
        fields = [
            "id",
            "api_key",
            "is_connected",
            "connected_at",
            "token_expires_at",
            "mcp_url",
            "is_token_valid",
        ]
        read_only_fields = [
            "is_connected",
            "connected_at",
            "token_expires_at",
            "is_token_valid",
        ]


class ZerodhaConfigUpdateSerializer(serializers.Serializer):
    """Request body for saving Zerodha config."""
    api_key = serializers.CharField()
    api_secret = serializers.CharField()
    mcp_url = serializers.URLField(
        default="https://mcp.kite.trade/mcp",
    )


class TokenExchangeSerializer(serializers.Serializer):
    """Request body for token exchange."""
    request_token = serializers.CharField()


class ZerodhaSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ZerodhaSession
        fields = [
            "id",
            "zerodha_user_id",
            "zerodha_username",
            "broker",
            "email",
            "user_type",
            "status",
            "login_at",
            "expires_at",
        ]


class OrderPlaceSerializer(serializers.Serializer):
    """Request body for placing a live order."""
    tradingsymbol = serializers.CharField()
    exchange = serializers.ChoiceField(
        choices=["NSE", "BSE", "NFO", "MCX"],
        default="NSE",
    )
    transaction_type = serializers.ChoiceField(choices=["BUY", "SELL"])
    quantity = serializers.IntegerField(min_value=1)
    order_type = serializers.ChoiceField(
        choices=["MARKET", "LIMIT", "SL", "SL-M"],
        default="MARKET",
    )
    product = serializers.ChoiceField(
        choices=["MIS", "NRML", "CNC"],
        default="MIS",
    )
    price = serializers.FloatField(default=0)
    trigger_price = serializers.FloatField(default=0)
    tag = serializers.CharField(default="", allow_blank=True)