import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.ai_summary_service import AISummaryService
from ..services.knowledge_service import KnowledgeService
from ..services.search_service import SearchService
from .serializers import (
    ArticleCreateSerializer,
    ArticleDetailSerializer,
    ArticleListSerializer,
    BookNoteSerializer,
    PromptCreateSerializer,
    PromptSerializer,
    TagSerializer,
    TradingRuleCreateSerializer,
    TradingRuleSerializer,
)

logger = logging.getLogger(__name__)


class TagListAPIView(APIView):
    """GET /api/knowledge/tags/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tags = KnowledgeService.get_tags()
        serializer = TagSerializer(tags, many=True)
        return ApiResponse.success(serializer.data)

    def post(self, request):
        try:
            tag = KnowledgeService.create_tag(request.data)
            return ApiResponse.success(
                data=TagSerializer(tag).data,
                message="Tag created.",
            )
        except Exception as e:
            return ApiResponse.error(message=str(e))


class ArticleListAPIView(APIView):
    """
    GET  /api/knowledge/articles/  — list articles
    POST /api/knowledge/articles/  — create article
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            category = request.query_params.get("category")
            tag = request.query_params.get("tag")
            featured = request.query_params.get("featured") == "1"
            limit = int(request.query_params.get("limit", 50))

            articles = KnowledgeService.get_articles(
                user=request.user,
                category=category,
                tag_slug=tag,
                featured=featured,
                limit=limit,
            )

            serializer = ArticleListSerializer(articles, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"ArticleListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch articles.")

    def post(self, request):
        serializer = ArticleCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )

        try:
            article = KnowledgeService.create_article(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=ArticleDetailSerializer(article).data,
                message="Article created.",
            )
        except Exception as e:
            logger.error(f"ArticleListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to create article.")


class ArticleDetailAPIView(APIView):
    """
    GET    /api/knowledge/articles/<slug>/
    PUT    /api/knowledge/articles/<slug>/
    DELETE /api/knowledge/articles/<slug>/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, slug: str):
        article = KnowledgeService.get_article(slug)
        if not article:
            return ApiResponse.error(message="Article not found.")
        return ApiResponse.success(ArticleDetailSerializer(article).data)

    def put(self, request, slug: str):
        article = KnowledgeService.get_article(slug)
        if not article or article.user != request.user:
            return ApiResponse.error(message="Article not found.")

        serializer = ArticleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )

        try:
            updated = KnowledgeService.update_article(
                article=article,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=ArticleDetailSerializer(updated).data,
                message="Article updated.",
            )
        except Exception as e:
            logger.error(f"ArticleDetailAPIView PUT error: {e}")
            return ApiResponse.error(message="Failed to update article.")

    def delete(self, request, slug: str):
        article = KnowledgeService.get_article(slug)
        if not article or article.user != request.user:
            return ApiResponse.error(message="Article not found.")
        KnowledgeService.delete_article(article)
        return ApiResponse.success(message="Article deleted.")


class ArticleSummarizeAPIView(APIView):
    """
    POST /api/knowledge/articles/<slug>/summarize/
    Generate AI summary for an article.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, slug: str):
        article = KnowledgeService.get_article(slug)
        if not article:
            return ApiResponse.error(message="Article not found.")

        try:
            service = AISummaryService()
            result = service.summarize(article)
            return ApiResponse.success(
                data=result,
                message="AI summary generated.",
            )
        except Exception as e:
            logger.error(f"ArticleSummarizeAPIView error: {e}")
            return ApiResponse.error(message="Failed to generate summary.")


class KnowledgeSearchAPIView(APIView):
    """
    GET /api/knowledge/search/?q=<query>
    Search across all knowledge base content.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()

        if not query:
            return ApiResponse.error(message="Query parameter 'q' is required.")

        try:
            results = SearchService.search(request.user, query)
            return ApiResponse.success(results)
        except Exception as e:
            logger.error(f"KnowledgeSearchAPIView error: {e}")
            return ApiResponse.error(message="Search failed.")


class BookNoteListAPIView(APIView):
    """
    GET  /api/knowledge/books/
    POST /api/knowledge/books/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        books = KnowledgeService.get_books(request.user)
        serializer = BookNoteSerializer(books, many=True)
        return ApiResponse.success(serializer.data)

    def post(self, request):
        serializer = BookNoteSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        try:
            book = KnowledgeService.create_book(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=BookNoteSerializer(book).data,
                message="Book note created.",
            )
        except Exception as e:
            logger.error(f"BookNoteListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to create book note.")


class BookNoteDetailAPIView(APIView):
    """
    GET /api/knowledge/books/<id>/
    PUT /api/knowledge/books/<id>/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        book = KnowledgeService.get_book(request.user, pk)
        if not book:
            return ApiResponse.error(message="Book note not found.")
        return ApiResponse.success(BookNoteSerializer(book).data)

    def put(self, request, pk: int):
        book = KnowledgeService.get_book(request.user, pk)
        if not book:
            return ApiResponse.error(message="Book note not found.")

        serializer = BookNoteSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        updated = KnowledgeService.update_book(book, serializer.validated_data)
        return ApiResponse.success(BookNoteSerializer(updated).data)


class TradingRuleListAPIView(APIView):
    """
    GET  /api/knowledge/rules/
    POST /api/knowledge/rules/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            rule_type = request.query_params.get("type")
            critical = request.query_params.get("critical") == "1"

            if critical:
                rules = KnowledgeService.get_critical_rules(request.user)
            else:
                rules = KnowledgeService.get_rules(request.user, rule_type)

            serializer = TradingRuleSerializer(rules, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"TradingRuleListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch rules.")

    def post(self, request):
        serializer = TradingRuleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        try:
            rule = KnowledgeService.create_rule(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=TradingRuleSerializer(rule).data,
                message="Trading rule created.",
            )
        except Exception as e:
            logger.error(f"TradingRuleListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to create rule.")


class TradingRuleDetailAPIView(APIView):
    """
    PUT    /api/knowledge/rules/<id>/
    DELETE /api/knowledge/rules/<id>/
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, pk: int):
        from ..repositories.knowledge_repository import TradingRuleRepository
        rule = TradingRuleRepository.first(id=pk, user=request.user)
        if not rule:
            return ApiResponse.error(message="Rule not found.")

        serializer = TradingRuleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        updated = KnowledgeService.update_rule(rule, serializer.validated_data)
        return ApiResponse.success(TradingRuleSerializer(updated).data)

    def delete(self, request, pk: int):
        from ..repositories.knowledge_repository import TradingRuleRepository
        rule = TradingRuleRepository.first(id=pk, user=request.user)
        if not rule:
            return ApiResponse.error(message="Rule not found.")
        KnowledgeService.delete_rule(rule)
        return ApiResponse.success(message="Rule deleted.")


class TradingRuleBrokenAPIView(APIView):
    """
    POST /api/knowledge/rules/<id>/broken/
    Record that a rule was broken.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        try:
            rule = KnowledgeService.record_rule_broken(pk, request.user)
            if not rule:
                return ApiResponse.error(message="Rule not found.")
            return ApiResponse.success(
                data=TradingRuleSerializer(rule).data,
                message="Rule breach recorded.",
            )
        except Exception as e:
            logger.error(f"TradingRuleBrokenAPIView error: {e}")
            return ApiResponse.error(message="Failed to record rule breach.")


class PromptListAPIView(APIView):
    """
    GET  /api/knowledge/prompts/
    POST /api/knowledge/prompts/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            prompt_type = request.query_params.get("type")
            public = request.query_params.get("public") == "1"

            if public:
                prompts = KnowledgeService.get_public_prompts()
            else:
                prompts = KnowledgeService.get_prompts(
                    request.user, prompt_type
                )

            serializer = PromptSerializer(prompts, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"PromptListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch prompts.")

    def post(self, request):
        serializer = PromptCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        try:
            prompt = KnowledgeService.create_prompt(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=PromptSerializer(prompt).data,
                message="Prompt created.",
            )
        except Exception as e:
            logger.error(f"PromptListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to create prompt.")


class PromptUseAPIView(APIView):
    """
    POST /api/knowledge/prompts/<id>/use/
    Increment use count and return prompt content.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        try:
            prompt = KnowledgeService.use_prompt(pk, request.user)
            if not prompt:
                return ApiResponse.error(message="Prompt not found.")
            return ApiResponse.success(
                data=PromptSerializer(prompt).data,
                message="Prompt retrieved.",
            )
        except Exception as e:
            logger.error(f"PromptUseAPIView error: {e}")
            return ApiResponse.error(message="Failed to use prompt.")