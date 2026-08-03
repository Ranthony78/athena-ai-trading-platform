from django.contrib import admin

from .models import JournalEntry, Lesson, TradeNote


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "date",
        "session",
        "market_bias",
        "mood",
        "trades_taken",
        "total_pnl",
        "rating",
    )
    list_filter = ("session", "market_bias", "mood")
    search_fields = ("user__username", "title")
    readonly_fields = ("ai_review", "ai_reviewed_at")


@admin.register(TradeNote)
class TradeNoteAdmin(admin.ModelAdmin):

    list_display = (
        "instrument",
        "outcome",
        "pnl",
        "followed_plan",
        "mistake_type",
        "created_at",
    )
    list_filter = ("outcome", "followed_plan", "mistake_type")
    search_fields = ("instrument__symbol",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "title",
        "category",
        "is_rule",
        "times_reinforced",
        "created_at",
    )
    list_filter = ("category", "is_rule")
    search_fields = ("title", "content")