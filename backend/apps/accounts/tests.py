"""
Tests for the accounts API: registration, login, Google sign-in, token
refresh, admin user management and password reset.

Several tests pin security fixes:
  * an unverified, pre-registered account cannot be kept by whoever created
    it once the real owner signs in with Google (pre-account takeover);
  * a password reset revokes existing sessions;
  * auth endpoints are rate limited;
  * production refuses to start with a weak SECRET_KEY.
"""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APITestCase
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

STRONG_PASSWORD = "Xk93!vZq-long-enough"
NEW_PASSWORD = "Mn47#pLw-brand-new"
GOOGLE_VERIFY = "google.oauth2.id_token.verify_oauth2_token"

# PBKDF2 is deliberately slow; these tests create and check many passwords.
FAST_HASHER = override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"]
)


class AuthAPITestCase(APITestCase):
    """Clears throttle counters so tests never rate-limit each other."""

    def setUp(self):
        cache.clear()

    def register(
        self, username="alice", email="alice@example.com", password=STRONG_PASSWORD
    ):
        return self.client.post(
            "/api/accounts/register/",
            {
                "username": username,
                "email": email,
                "password": password,
                "password_confirm": password,
            },
            format="json",
        )

    def login(self, username, password):
        return self.client.post(
            "/api/accounts/login/",
            {"username": username, "password": password},
            format="json",
        )

    def refresh(self, token):
        return self.client.post(
            "/api/accounts/token/refresh/", {"refresh": token}, format="json"
        )


@FAST_HASHER
class RegistrationAndLoginTests(AuthAPITestCase):

    def test_registration_issues_tokens_and_leaves_email_unverified(self):
        response = self.register()

        self.assertEqual(response.status_code, 201)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        user = User.objects.get(username="alice")
        self.assertFalse(user.is_email_verified)
        self.assertFalse(user.is_staff)

    def test_registration_cannot_grant_staff(self):
        response = self.client.post(
            "/api/accounts/register/",
            {
                "username": "mallory",
                "email": "mallory@example.com",
                "password": STRONG_PASSWORD,
                "password_confirm": STRONG_PASSWORD,
                "is_staff": True,
                "is_superuser": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="mallory")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_registration_rejects_duplicate_email_case_insensitively(self):
        self.register()
        response = self.register(username="alice2", email="ALICE@example.com")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 1)

    def test_registration_rejects_weak_or_mismatched_passwords(self):
        weak = self.register(password="12345678")
        self.assertEqual(weak.status_code, 400)

        mismatch = self.client.post(
            "/api/accounts/register/",
            {
                "username": "bob",
                "email": "bob@example.com",
                "password": STRONG_PASSWORD,
                "password_confirm": STRONG_PASSWORD + "x",
            },
            format="json",
        )
        self.assertEqual(mismatch.status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    def test_login_success_and_failure(self):
        self.register()

        self.assertEqual(self.login("alice", STRONG_PASSWORD).status_code, 200)
        self.assertEqual(self.login("alice", "wrong-password").status_code, 400)

    def test_inactive_user_cannot_log_in_or_use_existing_token(self):
        response = self.register()
        access = response.data["access"]
        User.objects.filter(username="alice").update(is_active=False)

        self.assertEqual(self.login("alice", STRONG_PASSWORD).status_code, 400)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(self.client.get("/api/accounts/profile/").status_code, 401)


@FAST_HASHER
class TokenRefreshTests(AuthAPITestCase):

    def test_refresh_returns_new_access_and_rotates_refresh(self):
        first = self.register().data

        response = self.refresh(first["refresh"])

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertNotEqual(response.data["refresh"], first["refresh"])

    def test_rotated_refresh_token_cannot_be_reused(self):
        first = self.register().data
        self.refresh(first["refresh"])

        reuse = self.refresh(first["refresh"])

        self.assertEqual(reuse.status_code, 401)

    def test_logout_blacklists_refresh_token(self):
        data = self.register().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {data['access']}")

        logout = self.client.post(
            "/api/accounts/logout/", {"refresh": data["refresh"]}, format="json"
        )

        self.assertEqual(logout.status_code, 200)
        self.client.credentials()
        self.assertEqual(self.refresh(data["refresh"]).status_code, 401)


@FAST_HASHER
@override_settings(GOOGLE_OAUTH_CLIENT_ID="test-client-id")
class GoogleLoginTests(AuthAPITestCase):

    def google(self, identity=None, credential="token"):
        with patch(GOOGLE_VERIFY, return_value=identity) as verify:
            response = self.client.post(
                "/api/accounts/google/", {"credential": credential}, format="json"
            )
        return response, verify

    def test_unverified_preregistered_account_is_not_kept_by_the_registrant(self):
        """Regression: pre-account takeover via registering someone else's email."""
        attacker = self.register(username="attacker", email="victim@example.com").data

        response, _ = self.google(
            {"email": "victim@example.com", "email_verified": True, "name": "Victim"}
        )

        # The real owner signs in...
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["username"], "attacker")
        user = User.objects.get(email="victim@example.com")
        self.assertTrue(user.is_email_verified)
        # ...and the registrant loses both the password and any live session.
        self.assertFalse(user.has_usable_password())
        self.assertEqual(self.login("attacker", STRONG_PASSWORD).status_code, 400)
        self.assertEqual(self.refresh(attacker["refresh"]).status_code, 401)

    def test_verified_account_keeps_its_password_and_sessions(self):
        self.register(username="carol", email="carol@example.com")
        User.objects.filter(username="carol").update(is_email_verified=True)
        session = RefreshToken.for_user(User.objects.get(username="carol"))

        response, _ = self.google(
            {"email": "carol@example.com", "email_verified": True}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.login("carol", STRONG_PASSWORD).status_code, 200)
        self.assertEqual(self.refresh(str(session)).status_code, 200)

    def test_new_google_user_gets_verified_account_without_password(self):
        response, _ = self.google(
            {"email": "new@example.com", "email_verified": True, "name": "New Person"}
        )

        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email="new@example.com")
        self.assertTrue(user.is_email_verified)
        self.assertFalse(user.has_usable_password())

    def test_audience_is_checked_against_configured_client_id(self):
        _, verify = self.google({"email": "a@example.com", "email_verified": True})

        self.assertEqual(verify.call_args.args[2], "test-client-id")

    def test_rejects_unverified_google_email(self):
        response, _ = self.google({"email": "a@example.com", "email_verified": False})

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email="a@example.com").exists())

    def test_rejects_invalid_credential(self):
        with patch(GOOGLE_VERIFY, side_effect=ValueError("bad token")):
            response = self.client.post(
                "/api/accounts/google/", {"credential": "forged"}, format="json"
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    def test_inactive_existing_account_is_refused(self):
        self.register(username="dave", email="dave@example.com")
        User.objects.filter(username="dave").update(is_active=False)

        response, _ = self.google({"email": "dave@example.com", "email_verified": True})

        self.assertEqual(response.status_code, 403)

    @override_settings(GOOGLE_OAUTH_CLIENT_ID="")
    def test_unconfigured_google_login_is_unavailable(self):
        response, _ = self.google({"email": "a@example.com", "email_verified": True})

        self.assertEqual(response.status_code, 503)


@FAST_HASHER
class UserManagementTests(AuthAPITestCase):

    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_user(
            "admin", "admin@example.com", STRONG_PASSWORD, is_staff=True
        )
        self.member = User.objects.create_user(
            "member", "member@example.com", STRONG_PASSWORD
        )

    def test_user_management_requires_staff(self):
        self.client.force_authenticate(self.member)

        self.assertEqual(self.client.get("/api/accounts/users/").status_code, 403)
        self.assertEqual(
            self.client.patch(
                f"/api/accounts/users/{self.admin.pk}/status/",
                {"is_active": False},
                format="json",
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                f"/api/accounts/users/{self.admin.pk}/password-reset/"
            ).status_code,
            403,
        )

    def test_staff_can_list_and_deactivate_users(self):
        self.client.force_authenticate(self.admin)

        listing = self.client.get("/api/accounts/users/")
        self.assertEqual(listing.status_code, 200)

        response = self.client.patch(
            f"/api/accounts/users/{self.member.pk}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)

    def test_staff_cannot_deactivate_themselves_or_a_superuser(self):
        root = User.objects.create_superuser(
            "root", "root@example.com", STRONG_PASSWORD
        )
        self.client.force_authenticate(self.admin)

        own = self.client.patch(
            f"/api/accounts/users/{self.admin.pk}/status/",
            {"is_active": False},
            format="json",
        )
        superuser = self.client.patch(
            f"/api/accounts/users/{root.pk}/status/",
            {"is_active": False},
            format="json",
        )

        self.assertEqual(own.status_code, 400)
        self.assertEqual(superuser.status_code, 403)
        root.refresh_from_db()
        self.assertTrue(root.is_active)

    def test_status_requires_a_boolean(self):
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            f"/api/accounts/users/{self.member.pk}/status/",
            {"is_active": "false"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)


@FAST_HASHER
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_URL="https://athena.example",
)
class PasswordResetTests(AuthAPITestCase):

    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_user(
            "admin", "admin@example.com", STRONG_PASSWORD, is_staff=True
        )
        self.member = User.objects.create_user(
            "member", "member@example.com", STRONG_PASSWORD
        )

    def reset_payload(self, user=None, token=None, password=NEW_PASSWORD):
        user = user or self.member
        return {
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": token or default_token_generator.make_token(user),
            "new_password": password,
            "password_confirm": password,
        }

    def confirm(self, payload):
        return self.client.post(
            "/api/accounts/password-reset/confirm/", payload, format="json"
        )

    def test_admin_reset_emails_the_user_not_the_admin(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            f"/api/accounts/users/{self.member.pk}/password-reset/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["member@example.com"])
        self.assertIn("https://athena.example/reset-password?uid=", mail.outbox[0].body)

    def test_reset_for_inactive_or_emailless_user_is_refused(self):
        self.client.force_authenticate(self.admin)
        User.objects.filter(pk=self.member.pk).update(is_active=False)
        inactive = self.client.post(
            f"/api/accounts/users/{self.member.pk}/password-reset/"
        )
        self.assertEqual(inactive.status_code, 400)

        User.objects.filter(pk=self.member.pk).update(is_active=True, email="")
        emailless = self.client.post(
            f"/api/accounts/users/{self.member.pk}/password-reset/"
        )
        self.assertEqual(emailless.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_confirm_changes_the_password(self):
        response = self.confirm(self.reset_payload())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.login("member", NEW_PASSWORD).status_code, 200)
        self.assertEqual(self.login("member", STRONG_PASSWORD).status_code, 400)

    def test_confirm_revokes_existing_sessions(self):
        session = str(RefreshToken.for_user(self.member))
        self.assertEqual(self.refresh(session).status_code, 200)  # works beforehand
        stale = str(RefreshToken.for_user(self.member))

        self.assertEqual(self.confirm(self.reset_payload()).status_code, 200)

        self.assertEqual(self.refresh(stale).status_code, 401)

    def test_reset_link_is_single_use(self):
        payload = self.reset_payload()
        self.assertEqual(self.confirm(payload).status_code, 200)

        again = self.confirm(
            {
                **payload,
                "new_password": "Zz81$qRt-another-one",
                "password_confirm": "Zz81$qRt-another-one",
            }
        )

        self.assertEqual(again.status_code, 400)
        self.assertEqual(self.login("member", NEW_PASSWORD).status_code, 200)

    def test_confirm_rejects_bad_token_bad_uid_inactive_user_and_weak_password(self):
        bad_token = self.confirm(self.reset_payload(token="not-a-token"))
        bad_uid = self.confirm({**self.reset_payload(), "uid": "!!!"})
        weak = self.confirm(self.reset_payload(password="12345678"))
        User.objects.filter(pk=self.member.pk).update(is_active=False)
        inactive = self.confirm(self.reset_payload())

        for response in (bad_token, bad_uid, weak, inactive):
            self.assertEqual(response.status_code, 400)
        # Invalid and expired links share one message: nothing to enumerate.
        self.assertEqual(bad_token.data["message"], bad_uid.data["message"])
        User.objects.filter(pk=self.member.pk).update(is_active=True)
        self.assertEqual(self.login("member", STRONG_PASSWORD).status_code, 200)


@FAST_HASHER
class ThrottlingTests(AuthAPITestCase):

    def test_login_is_rate_limited(self):
        self.register()
        with patch.object(ScopedRateThrottle, "THROTTLE_RATES", {"auth": "3/min"}):
            codes = [self.login("alice", f"wrong-{i}").status_code for i in range(5)]

        self.assertEqual(codes[:3], [400, 400, 400])
        self.assertEqual(codes[3:], [429, 429])

    def test_google_and_reset_confirm_share_the_auth_limit(self):
        with patch.object(ScopedRateThrottle, "THROTTLE_RATES", {"auth": "2/min"}):
            first = self.client.post("/api/accounts/google/", {}, format="json")
            second = self.client.post(
                "/api/accounts/password-reset/confirm/", {}, format="json"
            )
            third = self.login("nobody", "x")

        self.assertNotEqual(first.status_code, 429)
        self.assertNotEqual(second.status_code, 429)
        self.assertEqual(third.status_code, 429)

    def test_registration_is_rate_limited(self):
        with patch.object(ScopedRateThrottle, "THROTTLE_RATES", {"register": "2/hour"}):
            codes = [
                self.register(
                    username=f"user{i}", email=f"user{i}@example.com"
                ).status_code
                for i in range(3)
            ]

        self.assertEqual(codes, [201, 201, 429])

    def test_refresh_is_rate_limited(self):
        with patch.object(ScopedRateThrottle, "THROTTLE_RATES", {"refresh": "2/min"}):
            codes = [self.refresh("junk").status_code for _ in range(3)]

        self.assertEqual(codes[:2], [401, 401])
        self.assertEqual(codes[2], 429)


class ProductionSecretKeyTests(SimpleTestCase):
    """production.py must refuse to start with a missing or weak SECRET_KEY."""

    BACKEND_DIR = Path(__file__).resolve().parents[2]

    def load_production_settings(self, secret_key):
        env = {**os.environ, "DJANGO_SECRET_KEY": secret_key}
        return subprocess.run(
            [
                sys.executable,
                "-c",
                "import os, django; "
                "os.environ['DJANGO_SETTINGS_MODULE']='config.settings.production'; "
                "django.setup()",
            ],
            cwd=self.BACKEND_DIR,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_default_placeholder_key_is_rejected(self):
        result = self.load_production_settings("change-me")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)

    def test_short_key_is_rejected(self):
        result = self.load_production_settings("too-short-key")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)

    def test_strong_key_is_accepted(self):
        result = self.load_production_settings("k" * 50)

        self.assertEqual(result.returncode, 0, result.stderr)
