from rest_framework import serializers
from ..models import Article, BookNote, Prompt, Tag, TradingRule


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "color"]


class ArticleListSerializer(serializers.ModelSerializer):

    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "source",
            "summary",
            "tags",
            "is_featured",
            "view_count",
            "created_at",
        ]


class ArticleDetailSerializer(serializers.ModelSerializer):

    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "source",
            "source_url",
            "content",
            "summary",
            "key_points",
            "ai_summary",
            "ai_summarized_at",
            "tags",
            "is_featured",
            "view_count",
            "created_at",
            "updated_at",
        ]


class ArticleCreateSerializer(serializers.ModelSerializer):

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Article
        fields = [
            "title",
            "slug",
            "category",
            "source",
            "source_url",
            "content",
            "summary",
            "key_points",
            "tags",
            "is_featured",
        ]


class BookNoteSerializer(serializers.ModelSerializer):

    class Meta:
        model = BookNote
        fields = [
            "id",
            "title",
            "author",
            "isbn",
            "summary",
            "key_lessons",
            "rating",
            "started_at",
            "finished_at",
            "created_at",
        ]


class TradingRuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = TradingRule
        fields = [
            "id",
            "rule_number",
            "title",
            "description",
            "rule_type",
            "priority",
            "times_broken",
            "last_broken_at",
            "is_active",
            "created_at",
        ]


class TradingRuleCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TradingRule
        fields = [
            "rule_number",
            "title",
            "description",
            "rule_type",
            "priority",
        ]


class PromptSerializer(serializers.ModelSerializer):

    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Prompt
        fields = [
            "id",
            "title",
            "prompt_type",
            "content",
            "description",
            "tags",
            "use_count",
            "is_public",
            "created_at",
        ]


class PromptCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Prompt
        fields = [
            "title",
            "prompt_type",
            "content",
            "description",
            "is_public",
        ]