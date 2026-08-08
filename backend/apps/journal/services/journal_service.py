import logging
from typing import Optional

from django.db.models import QuerySet
from django.utils import timezone

from ..models import JournalEntry, Lesson, TradeNote
from ..repositories.journal_repository import (
    JournalEntryRepository,
    LessonRepository,
    TradeNoteRepository,
)

logger = logging.getLogger(__name__)


class JournalService:
    """
    Business logic for journal entry management.
    """

    # ------------------------------------------------------------------
    # Journal Entries
    # ------------------------------------------------------------------

    @staticmethod
    def get_entries(user, limit: int = 30) -> QuerySet[JournalEntry]:
        """Return recent journal entries."""
        return JournalEntryRepository.get_by_user(user, limit)

    @staticmethod
    def get_today(user) -> QuerySet[JournalEntry]:
        """Return today's entries."""
        return JournalEntryRepository.get_today(user)

    @staticmethod
    def get_by_date(user, date) -> QuerySet[JournalEntry]:
        """Return entries for a specific date."""
        return JournalEntryRepository.get_by_date(user, date)

    @staticmethod
    def get_entry(user, entry_id: int) -> Optional[JournalEntry]:
        """Return a single entry."""
        return JournalEntryRepository.get_by_id_for_user(user, entry_id)

    @staticmethod
    def create_entry(user, data: dict) -> JournalEntry:
        """Create a new journal entry."""
        data["user"] = user
        if "date" not in data:
            data["date"] = timezone.now().date()
        return JournalEntryRepository.create(**data)

    @staticmethod
    def update_entry(entry: JournalEntry, data: dict) -> JournalEntry:
        """Update an existing journal entry."""
        return JournalEntryRepository.update(entry, **data)

    @staticmethod
    def delete_entry(entry: JournalEntry) -> None:
        """Soft delete a journal entry."""
        JournalEntryRepository.soft_delete(entry)

    @staticmethod
    def get_stats(user) -> dict:
        """Return journal statistics."""
        return JournalEntryRepository.get_stats(user)

    # ------------------------------------------------------------------
    # Trade Notes
    # ------------------------------------------------------------------

    @staticmethod
    def add_trade_note(entry: JournalEntry, data: dict) -> TradeNote:
        """Add a trade note to a journal entry."""
        data["journal_entry"] = entry
        return TradeNoteRepository.create(**data)

    @staticmethod
    def get_trade_notes(entry: JournalEntry) -> QuerySet[TradeNote]:
        """Return trade notes for an entry."""
        return TradeNoteRepository.get_by_entry(entry)

    @staticmethod
    def get_mistakes(user) -> QuerySet[TradeNote]:
        """Return all mistake trades."""
        return TradeNoteRepository.get_mistakes(user)

    # ------------------------------------------------------------------
    # Lessons
    # ------------------------------------------------------------------

    @staticmethod
    def add_lesson(user, data: dict) -> Lesson:
        """Add a new lesson."""
        data["user"] = user
        return LessonRepository.create(**data)

    @staticmethod
    def get_lessons(
        user,
        category: str = None,
    ) -> QuerySet[Lesson]:
        """Return lessons for a user."""
        return LessonRepository.get_by_user(user, category)

    @staticmethod
    def get_rules(user) -> QuerySet[Lesson]:
        """Return hard trading rules."""
        return LessonRepository.get_rules(user)

    @staticmethod
    def reinforce_lesson(lesson: Lesson) -> Lesson:
        """Increment reinforcement count on a lesson."""
        lesson.times_reinforced += 1
        lesson.save()
        return lesson