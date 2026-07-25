import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.ai_review_service import AIReviewService
from ..services.journal_service import JournalService
from .serializers import (
    JournalEntryCreateSerializer,
    JournalEntrySerializer,
    LessonCreateSerializer,
    LessonSerializer,
    TradeNoteCreateSerializer,
    TradeNoteSerializer,
)

logger = logging.getLogger(__name__)


class JournalEntryListAPIView(APIView):
    """
    GET  /api/journal/entries/     — list entries
    POST /api/journal/entries/     — create entry
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            date = request.query_params.get("date")
            limit = int(request.query_params.get("limit", 30))

            if date:
                entries = JournalService.get_by_date(request.user, date)
            else:
                entries = JournalService.get_entries(request.user, limit)

            serializer = JournalEntrySerializer(entries, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"JournalEntryListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch journal entries.")

    def post(self, request):
        serializer = JournalEntryCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )

        try:
            entry = JournalService.create_entry(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=JournalEntrySerializer(entry).data,
                message="Journal entry created.",
            )
        except Exception as e:
            logger.error(f"JournalEntryListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to create journal entry.")


class JournalEntryDetailAPIView(APIView):
    """
    GET    /api/journal/entries/<id>/  — get entry
    PUT    /api/journal/entries/<id>/  — update entry
    DELETE /api/journal/entries/<id>/  — delete entry
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        entry = JournalService.get_entry(request.user, pk)
        if not entry:
            return ApiResponse.error(message="Journal entry not found.")
        return ApiResponse.success(JournalEntrySerializer(entry).data)

    def put(self, request, pk: int):
        entry = JournalService.get_entry(request.user, pk)
        if not entry:
            return ApiResponse.error(message="Journal entry not found.")

        serializer = JournalEntryCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )

        try:
            updated = JournalService.update_entry(
                entry=entry,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=JournalEntrySerializer(updated).data,
                message="Journal entry updated.",
            )
        except Exception as e:
            logger.error(f"JournalEntryDetailAPIView PUT error: {e}")
            return ApiResponse.error(message="Failed to update journal entry.")

    def delete(self, request, pk: int):
        entry = JournalService.get_entry(request.user, pk)
        if not entry:
            return ApiResponse.error(message="Journal entry not found.")

        JournalService.delete_entry(entry)
        return ApiResponse.success(message="Journal entry deleted.")


class JournalAIReviewAPIView(APIView):
    """
    POST /api/journal/entries/<id>/review/
    Generate AI review for a journal entry.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        entry = JournalService.get_entry(request.user, pk)
        if not entry:
            return ApiResponse.error(message="Journal entry not found.")

        try:
            service = AIReviewService()
            review = service.review_entry(entry)
            return ApiResponse.success(
                data={"review": review},
                message="AI review generated.",
            )
        except Exception as e:
            logger.error(f"JournalAIReviewAPIView error: {e}")
            return ApiResponse.error(message="Failed to generate AI review.")


class JournalStatsAPIView(APIView):
    """
    GET /api/journal/stats/
    Return journal statistics for the user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            stats = JournalService.get_stats(request.user)
            return ApiResponse.success(stats)
        except Exception as e:
            logger.error(f"JournalStatsAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch stats.")


class TradeNoteListAPIView(APIView):
    """
    GET  /api/journal/entries/<id>/notes/  — list trade notes
    POST /api/journal/entries/<id>/notes/  — add trade note
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        entry = JournalService.get_entry(request.user, pk)
        if not entry:
            return ApiResponse.error(message="Journal entry not found.")

        notes = JournalService.get_trade_notes(entry)
        serializer = TradeNoteSerializer(notes, many=True)
        return ApiResponse.success(serializer.data)

    def post(self, request, pk: int):
        entry = JournalService.get_entry(request.user, pk)
        if not entry:
            return ApiResponse.error(message="Journal entry not found.")

        serializer = TradeNoteCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )

        try:
            note = JournalService.add_trade_note(
                entry=entry,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=TradeNoteSerializer(note).data,
                message="Trade note added.",
            )
        except Exception as e:
            logger.error(f"TradeNoteListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to add trade note.")


class MistakeListAPIView(APIView):
    """
    GET /api/journal/mistakes/
    Return all trades with mistakes for pattern analysis.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            mistakes = JournalService.get_mistakes(request.user)
            serializer = TradeNoteSerializer(mistakes, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"MistakeListAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch mistakes.")


class LessonListAPIView(APIView):
    """
    GET  /api/journal/lessons/  — list lessons
    POST /api/journal/lessons/  — add lesson
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            category = request.query_params.get("category")
            lessons = JournalService.get_lessons(request.user, category)
            serializer = LessonSerializer(lessons, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"LessonListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch lessons.")

    def post(self, request):
        serializer = LessonCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )

        try:
            lesson = JournalService.add_lesson(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=LessonSerializer(lesson).data,
                message="Lesson added.",
            )
        except Exception as e:
            logger.error(f"LessonListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to add lesson.")


class RuleListAPIView(APIView):
    """
    GET /api/journal/rules/
    Return all hard trading rules.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            rules = JournalService.get_rules(request.user)
            serializer = LessonSerializer(rules, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"RuleListAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch rules.")


class LessonReinforceAPIView(APIView):
    """
    POST /api/journal/lessons/<id>/reinforce/
    Increment reinforcement count on a lesson.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        try:
            from ..repositories.journal_repository import LessonRepository
            lesson = LessonRepository.get_by_id(pk)

            if not lesson or lesson.user != request.user:
                return ApiResponse.error(message="Lesson not found.")

            lesson = JournalService.reinforce_lesson(lesson)
            return ApiResponse.success(
                data=LessonSerializer(lesson).data,
                message="Lesson reinforced.",
            )
        except Exception as e:
            logger.error(f"LessonReinforceAPIView error: {e}")
            return ApiResponse.error(message="Failed to reinforce lesson.")