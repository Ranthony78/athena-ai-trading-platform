from django.contrib import admin

from .models import PaperAccount, PaperOrder, PaperPosition, PaperTrade


@admin.register(PaperAccount)
class PaperAccountAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "balance",
        "total_pnl",
        "today_pnl",
        "total_trades",
        "winning_trades",
        "losing_trades",
    )


@admin.register(PaperOrder)
class PaperOrderAdmin(admin.ModelAdmin):

    list_display = (
        "instrument",
        "transaction_type",
        "order_type",
        "quantity",
        "price",
        "average_price",
        "status",
        "order_time",
    )

    list_filter = ("status", "transaction_type", "order_type")
    search_fields = ("instrument__symbol",)


@admin.register(PaperPosition)
class PaperPositionAdmin(admin.ModelAdmin):

    list_display = (
        "instrument",
        "direction",
        "quantity",
        "average_price",
        "last_price",
        "unrealized_pnl",
        "is_open",
    )

    list_filter = ("is_open", "direction")
    search_fields = ("instrument__symbol",)


@admin.register(PaperTrade)
class PaperTradeAdmin(admin.ModelAdmin):

    list_display = (
        "instrument",
        "direction",
        "quantity",
        "entry_price",
        "exit_price",
        "pnl",
        "net_pnl",
        "exit_time",
    )

    list_filter = ("direction", "product")
    search_fields = ("instrument__symbol",)