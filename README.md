# Yield Spread Monitor

A daily monitor of the Treasury yield curve: the 10-year yield minus the
2-year, every business day since June 1976. A GitHub Actions workflow
updates it every morning and publishes it with GitHub Pages.

**Live page:** https://finm-32800.github.io/yield_spread_monitor/

It is a teaching example for FINM 32800, *Data Pipelines for Quantitative
Research*. The point is the machinery, not the finance: the same pattern
runs the SVIX monitor in HW 3. The guide that walks through it is in the
course textbook: *Building a Live Monitor with GitHub Actions* (week 5).

## Three branches, one job each

| Branch | Holds | Changes |
|---|---|---|
| `main` | the code | only when you push code |
| `monitor-history` | one file, `spread_history.csv`: the state the job carries from one day to the next | one small commit a day |
| `gh-pages` | the built page, which GitHub Pages serves | one commit, replaced on every run |

Nothing a run produces is ever committed to `main`.

## Deploy your own copy (in class)

1. **Get a FRED API key.** Make a free account at
   [fredaccount.stlouisfed.org](https://fredaccount.stlouisfed.org/apikeys)
   and request a key. It is 32 lowercase letters and digits.
2. **Copy the repository.** On this page, *Use this template* > *Create a
   new repository*. Make it **public**: a public repository gets free
   Actions minutes and GitHub Pages.
3. **Add the key as a secret.** In your copy: *Settings* > *Secrets and
   variables* > *Actions* > *New repository secret*. Name: `FRED_API_KEY`.
   Value: your key. It goes nowhere else: not in a file, not in a commit.
4. **Backfill the history.** *Actions* > *Backfill the Yield Spread
   History* > *Run workflow*, with the default start date. About a minute.
   This creates the `monitor-history` branch.
5. **Publish.** *Actions* > *Build and Deploy the Yield Spread Monitor* >
   *Run workflow*. About a minute. This creates the `gh-pages` branch.
6. **Turn on Pages.** *Settings* > *Pages* > *Deploy from a branch* >
   `gh-pages` / `/ (root)` > *Save*. Your page appears at
   `https://<your-username>.github.io/<repository>/` a minute later.

From then on the workflow runs by itself every day at 22:00 UTC. Look at
the `monitor-history` branch tomorrow: one more commit, one more line.

## Run it on your laptop

The project uses [uv](https://docs.astral.sh/uv/), which installs Python
3.12 and the locked dependencies the first time.

```bash
cp .env.example .env              # then paste your FRED key into .env
uv run doit                       # the backfill: pull everything, build the history and the page
uv run doit latest                # the daily update: pull the last ten days
START_DATE=2020-01-01 uv run doit # backfill from a date (the pull reruns when the window changes)
uv run pytest                     # the tests, offline, about a second
open docs/index.html              # the page
```

## Files

| File | What it does |
|---|---|
| `src/pull_yields.py` | Pulls DGS10 and DGS2 from the FRED API (`--latest`: the last ten days) |
| `src/update_history.py` | Computes the spread, adds the new days to the history, and checks the history before anything publishes |
| `src/build_page.py` | Builds `docs/index.html` from the history alone |
| `src/settings.py` | Reads the key and the dates from `.env` or the environment |
| `dodo.py` | The tasks: `doit` (the backfill) and `doit latest` (the daily update) |
| `.github/workflows/deploy_pages.yml` | The daily job: restore the history, test, update, record, publish |
| `.github/workflows/backfill.yml` | The backfill, run by hand with a start date |
| `src/test_monitor.py` | Unit tests and the check that the key comes from the secret store |

## Data and terms

Source: Board of Governors of the Federal Reserve System (US), H.15
Selected Interest Rates: Market Yield on U.S. Treasury Securities at
10-Year and 2-Year Constant Maturity (FRED series DGS10 and DGS2),
retrieved from FRED, Federal Reserve Bank of St. Louis. Both series are in
the public domain. The monitor stores only the spread it computes, never
the yields themselves; the yields live in `_data/`, which is gitignored and
discarded after every run.

This product uses the FRED® API but is not endorsed or certified by the
Federal Reserve Bank of St. Louis. See the
[FRED API Terms of Use](https://fred.stlouisfed.org/docs/api/terms_of_use.html).
