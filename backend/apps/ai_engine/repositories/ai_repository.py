from typing import Optional

from django.db.models import QuerySet
from django.utils import timezone

from shared.repositories import BaseRepository

from ..models import AISignal, AnalysisSession, PromptTemplate


class PromptTemplateRepository(BaseRepository[PromptTemplate]):

    model = PromptTemplate

    @classmethod
    def get_by_type(cls, template_type: str) -> Optional[PromptTemplate]:
        """Return the default template for a given type."""
        return cls.model.objects.filter(
            template_type=template_type,
            is_default=True,
            is_active=True,
        ).first() or cls.model.objects.filter(
            template_type=template_type,
            is_active=True,
        ).first()

    @classmethod
    def get_by_name(cls, name: str) -> Optional[PromptTemplate]:
        """Return template by name."""
        return cls.model.objects.filter(name=name).first()


class AnalysisSessionRepository(BaseRepository[AnalysisSession]):

    model = AnalysisSession

    @classmethod
    def get_today(cls, user=None) -> QuerySet[AnalysisSession]:
        """Return today's sessions, scoped to the requesting user."""
        today = timezone.now().date()
        queryset = cls.model.objects.filter(
            session_time__date=today,
        )
        if user:
            queryset = queryset.filter(user=user)
        return queryset.select_related("instrument", "template").order_by("-session_time")

    @classmethod
    def get_by_instrument(
        cls,
        instrument,
        limit: int = 20,
    ) -> QuerySet[AnalysisSession]:
        """Return recent sessions for an instrument."""
        return cls.model.objects.filter(
            instrument=instrument,
        ).select_related("template").order_by("-session_time")[:limit]

    @classmethod
    def get_completed(cls, limit: int = 50) -> QuerySet[AnalysisSession]:
        """Return completed sessions."""
        return cls.model.objects.filter(
            status="COMPLETE",
        ).select_related("instrument").order_by("-session_time")[:limit]

    @classmethod
    def get_by_id_for_user(cls, session_id: int, user) -> Optional[AnalysisSession]:
        return cls.model.objects.filter(id=session_id, user=user).select_related(
            "instrument", "template",
        ).first()


class AISignalRepository(BaseRepository[AISignal]):

    model = AISignal

    @classmethod
    def get_today(cls, user=None) -> QuerySet[AISignal]:
        """Return today's AI signals, scoped to the requesting user."""
        today = timezone.now().date()
        queryset = cls.model.objects.filter(
            signal_time__date=today,
        )
        if user:
            queryset = queryset.filter(user=user)
        return queryset.select_related(
            "instrument", "session", "option_instrument",
        ).order_by("-signal_time")

    @classmethod
    def get_by_instrument(
        cls,
        instrument,
        limit: int = 20,
    ) -> QuerySet[AISignal]:
        """Return recent AI signals for an instrument."""
        return cls.model.objects.filter(
            instrument=instrument,
        ).order_by("-signal_time")[:limit]

    @classmethod
    def get_active(cls) -> QuerySet[AISignal]:
        """Return active AI signals."""
        return cls.model.objects.filter(
            is_active=True,
        ).select_related("instrument").order_by("-signal_time")
