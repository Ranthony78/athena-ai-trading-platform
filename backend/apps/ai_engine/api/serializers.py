from rest_framework import serializers

from ..models import AISignal, AnalysisSession, PromptTemplate


class PromptTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PromptTemplate
        fields = [
            "id",
            "name",
            "template_type",
            "model",
            "max_tokens",
            "temperature",
            "version",
            "is_default",
            "is_active",
        ]


class AnalysisSessionSerializer(serializers.ModelSerializer):

    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )
    template_name = serializers.CharField(
        source="template.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = AnalysisSession
        fields = [
            "id",
            "symbol",
            "template_name",
            "session_type",
            "status",
            "timeframe",
            "model_used",
            "tokens_used",
            "duration_ms",
            "parsed_output",
            "ai_response",
            "session_time",
        ]


class AISignalSerializer(serializers.ModelSerializer):

    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )

    class Meta:
        model = AISignal
        fields = [
            "id",
            "symbol",
            "signal",
            "confidence",
            "confidence_score",
            "price_at_signal",
            "target_price",
            "stop_loss",
            "reasoning",
            "key_levels",
            "risks",
            "signal_time",
        ]


class AnalysisRequestSerializer(serializers.Serializer):
    """Request body for triggering an analysis."""
    symbol = serializers.CharField()
    timeframe = serializers.ChoiceField(
        choices=["1m", "3m", "5m", "15m", "30m", "1h", "1d"],
        default="15m",
    )
    session_type = serializers.ChoiceField(
        choices=[
            "MARKET_ANALYSIS",
            "SETUP_SCANNER",
            "OPTION_CHAIN",
            "RISK_ASSESSMENT",
            "TRADE_REVIEW",
        ],
        default="MARKET_ANALYSIS",
    )
    persist = serializers.BooleanField(default=True)