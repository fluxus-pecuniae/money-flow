# Dashboard and UI Map

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

This note explains current founder-facing dashboard surfaces and what each surface can and cannot prove.

## Source Files

- `apps/dashboard/index.html`
- `apps/dashboard/evidence-dashboard.js`
- `apps/dashboard/evidence-dashboard.css`
- `apps/dashboard/README.md`
- `apps/dashboard/DESIGN.md`
- `scripts/run_dashboard_control_server.py`

## Current Visible Tabs

| Surface | Data Source | Use It For | Do Not Infer |
| --- | --- | --- | --- |
| Strategy | Static strategy/config summaries | Understand Money Flow v1.2 and variant ideas at a high level | Do not infer production approval |
| Historical Replay | Generated local chart/trade JSON from SV2.0.2, SOR-EV3, MF-ORIG-EV2 where present | Visual candle/indicator/trade review | Do not treat date filters as canonical evidence regeneration |
| Evidence | SV2.0.2 batch reports and generated replay rows | Run ledger and comparison tables | Do not treat aggregate sums as one-account PnL |
| Evidence Lab | SOR/MF-ORIG summary bundles and overlays | Variant review, loss anatomy, control-pocket review | Do not treat overlays as production candidates |
| Audit Review | EV-AUDIT1 summary JSON | Audit verdict, methodology/data confidence, issues, paper-readiness status | Do not treat audit display as strategy approval |
| Paper Observation | PT-RT1 local runtime summaries plus browser public-mainnet display polling | Observe synthetic paper lanes, scanner health, signal rows, and optionally start/stop local probes-disabled runs through the localhost control server | Do not infer live approval, production paper-runtime approval, order permission, or canonical evidence regeneration |

## Current Hidden / Legacy Surfaces

The old `Experiments` tab must not be promoted as current truth. Legacy UAT surfaces may remain hidden for regression and historical context, but they should not compete with current Strategy / Historical Replay / Evidence / Evidence Lab / Audit Review flows.

## Canonical vs Display-Only

- Canonical evidence lives in backend-generated evidence packs and committed founder-readable reports.
- Historical Replay chart JSON is visualization-only.
- Evidence Lab overlays are visualization-only.
- Date filters are display-only. Dashboard date filters are display-only recalculations.
- The Paper Observation Start Run helper is local runtime ergonomics only; it always forces `--disable-testnet-probes` and `--public-mainnet-only` and does not enable testnet probes.
- Dashboard output does not submit orders, call private/signed/order endpoints, import candles, or regenerate evidence packs.

## Known UI Limitations

- Local ignored chart-data files must exist for full candle/indicator/trade visualization.
- Missing overlay timestamps are shown as unavailable states, not guessed.
- Historical Replay strategy rows are evidence/research-only unless a later approved phase changes status.
