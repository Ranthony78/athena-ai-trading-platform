from django.db import models
from django.contrib.auth import get_user_model

from apps.market_data.models import Instrument
from apps.paper_trading.models import PaperTrade
from shared.models import BaseModel

User = get_user_model()


class JournalEntry(BaseModel):
    """
    A daily trading journal entry.
    Records market observations, trades, emotions, and lessons.
    """

    MOOD_CHOICES = [
        ("CONFIDENT", "Confident"),
        ("NEUTRAL", "Neutral"),
        ("ANXIOUS", "Anxious"),
        ("FEARFUL", "Fearful"),
        ("GREEDY", "Greedy"),
        ("DISCIPLINED", "Disciplined"),
    ]

    SESSION_CHOICES = [
        ("PRE_MARKET", "Pre Market"),
        ("INTRADAY", "Intraday"),
        ("POST_MARKET", "Post Market"),
        ("EOD", "End of Day"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="journal_entries",
    )

    date = models.DateField(db_index=True)
    session = models.CharField(
        max_length=15,
        choices=SESSION_CHOICES,
        default="EOD",
    )
    title = models.CharField(max_length=200)

    # Market observations
    market_bias = models.CharField(
        max_length=10,
        choices=[
            ("BULLISH", "Bullish"),
            ("BEARISH", "Bearish"),
            ("NEUTRAL", "Neutral"),
        ],
        blank=True,
    )
    market_notes = models.TextField(
        blank=True,
        help_text="Market structure, key levels, observations.",
    )

    # Trade summary
    trades_taken = models.IntegerField(default=0)
    winners = models.IntegerField(default=0)
    losers = models.IntegerField(default=0)
    total_pnl = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    # Psychology
    mood = models.CharField(
        max_length=15,
        choices=MOOD_CHOICES,
        blank=True,
    )
    emotion_notes = models.TextField(
        blank=True,
        help_text="Emotional state and psychological observations.",
    )

    # Lessons
    what_worked = models.TextField(blank=True)
    what_didnt_work = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)
    tomorrow_plan = models.TextField(blank=True)

    # AI Review
    ai_review = models.TextField(
        blank=True,
        help_text="AI-generated review of the journal entry.",
    )
    ai_reviewed_at = models.DateTimeField(null=True, blank=True)

    # Rating
    rating = models.IntegerField(
        default=0,
        help_text="Self-rating for the day 1-10.",
    )

    class Meta:
        db_table = "journal_entries"
        ordering = ["-date"]
        unique_together = [("user", "date", "session")]
        indexes = [
            models.Index(fields=["user", "date"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} | {self.date} | {self.session}"


class TradeNote(BaseModel):
    """
    Detailed notes attached to a specific trade.
    Links a journal entry to a paper trade with analysis.
    """

    OUTCOME_CHOICES = [
        ("WIN", "Win"),
        ("LOSS", "Loss"),
        ("BREAKEVEN", "Breakeven"),
    ]

    MISTAKE_CHOICES = [
        ("NONE", "No Mistake"),
        ("EARLY_ENTRY", "Early Entry"),
        ("LATE_ENTRY", "Late Entry"),
        ("EARLY_EXIT", "Early Exit"),
        ("LATE_EXIT", "Late Exit"),
        ("OVERSIZE", "Oversized Position"),
        ("NO_SL", "No Stop Loss"),
        ("REVENGE", "Revenge Trade"),
        ("FOMO", "FOMO Trade"),
        ("PLAN_DEVIATION", "Deviated from Plan"),
    ]

    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name="trade_notes",
    )
    trade = models.OneToOneField(
        PaperTrade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="journal_note",
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Trade details
    setup_description = models.TextField(
        help_text="Describe the setup that triggered this trade.",
    )
    entry_reason = models.TextField(blank=True)
    exit_reason = models.TextField(blank=True)

    outcome = models.CharField(
        max_length=10,
        choices=OUTCOME_CHOICES,
        blank=True,
    )
    pnl = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    # Analysis
    followed_plan = models.BooleanField(default=True)
    mistake_type = models.CharField(
        max_length=20,
        choices=MISTAKE_CHOICES,
        default="NONE",
    )
    mistake_notes = models.TextField(blank=True)
    improvement = models.TextField(
        blank=True,
        help_text="What would you do differently?",
    )

    # Screenshot
    screenshot_url = models.URLField(blank=True)

    class Meta:
        db_table = "journal_trade_notes"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        symbol = self.instrument.symbol if self.instrument else "N/A"
        return f"{symbol} | {self.outcome} | ₹{self.pnl}"


class Lesson(BaseModel):
    """
    A trading lesson extracted from journal entries.
    Builds a personal knowledge base over time.
    """

    CATEGORY_CHOICES = [
        ("ENTRY", "Entry Rules"),
        ("EXIT", "Exit Rules"),
        ("RISK", "Risk Management"),
        ("PSYCHOLOGY", "Psychology"),
        ("STRATEGY", "Strategy"),
        ("MARKET", "Market Observation"),
        ("GENERAL", "General"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="lessons",
    )
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lessons",
    )

    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(
        max_length=15,
        choices=CATEGORY_CHOICES,
        default="GENERAL",
        db_index=True,
    )

    times_reinforced = models.IntegerField(
        default=1,
        help_text="How many times this lesson was relearned.",
    )
    is_rule = models.BooleanField(
        default=False,
        help_text="Mark as a hard trading rule.",
    )

    class Meta:
        db_table = "journal_lessons"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "category"]),
        ]

    def __str__(self) -> str:
        return f"{self.category} | {self.title}"