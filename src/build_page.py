"""Build the monitor's page, docs/index.html, from the spread history.

The page reads only `_output/spread_history.csv`: it never calls FRED, so it
can be rebuilt from the history alone.
"""

import os
from datetime import datetime, timezone
from html import escape

import pandas as pd
import plotly.graph_objects as go

import settings
from update_history import load_history

LINE = "#1d4f91"
INVERTED = "rgba(196, 64, 64, 0.13)"


def inverted_spans(history):
    """(start, end) of each run of consecutive readings below zero."""
    below = history["spread"] < 0
    run_id = (below != below.shift()).cumsum()
    spans = []
    for _, run in history[below].groupby(run_id[below]):
        spans.append((run["date"].iloc[0], run["date"].iloc[-1]))
    return spans


def make_figure(history):
    fig = go.Figure()
    for start, end in inverted_spans(history):
        fig.add_vrect(x0=start, x1=end, fillcolor=INVERTED, line_width=0, layer="below")
    fig.add_hline(y=0, line_dash="dot", line_color="#7a7a7a", line_width=1)
    fig.add_trace(go.Scatter(
        x=history["date"], y=history["spread"], mode="lines", name="10-year minus 2-year",
        line=dict(color=LINE, width=1.4),
        hovertemplate="%{x|%b %d, %Y}<br><b>%{y:+.2f}</b> percentage points<extra></extra>",
    ))
    last = history.iloc[-1]
    fig.add_trace(go.Scatter(
        x=[last["date"]], y=[last["spread"]], mode="markers", name="Latest",
        marker=dict(color=LINE, size=8, line=dict(color="white", width=2)), hoverinfo="skip",
    ))
    # A legend entry for the shading, which shapes do not get on their own.
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode="markers", name="Inverted (spread below zero)",
        marker=dict(symbol="square", size=12, color="rgba(196, 64, 64, 0.35)"),
    ))
    fig.update_layout(
        template="plotly_white", height=470, margin=dict(l=60, r=20, t=10, b=10),
        font=dict(family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", size=13),
        # Zoom buttons on the left, legend on the right, both above the plot.
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="closest",
        yaxis=dict(title="Percentage points", ticksuffix=" ", zeroline=False),
        xaxis=dict(
            rangeselector=dict(x=0, y=1.02, yanchor="bottom", buttons=[
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=5, label="5Y", step="year", stepmode="backward"),
                dict(count=10, label="10Y", step="year", stepmode="backward"),
                dict(label="All", step="all"),
            ]),
            rangeslider=dict(visible=True, thickness=0.06),
        ),
    )
    return fig


def nearest_before(history, when):
    earlier = history[history["date"] <= when]
    return earlier.iloc[-1] if not earlier.empty else None


def reading_text(history):
    last = history.iloc[-1]
    spread = last["spread"]
    if spread > 0:
        shape = "The curve slopes up: the 10-year Treasury yields more than the 2-year."
    elif spread < 0:
        shape = "The curve is inverted: the 2-year Treasury yields more than the 10-year."
    else:
        shape = "The curve is flat: the two yields are equal."
    sign = history["spread"] < 0
    flips = history.loc[sign != sign.shift(), "date"]
    since = flips.iloc[-1] if len(flips) > 1 else None
    changes = []
    for label, offset in [("a month", pd.DateOffset(months=1)), ("a year", pd.DateOffset(years=1))]:
        then = nearest_before(history, last["date"] - offset)
        if then is not None:
            changes.append(f"{spread - then['spread']:+.2f} over {label}")
    lines = [shape]
    if since is not None:
        state = "above" if spread >= 0 else "below"
        lines.append(f"It has been {state} zero since {since:%B %-d, %Y}.")
    if changes:
        lines.append("Change: " + "; ".join(changes) + " (percentage points).")
    return last, lines


def build_html(history):
    fig = make_figure(history)
    last, lines = reading_text(history)
    repo = os.environ.get("GITHUB_REPOSITORY", "finm-32800/yield_spread_monitor")
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    run_id = os.environ.get("GITHUB_RUN_ID")
    now = datetime.now(timezone.utc)
    updated = f"{now:%B %-d, %Y at %H:%M} UTC"
    if run_id:
        updated = f'<a href="{server}/{repo}/actions/runs/{run_id}">{updated}</a>, by a GitHub Actions run'
    recent = history.tail(10).iloc[::-1]
    rows = "\n".join(
        f"<tr><td>{r.date:%a, %b %-d, %Y}</td><td class='num'>{r.spread:+.2f}</td></tr>" for r in recent.itertuples()
    )
    chart = fig.to_html(full_html=False, include_plotlyjs="cdn", config={"displaylogo": False, "responsive": True})
    first = history["date"].iloc[0]
    return TEMPLATE.format(
        value=f"{last['spread']:+.2f}", as_of=f"{last['date']:%B %-d, %Y}",
        reading="".join(f"<p>{escape(line)}</p>" for line in lines),
        chart=chart, first=f"{first:%B %Y}", days=f"{len(history):,}", rows=rows,
        updated=updated, repo_url=f"{server}/{repo}", repo=escape(repo),
    )


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Treasury Yield Spread Monitor</title>
<style>
  :root {{ --ink: #1b1f24; --muted: #5b6470; --rule: #e3e6ea; --accent: #1d4f91; --bg: #ffffff; --panel: #f6f8fa; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink);
         font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  main {{ max-width: 980px; margin: 0 auto; padding: 32px 20px 48px; }}
  .eyebrow {{ color: var(--accent); font-weight: 600; font-size: 13px; letter-spacing: .04em; text-transform: uppercase; margin: 0 0 6px; }}
  h1 {{ font-size: 32px; line-height: 1.2; margin: 0 0 8px; }}
  h2 {{ font-size: 19px; margin: 36px 0 10px; }}
  .lede {{ color: var(--muted); font-size: 18px; margin: 0 0 24px; }}
  .reading {{ display: flex; gap: 24px; align-items: center; background: var(--panel);
             border: 1px solid var(--rule); border-radius: 10px; padding: 18px 22px; margin-bottom: 22px; }}
  .stat {{ text-align: center; min-width: 150px; }}
  .stat .value {{ display: block; font-size: 44px; font-weight: 700; color: var(--accent); line-height: 1; }}
  .stat .unit {{ display: block; color: var(--muted); font-size: 13px; margin-top: 6px; }}
  .stat .date {{ display: block; font-weight: 600; font-size: 14px; margin-top: 4px; }}
  .reading p {{ margin: 4px 0; }}
  figure {{ margin: 0; }}
  figcaption {{ color: var(--muted); font-size: 14px; border-top: 1px solid var(--rule); padding-top: 10px; margin-top: 4px; }}
  table {{ border-collapse: collapse; min-width: 320px; font-size: 15px; }}
  td, th {{ padding: 5px 14px 5px 0; border-bottom: 1px solid var(--rule); text-align: left; }}
  td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  ol {{ padding-left: 22px; }} li {{ margin: 6px 0; }}
  code {{ background: var(--panel); padding: 1px 5px; border-radius: 4px; font-size: 14px; }}
  a {{ color: var(--accent); }}
  footer {{ margin-top: 40px; padding-top: 14px; border-top: 1px solid var(--rule); color: var(--muted); font-size: 13px; }}
  footer p {{ margin: 6px 0; }}
  @media (max-width: 640px) {{ .reading {{ flex-direction: column; text-align: center; }} h1 {{ font-size: 26px; }} }}
</style>
</head>
<body>
<main>
  <p class="eyebrow">Daily monitor &middot; updated by GitHub Actions</p>
  <h1>The Treasury yield curve spread</h1>
  <p class="lede">The 10-year Treasury yield minus the 2-year, every business day since {first}.</p>

  <section class="reading" aria-label="Latest reading">
    <div class="stat"><span class="value">{value}</span><span class="unit">percentage points</span><span class="date">{as_of}</span></div>
    <div>{reading}</div>
  </section>

  <figure>
    {chart}
    <figcaption><strong>Figure 1.</strong> The spread between the 10-year and 2-year Treasury constant-maturity
    yields, in percentage points, {days} business days. Shaded bands mark the days the curve was inverted, when
    the 2-year yielded more than the 10-year, the reading most often cited as a recession signal. Use the buttons
    or the slider below the chart to zoom; hover for the value on any day.</figcaption>
  </figure>

  <h2>Recent readings</h2>
  <table>
    <thead><tr><th>Date</th><th class="num">Spread (pp)</th></tr></thead>
    <tbody>
{rows}
    </tbody>
  </table>

  <h2>How this page is made</h2>
  <ol>
    <li>Every day at 14:30 UTC, a GitHub Actions workflow pulls the newest 10-year and 2-year yields from the
        FRED API, with an API key stored as a repository secret.</li>
    <li>It adds the new days to the history: one CSV of dates and spreads, kept on the repository's
        <code>monitor-history</code> branch, one small commit a day. The <code>main</code> branch holds only code.</li>
    <li>It rebuilds this page and publishes it on the <code>gh-pages</code> branch, which GitHub Pages serves.</li>
  </ol>
  <p>Last updated {updated}. Code and history: <a href="{repo_url}">{repo}</a>.</p>

  <footer>
    <p><strong>Source:</strong> Board of Governors of the Federal Reserve System (US), H.15 Selected Interest Rates:
    Market Yield on U.S. Treasury Securities at 10-Year (DGS10) and 2-Year (DGS2) Constant Maturity, retrieved from
    FRED, Federal Reserve Bank of St. Louis. Both series are in the public domain; the spread is computed here.</p>
    <p>This product uses the FRED&reg; API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.
    <a href="https://fred.stlouisfed.org/docs/api/terms_of_use.html">FRED API Terms of Use</a>.</p>
    <p>A teaching example for FINM 32800, Data Pipelines for Quantitative Research, University of Chicago.</p>
  </footer>
</main>
</body>
</html>
"""


if __name__ == "__main__":
    history = load_history()
    if history.empty:
        raise SystemExit("No history yet: run `doit` (the backfill) or `doit latest` first.")
    settings.DOCS_DIR.mkdir(exist_ok=True)
    (settings.DOCS_DIR / "index.html").write_text(build_html(history))
    (settings.DOCS_DIR / ".nojekyll").touch()
    print(f"Wrote docs/index.html ({len(history):,} days, latest {history['date'].iloc[-1]:%Y-%m-%d})")
