from rest_framework import serializers

from ..models import AISignal, AnalysisSession, PromptTemplate


class AIProviderCredentialSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=["gemini", "kimi", "claude", "groq"])
    api_key = serializers.CharField(write_only=True, trim_whitespace=True, min_length=8, max_length=512)


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
    template_version = serializers.CharField(
        source="template.version",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = AnalysisSession
        fields = [
            "id",
            "symbol",
            "template_name",
            "template_version",
            "session_type",
            "status",
            "timeframe",
            "model_used",
            "tokens_used",
            "duration_ms",
            "parsed_output",
            "ai_response",
            "session_time",
            "forecast_horizon_minutes",
            "forecast_anchor_price",
            "forecast_target_time",
            "forecast_outcome_status",
            "forecast_actual_class",
            "forecast_outcome_price",
            "forecast_resolved_at",
            "forecast_brier_score",
            "probability_method_version",
            "prompt_version", "prompt_hash", "provider_used", "paper_evaluation", "error_message",
        ]


class AISignalSerializer(serializers.ModelSerializer):

    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )
    suggested_contract = serializers.SerializerMethodField()

    @staticmethod
    def get_suggested_contract(obj):
        instrument = obj.option_instrument
        if not instrument or not obj.entry_premium:
            return None
        return {
            "instrument_id": instrument.id,
            "trading_symbol": instrument.trading_symbol,
            "expiry": instrument.expiry.isoformat() if instrument.expiry else None,
            "strike": float(instrument.strike) if instrument.strike is not None else None,
            "option_type": instrument.option_type or instrument.instrument_type,
            "lot_size": instrument.lot_size,
            "entry_premium": float(obj.entry_premium),
        }

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
            "suggested_contract",
        ]


class AnalysisRequestSerializer(serializers.Serializer):
    """Request body for triggering an analysis."""
    symbol = serializers.CharField()
    timeframe = serializers.ChoiceField(
        choices=["1m", "3m", "5m", "15m", "30m", "1h", "1d"],
        default="15m",
    )
    forecast_horizon_minutes = serializers.ChoiceField(
        choices=[5, 15, 30, 60],
        default=15,
    )
    analysis_mode = serializers.ChoiceField(
        choices=[("LIVE", "Live session"), ("NEXT_SESSION", "Next session outlook")],
        default="LIVE",
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
    paper_evaluate = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if attrs["analysis_mode"] == "NEXT_SESSION" and attrs["paper_evaluate"]:
            raise serializers.ValidationError({
                "paper_evaluate": "Paper evaluation is unavailable for next-session outlooks; they are planning only."
            })
        if attrs["paper_evaluate"] and not attrs["persist"]:
            raise serializers.ValidationError("Paper evaluation requires a saved analysis.")
        return attrs
