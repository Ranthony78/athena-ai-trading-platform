"""
Copy the SQLite database into the PostgreSQL one named by DATABASE_URL.

    cd backend
    python scripts/copy_sqlite_to_postgres.py [path/to/db.sqlite3]

Run 'python manage.py migrate' on the PostgreSQL database first. The target
must be empty. See shared/db_copy.py for the rules this enforces.
"""

import os
import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django  # noqa: E402

django.setup()

from shared import db_copy  # noqa: E402


def main(argv) -> int:
    source = Path(argv[1]) if len(argv) > 1 else BACKEND / "db.sqlite3"
    print(f"source: {source}")
    started = time.time()
    try:
        copied = db_copy.run(source)
    except db_copy.CopyError as error:
        print(f"STOPPED: {error}")
        print("Nothing was changed in the target database.")
        return 1
    print(
        f"done: {sum(copied.values())} rows in {len(copied)} tables, {time.time() - started:.0f} s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
