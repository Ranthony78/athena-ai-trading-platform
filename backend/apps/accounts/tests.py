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


# Most tests below sign accounts up and use the tokens straight away, which is
# what "open" mode does. The approval and closed modes have their own classes.
@override_settings(REGISTRATION_MODE="open")
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


MAIL_SETTINGS = override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_URL="https://athena.example",
)


@FAST_HASHER
@MAIL_SETTINGS
@override_settings(
    REGISTRATION_MODE="approval", GOOGLE_OAUTH_CLIENT_ID="test-client-id"
)
class ApprovalModeTests(AuthAPITestCase):
    """Anyone may sign up, but nothing works until staff approve the account."""

    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_user(
            "admin", "admin@example.com", STRONG_PASSWORD, is_staff=True
        )

    def google(self, email, **extra):
        identity = {"email": email, "email_verified": True, **extra}
        with patch(GOOGLE_VERIFY, return_value=identity):
            return self.client.post(
                "/api/accounts/google/", {"credential": "x"}, format="json"
            )

    def approve(self, username):
        self.client.force_authenticate(self.admin)
        user_id = User.objects.get(username=username).pk
        response = self.client.patch(
            f"/api/accounts/users/{user_id}/status/", {"is_active": True}, format="json"
        )
        self.client.force_authenticate(None)
        return response

    def test_signup_creates_an_inactive_account_and_issues_no_tokens(self):
        response = self.register()

        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.data["pending_approval"])
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        user = User.objects.get(username="alice")
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)

    def test_pending_user_is_told_why_only_after_giving_the_right_password(self):
        self.register()

        right = self.login("alice", STRONG_PASSWORD)
        wrong = self.login("alice", "not-the-password")
        unknown = self.login("nobody", STRONG_PASSWORD)

        self.assertEqual(right.status_code, 400)
        self.assertIn("approval", str(right.data).lower())
        # Without the password, a pending account looks like any bad login.
        self.assertEqual(str(wrong.data), str(unknown.data))
        self.assertIn("Invalid username or password", str(wrong.data))

    def test_staff_approval_lets_the_user_sign_in(self):
        self.register()

        self.assertEqual(self.approve("alice").status_code, 200)

        self.assertEqual(self.login("alice", STRONG_PASSWORD).status_code, 200)

    def test_invalid_signup_still_fails_and_creates_nothing(self):
        response = self.register(password="12345678")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.filter(username="alice").count(), 0)

    def test_staff_are_emailed_about_a_pending_account(self):
        User.objects.create_user("member", "member@example.com", STRONG_PASSWORD)

        self.register()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["admin@example.com"])
        self.assertIn("alice", mail.outbox[0].body)
        self.assertIn("https://athena.example/admin/users", mail.outbox[0].body)

    def test_a_mail_failure_does_not_break_signup(self):
        with patch(
            "apps.accounts.registration.send_mail", side_effect=OSError("smtp down")
        ):
            response = self.register()

        self.assertEqual(response.status_code, 202)
        self.assertTrue(User.objects.filter(username="alice").exists())

    def test_signup_works_when_no_staff_can_be_emailed(self):
        User.objects.filter(pk=self.admin.pk).update(email="")

        self.assertEqual(self.register().status_code, 202)
        self.assertEqual(len(mail.outbox), 0)

    def test_user_list_can_be_filtered_to_pending_accounts(self):
        self.register()  # pending: inactive and never signed in
        used = User.objects.create_user("used", "used@example.com", STRONG_PASSWORD)
        User.objects.filter(pk=used.pk).update(
            is_active=False, last_login="2026-01-01T00:00:00Z"
        )
        self.client.force_authenticate(self.admin)

        def names(status):
            response = self.client.get("/api/accounts/users/", {"status": status})
            self.assertEqual(response.status_code, 200)
            return {row["username"] for row in response.data["results"]}

        self.assertEqual(names("pending"), {"alice"})
        self.assertEqual(names("inactive"), {"alice", "used"})
        self.assertEqual(names("active"), {"admin"})
        rows = {
            row["username"]: row
            for row in self.client.get("/api/accounts/users/").data["results"]
        }
        self.assertTrue(rows["alice"]["is_pending"])
        self.assertFalse(rows["used"]["is_pending"])
        self.assertFalse(rows["admin"]["is_pending"])

    def test_first_google_sign_in_also_waits_for_approval(self):
        response = self.google("new@example.com", name="New Person")

        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.data["pending_approval"])
        self.assertNotIn("access", response.data)
        user = User.objects.get(email="new@example.com")
        self.assertFalse(user.is_active)
        self.assertTrue(user.is_email_verified)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(len(mail.outbox), 1)

        # Still blocked on a second attempt, until staff approve.
        blocked = self.google("new@example.com")
        self.assertEqual(blocked.status_code, 403)
        self.approve(user.username)
        self.assertEqual(self.google("new@example.com").status_code, 200)

    def test_existing_active_google_user_is_unaffected(self):
        User.objects.create_user(
            "carol", "carol@example.com", STRONG_PASSWORD, is_email_verified=True
        )

        self.assertEqual(self.google("carol@example.com").status_code, 200)

    def test_mode_endpoint_reports_approval(self):
        response = self.client.get("/api/accounts/registration/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["mode"], "approval")


@FAST_HASHER
@MAIL_SETTINGS
@override_settings(REGISTRATION_MODE="closed", GOOGLE_OAUTH_CLIENT_ID="test-client-id")
class ClosedModeTests(AuthAPITestCase):
    """Nobody can sign up; people who already have accounts are unaffected."""

    def google(self, email):
        identity = {"email": email, "email_verified": True}
        with patch(GOOGLE_VERIFY, return_value=identity):
            return self.client.post(
                "/api/accounts/google/", {"credential": "x"}, format="json"
            )

    def test_signup_is_refused_and_creates_nothing(self):
        response = self.register()

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["code"], "registration_closed")
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_refusal_reveals_nothing_about_existing_accounts(self):
        User.objects.create_user("taken", "taken@example.com", STRONG_PASSWORD)

        taken = self.register(username="taken", email="taken@example.com")
        fresh = self.register(username="fresh", email="fresh@example.com")
        garbage = self.client.post("/api/accounts/register/", {}, format="json")

        self.assertEqual(
            {taken.status_code, fresh.status_code, garbage.status_code}, {403}
        )
        self.assertEqual(taken.data, fresh.data)

    def test_new_google_user_is_refused(self):
        response = self.google("new@example.com")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "registration_closed")
        self.assertFalse(User.objects.filter(email="new@example.com").exists())

    def test_existing_users_can_still_sign_in_with_a_password_or_google(self):
        User.objects.create_user(
            "carol", "carol@example.com", STRONG_PASSWORD, is_email_verified=True
        )

        self.assertEqual(self.login("carol", STRONG_PASSWORD).status_code, 200)
        self.assertEqual(self.google("carol@example.com").status_code, 200)

    def test_mode_endpoint_reports_closed(self):
        response = self.client.get("/api/accounts/registration/")

        self.assertEqual(response.data["mode"], "closed")


class OpenModeTests(AuthAPITestCase):

    def test_mode_endpoint_reports_open_without_authentication(self):
        response = self.client.get("/api/accounts/registration/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["mode"], "open")


class RegistrationModeSettingTests(SimpleTestCase):
    """A typo in REGISTRATION_MODE must stop the app, not quietly open sign-up."""

    BACKEND_DIR = Path(__file__).resolve().parents[2]

    def load_settings(self, mode):
        env = {**os.environ, "REGISTRATION_MODE": mode}
        return subprocess.run(
            [
                sys.executable,
                "-c",
                "import os, django; "
                "os.environ['DJANGO_SETTINGS_MODULE']='config.settings'; "
                "django.setup(); "
                "from django.conf import settings; print(settings.REGISTRATION_MODE)",
            ],
            cwd=self.BACKEND_DIR,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_valid_modes_are_accepted_case_insensitively(self):
        for mode in ("open", "approval", "closed", " Closed "):
            result = self.load_settings(mode)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), mode.strip().lower())

    def test_unknown_mode_stops_startup(self):
        for mode in ("opne", "", "public"):
            result = self.load_settings(mode)
            self.assertNotEqual(result.returncode, 0, mode)
            self.assertIn("REGISTRATION_MODE", result.stderr)


@FAST_HASHER
@MAIL_SETTINGS
class ActivationEmailTests(AuthAPITestCase):
    """Users are told when staff activate their account (no password is ever sent)."""

    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_user(
            "admin", "admin@example.com", STRONG_PASSWORD, is_staff=True
        )
        self.client.force_authenticate(self.admin)

    def make_user(self, username="pia", email="pia@example.com", **extra):
        return User.objects.create_user(username, email, STRONG_PASSWORD, **extra)

    def set_active(self, user, value):
        return self.client.patch(
            f"/api/accounts/users/{user.pk}/status/",
            {"is_active": value},
            format="json",
        )

    def test_approving_a_pending_user_emails_them_a_sign_in_link(self):
        pending = self.make_user(is_active=False)

        response = self.set_active(pending, True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["pia@example.com"])
        self.assertIn("https://athena.example/login", message.body)
        self.assertNotIn(STRONG_PASSWORD, message.body)
        self.assertNotIn("token", message.body.lower())

    def test_no_email_when_the_account_was_already_active(self):
        active = self.make_user()

        self.assertEqual(self.set_active(active, True).status_code, 200)

        self.assertEqual(len(mail.outbox), 0)

    def test_no_email_when_deactivating(self):
        active = self.make_user()

        self.assertEqual(self.set_active(active, False).status_code, 200)

        self.assertEqual(len(mail.outbox), 0)

    def test_switching_a_deactivated_account_back_on_also_emails(self):
        user = self.make_user(is_active=False)
        User.objects.filter(pk=user.pk).update(last_login="2026-01-01T00:00:00Z")

        self.set_active(user, True)

        self.assertEqual(len(mail.outbox), 1)

    def test_a_user_without_an_email_is_activated_quietly(self):
        user = self.make_user(email="", is_active=False)

        response = self.set_active(user, True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_a_mail_failure_does_not_undo_the_activation(self):
        pending = self.make_user(is_active=False)

        with patch(
            "apps.accounts.registration.send_mail", side_effect=OSError("smtp down")
        ):
            response = self.set_active(pending, True)

        self.assertEqual(response.status_code, 200)
        pending.refresh_from_db()
        self.assertTrue(pending.is_active)


@FAST_HASHER
class ProfileTests(AuthAPITestCase):
    """Users can edit their own name, phone and timezone, and nothing else."""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            "pat",
            "pat@example.com",
            STRONG_PASSWORD,
            first_name="Pat",
            last_name="Old",
        )
        self.other = User.objects.create_user("sam", "sam@example.com", STRONG_PASSWORD)
        self.client.force_authenticate(self.user)

    def patch(self, payload):
        return self.client.patch("/api/accounts/profile/", payload, format="json")

    def test_profile_can_be_read(self):
        response = self.client.get("/api/accounts/profile/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["username"], "pat")

    def test_name_phone_and_timezone_can_be_updated(self):
        response = self.patch(
            {
                "first_name": "Patricia",
                "last_name": "New",
                "phone": "+91 98765-43210",
                "timezone": "Asia/Dubai",
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.user.refresh_from_db()
        self.assertEqual(
            (
                self.user.first_name,
                self.user.last_name,
                self.user.phone,
                self.user.timezone,
            ),
            ("Patricia", "New", "+91 98765-43210", "Asia/Dubai"),
        )
        self.assertEqual(response.data["user"]["first_name"], "Patricia")

    def test_a_partial_update_leaves_other_fields_alone(self):
        self.patch({"phone": "12345"})

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Pat")
        self.assertEqual(self.user.phone, "12345")

    def test_identity_and_privilege_fields_cannot_be_changed(self):
        original_hash = self.user.password

        response = self.patch(
            {
                "username": "hijacked",
                "email": "victim@example.com",
                "is_staff": True,
                "is_superuser": True,
                "is_active": False,
                "is_email_verified": True,
                "password": "Overwritten!12345",
                "first_name": "Still Allowed",
            }
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "pat")
        self.assertEqual(self.user.email, "pat@example.com")
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_email_verified)
        self.assertEqual(self.user.password, original_hash)
        self.assertEqual(self.user.first_name, "Still Allowed")

    def test_invalid_values_are_rejected_without_changing_anything(self):
        for payload in (
            {"timezone": "Mars/Olympus"},
            {"phone": "call me maybe"},
            {"phone": "1" * 21},
            {"first_name": "x" * 151},
        ):
            response = self.patch(payload)
            self.assertEqual(response.status_code, 400, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.timezone, "Asia/Kolkata")
        self.assertEqual(self.user.phone, "")

    def test_it_only_ever_edits_the_signed_in_user(self):
        self.patch({"first_name": "Mine"})

        self.other.refresh_from_db()
        self.assertEqual(self.other.first_name, "")

    def test_requires_authentication(self):
        self.client.force_authenticate(None)

        self.assertIn(self.patch({"first_name": "x"}).status_code, (401, 403))
