"""Settings, read from the environment or from a `.env` file, and the committed window.

FRED_API_KEY  your FRED API key. Locally it comes from `.env`; on GitHub
              Actions it comes from the repository secret of the same name.

START_DATE and END_DATE, the window the backfill pulls, are not settings:
they are committed constants, defined below, and are never read from `.env`
or the environment.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

## The data window, as date strings: committed constants, not settings. Two
## people with different `.env` files who build the same commit must get the
## same bytes. `.env` holds secrets and machine facts (API keys,
## WRDS_USERNAME, DATA_DIR); anything that changes what is computed lives in
## a committed file. The default `doit`, which is also the backfill, pulls
## DGS10 and DGS2 from START_DATE to END_DATE in one FRED request each;
## END_DATE is the cutoff, and no pull keeps data past it. To backfill
## further, move START_DATE earlier and commit: the pull reruns when the
## window changes (`config_changed` in dodo.py). The window is never read
## from `.env` or the environment, so a stale `.env` cannot override it;
## import it instead: `from settings import START_DATE, END_DATE`. The daily
## update, `doit latest`, does not use this window: `pull_yields.py --latest`
## pulls the last ten days, the one path in this project that reads today's
## date. The 2-year yield starts on June 1, 1976, so that is START_DATE;
## END_DATE is the day the published history ran through when it was set.
START_DATE = "1976-06-01"
END_DATE = "2026-10-30"

DATA_DIR = BASE_DIR / "_data"  # pulled data, never committed
OUTPUT_DIR = BASE_DIR / "_output"  # the history CSV
DOCS_DIR = BASE_DIR / "docs"  # the built page

HISTORY_CSV = OUTPUT_DIR / "spread_history.csv"
YIELDS_CSV = DATA_DIR / "yields.csv"
