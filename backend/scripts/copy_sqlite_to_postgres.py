"""
Copy the SQLite database into the PostgreSQL one named by DATABASE_URL.

    cd backend
    python scripts/copy_sqlite_to_postgres.py [path/to/db.sqlite3] [--only app.model,app.model]

With --only, just those models are copied (for a fresh start that keeps, say,
the user accounts). Everything else is left empty in the target.

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
    args = list(argv[1:])
    only = None
    if "--only" in args:
        index = args.index("--only")
        if index + 1 >= len(args):
            print("--only needs a comma-separated list of models, e.g. accounts.user")
            return 2
        only = [name for name in args[index + 1].split(",") if name.strip()]
        del args[index : index + 2]
    source = Path(args[0]) if args else BACKEND / "db.sqlite3"
    print(f"source: {source}")
    if only:
        print("copying only:", ", ".join(only))
    started = time.time()
    try:
        copied = db_copy.run(source, only=only)
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
