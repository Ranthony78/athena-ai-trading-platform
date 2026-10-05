"""
Database settings from the environment.

SQLite stays the default so a fresh checkout works with no setup. Set
DATABASE_URL (for example postgres://user:password@localhost:5432/athena_db)
or the separate DB_* variables to use PostgreSQL. Passwords may contain
special characters; in a URL they must be percent-encoded.
"""

from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

POSTGRES_SCHEMES = {"postgres", "postgresql", "pgsql"}
CONNECTION_MAX_AGE = 60  # seconds a connection is reused


def _sqlite(base_dir: Path) -> dict:
    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": base_dir / "db.sqlite3",
    }


def _postgres(name, user, password, host, port, sslmode="") -> dict:
    if not name or not user:
        raise ImproperlyConfigured(
            "PostgreSQL needs a database name and a user (DB_NAME and DB_USER, "
            "or a full DATABASE_URL)."
        )
    config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": name,
        "USER": user,
        "PASSWORD": password or "",
        "HOST": host or "localhost",
        "PORT": str(port or "5432"),
        "CONN_MAX_AGE": CONNECTION_MAX_AGE,
        "CONN_HEALTH_CHECKS": True,
    }
    if sslmode:
        config["OPTIONS"] = {"sslmode": sslmode}
    return config


def _from_url(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in POSTGRES_SCHEMES:
        raise ImproperlyConfigured(
            "DATABASE_URL must start with postgres:// or postgresql://."
        )
    query = parse_qs(parsed.query)
    return _postgres(
        name=unquote(parsed.path.lstrip("/")),
        user=unquote(parsed.username or ""),
        password=unquote(parsed.password or ""),
        host=parsed.hostname,
        port=parsed.port,
        sslmode=(query.get("sslmode") or [""])[0],
    )


def database_config(env, base_dir: Path) -> dict:
    """The `default` entry of DATABASES for the given environment mapping."""
    url = (env.get("DATABASE_URL") or "").strip()
    if url:
        return _from_url(url)

    engine = (env.get("DB_ENGINE") or "sqlite").strip().lower()
    if engine in ("", "sqlite", "sqlite3"):
        return _sqlite(base_dir)
    if engine in POSTGRES_SCHEMES:
        return _postgres(
            name=env.get("DB_NAME", ""),
            user=env.get("DB_USER", ""),
            password=env.get("DB_PASSWORD", ""),
            host=env.get("DB_HOST", ""),
            port=env.get("DB_PORT", ""),
            sslmode=env.get("DB_SSLMODE", ""),
        )
    raise ImproperlyConfigured(f"DB_ENGINE must be sqlite or postgres, not {engine!r}.")
