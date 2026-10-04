from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.apps import apps
from django.test import SimpleTestCase, TestCase

from apps.paper_trading.models import PaperAccount
from apps.zerodha.models import LiveTradingArming
from shared import db_copy


class ModelSelectionTests(SimpleTestCase):

    def test_rebuilt_tables_are_never_copied(self):
        labels = {m._meta.label_lower for m in db_copy.models_to_copy()}
        for skipped in db_copy.SKIPPED_MODELS:
            self.assertNotIn(skipped, labels)

    def test_real_data_tables_are_copied(self):
        labels = {m._meta.label_lower for m in db_copy.models_to_copy()}
        for wanted in (
            "accounts.user",
            "market_data.candle",
            "market_data.instrument",
            "zerodha.zerodhaconfig",
            "token_blacklist.outstandingtoken",
        ):
            self.assertIn(wanted, labels)

    def test_automatic_many_to_many_tables_are_included(self):
        tables = {m._meta.db_table for m in db_copy.models_to_copy()}
        self.assertIn("knowledge_articles_tags", tables)

    def test_parents_come_before_children(self):
        ordered = db_copy.dependency_order(db_copy.models_to_copy())
        position = {m._meta.label_lower: i for i, m in enumerate(ordered)}
        pairs = [
            ("accounts.user", "paper_trading.paperaccount"),
            ("paper_trading.paperaccount", "paper_trading.paperorder"),
            ("market_data.instrument", "market_data.candle"),
            ("zerodha.zerodhaconfig", "zerodha.zerodhasession"),
            ("backtesting.backtestrun", "backtesting.backtesttrade"),
            ("token_blacklist.outstandingtoken", "token_blacklist.blacklistedtoken"),
        ]
        for parent, child in pairs:
            self.assertLess(
                position[parent], position[child], f"{parent} before {child}"
            )

    def test_every_model_appears_once(self):
        ordered = db_copy.dependency_order(db_copy.models_to_copy())
        self.assertEqual(len(ordered), len(set(ordered)))
        self.assertEqual(set(ordered), set(db_copy.models_to_copy()))


class KeepTimestampsTests(SimpleTestCase):

    def stamps(self):
        return {
            (m._meta.label, f.name): (f.auto_now, f.auto_now_add)
            for m in apps.get_models(include_auto_created=True)
            for f in m._meta.concrete_fields
            if hasattr(f, "auto_now")
        }

    def test_auto_timestamps_are_off_inside_and_restored_after(self):
        before = self.stamps()
        self.assertTrue(any(auto_now or add for auto_now, add in before.values()))
        with db_copy.keep_timestamps():
            self.assertTrue(all(not a and not b for a, b in self.stamps().values()))
        self.assertEqual(self.stamps(), before)

    def test_restored_even_when_the_copy_fails(self):
        before = self.stamps()
        with self.assertRaises(RuntimeError):
            with db_copy.keep_timestamps():
                raise RuntimeError("boom")
        self.assertEqual(self.stamps(), before)


class SafetyChecksTests(TestCase):

    def test_refuses_a_target_that_is_not_postgresql(self):
        # The test database may itself be SQLite or PostgreSQL; force the vendor.
        with patch("shared.db_copy.connections") as connections:
            connections.__getitem__.return_value.vendor = "sqlite"
            with self.assertRaises(db_copy.CopyError) as caught:
                db_copy.check_ready()
        self.assertIn("must be PostgreSQL", str(caught.exception))

    def test_refuses_a_target_that_already_has_data(self):
        from django.db import connection

        if connection.vendor != "postgresql":
            self.skipTest("needs a PostgreSQL test database")
        PaperAccount.objects.count()  # table exists
        from django.contrib.auth import get_user_model

        get_user_model().objects.create_user(
            username="x", email="x@example.com", password="pw12345678"
        )
        with self.assertRaises(db_copy.CopyError) as caught:
            db_copy.check_ready()
        self.assertIn("users", str(caught.exception))

    def test_missing_sqlite_file_is_a_clear_error(self):
        with TemporaryDirectory() as folder:
            with self.assertRaises(db_copy.CopyError) as caught:
                db_copy.register_source(Path(folder) / "nope.sqlite3")
        self.assertIn("not found", str(caught.exception))

    def test_run_refuses_when_database_url_is_not_postgresql(self):
        with patch.dict(
            "shared.db_copy.settings.DATABASES",
            {"default": {"ENGINE": "django.db.backends.sqlite3"}},
        ):
            with self.assertRaises(db_copy.CopyError):
                db_copy.run("whatever.sqlite3")

    def test_arming_rows_do_not_point_at_rebuilt_tables(self):
        # Users and arming are copied as ordinary rows: nothing links to content types.
        self.assertFalse(db_copy._points_at_skipped(LiveTradingArming))
