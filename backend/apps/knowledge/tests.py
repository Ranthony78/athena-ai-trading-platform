"""
Tests for per-user ownership of knowledge articles.

Articles belong to the user who wrote them. Slugs are globally unique, so a
slug must never be enough to read, summarize or count a view on someone
else's article.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Article

User = get_user_model()

SUMMARY_SERVICE = "apps.knowledge.api.views.AISummaryService"


class ArticleOwnershipTests(APITestCase):

    def setUp(self):
        self.alice = User.objects.create_user(
            "alice", "alice@example.com", "pw-Alice-123"
        )
        self.bob = User.objects.create_user("bob", "bob@example.com", "pw-Bob-12345")
        self.alices = Article.objects.create(
            user=self.alice,
            title="Alice's private notes",
            slug="alice-private-notes",
            content="Position sizing rules only Alice should read.",
        )
        self.client.force_authenticate(self.bob)

    def detail(self, slug):
        return self.client.get(reverse("knowledge-article-detail", args=[slug]))

    def test_owner_can_read_their_article_and_the_view_is_counted(self):
        self.client.force_authenticate(self.alice)

        response = self.detail("alice-private-notes")

        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["title"], "Alice's private notes")
        self.alices.refresh_from_db()
        self.assertEqual(self.alices.view_count, 1)

    def test_another_users_article_is_indistinguishable_from_a_missing_one(self):
        other = self.detail("alice-private-notes")
        missing = self.detail("no-such-article")

        self.assertFalse(other.data["success"])
        self.assertEqual(other.status_code, missing.status_code)
        self.assertEqual(other.data, missing.data)
        self.assertNotIn("Position sizing", str(other.data))

    def test_reading_someone_elses_article_does_not_bump_their_view_count(self):
        self.detail("alice-private-notes")
        self.detail("alice-private-notes")

        self.alices.refresh_from_db()
        self.assertEqual(self.alices.view_count, 0)

    def test_summarize_is_refused_for_someone_elses_article(self):
        with patch(SUMMARY_SERVICE) as summary_service:
            response = self.client.post(
                reverse("knowledge-article-summarize", args=["alice-private-notes"])
            )

        self.assertFalse(response.data["success"])
        summary_service.assert_not_called()

    def test_owner_can_summarize_their_article(self):
        self.client.force_authenticate(self.alice)

        with patch(SUMMARY_SERVICE) as summary_service:
            summary_service.return_value.summarize.return_value = {"summary": "ok"}
            response = self.client.post(
                reverse("knowledge-article-summarize", args=["alice-private-notes"])
            )

        self.assertTrue(response.data["success"])
        summary_service.return_value.summarize.assert_called_once()

    def test_update_and_delete_are_refused_for_someone_elses_article(self):
        url = reverse("knowledge-article-detail", args=["alice-private-notes"])
        payload = {"title": "Hijacked", "content": "x", "category": "CONCEPT"}

        put = self.client.put(url, payload, format="json")
        delete = self.client.delete(url)

        self.assertFalse(put.data["success"])
        self.assertFalse(delete.data["success"])
        self.alices.refresh_from_db()
        self.assertEqual(self.alices.title, "Alice's private notes")
        self.assertTrue(self.alices.is_active)

    def test_list_and_search_only_show_the_requesters_articles(self):
        Article.objects.create(
            user=self.bob, title="Bob on sizing", slug="bob-on-sizing", content="sizing"
        )

        listing = self.client.get(reverse("knowledge-articles"))
        search = self.client.get(reverse("knowledge-search"), {"q": "sizing"})

        listed = {row["slug"] for row in listing.data["data"]}
        found = {row["slug"] for row in search.data["data"]["articles"]}
        self.assertEqual(listed, {"bob-on-sizing"})
        self.assertEqual(found, {"bob-on-sizing"})

    def test_requires_authentication(self):
        self.client.force_authenticate(None)

        response = self.detail("alice-private-notes")

        self.assertIn(response.status_code, (401, 403))
