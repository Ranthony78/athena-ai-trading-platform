from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.database import database_config

BASE = Path("/project/backend")


def cfg(**env):
    return database_config(env, BASE)


class DefaultTests(SimpleTestCase):

    def test_empty_environment_is_sqlite_beside_the_project(self):
        config = cfg()
        self.assertEqual(config["ENGINE"], "django.db.backends.sqlite3")
        self.assertEqual(config["NAME"], BASE / "db.sqlite3")

    def test_blank_values_still_mean_sqlite(self):
        self.assertEqual(
            cfg(DATABASE_URL="  ", DB_ENGINE="")["ENGINE"],
            "django.db.backends.sqlite3",
        )

    def test_explicit_sqlite(self):
        self.assertEqual(
            cfg(DB_ENGINE="SQLite")["ENGINE"], "django.db.backends.sqlite3"
        )


class UrlTests(SimpleTestCase):

    def test_full_url(self):
        config = cfg(DATABASE_URL="postgres://athena:secret@db.example:6543/athena_db")
        self.assertEqual(config["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(
            (
                config["NAME"],
                config["USER"],
                config["PASSWORD"],
                config["HOST"],
                config["PORT"],
            ),
            ("athena_db", "athena", "secret", "db.example", "6543"),
        )

    def test_defaults_for_host_and_port(self):
        config = cfg(DATABASE_URL="postgresql://athena:pw@/athena_db")
        self.assertEqual((config["HOST"], config["PORT"]), ("localhost", "5432"))

    def test_percent_encoded_password_is_decoded(self):
        config = cfg(
            DATABASE_URL="postgres://athena:p%40ss%2Fw%3Ard@localhost/athena_db"
        )
        self.assertEqual(config["PASSWORD"], "p@ss/w:rd")

    def test_sslmode_from_the_query(self):
        config = cfg(DATABASE_URL="postgres://a:b@h/db?sslmode=require")
        self.assertEqual(config["OPTIONS"], {"sslmode": "require"})
        self.assertNotIn("OPTIONS", cfg(DATABASE_URL="postgres://a:b@h/db"))

    def test_connections_are_reused_and_health_checked(self):
        config = cfg(DATABASE_URL="postgres://a:b@h/db")
        self.assertEqual(config["CONN_MAX_AGE"], 60)
        self.assertTrue(config["CONN_HEALTH_CHECKS"])

    def test_url_wins_over_separate_variables(self):
        config = cfg(
            DATABASE_URL="postgres://a:b@h/from_url",
            DB_ENGINE="postgres",
            DB_NAME="from_vars",
            DB_USER="x",
        )
        self.assertEqual(config["NAME"], "from_url")

    def test_wrong_scheme_or_missing_parts_are_refused(self):
        for url in ("mysql://a:b@h/db", "postgres://h/db", "postgres://a:b@h/"):
            with self.assertRaises(ImproperlyConfigured, msg=url):
                cfg(DATABASE_URL=url)

    def test_errors_never_echo_the_password(self):
        with self.assertRaises(ImproperlyConfigured) as caught:
            cfg(DATABASE_URL="mysql://a:topsecret@h/db")
        self.assertNotIn("topsecret", str(caught.exception))


class SeparateVariableTests(SimpleTestCase):

    def test_postgres_from_variables(self):
        config = cfg(
            DB_ENGINE="postgres",
            DB_NAME="athena_db",
            DB_USER="athena",
            DB_PASSWORD="pw",
            DB_HOST="10.0.0.5",
            DB_PORT="5433",
            DB_SSLMODE="verify-full",
        )
        self.assertEqual(config["HOST"], "10.0.0.5")
        self.assertEqual(config["PORT"], "5433")
        self.assertEqual(config["OPTIONS"], {"sslmode": "verify-full"})

    def test_missing_name_or_user_is_refused(self):
        with self.assertRaises(ImproperlyConfigured):
            cfg(DB_ENGINE="postgres", DB_USER="athena")
        with self.assertRaises(ImproperlyConfigured):
            cfg(DB_ENGINE="postgres", DB_NAME="athena_db")

    def test_unknown_engine_is_refused(self):
        with self.assertRaises(ImproperlyConfigured):
            cfg(DB_ENGINE="oracle")
