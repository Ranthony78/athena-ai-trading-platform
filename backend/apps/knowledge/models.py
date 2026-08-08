from django.db import models
from django.contrib.auth import get_user_model

from shared.models import BaseModel

User = get_user_model()


class Tag(BaseModel):
    """
    Tag for categorizing knowledge base content.
    """

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        help_text="Hex color code for UI display.",
    )

    class Meta:
        db_table = "knowledge_tags"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Article(BaseModel):
    """
    A knowledge base article.
    Can be a trading concept, strategy note, market observation,
    or imported content from external sources.
    """

    CATEGORY_CHOICES = [
        ("CONCEPT", "Trading Concept"),
        ("STRATEGY", "Strategy"),
        ("INDICATOR", "Technical Indicator"),
        ("OPTION", "Options Theory"),
        ("PSYCHOLOGY", "Psychology"),
        ("RISK", "Risk Management"),
        ("MARKET", "Market Structure"),
        ("ZERODHA", "Zerodha Varsity"),
        ("BOOK", "Book Notes"),
        ("RESEARCH", "Research"),
        ("OTHER", "Other"),
    ]

    SOURCE_CHOICES = [
        ("MANUAL", "Manual Entry"),
        ("VARSITY", "Zerodha Varsity"),
        ("BOOK", "Book"),
        ("BLOG", "Blog/Article"),
        ("VIDEO", "Video"),
        ("AI", "AI Generated"),
        ("TRANSCRIPT", "Transcript"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles",
    )

    title = models.CharField(max_length=300, db_index=True)
    slug = models.SlugField(max_length=300, unique=True)
    category = models.CharField(
        max_length=15,
        choices=CATEGORY_CHOICES,
        default="CONCEPT",
        db_index=True,
    )
    source = models.CharField(
        max_length=15,
        choices=SOURCE_CHOICES,
        default="MANUAL",
    )
    source_url = models.URLField(blank=True)

    content = models.TextField()
    summary = models.TextField(
        blank=True,
        help_text="Short summary — AI generated or manual.",
    )
    key_points = models.JSONField(
        default=list,
        help_text="List of key takeaways.",
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="articles",
    )

    # AI Summary
    ai_summary = models.TextField(blank=True)
    ai_summarized_at = models.DateTimeField(null=True, blank=True)

    # Engagement
    view_count = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)

    class Meta:
        db_table = "knowledge_articles"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["user", "category"]),
        ]

    def __str__(self) -> str:
        return self.title


class BookNote(BaseModel):
    """
    Notes from a trading book.
    Groups articles and highlights from a single book.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="book_notes",
    )

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200, blank=True)
    isbn = models.CharField(max_length=20, blank=True)

    summary = models.TextField(blank=True)
    key_lessons = models.JSONField(
        default=list,
        help_text="List of key lessons from the book.",
    )
    rating = models.IntegerField(
        default=0,
        help_text="Personal rating 1-10.",
    )

    articles = models.ManyToManyField(
        Article,
        blank=True,
        related_name="books",
    )

    started_at = models.DateField(null=True, blank=True)
    finished_at = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "knowledge_book_notes"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} by {self.author}"


class TradingRule(BaseModel):
    """
    A hard trading rule extracted from experience or books.
    The personal rulebook — enforced by discipline.
    """

    RULE_TYPE_CHOICES = [
        ("ENTRY", "Entry Rule"),
        ("EXIT", "Exit Rule"),
        ("RISK", "Risk Rule"),
        ("PSYCHOLOGY", "Psychology Rule"),
        ("SYSTEM", "System Rule"),
    ]

    PRIORITY_CHOICES = [
        ("CRITICAL", "Critical — Never Break"),
        ("HIGH", "High — Rarely Break"),
        ("MEDIUM", "Medium — Use Judgment"),
        ("LOW", "Low — Guideline"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="trading_rules",
    )

    rule_number = models.IntegerField(
        help_text="Rule number for ordering.",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    rule_type = models.CharField(
        max_length=15,
        choices=RULE_TYPE_CHOICES,
        default="SYSTEM",
        db_index=True,
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="HIGH",
    )

    # How many times this rule was broken
    times_broken = models.IntegerField(default=0)
    last_broken_at = models.DateTimeField(null=True, blank=True)

    source_article = models.ForeignKey(
        Article,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rules",
    )

    class Meta:
        db_table = "knowledge_trading_rules"
        ordering = ["rule_number"]
        unique_together = [("user", "rule_number")]
        indexes = [
            models.Index(fields=["user", "rule_type"]),
            models.Index(fields=["user", "priority"]),
        ]

    def __str__(self) -> str:
        return f"Rule #{self.rule_number}: {self.title}"


class Prompt(BaseModel):
    """
    Stored AI prompts for the prompt library.
    Reusable prompts for analysis, research, and strategy development.
    """

    PROMPT_TYPE_CHOICES = [
        ("ANALYSIS", "Market Analysis"),
        ("RESEARCH", "Research"),
        ("STRATEGY", "Strategy Development"),
        ("REVIEW", "Trade Review"),
        ("LEARNING", "Learning"),
        ("CUSTOM", "Custom"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="prompts",
    )

    title = models.CharField(max_length=200)
    prompt_type = models.CharField(
        max_length=15,
        choices=PROMPT_TYPE_CHOICES,
        default="CUSTOM",
        db_index=True,
    )
    content = models.TextField()
    description = models.TextField(blank=True)

    tags = models.ManyToManyField(
        Tag,
        blank=True,
    )

    use_count = models.IntegerField(default=0)
    is_public = models.BooleanField(default=False)

    class Meta:
        db_table = "knowledge_prompts"
        ordering = ["-use_count", "-created_at"]

    def __str__(self) -> str:
        return self.title