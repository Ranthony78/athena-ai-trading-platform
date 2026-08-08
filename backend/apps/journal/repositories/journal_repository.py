from typing import Optional

from django.db.models import QuerySet, Sum, Avg
from django.utils import timezone

from shared.repositories import BaseRepository

from ..models import JournalEntry, Lesson, TradeNote


class JournalEntryRepository(BaseRepository[JournalEntry]):

    model = JournalEntry

    @classmethod
    def get_by_user(
        cls,
        user,
        limit: int = 30,
    ) -> QuerySet[JournalEntry]:
        """Return recent journal entries for a user."""
        return cls.model.objects.filter(
            user=user,
        ).prefetch_related("trade_notes").order_by("-date")[:limit]

    @classmethod
    def get_by_date(
        cls,
        user,
        date,
    ) -> QuerySet[JournalEntry]:
        """Return all entries for a specific date."""
        return cls.model.objects.filter(
            user=user,
            date=date,
        ).prefetch_related("trade_notes")

    @classmethod
    def get_today(cls, user) -> QuerySet[JournalEntry]:
        """Return today's entries."""
        return cls.get_by_date(user, timezone.now().date())

    @classmethod
    def get_by_id_for_user(
        cls,
        user,
        entry_id: int,
    ) -> Optional[JournalEntry]:
        """Return a single entry owned by the user."""
        return cls.model.objects.filter(
            id=entry_id,
            user=user,
        ).prefetch_related("trade_notes", "lessons").first()

    @classmethod
    def get_stats(cls, user) -> dict:
        """Return journal statistics for a user."""
        entries = cls.model.objects.filter(user=user)
        total = entries.count()

        if total == 0:
            return {
                "total_entries": 0,
                "avg_rating": 0,
                "total_pnl": 0,
                "total_trades": 0,
                "best_day": None,
                "worst_day": None,
            }

        aggregates = entries.aggregate(
            avg_rating=Avg("rating"),
            total_pnl=Sum("total_pnl"),
            total_trades=Sum("trades_taken"),
        )

        best = entries.order_by("-total_pnl").first()
        worst = entries.order_by("total_pnl").first()

        return {
            "total_entries": total,
            "avg_rating": round(float(aggregates["avg_rating"] or 0), 1),
            "total_pnl": float(aggregates["total_pnl"] or 0),
            "total_trades": aggregates["total_trades"] or 0,
            "best_day": {
                "date": str(best.date),
                "pnl": float(best.total_pnl),
            } if best else None,
            "worst_day": {
                "date": str(worst.date),
                "pnl": float(worst.total_pnl),
            } if worst else None,
        }


class TradeNoteRepository(BaseRepository[TradeNote]):

    model = TradeNote

    @classmethod
    def get_by_entry(
        cls,
        entry: JournalEntry,
    ) -> QuerySet[TradeNote]:
        """Return all trade notes for a journal entry."""
        return cls.model.objects.filter(
            journal_entry=entry,
        ).select_related("instrument", "trade")

    @classmethod
    def get_mistakes(cls, user) -> QuerySet[TradeNote]:
        """Return all trade notes with mistakes."""
        return cls.model.objects.filter(
            journal_entry__user=user,
        ).exclude(
            mistake_type="NONE",
        ).select_related("instrument").order_by("-created_at")


class LessonRepository(BaseRepository[Lesson]):

    model = Lesson

    @classmethod
    def get_by_user(
        cls,
        user,
        category: str = None,
    ) -> QuerySet[Lesson]:
        """Return lessons for a user, optionally filtered by category."""
        qs = cls.model.objects.filter(user=user)
        if category:
            qs = qs.filter(category=category)
        return qs.order_by("-times_reinforced", "-created_at")

    @classmethod
    def get_rules(cls, user) -> QuerySet[Lesson]:
        """Return hard trading rules."""
        return cls.model.objects.filter(
            user=user,
            is_rule=True,
        ).order_by("category")