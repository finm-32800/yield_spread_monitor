"""Tests for the monitor. They run offline, with no API key, in about a second."""

import re
from pathlib import Path

import pandas as pd

from build_page import inverted_spans
from pull_yields import observations_to_frame
from update_history import check_history, compute_spread, merge_history

ROOT = Path(__file__).resolve().parent.parent


def frame(rows):
    return pd.DataFrame(rows, columns=["date", "spread"]).assign(date=lambda d: pd.to_datetime(d["date"]))


def test_fred_writes_a_missing_day_as_a_dot():
    observations = [{"date": "2026-10-12", "value": "."}, {"date": "2026-10-13", "value": "4.05"}]
    df = observations_to_frame(observations)
    assert df["value"].isna().tolist() == [True, False]
    assert df["value"].iloc[1] == 4.05


def test_spread_is_ten_year_minus_two_year_on_days_with_both():
    yields = pd.DataFrame({
        "date": pd.to_datetime(["2026-10-12", "2026-10-13", "2026-10-14"]),
        "y10": [None, 4.05, 4.10],
        "y2": [3.60, 3.70, None],
    })
    spread = compute_spread(yields)
    assert spread["date"].dt.strftime("%Y-%m-%d").tolist() == ["2026-10-13"]
    assert spread["spread"].tolist() == [0.35]


def test_merging_keeps_one_row_per_date_and_the_newest_value():
    history = frame([("2026-10-13", 0.35), ("2026-10-14", 0.30)])
    new = frame([("2026-10-14", 0.31), ("2026-10-15", 0.33)])
    merged = merge_history(history, new)
    assert merged["date"].dt.strftime("%Y-%m-%d").tolist() == ["2026-10-13", "2026-10-14", "2026-10-15"]
    assert merged["spread"].tolist() == [0.35, 0.31, 0.33]


def test_checks_pass_a_clean_history_and_stop_a_bad_one():
    clean = frame([("2026-10-13", 0.35), ("2026-10-14", 0.31)])
    assert check_history(clean, today="2026-10-16") == []
    assert any("days old" in p for p in check_history(clean, today="2026-11-30"))
    wild = frame([("2026-10-13", 0.35), ("2026-10-14", 31.0)])
    assert any("beyond" in p for p in check_history(wild, today="2026-10-16"))


def test_inverted_spans_cover_each_run_below_zero():
    history = frame([("2022-07-05", 0.05), ("2022-07-06", -0.02), ("2022-07-07", -0.04), ("2022-07-08", 0.01)])
    spans = inverted_spans(history)
    assert [(a.strftime("%m-%d"), b.strftime("%m-%d")) for a, b in spans] == [("07-06", "07-07")]


def test_the_key_comes_from_the_secret_store():
    for name in ["deploy_pages.yml", "backfill.yml"]:
        text = (ROOT / ".github" / "workflows" / name).read_text()
        assert re.search(r"FRED_API_KEY:\s*\$\{\{\s*secrets\.FRED_API_KEY\s*\}\}", text), name
        assert not re.search(r"\b[a-f0-9]{32}\b", text), f"{name} must never contain a key"
