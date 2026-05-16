# PT-RT1.2 Runtime State And Testnet Probe Transport Gates

## Scope

PT-RT1.2 fixes the runtime correctness issues found in the latest local paper-observation run and adds explicit gates for any future 20 USDC Hyperliquid testnet probe transport.

This phase is runtime correctness and plumbing-gate work only.

## What Changed

- The PT-RT1 runner now persists paper runtime state in `reports/paper_runtime/.../state.json`.
- Persisted state includes processed signal keys, open synthetic positions, realized equity by lane, last processed candle close by lane/symbol/timeframe, duplicate-open blocks, open totals, and close totals.
- Repeated same-candle synthetic opens are converted into held/blocked decisions with `duplicate_signal_ignored` / `existing_same_candle_signal_blocked` instead of new `paper_opened` rows.
- Synthetic paper PnL remains based only on public-mainnet candle data and the local synthetic paper ledger.
- `data_unavailable` now has a summary separating public market-data rows from lane-expanded decisions. One unavailable symbol/timeframe candle fetch can still produce one `data_unavailable` decision per strategy lane, but the summary makes that expansion explicit.
- The dashboard Paper Observation tab now displays persisted runtime state, duplicate blocks, market-row unavailable counts, lane-expanded unavailable counts, open synthetic positions, transport mode, submitted/cancel/reconcile counts, and the synthetic paper PnL source.

## Testnet Probe Transport Policy

Normal dashboard-started PT-RT1.2 sessions remain audit/order-shape mode:

- `--enable-testnet-probes`
- `--founder-approved-testnet-probes-20usdc`
- `--testnet-probe-notional-usdc 20`
- `--public-mainnet-only`
- compact decision logging

Signed transport is still not configured by default. A separate CLI path exists behind:

- `--submit-testnet-probes`
- `--founder-approved-pt-rt1-2-testnet-transport-20usdc`
- exact 20 USDC notional
- a configured transport client

Without the explicit transport approval and configured client, the runner records a blocked transport status and calls no signed/order endpoint.

## Boundary Confirmation

- Production Money Flow rules changed: no
- Strategy paper runtime approved as production behavior: no
- Live trading approved: no
- Live endpoints used: no
- Private/signed/order endpoints called during implementation/tests: no
- API keys used: no
- Testnet fills/prices update paper PnL: no
- SOR/fanout/CBBO/cross-venue routing added: no

## Current Operator Meaning

If the founder sees repeated `paper_opened` rows for the same candle after PT-RT1.2, that should be treated as a bug. The intended behavior is:

1. First valid open signal creates one synthetic position.
2. Repeated same-candle open attempts are held/blocked.
3. A later close signal closes the synthetic position and records a synthetic paper trade.
4. Testnet probe rows remain plumbing-only and do not alter paper PnL.

## Limitations

- The default runtime does not submit signed Hyperliquid testnet transport.
- The fakeable transport interface is test-covered, but a real credentialed transport client is not configured in this phase.
- Dashboard date filters remain display-only and do not regenerate canonical evidence or runtime state.
- Forward observation still requires a running local process and an awake/networked machine.

## Recommended Next Step

Run a fresh PT-RT1.2 observation session through the local dashboard control server, then review:

- `summary.json`
- `state.json`
- `decisions.jsonl`
- `trades.jsonl`
- `data_health.json`
- `testnet_probe_audit.jsonl`
- `testnet_probe_transport.jsonl`

Proceed to signed testnet transport only after the runtime state behavior is clean and the founder explicitly approves the transport path.
