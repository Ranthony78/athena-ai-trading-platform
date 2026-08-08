from django.contrib import admin

from .models import BacktestResult, BacktestRun, BacktestTrade


@admin.register(BacktestRun)
class BacktestRunAdmin(admin.ModelAdmin):

    list_display = (
        "strategy",
        "instrument",
        "timeframe",
        "from_date",
        "to_date",
        "status",
        "candles_processed",
        "duration_seconds",
        "created_at",
    )
    list_filter = ("status", "timeframe")
    search_fields = ("strategy__name", "instrument__symbol")
    readonly_fields = (
        "status",
        "started_at",
        "completed_at",
        "duration_seconds",
        "candles_processed",
        "error_message",
    )


@admin.register(BacktestTrade)
class BacktestTradeAdmin(admin.ModelAdmin):

    list_display = (
        "run",
        "direction",
        "entry_price",
        "exit_price",
        "pnl",
        "net_pnl",
        "exit_reason",
        "entry_time",
    )
    list_filter = ("direction", "exit_reason", "signal")


@admin.register(BacktestResult)
class BacktestResultAdmin(admin.ModelAdmin):

    list_display = (
        "run",
        "total_trades",
        "win_rate",
        "total_return_pct",
        "max_drawdown_pct",
        "sharpe_ratio",
        "profit_factor",
    )
    readonly_fields = (
        "equity_curve",
    )