from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.ai_engine.models import AnalysisPreference
from apps.ai_engine.services import setup_strictness as ss
from apps.ai_engine.services.prompt_service import PromptService


class SetupStrictnessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("u", "u@example.com", "x")

    def test_default_is_balanced_when_nothing_saved(self):
        self.assertEqual(ss.get_level(self.user), "BALANCED")
        self.assertEqual(ss.get_level(None), "BALANCED")

    def test_unknown_values_fall_back_to_balanced(self):
        self.assertEqual(ss.normalize("whatever"), "BALANCED")
        self.assertEqual(ss.normalize("strict"), "STRICT")

    def test_strict_adds_nothing_to_the_prompt(self):
        base = PromptService.request_config(setup_strictness="STRICT")["system_prompt"]
        self.assertEqual(base, PromptService.request_config()["system_prompt"])

    def test_balanced_and_exploratory_append_a_policy_that_keeps_safety_rules(self):
        for level in ("BALANCED", "EXPLORATORY"):
            text = PromptService.request_config(setup_strictness=level)["system_prompt"]
            self.assertIn(f"SETUP STRICTNESS: {level}", text)
            self.assertIn("Never raise confidence", text)
            # the policy comes last so it is the final word on the default
            self.assertTrue(text.rstrip().endswith("justify a setup."))

    def test_saved_choice_is_used(self):
        AnalysisPreference.objects.create(user=self.user, setup_strictness="STRICT")
        self.assertEqual(ss.get_level(self.user), "STRICT")


class PreferenceApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("u", "u@example.com", "x")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_get_defaults_to_balanced_with_three_options(self):
        data = self.client.get("/api/ai/preferences/").json()["data"]
        self.assertEqual(data["setup_strictness"], "BALANCED")
        self.assertEqual(len(data["options"]), 3)

    def test_put_saves_and_rejects_bad_values(self):
        ok = self.client.put(
            "/api/ai/preferences/", {"setup_strictness": "exploratory"}, format="json"
        )
        self.assertEqual(ok.json()["data"]["setup_strictness"], "EXPLORATORY")
        self.assertEqual(ss.get_level(self.user), "EXPLORATORY")
        bad = self.client.put(
            "/api/ai/preferences/", {"setup_strictness": "reckless"}, format="json"
        )
        self.assertFalse(bad.json().get("success", True))
        self.assertEqual(ss.get_level(self.user), "EXPLORATORY")

    def test_requires_login(self):
        self.assertIn(APIClient().get("/api/ai/preferences/").status_code, (401, 403))
