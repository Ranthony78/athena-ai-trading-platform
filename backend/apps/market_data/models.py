from django.db import models

from shared.models import BaseModel


class Instrument(BaseModel):
    """
    Represents a tradeable instrument — equity, index, future, or option.
    
    Key design decisions:
    - symbol: underlying name (NIFTY, BANKNIFTY, RELIANCE) — NOT unique
    - trading_symbol: Zerodha's unique identifier per contract — unique per exchange
    - instrument_token: Zerodha's numeric ID — globally unique
    """

    EXCHANGE_CHOICES = [
        ("NSE", "NSE"),
        ("BSE", "BSE"),
        ("NFO", "NFO"),
        ("MCX", "MCX"),
    ]

    OPTION_TYPE_CHOICES = [
        ("", "N/A"),
        ("CE", "CE"),
        ("PE", "PE"),
    ]

    INSTRUMENT_TYPE_CHOICES = [
        ("EQ", "Equity"),
        ("IDX", "Index"),
        ("FUT", "Future"),
        ("CE", "Call Option"),
        ("PE", "Put Option"),
    ]

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    instrument_token = models.BigIntegerField(
        unique=True,
        db_index=True,
        help_text="Zerodha's unique numeric token for this instrument.",
    )

    exchange_token = models.BigIntegerField(
        default=0,
        help_text="Exchange-level token.",
    )

    exchange = models.CharField(
        max_length=10,
        choices=EXCHANGE_CHOICES,
        db_index=True,
    )

    symbol = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Underlying symbol — e.g. NIFTY, RELIANCE. Not unique for derivatives.",
    )

    trading_symbol = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Zerodha trading symbol — unique per exchange e.g. NIFTY2572524000CE.",
    )

    instrument_type = models.CharField(
        max_length=10,
        choices=INSTRUMENT_TYPE_CHOICES,
        default="EQ",
        db_index=True,
    )

    # ------------------------------------------------------------------
    # Contract Details
    # ------------------------------------------------------------------

    lot_size = models.IntegerField(default=1)

    tick_size = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
    )

    # ------------------------------------------------------------------
    # Derivative Fields (null for equities/indices)
    # ------------------------------------------------------------------

    expiry = models.DateField(
        null=True,
        blank=True,
        db_index=True,
    )

    strike = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    option_type = models.CharField(
        max_length=2,
        choices=OPTION_TYPE_CHOICES,
        blank=True,
        default="",
        db_index=True,
    )

    class Meta:
        db_table = "market_instruments"
        ordering = ["symbol", "expiry", "strike"]
        # trading_symbol is unique within an exchange
        unique_together = [("exchange", "trading_symbol")]
        indexes = [
            models.Index(fields=["symbol", "exchange"]),
            models.Index(fields=["symbol", "expiry", "option_type"]),
            models.Index(fields=["instrument_token"]),
        ]

    def __str__(self) -> str:
        return self.trading_symbol

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_index(self) -> bool:
        """True if this is an index instrument."""
        return self.instrument_type == "IDX"

    @property
    def is_option(self) -> bool:
        """True if this is a CE or PE option."""
        return self.option_type in ("CE", "PE")

    @property
    def is_future(self) -> bool:
        """True if this is a futures contract."""
        return self.instrument_type == "FUT"

    @property
    def is_equity(self) -> bool:
        """True if this is an equity instrument."""
        return self.instrument_type == "EQ"


class Quote(BaseModel):
    """
    Real-time price snapshot for an instrument.
    Updated on every market tick from the live engine.
    One quote per instrument (OneToOne).
    """

    instrument = models.OneToOneField(
        Instrument,
        on_delete=models.CASCADE,
        related_name="quote",
    )

    last_price = models.DecimalField(max_digits=12, decimal_places=2)
    open_price = models.DecimalField(max_digits=12, decimal_places=2)
    high_price = models.DecimalField(max_digits=12, decimal_places=2)
    low_price = models.DecimalField(max_digits=12, decimal_places=2)
    close_price = models.DecimalField(max_digits=12, decimal_places=2)

    change = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    change_percent = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0,
    )

    volume = models.BigIntegerField(default=0)
    oi = models.BigIntegerField(default=0)

    bid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ask = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    bid_qty = models.BigIntegerField(default=0)
    ask_qty = models.BigIntegerField(default=0)

    class Meta:
        db_table = "market_quotes"

    def __str__(self) -> str:
        return f"{self.instrument.trading_symbol} @ {self.last_price}"


class Candle(BaseModel):
    """
    OHLCV candle for an instrument at a given timeframe.
    Used for technical analysis and backtesting.
    """

    TIMEFRAME_CHOICES = [
        ("1m", "1 Minute"),
        ("3m", "3 Minute"),
        ("5m", "5 Minute"),
        ("15m", "15 Minute"),
        ("30m", "30 Minute"),
        ("1h", "1 Hour"),
        ("1d", "1 Day"),
    ]

    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="candles",
    )

    timeframe = models.CharField(
        max_length=10,
        choices=TIMEFRAME_CHOICES,
        db_index=True,
    )

    candle_time = models.DateTimeField(db_index=True)

    open = models.DecimalField(max_digits=12, decimal_places=2)
    high = models.DecimalField(max_digits=12, decimal_places=2)
    low = models.DecimalField(max_digits=12, decimal_places=2)
    close = models.DecimalField(max_digits=12, decimal_places=2)

    volume = models.BigIntegerField(default=0)

    class Meta:
        db_table = "market_candles"
        ordering = ["-candle_time"]
        # Prevent duplicate candles for same instrument+timeframe+time
        unique_together = [("instrument", "timeframe", "candle_time")]
        indexes = [
            models.Index(fields=["instrument", "timeframe", "candle_time"]),
        ]

    def __str__(self) -> str:
        return f"{self.instrument.trading_symbol} {self.timeframe} @ {self.candle_time}"