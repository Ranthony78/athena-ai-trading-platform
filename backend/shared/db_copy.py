"""
Copy every application table from a SQLite file into the configured
PostgreSQL database, keeping primary keys, timestamps (to the microsecond),
decimals and JSON exactly as they are.

Why not dumpdata/loaddata: Django's JSON export rounds timestamps to
milliseconds and, with natural primary keys, renumbers users. This copies
rows straight between the two databases instead.

Safety rules:
- the source is opened read-only;
- the target must be PostgreSQL, fully migrated, and EMPTY of application data;
- everything runs in one transaction, so a failure leaves the target empty;
- tables that must not be copied (content types, permissions, admin log,
  sessions) are rebuilt by Django on the target, and the copy refuses to run
  if the source has rows that point at them.
"""

from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.color import no_style
from django.db import connections, transaction

SOURCE_ALIAS = "sqlite_source"

# Rebuilt by Django on the target database; never copied.
SKIPPED_MODELS = {
    "contenttypes.contenttype",
    "auth.permission",
    "admin.logentry",
    "sessions.session",
}


class CopyError(Exception):
    """A rule was broken; the target has not been changed."""


def register_source(path: Path) -> None:
    """Add the SQLite file as a read-only second database."""
    path = Path(path).resolve()
    if not path.exists():
        raise CopyError(f"SQLite file not found: {path}")
    connections.databases[SOURCE_ALIAS] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": f"file:{path.as_posix()}?mode=ro",
        "OPTIONS": {"uri": True},
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "CONN_MAX_AGE": 0,
        "CONN_HEALTH_CHECKS": False,
        "TIME_ZONE": None,
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
        "TEST": {},
    }


def _label(model) -> str:
    return model._meta.label_lower


def models_to_copy(only=None):
    """
    All concrete models, including automatic many-to-many tables. With
    `only` (labels such as "accounts.user"), just those models.
    """
    chosen = {label.lower() for label in only} if only else None
    models_list = [
        m
        for m in apps.get_models(include_auto_created=True)
        if _label(m) not in SKIPPED_MODELS and not m._meta.proxy
    ]
    if chosen is None:
        return models_list
    unknown = chosen - {_label(m) for m in models_list}
    if unknown:
        raise CopyError("Unknown or non-copyable models: " + ", ".join(sorted(unknown)))
    return [m for m in models_list if _label(m) in chosen]


def _points_at_skipped(model) -> bool:
    return any(
        f.is_relation and f.remote_field and _label(f.related_model) in SKIPPED_MODELS
        for f in model._meta.concrete_fields
    )


def dependency_order(models_list):
    """Parents before children (foreign keys and one-to-ones), ignoring self-references."""
    wanted = set(models_list)
    deps = defaultdict(set)
    for model in models_list:
        for field in model._meta.concrete_fields:
            if field.is_relation and field.related_model in wanted:
                if field.related_model is not model:
                    deps[model].add(field.related_model)
    ordered, done = [], set()
    remaining = list(models_list)
    while remaining:
        progress = False
        for model in list(remaining):
            if deps[model] <= done:
                ordered.append(model)
                done.add(model)
                remaining.remove(model)
                progress = True
        if (
            not progress
        ):  # a cycle: fall back to the given order (constraints are deferred)
            ordered.extend(remaining)
            break
    return ordered


@contextmanager
def keep_timestamps():
    """
    auto_now / auto_now_add would overwrite the copied timestamps with 'now'.
    Switch them off while copying and always switch them back.
    """
    changed = []
    try:
        for model in apps.get_models(include_auto_created=True):
            for field in model._meta.concrete_fields:
                if getattr(field, "auto_now", False) or getattr(
                    field, "auto_now_add", False
                ):
                    changed.append((field, field.auto_now, field.auto_now_add))
                    field.auto_now = False
                    field.auto_now_add = False
        yield
    finally:
        for field, auto_now, auto_now_add in changed:
            field.auto_now = auto_now
            field.auto_now_add = auto_now_add


def check_ready(target_alias="default", only=None):
    """Refuse to run unless the target is a migrated, empty PostgreSQL database."""
    target = connections[target_alias]
    if target.vendor != "postgresql":
        raise CopyError(
            f"The target database must be PostgreSQL, but it is {target.vendor}. "
            "Set DATABASE_URL first."
        )
    from django.db.migrations.executor import MigrationExecutor

    pending = MigrationExecutor(target).migration_plan(
        MigrationExecutor(target).loader.graph.leaf_nodes()
    )
    if pending:
        raise CopyError(
            f"The target has {len(pending)} unapplied migrations. Run 'manage.py migrate' on it first."
        )
    filled = []
    for model in models_to_copy(only):
        if model.objects.using(target_alias).exists():
            filled.append(model._meta.db_table)
    if filled:
        raise CopyError(
            "The target already contains data in: " + ", ".join(sorted(filled)) + ". "
            "Use an empty database."
        )


def check_source_can_be_copied(only=None):
    """Rows that point at rebuilt tables would end up pointing at the wrong ids."""
    problems = []
    for model in (
        models_to_copy(only) if only else apps.get_models(include_auto_created=True)
    ):
        if _label(model) in SKIPPED_MODELS or model._meta.proxy:
            continue
        if _points_at_skipped(model) and model.objects.using(SOURCE_ALIAS).exists():
            problems.append(model._meta.db_table)
    if problems:
        raise CopyError(
            "The source has rows that point at content types or permissions, which are "
            "renumbered on the target: "
            + ", ".join(sorted(problems))
            + ". Copy them by hand."
        )


def copy_all(target_alias="default", batch_size=2000, log=print, only=None) -> dict:
    """Copy every table (or just those in `only`); returns {table: rows_copied}."""
    ordered = dependency_order(models_to_copy(only))
    copied = {}
    with keep_timestamps(), transaction.atomic(using=target_alias):
        for model in ordered:
            if _points_at_skipped(model):
                continue  # verified empty in the source
            table = model._meta.db_table
            batch, total = [], 0
            for row in (
                model.objects.using(SOURCE_ALIAS)
                .order_by("pk")
                .iterator(chunk_size=batch_size)
            ):
                batch.append(row)
                if len(batch) >= batch_size:
                    model.objects.using(target_alias).bulk_create(batch)
                    total += len(batch)
                    batch = []
            if batch:
                model.objects.using(target_alias).bulk_create(batch)
                total += len(batch)
            copied[table] = total
            log(f"  copied {table}: {total}")

        # Make auto-numbering continue after the highest copied id.
        connection = connections[target_alias]
        with connection.cursor() as cursor:
            for sql in connection.ops.sequence_reset_sql(no_style(), ordered):
                cursor.execute(sql)
        # Check every foreign key now rather than at commit.
        connection.check_constraints()
    return copied


def compare_counts(target_alias="default", only=None) -> list:
    """(table, source_rows, target_rows) for every table that differs."""
    differences = []
    for model in models_to_copy(only):
        if _points_at_skipped(model):
            continue
        source = model.objects.using(SOURCE_ALIAS).count()
        target = model.objects.using(target_alias).count()
        if source != target:
            differences.append((model._meta.db_table, source, target))
    return differences


def run(sqlite_path, target_alias="default", log=print, only=None) -> dict:
    """Validate, copy, verify. Raises CopyError or returns the per-table counts."""
    if settings.DATABASES[target_alias]["ENGINE"] != "django.db.backends.postgresql":
        raise CopyError("DATABASE_URL must point at PostgreSQL before copying.")
    register_source(sqlite_path)
    check_ready(target_alias, only)
    check_source_can_be_copied(only)
    copied = copy_all(target_alias, log=log, only=only)
    differences = compare_counts(target_alias, only)
    if differences:
        raise CopyError(f"Row counts differ after copying: {differences}")
    return copied
