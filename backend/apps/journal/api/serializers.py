from rest_framework import serializers

from ..models import JournalEntry, Lesson, TradeNote


class TradeNoteSerializer(serializers.ModelSerializer):

    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = TradeNote
        fields = [
            "id",
            "symbol",
            "setup_description",
            "entry_reason",
            "exit_reason",
            "outcome",
            "pnl",
            "followed_plan",
            "mistake_type",
            "mistake_notes",
            "improvement",
            "screenshot_url",
            "created_at",
        ]


class TradeNoteCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TradeNote
        fields = [
            "trade",
            "instrument",
            "setup_description",
            "entry_reason",
            "exit_reason",
            "outcome",
            "pnl",
            "followed_plan",
            "mistake_type",
            "mistake_notes",
            "improvement",
            "screenshot_url",
        ]


class JournalEntrySerializer(serializers.ModelSerializer):

    trade_notes = TradeNoteSerializer(many=True, read_only=True)

    class Meta:
        model = JournalEntry
        fields = [
            "id",
            "date",
            "session",
            "title",
            "market_bias",
            "market_notes",
            "trades_taken",
            "winners",
            "losers",
            "total_pnl",
            "mood",
            "emotion_notes",
            "what_worked",
            "what_didnt_work",
            "lessons_learned",
            "tomorrow_plan",
            "ai_review",
            "ai_reviewed_at",
            "rating",
            "trade_notes",
            "created_at",
            "updated_at",
        ]


class JournalEntryCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = JournalEntry
        fields = [
            "date",
            "session",
            "title",
            "market_bias",
            "market_notes",
            "trades_taken",
            "winners",
            "losers",
            "total_pnl",
            "mood",
            "emotion_notes",
            "what_worked",
            "what_didnt_work",
            "lessons_learned",
            "tomorrow_plan",
            "rating",
        ]


class LessonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "content",
            "category",
            "is_rule",
            "times_reinforced",
            "created_at",
            "updated_at",
        ]


class LessonCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Lesson
        fields = [
            "title",
            "content",
            "category",
            "is_rule",
        ]