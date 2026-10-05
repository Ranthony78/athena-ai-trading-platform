"""
Back up the PostgreSQL database named by DATABASE_URL (project-root .env).

    python backend/scripts/pg_backup.py [--dest DIR] [--keep N]

Writes athena_db-<timestamp>.dump (pg_dump custom format), checks it can be
read with pg_restore, then deletes all but the newest N dumps (default 14).
The password is passed to pg_dump through the environment, never on the
command line, and is never printed. Exit code is non-zero on any failure.
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEST = Path(r"C:\DevOpsProject\athena-backups")
PREFIX = "athena_db-"


def find_tool(name: str) -> str:
    """pg_dump/pg_restore from PATH, else the newest standard Windows install."""
    found = shutil.which(name)
    if found:
        return found
    candidates = sorted(Path(r"C:\Program Files\PostgreSQL").glob(f"*/bin/{name}.exe"))
    if candidates:
        return str(candidates[-1])
    raise SystemExit(f"{name} not found; install PostgreSQL client tools.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--keep", type=int, default=14)
    args = parser.parse_args()

    url = (dotenv_values(ROOT / ".env").get("DATABASE_URL") or "").strip()
    parsed = urlparse(url)
    if not parsed.scheme.startswith("postgres"):
        print("DATABASE_URL is not a PostgreSQL URL; nothing to back up.")
        return 1

    args.dest.mkdir(parents=True, exist_ok=True)
    out = args.dest / f"{PREFIX}{datetime.now():%Y%m%d-%H%M%S}.dump"
    env = dict(os.environ, PGPASSWORD=unquote(parsed.password or ""))
    dump = subprocess.run(
        [
            find_tool("pg_dump"),
            "-h",
            parsed.hostname or "localhost",
            "-p",
            str(parsed.port or 5432),
            "-U",
            unquote(parsed.username or ""),
            "-d",
            parsed.path.lstrip("/"),
            "-F",
            "c",
            "-f",
            str(out),
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    if dump.returncode != 0:
        out.unlink(missing_ok=True)
        print("pg_dump failed:", dump.stderr.strip()[:300])
        return 1

    check = subprocess.run(
        [find_tool("pg_restore"), "--list", str(out)], capture_output=True, text=True
    )
    if check.returncode != 0:
        print("backup written but pg_restore cannot read it:", out)
        return 1
    print(
        f"{datetime.now():%Y-%m-%d %H:%M} ok {out.name} {out.stat().st_size / 1048576:.1f} MB"
    )

    # Retention: only files this script names, newest N kept.
    dumps = sorted(args.dest.glob(f"{PREFIX}*.dump"))
    for old in dumps[: max(0, len(dumps) - args.keep)]:
        old.unlink()
        print("removed old backup", old.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
