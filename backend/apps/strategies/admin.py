from django.contrib import admin

from .models import Strategy, StrategySignal


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "strategy_type",
        "timeframe",
        "is_enabled",
        "is_active",
        "created_at",
    )

    list_filter = (
        "strategy_type",
        "timeframe",
        "is_enabled",
    )

    search_fields = ("name",)


@admin.register(StrategySignal)
class StrategySignalAdmin(admin.ModelAdmin):

    list_display = (
        "strategy",
        "instrument",
        "signal",
        "strength",
        "status",
        "price_at_signal",
        "signal_time",
    )

    list_filter = (
        "signal",
        "strength",
        "status",
        "timeframe",
    )

    search_fields = (
        "instrument__symbol",
        "strategy__name",
    )