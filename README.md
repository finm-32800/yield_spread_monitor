# Yield Spread Monitor: history

The state the daily workflow carries from one day to the next, declared as a ChartBook dataframe. The code is on `main`.

To read it from another ChartBook pipeline, add this line to `[dependencies]` in its `chartbook.toml`, then run `chartbook pin`:

```toml
"finm-32800/yield_spread_monitor" = { git = "https://github.com/finm-32800/yield_spread_monitor", rev = "monitor-history" }
```
