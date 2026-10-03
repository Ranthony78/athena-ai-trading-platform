"""
Tests for project-wide settings: CORS.

Only listed frontend origins may call the API from a browser. The frontend
authenticates with a JWT header, so credentialed cross-origin requests are not
needed and stay off.
"""

import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase, override_settings

ALLOWED = "https://app.example.com"
STRANGER = "https://evil.example.org"


@override_settings(CORS_ALLOWED_ORIGINS=[ALLOWED], CORS_ALLOW_CREDENTIALS=False)
class CorsBehaviourTests(SimpleTestCase):

    def test_a_listed_origin_is_allowed(self):
        response = self.client.get("/api/accounts/registration/", HTTP_ORIGIN=ALLOWED)

        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), ALLOWED)

    def test_an_unlisted_origin_gets_no_cors_headers(self):
        response = self.client.get("/api/accounts/registration/", HTTP_ORIGIN=STRANGER)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Access-Control-Allow-Origin", response.headers)

    def test_a_preflight_from_an_unlisted_origin_is_not_approved(self):
        response = self.client.options(
            "/api/accounts/login/",
            HTTP_ORIGIN=STRANGER,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization,content-type",
        )

        self.assertNotIn("Access-Control-Allow-Origin", response.headers)

    def test_a_preflight_from_a_listed_origin_is_approved(self):
        response = self.client.options(
            "/api/accounts/login/",
            HTTP_ORIGIN=ALLOWED,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization,content-type",
        )

        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), ALLOWED)

    def test_credentialed_cross_origin_requests_are_not_enabled(self):
        response = self.client.get("/api/accounts/registration/", HTTP_ORIGIN=ALLOWED)

        self.assertNotIn("Access-Control-Allow-Credentials", response.headers)


class CorsSettingsTests(SimpleTestCase):
    """How CORS_ALLOWED_ORIGINS is read from the environment."""

    BACKEND_DIR = Path(__file__).resolve().parents[1]

    def run_python(self, code, settings_module, **env_overrides):
        env = {
            **os.environ,
            "DJANGO_SETTINGS_MODULE": settings_module,
            "DJANGO_SECRET_KEY": "k" * 50,
            **env_overrides,
        }
        return subprocess.run(
            [sys.executable, "-c", code],
            cwd=self.BACKEND_DIR,
            env=env,
            capture_output=True,
            text=True,
        )

    PRINT_SETTINGS = (
        "import django; django.setup(); "
        "from django.conf import settings; "
        "print(settings.CORS_ALLOWED_ORIGINS, settings.CORS_ALLOW_CREDENTIALS)"
    )

    def test_origins_are_parsed_from_a_comma_separated_list(self):
        result = self.run_python(
            self.PRINT_SETTINGS,
            "config.settings",
            CORS_ALLOWED_ORIGINS=" https://a.example , https://b.example ,, ",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(), "['https://a.example', 'https://b.example'] False"
        )

    def test_production_allows_no_cross_origin_access_by_default(self):
        # An empty value (not unset) keeps a developer's .env from leaking in.
        result = self.run_python(
            self.PRINT_SETTINGS, "config.settings.production", CORS_ALLOWED_ORIGINS=""
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "[] False")

    def test_production_does_not_inherit_the_local_dev_origins(self):
        result = self.run_python(
            self.PRINT_SETTINGS,
            "config.settings.production",
            CORS_ALLOWED_ORIGINS="https://app.example.com",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "['https://app.example.com'] False")

    def test_a_wildcard_or_schemeless_origin_fails_the_system_check(self):
        for bad in ("*", "app.example.com"):
            result = self.run_python(
                "from django.core.management import call_command; "
                "import django; django.setup(); call_command('check')",
                "config.settings",
                CORS_ALLOWED_ORIGINS=bad,
            )
            self.assertNotEqual(result.returncode, 0, bad)
            self.assertIn("corsheaders", result.stderr, bad)
