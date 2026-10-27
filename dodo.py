"""The monitor's tasks. Plain `doit` is the backfill; `doit latest` is the daily update.

    uv run doit           # pull START_DATE..END_DATE (all of it, by default), update the history, build the page
    uv run doit latest    # pull the last ten days, update the history, build the page
    uv run doit list      # list the tasks

Every task reads and writes only `_data/`, `_output/`, and `docs/`, which are
gitignored. Nothing a run produces is ever committed to `main`.
"""

import sys

sys.path.insert(1, "./src")

from doit.tools import config_changed  # noqa: E402

import settings  # noqa: E402

DOIT_CONFIG = {
    "default_tasks": ["pull", "history", "page"],
    "backend": "sqlite3",
    "dep_file": ".doit-db.sqlite",
    "verbosity": 2,
}


def task_pull():
    """Pull the 10-year and 2-year yields from FRED, START_DATE to END_DATE"""
    return {
        "actions": ["python src/pull_yields.py"],
        "file_dep": ["src/pull_yields.py", "src/settings.py"],
        "targets": [settings.YIELDS_CSV],
        # Pull again when the window changes, not only when the code does:
        # set START_DATE earlier and `doit` backfills further.
        "uptodate": [config_changed({"start": settings.START_DATE, "end": settings.END_DATE})],
    }


def task_history():
    """Add the pulled days to the spread history, and check it"""
    return {
        "actions": ["python src/update_history.py"],
        "file_dep": ["src/update_history.py", settings.YIELDS_CSV],
        "targets": [settings.HISTORY_CSV],
    }


def task_page():
    """Build docs/index.html from the history"""
    return {
        "actions": ["python src/build_page.py"],
        "file_dep": ["src/build_page.py", settings.HISTORY_CSV],
        "targets": [settings.DOCS_DIR / "index.html"],
    }


def task_latest():
    """The daily update: pull the last ten days, add them to the history, rebuild the page"""
    return {
        "actions": [
            "python src/pull_yields.py --latest",
            "python src/update_history.py",
            "python src/build_page.py",
        ],
        "file_dep": ["src/pull_yields.py", "src/update_history.py", "src/build_page.py"],
        # A daily update checks again every time it is run, so it is never
        # up to date. It has no targets: the history and the page are also
        # the targets of `history` and `page`, and doit lets only one task
        # claim a file.
        "uptodate": [False],
    }
