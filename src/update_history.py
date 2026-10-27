"""Add the pulled days to the spread history, then check it before anything publishes.

The history is one small CSV, `_output/spread_history.csv`, with two columns:
date and spread (10-year minus 2-year, in percentage points). Only the spread
is stored, never the yields themselves. On GitHub Actions the file lives on
the `monitor-history` branch between runs.
"""

import sys
from datetime import date

import pandas as pd

import settings

MAX_ABS_SPREAD = 6.0  # percentage points; the widest since 1976 is under 3
MAX_STALE_DAYS = 10  # calendar days between today and the newest reading


def compute_spread(yields):
    """10-year minus 2-year, on the days both are published."""
    both = yields.dropna(subset=["y10", "y2"])
    return pd.DataFrame({"date": both["date"], "spread": (both["y10"] - both["y2"]).round(2)})


def merge_history(history, new_rows):
    """One row per date, oldest first. A date already in the history takes the new value."""
    merged = pd.concat([history, new_rows], ignore_index=True)
    merged = merged.drop_duplicates(subset="date", keep="last").sort_values("date")
    return merged.reset_index(drop=True)


def check_history(history, today=None):
    """Return a list of problems; an empty list means the history may be published.

    These are data checks, not unit tests: they run on every update and stop
    the run before a bad number reaches the site. Yesterday's page stays up.
    """
    today = pd.Timestamp(today or date.today())
    problems = []
    if history.empty:
        return ["the history is empty"]
    if history["date"].duplicated().any():
        problems.append("duplicate dates")
    if not history["date"].is_monotonic_increasing:
        problems.append("dates out of order")
    if history["spread"].isna().any():
        problems.append("missing spreads")
    if (history["spread"].abs() > MAX_ABS_SPREAD).any():
        problems.append(f"a spread beyond +/-{MAX_ABS_SPREAD} percentage points")
    stale = (today - history["date"].max()).days
    if stale > MAX_STALE_DAYS:
        problems.append(f"the newest reading is {stale} days old")
    return problems


def load_history(path=settings.HISTORY_CSV):
    if not path.exists():
        return pd.DataFrame({"date": pd.Series(dtype="datetime64[ns]"), "spread": pd.Series(dtype=float)})
    return pd.read_csv(path, parse_dates=["date"])


if __name__ == "__main__":
    yields = pd.read_csv(settings.YIELDS_CSV, parse_dates=["date"])
    history = load_history()
    updated = merge_history(history, compute_spread(yields))
    problems = check_history(updated)
    if problems:
        sys.exit("Not publishing: " + "; ".join(problems))
    settings.OUTPUT_DIR.mkdir(exist_ok=True)
    updated.to_csv(settings.HISTORY_CSV, index=False, date_format="%Y-%m-%d")
    latest = updated.iloc[-1]
    print(f"History: {len(updated):,} days ({len(updated) - len(history):+,}); "
          f"latest {latest['date']:%Y-%m-%d}: {latest['spread']:+.2f} pp")
