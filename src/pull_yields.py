"""Pull the 10-year and 2-year Treasury yields from the FRED API.

    python src/pull_yields.py            # START_DATE to END_DATE (the backfill)
    python src/pull_yields.py --latest   # the last LATEST_DAYS days (the daily update)

Both series come from the Federal Reserve Board's H.15 release and are in the
public domain. FRED's own spread series, T10Y2Y, is tagged as copyrighted,
which is one reason this project computes the spread itself.
"""

import argparse
import sys
import time
from datetime import date, timedelta

import pandas as pd
import requests

import settings

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"
SERIES = {"DGS10": "y10", "DGS2": "y2"}
LATEST_DAYS = 10  # reaches back over a long weekend and FRED's one-day lag


def fetch_series(series_id, start, end, api_key, tries=3):
    """One FRED series as a DataFrame with columns date and value.

    FRED writes a missing observation (a holiday) as ".", which becomes NaN.
    """
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
        "observation_end": end,
    }
    for attempt in range(1, tries + 1):
        try:
            response = requests.get(FRED_URL, params=params, timeout=30)
            response.raise_for_status()
            break
        except requests.RequestException as error:
            if attempt == tries:
                raise
            print(f"FRED request failed ({error}); retrying in {5 * attempt} s")
            time.sleep(5 * attempt)
    return observations_to_frame(response.json()["observations"])


def observations_to_frame(observations):
    df = pd.DataFrame(observations, columns=["date", "value"])
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")  # "." -> NaN
    return df


def pull_yields(start, end, api_key):
    """Both yields side by side, one row per day."""
    frames = []
    for series_id, column in SERIES.items():
        frames.append(fetch_series(series_id, start, end, api_key).rename(columns={"value": column}))
    return frames[0].merge(frames[1], on="date", how="outer").sort_values("date")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--latest", action="store_true", help=f"pull only the last {LATEST_DAYS} days")
    args = parser.parse_args()
    if not settings.FRED_API_KEY:
        sys.exit(
            "FRED_API_KEY is not set. Locally: copy .env.example to .env and add your key. "
            "On GitHub: Settings > Secrets and variables > Actions > New repository secret."
        )
    if args.latest:
        start, end = (date.today() - timedelta(days=LATEST_DAYS)).isoformat(), date.today().isoformat()
    else:
        start, end = settings.START_DATE, settings.END_DATE
    yields = pull_yields(start, end, settings.FRED_API_KEY)
    settings.DATA_DIR.mkdir(exist_ok=True)
    yields.to_csv(settings.YIELDS_CSV, index=False)
    print(f"Pulled {len(yields):,} days of DGS10 and DGS2, {start} to {end}")
