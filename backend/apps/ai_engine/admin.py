from django.contrib import admin

from .models import AISignal, AnalysisSession, PromptTemplate


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "template_type",
        "model",
        "version",
        "is_default",
        "is_active",
    )
    list_filter = ("template_type", "model", "is_default")
    search_fields = ("name",)


@admin.register(AnalysisSession)
class AnalysisSessionAdmin(admin.ModelAdmin):

    list_display = (
        "session_type",
        "instrument",
        "status",
        "model_used",
        "tokens_used",
        "duration_ms",
        "session_time",
    )
    list_filter = ("session_type", "status")
    search_fields = ("instrument__symbol",)
    readonly_fields = (
        "prompt_used",
        "ai_response",
        "parsed_output",
        "market_context",
        "tokens_used",
        "duration_ms",
        "session_time",
    )


@admin.register(AISignal)
class AISignalAdmin(admin.ModelAdmin):

    list_display = (
        "instrument",
        "signal",
        "confidence",
        "confidence_score",
        "price_at_signal",
        "signal_time",
    )
    list_filter = ("signal", "confidence")
    search_fields = ("instrument__symbol",)