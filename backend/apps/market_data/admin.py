from django.contrib import admin

from .models import Candle, Instrument, Quote


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):

    list_display = (
        "symbol",
        "exchange",
        "instrument_token",
        "lot_size",
        "expiry",
    )

    search_fields = (
        "symbol",
        "trading_symbol",
    )

    list_filter = (
        "exchange",
    )


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):

    list_display = (
        "instrument",
        "last_price",
        "volume",
        "updated_at",
    )


@admin.register(Candle)
class CandleAdmin(admin.ModelAdmin):

    list_display = (
        "instrument",
        "timeframe",
        "candle_time",
        "close",
    )

    list_filter = (
        "timeframe",
    )