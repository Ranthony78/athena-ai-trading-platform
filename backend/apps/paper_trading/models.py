from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model

from apps.market_data.models import Instrument
from shared.models import BaseModel

User = get_user_model()


class PaperAccount(BaseModel):
    """
    Virtual trading account for paper trading.
    Each user has one paper account.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="paper_account",
    )

    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("1000000.00"),
        help_text="Available cash balance.",
    )
    initial_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("1000000.00"),
    )
    used_margin = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    total_pnl = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Cumulative realized PnL.",
    )
    today_pnl = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)

    class Meta:
        db_table = "paper_accounts"

    def __str__(self) -> str:
        return f"{self.user.username} — ₹{self.balance}"

    @property
    def win_rate(self) -> float:
        """Return win rate as percentage."""
        if self.total_trades == 0:
            return 0.0
        return round(self.winning_trades / self.total_trades * 100, 2)

    @property
    def available_balance(self) -> float:
        """Return available balance after margin."""
        return float(self.balance) - float(self.used_margin)

    @property
    def total_return_pct(self) -> float:
        """Return total return as percentage."""
        if self.initial_balance == 0:
            return 0.0
        return round(
            float(self.total_pnl) / float(self.initial_balance) * 100, 2
        )


class PaperOrder(BaseModel):
    """
    A paper trading order.
    Mimics a real broker order without actual execution.
    """

    ORDER_TYPE_CHOICES = [
        ("MARKET", "Market"),
        ("LIMIT", "Limit"),
        ("SL", "Stop Loss"),
        ("SL_M", "Stop Loss Market"),
    ]

    TRANSACTION_TYPE_CHOICES = [
        ("BUY", "Buy"),
        ("SELL", "Sell"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("OPEN", "Open"),
        ("COMPLETE", "Complete"),
        ("CANCELLED", "Cancelled"),
        ("REJECTED", "Rejected"),
    ]

    PRODUCT_CHOICES = [
        ("MIS", "Intraday (MIS)"),
        ("NRML", "Normal (NRML)"),
        ("CNC", "Delivery (CNC)"),
    ]

    account = models.ForeignKey(
        PaperAccount,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="paper_orders",
    )

    order_type = models.CharField(
        max_length=10,
        choices=ORDER_TYPE_CHOICES,
        default="MARKET",
    )
    transaction_type = models.CharField(
        max_length=5,
        choices=TRANSACTION_TYPE_CHOICES,
        db_index=True,
    )
    product = models.CharField(
        max_length=5,
        choices=PRODUCT_CHOICES,
        default="MIS",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
    )

    quantity = models.IntegerField()
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Limit price. 0 for market orders.",
    )
    trigger_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Trigger price for SL orders.",
    )
    average_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Actual execution price.",
    )

    filled_quantity = models.IntegerField(default=0)
    pending_quantity = models.IntegerField(default=0)

    order_time = models.DateTimeField(auto_now_add=True, db_index=True)
    execution_time = models.DateTimeField(null=True, blank=True)

    # Source of the order
    tag = models.CharField(
        max_length=50,
        blank=True,
        help_text="Tag to identify order source e.g. strategy name.",
    )
    notes = models.TextField(blank=True)
    reject_reason = models.TextField(blank=True)

    class Meta:
        db_table = "paper_orders"
        ordering = ["-order_time"]
        indexes = [
            models.Index(fields=["account", "status"]),
            models.Index(fields=["account", "order_time"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.transaction_type} {self.quantity} "
            f"{self.instrument.symbol} @ {self.price} [{self.status}]"
        )


class PaperPosition(BaseModel):
    """
    An open paper trading position.
    Created when an order is executed, updated on partial fills.
    """

    DIRECTION_CHOICES = [
        ("LONG", "Long"),
        ("SHORT", "Short"),
    ]

    account = models.ForeignKey(
        PaperAccount,
        on_delete=models.CASCADE,
        related_name="positions",
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="paper_positions",
    )

    direction = models.CharField(
        max_length=5,
        choices=DIRECTION_CHOICES,
    )
    quantity = models.IntegerField()
    average_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    last_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    unrealized_pnl = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    realized_pnl = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    open_time = models.DateTimeField(auto_now_add=True)
    close_time = models.DateTimeField(null=True, blank=True)
    is_open = models.BooleanField(default=True, db_index=True)

    product = models.CharField(max_length=5, default="MIS")
    tag = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "paper_positions"
        ordering = ["-open_time"]
        indexes = [
            models.Index(fields=["account", "is_open"]),
            models.Index(fields=["account", "instrument"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.direction} {self.quantity} "
            f"{self.instrument.symbol} @ {self.average_price}"
        )

    @property
    def current_value(self) -> float:
        """Current market value of the position."""
        return float(self.quantity) * float(self.last_price)

    @property
    def invested_value(self) -> float:
        """Original invested value."""
        return float(self.quantity) * float(self.average_price)

    @property
    def pnl_pct(self) -> float:
        """PnL as percentage of invested value."""
        if self.invested_value == 0:
            return 0.0
        return round(
            float(self.unrealized_pnl) / self.invested_value * 100, 2
        )


class PaperTrade(BaseModel):
    """
    A completed paper trade — records the full lifecycle.
    Created when a position is closed.
    Used for journaling and backtesting.
    """

    account = models.ForeignKey(
        PaperAccount,
        on_delete=models.CASCADE,
        related_name="trades",
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="paper_trades",
    )
    position = models.OneToOneField(
        PaperPosition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trade",
    )

    direction = models.CharField(max_length=5)
    quantity = models.IntegerField()

    entry_price = models.DecimalField(max_digits=12, decimal_places=2)
    exit_price = models.DecimalField(max_digits=12, decimal_places=2)

    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField()

    pnl = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Realized PnL for this trade.",
    )
    pnl_pct = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0,
    )

    brokerage = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
    )
    net_pnl = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="PnL after brokerage.",
    )

    product = models.CharField(max_length=5, default="MIS")
    tag = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    # Source signals
    strategy_signal = models.CharField(max_length=50, blank=True)
    ai_signal = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "paper_trades"
        ordering = ["-exit_time"]
        indexes = [
            models.Index(fields=["account", "exit_time"]),
            models.Index(fields=["instrument", "exit_time"]),
        ]

    def __str__(self) -> str:
        result = "WIN" if float(self.pnl) > 0 else "LOSS"
        return (
            f"{result} | {self.direction} {self.quantity} "
            f"{self.instrument.symbol} | ₹{self.pnl}"
        )