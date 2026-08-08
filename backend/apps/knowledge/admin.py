from django.contrib import admin

from .models import Article, BookNote, Prompt, Tag, TradingRule


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "category",
        "source",
        "is_featured",
        "view_count",
        "is_active",
        "created_at",
    )
    list_filter = ("category", "source", "is_featured")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    readonly_fields = ("ai_summary", "ai_summarized_at", "view_count")


@admin.register(BookNote)
class BookNoteAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "author",
        "rating",
        "started_at",
        "finished_at",
    )
    search_fields = ("title", "author")
    filter_horizontal = ("articles",)


@admin.register(TradingRule)
class TradingRuleAdmin(admin.ModelAdmin):

    list_display = (
        "rule_number",
        "title",
        "rule_type",
        "priority",
        "times_broken",
        "is_active",
    )
    list_filter = ("rule_type", "priority")
    search_fields = ("title", "description")


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "prompt_type",
        "use_count",
        "is_public",
        "created_at",
    )
    list_filter = ("prompt_type", "is_public")
    search_fields = ("title", "content")