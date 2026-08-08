from rest_framework import serializers

from ..models import Candle, Instrument, Quote


class InstrumentSerializer(serializers.ModelSerializer):
    """Serializer for instrument list and search."""

    is_option = serializers.BooleanField(read_only=True)
    is_future = serializers.BooleanField(read_only=True)
    is_index = serializers.BooleanField(read_only=True)

    class Meta:
        model = Instrument
        fields = [
            "id",
            "instrument_token",
            "exchange_token",
            "exchange",
            "symbol",
            "trading_symbol",
            "instrument_type",
            "lot_size",
            "tick_size",
            "expiry",
            "strike",
            "option_type",
            "is_option",
            "is_future",
            "is_index",
            "is_active",
            "created_at",
            "updated_at",
        ]


class QuoteSerializer(serializers.Serializer):
    """Serializer for live quote data from provider."""

    symbol = serializers.CharField()
    ltp = serializers.FloatField()
    open = serializers.FloatField()
    high = serializers.FloatField()
    low = serializers.FloatField()
    close = serializers.FloatField()
    change = serializers.FloatField()
    change_percent = serializers.FloatField()
    volume = serializers.IntegerField()
    oi = serializers.IntegerField(default=0)
    bid = serializers.FloatField(default=0)
    ask = serializers.FloatField(default=0)
    timestamp = serializers.DateTimeField()


class CandleSerializer(serializers.ModelSerializer):
    """Serializer for OHLCV candle data."""

    class Meta:
        model = Candle
        fields = [
            "id",
            "timeframe",
            "candle_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]


class OptionChainSerializer(serializers.Serializer):
    """Serializer for a single option chain row."""

    strike = serializers.FloatField()
    option_type = serializers.CharField()
    ltp = serializers.FloatField()
    oi = serializers.IntegerField()
    volume = serializers.IntegerField()
    iv = serializers.FloatField(default=0)
    delta = serializers.FloatField(default=0)
    theta = serializers.FloatField(default=0)


class ExpirySerializer(serializers.Serializer):
    """Serializer for expiry date list."""

    expiry = serializers.DateField()


class BulkQuoteRequestSerializer(serializers.Serializer):
    """Serializer for validating bulk quote request body."""

    symbols = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        max_length=50,
    )

class OptionChainSummarySerializer(serializers.Serializer):
    """Serializer for chain-level analytics (PCR, max pain, ATM)."""

    symbol = serializers.CharField()
    spot_price = serializers.FloatField(allow_null=True)
    expiry = serializers.CharField(allow_null=True)
    available_expiries = serializers.ListField(child=serializers.CharField())
    atm_strike = serializers.FloatField(allow_null=True)
    pcr_oi = serializers.FloatField(allow_null=True)
    pcr_volume = serializers.FloatField(allow_null=True)
    max_pain = serializers.FloatField(allow_null=True)