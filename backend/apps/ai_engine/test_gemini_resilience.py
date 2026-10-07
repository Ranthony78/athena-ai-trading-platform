from unittest.mock import patch

import httpx
from django.test import SimpleTestCase, override_settings

from apps.ai_engine.providers.gemini_provider import GeminiProvider

REQ = httpx.Request("POST", "https://generativelanguage.googleapis.com/test")


def reply(text, finish="STOP"):
    return httpx.Response(
        200,
        json={
            "candidates": [
                {"content": {"parts": [{"text": text}]}, "finishReason": finish}
            ],
            "usageMetadata": {"totalTokenCount": 10},
        },
        request=REQ,
    )


@override_settings(GEMINI_API_KEY="k", GEMINI_MODEL="gemini-3.5-flash")
@patch("apps.ai_engine.providers.gemini_provider.httpx.post")
class GeminiResilienceTests(SimpleTestCase):
    def test_one_timeout_is_retried(self, post):
        post.side_effect = [httpx.ReadTimeout("slow", request=REQ), reply("{}")]
        self.assertEqual(GeminiProvider().complete("s", "u")["content"], "{}")
        self.assertEqual(post.call_count, 2)

    def test_second_timeout_fails_plainly(self, post):
        post.side_effect = httpx.ReadTimeout("slow", request=REQ)
        with self.assertRaisesRegex(Exception, "timed out"):
            GeminiProvider().complete("s", "u")
        self.assertEqual(post.call_count, 1 + GeminiProvider.MAX_TIMEOUT_RETRIES)

    def test_cut_off_reply_is_retried_with_a_bigger_budget(self, post):
        post.side_effect = [reply('{"signal": "NO_', "MAX_TOKENS"), reply("{}")]
        result = GeminiProvider().complete("s", "u", max_tokens=6000)
        self.assertEqual(result["content"], "{}")
        budgets = [
            c.kwargs["json"]["generationConfig"]["maxOutputTokens"]
            for c in post.call_args_list
        ]
        self.assertEqual(budgets[-1], 12000)

    def test_cut_off_twice_is_an_error_not_a_saved_analysis(self, post):
        post.side_effect = [reply("{", "MAX_TOKENS"), reply("{", "MAX_TOKENS")]
        with self.assertRaisesRegex(Exception, "cut off"):
            GeminiProvider().complete("s", "u", max_tokens=256)
        self.assertEqual(post.call_count, 2)  # one retry only
