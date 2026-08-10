from django.db import models
from django.contrib.auth import get_user_model

from apps.market_data.models import Instrument
from apps.strategies.models import Strategy
from shared.models import BaseModel

User = get_user_model()


class BacktestRun(BaseModel):
    """
    A backtesting run configuration and execution record.
    Defines what strategy, symbol, timeframe, and date range to test.
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETE", "Complete"),
        ("FAILED", "Failed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="backtest_runs",
    )
    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.CASCADE,
        related_name="backtest_runs",
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="backtest_runs",
    )

    # Configuration
    timeframe = models.CharField(max_length=10)
    from_date = models.DateField()
    to_date = models.DateField()
    initial_capital = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=100000.00,
    )
    position_size_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        help_text="Percentage of capital per trade.",
    )
    brokerage_per_trade = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=20.00,
    )

    # Execution
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(default=0)
    error_message = models.TextField(blank=True)
    candles_processed = models.IntegerField(default=0)

    class Meta:
        db_table = "backtest_runs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["strategy", "instrument"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.strategy.name} | "
            f"{self.instrument.symbol} | "
            f"{self.from_date} → {self.to_date} | "
            f"{self.status}"
        )


class BacktestTrade(BaseModel):
    """
    A single trade executed during a backtest run.
    Records entry, exit, PnL, and signal context.
    """

    DIRECTION_CHOICES = [
        ("LONG", "Long"),
        ("SHORT", "Short"),
    ]

    run = models.ForeignKey(
        BacktestRun,
        on_delete=models.CASCADE,
        related_name="trades",
    )

    direction = models.CharField(
        max_length=5,
        choices=DIRECTION_CHOICES,
    )
    quantity = models.IntegerField(default=1)

    entry_price = models.DecimalField(max_digits=12, decimal_places=2)
    exit_price = models.DecimalField(max_digits=12, decimal_places=2)
    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField()

    pnl = models.DecimalField(max_digits=12, decimal_places=2)
    pnl_pct = models.DecimalField(max_digits=8, decimal_places=4)
    brokerage = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    net_pnl = models.DecimalField(max_digits=12, decimal_places=2)

    # Signal context at entry
    signal = models.CharField(max_length=10)
    signal_strength = models.CharField(max_length=10, blank=True)
    signal_notes = models.TextField(blank=True)
    signal_context = models.JSONField(default=dict)

    # Exit reason
    exit_reason = models.CharField(
        max_length=20,
        choices=[
            ("SIGNAL", "Opposite Signal"),
            ("STOP_LOSS", "Stop Loss"),
            ("TARGET", "Target Hit"),
            ("EOD", "End of Day"),
            ("END_OF_DATA", "End of Data"),
        ],
        default="SIGNAL",
    )

    # Running capital after this trade
    capital_after = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    class Meta:
        db_table = "backtest_trades"
        ordering = ["entry_time"]
        indexes = [
            models.Index(fields=["run", "entry_time"]),
        ]

    def __str__(self) -> str:
        result = "WIN" if float(self.pnl) > 0 else "LOSS"
        return (
            f"{result} | {self.direction} @ "
            f"{self.entry_price} → {self.exit_price} | "
            f"₹{self.net_pnl}"
        )


class BacktestResult(BaseModel):
    """
    Aggregated statistics for a completed backtest run.
    One result per run.
    """

    run = models.OneToOneField(
        BacktestRun,
        on_delete=models.CASCADE,
        related_name="result",
    )

    # Trade statistics
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    win_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
    )

    # PnL statistics
    total_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_net_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    avg_pnl_per_trade = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_win = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_loss = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    largest_win = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    largest_loss = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_factor = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # Capital statistics
    initial_capital = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    final_capital = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_return_pct = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    max_drawdown = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_drawdown_pct = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # Risk statistics
    sharpe_ratio = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    expectancy = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    risk_reward_ratio = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    consecutive_wins = models.IntegerField(default=0)
    consecutive_losses = models.IntegerField(default=0)

    # Equity curve (stored as JSON list)
    equity_curve = models.JSONField(
        default=list,
        help_text="List of {time, capital} dicts for plotting.",
    )

    class Meta:
        db_table = "backtest_results"

    def __str__(self) -> str:
        return (
            f"{self.run.strategy.name} | "
            f"WR: {self.win_rate}% | "
            f"Return: {self.total_return_pct}%"
        )