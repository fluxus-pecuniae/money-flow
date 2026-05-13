# Strategy Validation Map

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

## What Strategy Validation Did

| Phase Range | Purpose | Outcome |
| --- | --- | --- |
| SV1.0-SV1.2.1 | Baseline backtest truth | Fill timing, drawdown, window, coverage, and regime truth established. |
| SV1.3-SV1.4.1 | Campaigns / evidence packs | Repeatable evidence workflow and collision-safe packs. |
| SV1.5-SV1.9.1 | Data / import / DB governance | Candle import, DB target truth, schema gates, timestamp truth, and Obsidian governance. |
| SV1.10-SV1.12.5.1 | Hyperliquid data readiness / import | Intended DB migrated, research identity seeded, and 9 public campaign files imported. |
| SV1.13-SV1.13.2 | First evidence + dynamic equity | Hyperliquid public evidence generated; ETH `sleeve_1h` was strongest observed pocket. |
| SV1.14-SV1.17 | Diagnostics / replay experiments | Trade anatomy, market-structure diagnostics, completed-trade overlays, rejected-signal replay, and full-suite true replay experiments. Variants did not beat the ETH 1h baseline control pocket. |
| SV1.18-SV1.18.1 | Closeout / UAT candidate freeze | ETH 1h baseline frozen for UAT observation; coordination handoff cleaned up. |
| SV2.0 | 1D sleeve / expanded public-mainnet evidence refresh | Money Flow v1.2 adds real `sleeve_1d`; BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX/SHIB are resolved through Hyperliquid public mainnet metadata; SHIB maps to `kSHIB`; 15m/1h/4h/1D public candle readiness and compact dynamic-equity evidence are recorded. |
| SV2.0.1 | Canonical evidence truth hotfix | Compact SV2 rows are explicitly noncanonical; dataset-end open positions are force-closed with entry-fee accounting; Hyperliquid close slots are normalized; staged/imported/canonical-evidence truth is separated; runtime allocations are 0.25 each; internal timeframe is `1d` with display label `1D`; missing indicators are invalid instead of zero. Canonical evidence packs remain blocked. |
| SV2.0.2 | Hardened DB import / canonical evidence packs | Normalized Hyperliquid public mainnet candles are imported through the hardened importer into the intended DB, 36 fully closed per-pair Money Flow v1.2 evidence packs are generated for BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX x 15m/1h/4h/1d, and SHIB/kSHIB is deferred with explicit reason codes. |
| SOR-EV1 | Loss anatomy / evidence-only variants | Canonical SV2.0.2 packs are analyzed for worst losses, adverse-move/late-entry patterns, fixed-stop completed-trade overlays, deferred true-replay variants, control-pocket impact, and no production candidates. |
| SOR-EV2 | True-forward stop/exit and rejected-signal replay | Baseline parity passes for all 72 canonical SV2.0.2 scenarios; stop/exit and entry variants are replayed from persisted candle truth; large-loss candle context and control-pocket impact are reported; no variant is promoted. |
| SOR-EV2.1 | Evidence Lab / Variant Review UI | Dashboard visualization loads SOR-EV1/SOR-EV2 summaries, labels SV2.0.2 as canonical baseline, and shows variant matrix, control pockets, worst trades, late-entry, adverse-candle, and RSI/MACD panels. The Variant Summary Matrix now uses founder-review labels for promising, mixed, deferred, no-op, diagnostic-only, and hard-rejected rows. It is UI-only and promotes no variant. |
| SOR-EV2.2 | Variant chart overlay / founder review workflow | Evidence Lab overlays baseline SV2.0.2 entry/exit markers against linkable SOR-EV2 variant/adverse-candle context, adds worst-trade focus and control-pocket overlay review, and shows unavailable states where exact marker data is missing. It is UI-only and promotes no variant. |
| SOR-EV3 | Founder-selected avoid sideways / low-volatility drilldown | Baseline parity passes for all 72 canonical SV2.0.2 scenarios. ATR-percentile, flat trend, rolling-range compression, MACD-flat chop, and conservative combined blockers are tested as true-forward replay with blocked-entry attribution, avoided-loser/missed-winner counts, loss concentration, and control-pocket impact. No variant is promoted. Founder-review labels now distinguish promising rolling-range variants from hard rejections: `avoid_low_rolling_range_20` is `promising_control_pocket_risk`, `avoid_low_rolling_range_50` is `promising_high_pnl_control_risk`, and `avoid_low_atr_percentile_30` is `rejected_negative_aggregate`. Historical Replay chart-data regeneration now includes full research-only `avoid_low_rolling_range_20` and `avoid_low_rolling_range_50` rows across 9 symbols x 4 timeframes x 2 fills. |
| MF-ORIG-EV1 | Original Money Flow reconstruction / gap matrix | The original Money Flow Trading System is reconstructed from the prompt-provided Gerald Peters source summary as a Strategy Validation-only research family. It documents source-vs-v1.2 drift, treats `1d` as primary source timeframe, tests 5 EMA / 20 SMA stage/crossover, breakout, pullback/reclaim, and stage-filter hypotheses with RSI warning trims, MACD-as-TSI substitute, structure-stop proxies, and 1% risk sizing. Production Money Flow v1.2 remains unchanged. The source PDF was not locally available. |
| MF-ORIG-EV1.1 | Accounting / drawdown hotpatch | Pre-hotpatch MF-ORIG-EV1 PnL/drawdown conclusions are quarantined. Regenerated MF-ORIG reports now use event-ledger accounting, single-counted entry fees and trim PnL, final closes on remaining quantity only, peak-to-trough realized and mark-to-market drawdown, an all-trade accounting invariant audit, and baseline-positive 1d control-pocket filtering. Candidate gates were re-run and still mark all original hypotheses `source_faithful_but_underperformed`. |
| MF-ORIG-EV2 | Multi-timeframe evidence packs / Historical Replay UI | Corrected Original Money Flow hypotheses are replayed across BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX x 15m/1h/4h/1d x next_candle_open/next_candle_close. The run generates 144 ignored evidence-pack directories, 36 ignored dashboard chart-data files, and compact committed Markdown/JSON summaries. Historical Replay and Evidence Run Ledger can visualize MF-ORIG-EV2 strategies. Production Money Flow v1.2 remains unchanged and no hypothesis is approved. |

## What Strategy Validation Proved

- ETH `sleeve_1h` baseline is the strongest observed Hyperliquid public-candle candidate.
- Hyperliquid public evidence justifies tightly scoped UAT observation only.
- Dynamic-equity per-scenario simulation exists.
- Lower-RSI variants did not beat ETH `sleeve_1h` baseline in the accepted true replay work.
- 15m and 4h are excluded from current UAT candidate scope.
- SV2.0 proves only that 1D is now represented as a baseline Money Flow sleeve and that expanded Hyperliquid public-mainnet readiness/evidence can be generated for the requested universe; it does not prove profitability.
- SV2.0.1 proves evidence-truth guardrails are explicit; it does not generate canonical evidence packs.
- SV2.0.2 proves the SV2 baseline now has DB-backed canonical evidence-pack paths with dynamic equity, canonical close slots, fully closed end-boundaries, explicit open-position handling, per-pair full available imported windows, and supported/deferred symbol truth; it still does not prove profitability.
- SOR-EV1 proves the largest-loss review and evidence-only variant triage can be performed from the canonical SV2.0.2 packs without changing production rules; it does not approve any stop/entry variant.
- SOR-EV2 proves true-forward replay can test those hypotheses from persisted candle truth with baseline parity; it still does not promote variants or approve production changes.
- SOR-EV2.1 proves the founder can visually review SOR-EV1/SOR-EV2 bundle outputs in the dashboard; it does not create canonical evidence or approve variants.
- SOR-EV2.2 proves the founder can inspect baseline markers plus linkable SOR-EV2 context on historical candles in Evidence Lab; unavailable exact variant timestamps are explicit and not guessed.
- SOR-EV3 proves the broad `avoid_sideways_low_volatility` family can be objectively tested true-forward against canonical SV2.0.2 with blocked-entry attribution. It does not produce a production candidate, but founder-review labels now preserve promising-but-not-promoted rolling-range signals instead of flattening all non-candidates into rejected. Historical Replay now has generated local chart/trade JSON for the two rolling-range variants so founder review can happen in the candle/indicator/trade-inspector workflow, not only Evidence Lab tables.
- MF-ORIG-EV1.1 proves the MF-ORIG reconstruction accounting/drawdown truth has been hotpatched. Current Money Flow v1.2 is still Money Flow-inspired rather than source-faithful to the original hierarchy, but pre-hotpatch MF-ORIG-EV1 PnL/drawdown conclusions should not be used. The regenerated original hypotheses show pre-gate aggregate PnL/drawdown improvement, but still fail candidate gate because baseline-positive 1d control pockets are not preserved, so no original hypothesis is production-approved.
- MF-ORIG-EV2 proves the corrected original reconstruction can be replayed over the same canonical SV2.0.2 multi-symbol/multi-timeframe substrate and visualized in Historical Replay. It still does not approve a hypothesis; `1d` source-primary rows remain weak versus positive 1d controls while 1h/4h/15m fractal/stress-test rows are useful founder-review evidence only.

## What Strategy Validation Did Not Prove

- It did not prove profitability.
- It did not approve paper trading.
- It did not approve live trading.
- It did not validate cross-venue performance.
- It did not model funding.
- It did not model liquidation.
- It did not model production exchange margin behavior.
- It did not model real order-book fills.
- It did not model partial fills.
- It did not model latency or outages.
- It did not model live reject / cancel / fill reconciliation behavior.
- SV2.0 did not optimize 1D parameters, approve live trading, submit orders, or generate full committed evidence-pack directories.
- SV2.0.1 did not make compact staged rows canonical evidence, did not import staged candles into the DB, and did not unblock SOR-EV1 by itself.
- SV2.0.2 did not optimize parameters, add stop-loss or RSI/MACD variants, submit orders, call private/signed/order endpoints, use testnet data as strategy truth, commit large generated evidence packs, or approve live trading.
- SOR-EV1 did not run true-forward stop/entry replay, did not promote variants, did not change rules, and did not approve paper/live trading.
- SOR-EV2 did not promote variants, did not change rules, did not approve paper/live trading, and did not use dashboard date-filter numbers as canonical evidence.
- SOR-EV2.1 did not change Money Flow rules, approve variants, regenerate evidence packs, submit orders, call private/signed/order endpoints, use testnet prices as strategy truth, or make dashboard date-filter/overlay outputs canonical.
- SOR-EV2.2 did not change Money Flow rules, approve variants, regenerate evidence packs, submit orders, call private/signed/order endpoints, use testnet prices as strategy truth, or make dashboard overlays/date filters canonical evidence.
- SOR-EV3 did not change Money Flow rules, approve variants, run a broad parameter grid, submit orders, call private/signed/order endpoints, use testnet prices as strategy truth, or use dashboard date filters as canonical evidence.
- MF-ORIG-EV1.1 did not change production Money Flow rules, approve an original strategy, submit orders, call private/signed/order endpoints, use testnet prices as strategy truth, use dashboard date filters as canonical evidence, start MF-ORIG-EV2, or directly verify the PDF text because the PDF was not present locally.
- MF-ORIG-EV2 did not change production Money Flow rules, approve an original strategy, submit orders, call private/signed/order endpoints, use testnet prices as strategy truth, use dashboard date filters as canonical evidence, import/refetch candles, or directly verify the PDF text because the PDF was not present locally.

## Current Candidate

See [[30 Strategy/UAT Candidate Freeze|UAT Candidate Freeze]].

Candidate id: `money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

## Excluded From Current UAT Scope

- 15m sleeve.
- 4h sleeve.
- BTC `sleeve_1h`.
- SOL `sleeve_1h`.
- Lower-RSI variants.
- Market-structure variants.
- Aster / Binance / OKX / Coinbase / Kraken.
- Cross-venue comparison.

## Interpretation Rule

Every SV result remains research-only. A scenario can be observed, diagnostically useful, or suitable for UAT/PT observation without proving profitability or authorizing live trading.

PAPER TRADING IS APPROVED. Paper trading is approved for Hyperliquid testnet/sandbox only under PT0. BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED. Broader top-20 Hyperliquid-supported paper/sandbox trading is approved under metadata, precision, risk, lease, label, and no-live gates. Live trading is not approved. Live exchange order submission is not approved.
