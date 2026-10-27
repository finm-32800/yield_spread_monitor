"""Settings, read from the environment or from a `.env` file.

FRED_API_KEY  your FRED API key. Locally it comes from `.env`; on GitHub
              Actions it comes from the repository secret of the same name.
START_DATE    first day the default `doit` pulls (the backfill). The 2-year
              yield starts on June 1, 1976, so that is the default.
END_DATE      last day pulled, today by default.
"""

import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
# `or` and not a default argument: a workflow that passes an empty input
# sets the variable to "", and "" should mean "use the default".
START_DATE = os.environ.get("START_DATE") or "1976-06-01"
END_DATE = os.environ.get("END_DATE") or date.today().isoformat()

DATA_DIR = BASE_DIR / "_data"  # pulled data, never committed
OUTPUT_DIR = BASE_DIR / "_output"  # the history CSV
DOCS_DIR = BASE_DIR / "docs"  # the built page

HISTORY_CSV = OUTPUT_DIR / "spread_history.csv"
YIELDS_CSV = DATA_DIR / "yields.csv"
