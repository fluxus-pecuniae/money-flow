# CHANGELOG

Canonical repo changelog. This is the single changelog file for the repository.

Entry schema:

- `version`
- `recorded_at_utc`
- `scope`
- `intent`
- `affected_files`
- `validation_performed`

---

## v2026.05.02.002

- `recorded_at_utc`: `2026-05-02T07:04:32Z`
- `scope`: `SV1.4.1 Money Flow evidence-pack collision and overwrite integrity hotfix`
- `intent`: `Native entry. Hardened the Strategy Validation campaign evidence-pack writer so research records cannot be silently overwritten before SV1.5 starts generating real campaign evidence. Evidence-pack output now uses an explicit collision policy: default `unique_suffix` reserves a new suffixed run directory when the requested campaign/timestamp directory already exists, while `fail_if_exists` raises an explicit collision error. Pack file writes refuse existing paths, and manifests now record campaign slug, requested run timestamp/id, final run id, final evidence-pack path, collision policy, whether a collision occurred, and the suffix used. The campaign CLI exposes `--collision-policy`. This is evidence-record write safety only: no Money Flow rules, parameter optimization, strategy recommendations, paper/live trading, live artifacts, routing, execution automation, exchange calls, route executor behavior, fanout, target reselection, or auto-submit were added.`
- `affected_files`:
  - `services/strategy_validation/campaigns.py`
  - `services/strategy_validation/__init__.py`
  - `scripts/run_money_flow_research_campaign.py`
  - `tests/test_sv141_evidence_pack_integrity.py`
  - `tests/test_operational_docs.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/00 Maps/Current State Dashboard.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall services/strategy_validation scripts/run_money_flow_research_campaign.py tests/test_sv141_evidence_pack_integrity.py` passed during focused development.
  - `.venv/bin/python -m pytest -q tests/test_sv141_evidence_pack_integrity.py` passed with 3 tests during focused development.
  - `.venv/bin/python -m pytest -q tests/test_sv13_research_campaigns.py tests/test_sv14_evidence_readiness.py tests/test_sv141_evidence_pack_integrity.py` passed with 13 tests during focused campaign regression.
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py tests/test_sv11_strategy_validation_batch.py tests/test_sv12_strategy_validation_regimes.py tests/test_sv13_research_campaigns.py tests/test_sv14_evidence_readiness.py tests/test_sv141_evidence_pack_integrity.py` passed with 31 tests.
  - `.venv/bin/python -m pytest -q tests/test_phase3_strategy.py tests/test_operational_docs.py` passed with 17 tests.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed with 499 tests.
  - `git diff --check` passed.
  - `.venv/bin/python -m compileall core services apps tests scripts` passed after final docs/code cleanup.
  - `.venv/bin/python -m pytest -q tests/test_sv141_evidence_pack_integrity.py tests/test_operational_docs.py` passed with 13 tests after final docs/code cleanup.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py tests/test_sv11_strategy_validation_batch.py tests/test_sv12_strategy_validation_regimes.py tests/test_sv13_research_campaigns.py tests/test_sv14_evidence_readiness.py tests/test_sv141_evidence_pack_integrity.py` passed with 31 tests after final docs/code cleanup.
  - `.venv/bin/python -m pytest -q tests/test_phase3_strategy.py tests/test_operational_docs.py` passed with 17 tests after final docs/code cleanup.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-sv1.4.1-review.zip` created the SV1.4.1 review bundle; bundle inspection found no `.env`, virtualenvs, Git metadata, pytest caches, local DB/SQLite files, nested archives, Obsidian app state, or generated `reports/strategy_validation/` evidence packs.

## v2026.05.02.001

- `recorded_at_utc`: `2026-05-02T05:32:35Z`
- `scope`: `SV1.4 Money Flow evidence-pack review discipline and data-readiness baseline`
- `intent`: `Native entry. Added the first evidence-pack review and historical data-readiness baseline on top of SV1.3 research campaigns without changing Money Flow rules. SV1.4 adds canonical editable campaign configs under `configs/strategy_validation/campaigns/`, a read-only campaign data-readiness audit that counts persisted candle closes by symbol/component/window under the accepted `(start_at, end_at]` convention, an `--audit-only` campaign CLI mode, evidence-pack manifest/Markdown review checklist output, and manual paper-trading readiness criteria. The audit reports expected candles, actual candles, missing candles, coverage percent, gap counts, largest gap, warning reason codes, and likely blocked windows/runs so founder/operator review can identify thin or missing data before interpreting campaign evidence. Operational-doc tests now assert the current phase line rather than stale historical text. This is research governance only: no Money Flow rule changes, parameter optimization, strategy recommendations, paper/live trading, live artifacts, routing, execution automation, exchange calls, route executor behavior, fanout, target reselection, or auto-submit were added.`
- `affected_files`:
  - `configs/strategy_validation/campaigns/money_flow_core_btc.json`
  - `configs/strategy_validation/campaigns/money_flow_core_multi_symbol.json`
  - `services/strategy_validation/__init__.py`
  - `services/strategy_validation/campaigns.py`
  - `scripts/run_money_flow_research_campaign.py`
  - `tests/test_sv14_evidence_readiness.py`
  - `tests/test_operational_docs.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/00 Maps/Current State Dashboard.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_sv14_evidence_readiness.py` passed with 4 tests during focused development.
  - `.venv/bin/python -m pytest -q tests/test_sv13_research_campaigns.py tests/test_sv14_evidence_readiness.py` passed with 10 tests during focused regression.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py tests/test_sv11_strategy_validation_batch.py tests/test_sv12_strategy_validation_regimes.py tests/test_sv13_research_campaigns.py tests/test_sv14_evidence_readiness.py` passed with 28 tests during Strategy Validation regression.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed with 10 tests during docs workflow validation.
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase3_strategy.py tests/test_operational_docs.py` passed with 17 tests.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed with 496 tests.
  - `git diff --check` passed.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed with 10 tests after final docs/Obsidian updates.
  - `.venv/bin/python -m pytest -q tests/test_sv14_evidence_readiness.py` passed with 4 tests after final docs/Obsidian updates.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-sv1.4-review.zip` created the SV1.4 review bundle; bundle inspection found 224 files, included the canonical campaign configs and SV1.4 tests, and found no `.env`, virtualenvs, Git metadata, pytest caches, local DB/SQLite files, nested archives, Obsidian app state, or generated `reports/strategy_validation/` evidence packs.

## v2026.05.01.017

- `recorded_at_utc`: `2026-05-01T21:08:26Z`
- `scope`: `SV1.3 Money Flow research campaigns and evidence packs`
- `intent`: `Native entry. Added repeatable Money Flow research campaign workflows on top of the existing Strategy Validation batch runner without changing Money Flow rules. SV1.3 fixes the remaining single-run CLI wording mismatch so `scripts/run_money_flow_backtest.py --start` no longer says inclusive and instead describes the accepted `(start_at, end_at]` candle-close convention. The new campaign config/runner layer parses explicit JSON campaign configs with symbols/instruments, components, fill timings, named windows, fee/slippage assumptions, capital, sizing, output directory, and report formats; expands them into existing `StrategyValidationBatchRequest` runs; writes timestamped evidence packs with normalized config, manifest, JSON report, Markdown report, and README; preserves blocked-run counts/reasons; records window convention and assumptions hash; and keeps generated packs out of Git/review bundles by default. This is research workflow only: no Money Flow rule changes, optimization, strategy recommendation, paper/live trading, live artifacts, routing, execution automation, exchange calls, route executor behavior, fanout, target reselection, or auto-submit were added.`
- `affected_files`:
  - `.archiveignore`
  - `.gitignore`
  - `configs/strategy_validation/money_flow_research_campaign.example.json`
  - `services/strategy_validation/__init__.py`
  - `services/strategy_validation/campaigns.py`
  - `services/strategy_validation/service.py`
  - `scripts/run_money_flow_backtest.py`
  - `scripts/run_money_flow_research_campaign.py`
  - `tests/test_sv13_research_campaigns.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests scripts` passed during development.
  - `.venv/bin/python -m pytest -q tests/test_sv13_research_campaigns.py` passed with 6 tests during focused development.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py` passed with 7 tests during regression development.
  - `.venv/bin/python -m pytest -q tests/test_sv11_strategy_validation_batch.py` passed with 4 tests during regression development.
  - `.venv/bin/python -m pytest -q tests/test_sv12_strategy_validation_regimes.py` passed with 7 tests during regression development.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py tests/test_sv11_strategy_validation_batch.py tests/test_sv12_strategy_validation_regimes.py tests/test_sv13_research_campaigns.py` passed with 24 tests.
  - `.venv/bin/python -m pytest -q tests/test_phase3_strategy.py tests/test_operational_docs.py` passed with 17 tests.
  - `git diff --check` passed.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed with 492 tests.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-sv1.3-review.zip` created the SV1.3 review bundle; bundle inspection found 221 files, included the campaign script and sample config, and found no `.env`, virtualenvs, Git metadata, pytest caches, local DB/SQLite files, nested archives, secrets, Obsidian app state, or generated `reports/strategy_validation/` evidence packs.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed with 10 tests after final docs/Obsidian updates.
  - `.venv/bin/python -m pytest -q tests/test_sv13_research_campaigns.py` passed with 6 tests after final docs/Obsidian updates.

## v2026.05.01.016

- `recorded_at_utc`: `2026-05-01T20:17:05Z`
- `scope`: `SV1.2.1 Money Flow validation window and coverage research-truth hotfix`
- `intent`: `Native entry. Hardened the SV1.2 market-regime/data-coverage validation layer before SV1.3 campaign/evidence-pack work. Strategy Validation now applies one candle-close window convention everywhere: `(start_at, end_at]`, meaning candle closes exactly at the start boundary are excluded and closes on or before the end boundary are included. Strategy evaluation, data coverage, regime summaries, forced-close lookup, batch date-window comparison, CLI wording, JSON, and Markdown now share that convention. Coverage expected counts are derived from expected close slots, unaligned window boundaries produce explicit warnings, coverage percent is capped at 100%, and grouped batch comparisons include blocked-run counts and blocked reason counts while computing performance metrics only from completed runs. No Money Flow rules, optimization, strategy recommendations, paper/live trading, live artifacts, routing, execution automation, exchange calls, route executor behavior, fanout, target reselection, or auto-submit were added.`
- `affected_files`:
  - `core/domain/models.py`
  - `services/strategy_validation/service.py`
  - `scripts/run_money_flow_validation_batch.py`
  - `tests/test_sv12_strategy_validation_regimes.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services scripts tests` passed during development.
  - `.venv/bin/python -m pytest -q tests/test_sv12_strategy_validation_regimes.py` passed with 7 tests during focused development.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py` passed with 7 tests.
  - `.venv/bin/python -m pytest -q tests/test_sv11_strategy_validation_batch.py` passed with 4 tests.
  - `.venv/bin/python -m pytest -q tests/test_phase3_strategy.py tests/test_operational_docs.py` passed with 17 tests.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py tests/test_sv11_strategy_validation_batch.py tests/test_sv12_strategy_validation_regimes.py` passed with 18 tests.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py tests/test_sv11_strategy_validation_batch.py tests/test_sv12_strategy_validation_regimes.py tests/test_phase3_strategy.py tests/test_operational_docs.py` passed with 35 tests.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed with 486 tests.
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed with 10 tests after final docs/Obsidian updates.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-sv1.2.1-review.zip` created the SV1.2.1 review bundle; bundle inspection found 217 files and no `.env`, virtualenvs, Git metadata, pytest caches, local DB/SQLite files, nested archives, secrets, or Obsidian app state.

## v2026.05.01.015

- `recorded_at_utc`: `2026-05-01T19:20:34Z`
- `scope`: `SV1.2 Money Flow data-coverage and market-regime validation`
- `intent`: `Native entry. Added data-coverage and deterministic market-regime analysis to Money Flow strategy validation without changing Money Flow rules. Single-run reports now include requested-versus-available candle coverage, expected/actual/missing candle counts where timeframe spacing is derivable, gap and thin-coverage warning reason codes, deterministic trend/volatility methodology, trade-level entry-signal regime fields, and regime-grouped performance summaries. Batch reports now include data-coverage and market-regime comparison sections, and the comparative CLI accepts repeated `--window start,end` inputs for explicit multi-window research. Regime labels are descriptive only and are not used to alter entries, exits, parameters, paper/live trading, routing, execution automation, exchange calls, or live artifacts.`
- `affected_files`:
  - `core/domain/models.py`
  - `services/strategy_validation/service.py`
  - `scripts/run_money_flow_validation_batch.py`
  - `tests/test_sv12_strategy_validation_regimes.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services scripts tests` passed during development.
  - `.venv/bin/python -m pytest -q tests/test_sv12_strategy_validation_regimes.py` passed with 4 tests during focused development.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py tests/test_sv11_strategy_validation_batch.py tests/test_sv12_strategy_validation_regimes.py` passed with 15 tests during focused development.
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py` passed with 7 tests.
  - `.venv/bin/python -m pytest -q tests/test_sv11_strategy_validation_batch.py` passed with 4 tests.
  - `.venv/bin/python -m pytest -q tests/test_sv12_strategy_validation_regimes.py` passed with 4 tests.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py tests/test_sv11_strategy_validation_batch.py tests/test_phase3_strategy.py tests/test_operational_docs.py` passed with 28 tests.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py tests/test_sv11_strategy_validation_batch.py tests/test_sv12_strategy_validation_regimes.py tests/test_phase3_strategy.py tests/test_operational_docs.py` passed with 32 tests.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed with 483 tests.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed with 10 tests after final docs updates.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-sv1.2-review.zip` created the SV1.2 review bundle; bundle inspection found 217 files and no `.env`, virtualenvs, Git metadata, pytest caches, local DB/SQLite files, nested archives, secrets, or Obsidian app state.

## v2026.05.01.014

- `recorded_at_utc`: `2026-05-01T18:41:11Z`
- `scope`: `SV1.1 comparative Money Flow strategy validation`
- `intent`: `Native entry. Added comparative Money Flow strategy-validation batch reporting without changing Money Flow strategy rules. The new batch request/report models and service method run explicit sets of existing single-run validation requests across components/timeframes, fill-timing assumptions, symbols, date windows, fees, and slippage assumptions, then emit deterministic JSON/Markdown comparison output. Reports include an assumptions matrix, per-run metrics, fill-timing comparison, component comparison, optional symbol/date-window comparison, observed top/bottom runs, warnings, and limitations. The comparison is descriptive research only: it does not optimize parameters, recommend a strategy variant, create live desired trades, child intents, readiness evaluations, submitted orders, routing artifacts, approvals, exchange calls, paper trading, live execution, smart routing, best-binding selection, CBBO, ranking/scoring, fanout, target reselection, route executor behavior, or auto-submit.`
- `affected_files`:
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `services/strategy_validation/__init__.py`
  - `services/strategy_validation/service.py`
  - `scripts/run_money_flow_validation_batch.py`
  - `tests/test_sv11_strategy_validation_batch.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py tests/test_sv11_strategy_validation_batch.py` passed with 11 tests during focused development.
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py` passed with 7 tests.
  - `.venv/bin/python -m pytest -q tests/test_sv11_strategy_validation_batch.py` passed with 4 tests.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py tests/test_phase3_strategy.py tests/test_operational_docs.py` passed with 24 tests.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py tests/test_sv11_strategy_validation_batch.py tests/test_phase3_strategy.py tests/test_operational_docs.py` passed with 28 tests.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed with 479 tests.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed with 10 tests after final docs updates.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-sv1.1-review.zip` created the SV1.1 review bundle; bundle inspection found 216 files and no `.env`, virtualenvs, Git metadata, pytest caches, local DB/SQLite files, nested archives, secrets, or Obsidian app state.

## v2026.05.01.013

- `recorded_at_utc`: `2026-05-01T18:23:34Z`
- `scope`: `Investor-facing plain-language overview merged into SV baseline`
- `intent`: `Native merge entry. Brought the pre-SV investor overview branch into the SV baseline before SV1.1 work. The new `docs/investors.md` page explains Money Flow in plain language for non-trading-systems readers, including what exists today, what is intentionally not yet implemented, and where the product can go next. README and Obsidian business/product notes link to the page, and operational-doc tests keep it discoverable. This is documentation only: no product behavior, trading automation, routing logic, migration, config, exchange behavior, smart routing, best-binding selection, CBBO, ranking/scoring, fanout, target reselection, route executor, auto-submit, cross-binding recovery, cross-venue retry, strategy-rule change, or validation behavior change was added.`
- `affected_files`:
  - `docs/investors.md`
  - `README.md`
  - `REPO_TREE.md`
  - `tests/test_operational_docs.py`
  - `money-flow/Money Flow Command Center.md`
  - `money-flow/30 Strategy/Product North Star.md`
  - `money-flow/30 Strategy/Business and Product Track.md`
  - `money-flow/05_Agent_Coordination.md`
  - `CHANGELOG.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed on the original investor overview branch.

## v2026.05.01.012

- `recorded_at_utc`: `2026-05-01T18:12:47Z`
- `scope`: `SV1.0.1 strategy-validation research-truth and report hardening`
- `intent`: `Native entry. Hardened the SV1.0 Money Flow validation report so founder/operator research review sees the simulation assumptions and limitations clearly. Reports now include explicit fill timing with `same_candle_close_research_only`, `next_candle_open`, and `next_candle_close`; same-candle close remains available but is labeled research-only and potentially optimistic. Metrics now expose closed-trade drawdown separately from mark-to-market drawdown, with mark-to-market drawdown derived from intrabar adverse open-position movement for long simulated trades. Markdown output now includes report context, assumptions, aggregate metrics, component comparison, component metrics, trade summary, no-trade/invalid reason counts, and prominent limitations. JSON output is extended deterministically with fill timing, drawdown methodology, closed-trade drawdown, mark-to-market drawdown, component comparison, and trade fill metadata. This phase changes validation/reporting truth only: Money Flow strategy rules were not optimized or changed, no live artifacts are created, no routing/execution automation is added, no exchange adapters are called, and simulated trades remain separate from `SubmittedOrder`.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `services/strategy_validation/service.py`
  - `scripts/run_money_flow_backtest.py`
  - `tests/test_sv10_strategy_validation.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py` passed with 7 tests during focused development.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py tests/test_phase3_strategy.py tests/test_operational_docs.py` passed with 23 tests.
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed with 474 tests.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed with 9 tests after final docs updates.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-sv1.0.1-review.zip` created the SV1.0.1 review bundle; bundle inspection found no `.env`, virtualenvs, Git metadata, pytest caches, local DB/SQLite files, nested archives, secrets, or Obsidian app state.

## v2026.05.01.011

- `recorded_at_utc`: `2026-05-01T17:40:40Z`
- `scope`: `SV1.0 Money Flow strategy validation framework`
- `intent`: `Native entry. Added the first Strategy Validation framework for Money Flow. The new service boundary reads persisted historical candles, computes indicator snapshots in memory, reuses the current Money Flow strategy rules without optimization, simulates research-only trades with explicit initial-capital, fee, slippage, and sizing assumptions, and returns deterministic component/aggregate performance reports. The report includes simulated trades, win/loss rates, average win/loss, profit factor, net/gross PnL, fees, slippage cost, max drawdown, average duration, best/worst trade, return on initial capital, component/timeframe grouping, and no-trade/invalid reason counts. A CLI can emit JSON or Markdown reports. Validation artifacts are separate from live execution artifacts: SV1.0 creates no desired trades, child intents, prepared orders, readiness assessments, submitted orders, routing artifacts, approval changes, exchange calls, new automation behavior, smart routing, fanout, ranking/scoring, CBBO, target reselection, route executor behavior, new exchanges, or strategy-rule optimization.`
- `affected_files`:
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `services/strategy_validation/__init__.py`
  - `services/strategy_validation/service.py`
  - `services/backtest/engine.py`
  - `scripts/run_money_flow_backtest.py`
  - `tests/test_sv10_strategy_validation.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py` passed with 4 tests during focused development.
  - `.venv/bin/python -m compileall core services apps tests scripts` passed during focused development.
  - `.venv/bin/python -m pytest -q tests/test_sv10_strategy_validation.py tests/test_phase3_strategy.py tests/test_operational_docs.py` passed with 20 tests.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed with 471 tests.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed with 9 tests after final docs updates.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-sv1.0-review.zip` created the SV1.0 review bundle; bundle inspection found no `.env`, virtualenvs, Git metadata, pytest caches, local DB/SQLite files, nested archives, secrets, or Obsidian app state.

## v2026.05.01.010

- `recorded_at_utc`: `2026-05-01T15:04:52Z`
- `scope`: `Phase 8.0.2 active submit-lease operator-summary truth hotfix`
- `intent`: `Native entry. Fixed the read-only operator routed workflow summary so an active, unexpired child-intent submit lease is treated as an in-progress submission blocker. The summary now reports `submission_in_progress`, sets submitted-order handoff safety to `repeat_submit_blocked=true` with `repeat_submit_policy=blocked_while_submission_in_progress`, and reports `next_safe_operator_action.action=submission_in_progress` with `safe_to_automate=false`. Terminal uncertainty states `adapter_submit_may_have_started` and `adapter_submit_persistence_unknown` remain manual-reconciliation-required repeat-submit blockers, while expired pre-adapter active leases remain stale-replaceable rather than terminal uncertainty. This phase changes read-only truth surfaces only; it adds no trading behavior, no new automation action stage, no manual-resolution mutation, no migration/config, no smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor behavior, cross-binding/cross-venue retry, submit/cancel/amend/retry from inspection, or new exchange behavior.`
- `affected_files`:
  - `services/routing/service.py`
  - `tests/test_phase80_operator_observability.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_phase80_operator_observability.py` passed with 5 tests during focused development.
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase80_operator_observability.py` passed with 5 tests after final source/docs updates.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed with 9 tests.
  - `.venv/bin/python -m pytest -q tests/test_phase75_approval_gated_submission_handoff.py tests/test_phase76_automation_closeout.py tests/test_phase80_operator_observability.py` passed with 34 tests.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-8.0.2-review.zip` created the Phase 8.0.2 review bundle; bundle inspection found no `.env`, virtualenvs, Git metadata, pytest caches, local DB/SQLite files, nested archives, secrets, or Obsidian app state.

## v2026.05.01.009

- `recorded_at_utc`: `2026-05-01T14:19:39Z`
- `scope`: `Phase 8.0.1 Obsidian memory and working-tree cleanup`
- `intent`: `Native entry. Resolved the dirty Obsidian full-project-memory and working-tree state left after accepted Phase 8.0. The pre-existing Obsidian brain refresh for accepted Phase 7.6 / proposed Phase 8.0 was inspected, accepted as intentional strategic-memory baseline, and updated so canonical Obsidian notes describe Phase 8.0 as implemented and Phase 8.0.1 as workflow hygiene only. The repo-root `money_flow_project_memory.md` remains a pointer only; the full strategic memory remains at `money-flow/Project_Memory/money_flow_project_memory.md`. This phase adds no product behavior, service logic, routing/execution/API behavior, schema, migration, test behavior, exchange behavior, smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor behavior, cross-venue/cross-binding recovery, auto-submit, or manual-resolution mutation.`
- `affected_files`:
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
  - `money-flow/Project_Memory/money_flow_project_memory.md`
  - `money-flow/Money Flow Command Center.md`
  - `money-flow/00 Maps/Component Map.md`
  - `money-flow/00 Maps/Current State Dashboard.md`
  - `money-flow/00 Maps/System Map.md`
  - `money-flow/20 Workflows/Operator Observability and Manual Resolution.md`
  - `money-flow/40 Operations/Operational Memory.md`
  - `money-flow/40 Operations/Phase 8 Focus.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_phase80_operator_observability.py` passed with 4 tests.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-8.0.1-review.zip` created the Phase 8.0.1 review bundle; bundle inspection found no `.env`, virtualenvs, Git metadata, pytest caches, local DB files, SQLite files, nested archives, secrets, or Obsidian app state.

## v2026.05.01.008

- `recorded_at_utc`: `2026-05-01T13:20:57Z`
- `scope`: `Phase 8.0 operator observability and manual-resolution inspection`
- `intent`: `Native entry. Added the first operator-grade observability surface for the accepted controlled routed automation chain. The new read-only operator summary by desired trade aggregates existing routed workflow artifacts, approval states, approval gate truth, manual-resolution requirements, submitted-order handoff safety facts, and submit-lease/concurrency state without creating target choices, child intents, readiness evaluations, submitted orders, manual-resolution markers, exchange calls, or approval consumption. The summary surfaces `consumption_pending`, stale-lineage/expired approvals, blocked recommendations/readiness, `adapter_submit_may_have_started`, `adapter_submit_persistence_unknown`, repeat-submit safety policy, and the next safe operator action. This phase adds no smart routing, best-binding selection, ranking/scoring, CBBO, fanout, split allocation, target reselection, route executor behavior, cross-binding/cross-venue recovery, new automation action stage, broad auto-submit, migration, config, new exchange behavior, or full Obsidian project-memory edit.`
- `affected_files`:
  - `services/routing/service.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase80_operator_observability.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests scripts` passed during focused development.
  - `.venv/bin/python -m pytest -q tests/test_phase80_operator_observability.py` passed with 4 tests during focused development.
  - `.venv/bin/python -m pytest -q tests/test_phase80_operator_observability.py tests/test_phase76_automation_closeout.py tests/test_phase75_approval_gated_submission_handoff.py tests/test_phase69_routed_workflow_inspection.py tests/test_api.py tests/test_operational_docs.py` passed with 59 tests.
  - `.venv/bin/python -m pytest -q tests/test_phase70_routing_automation.py tests/test_phase71_routing_automation_approvals.py tests/test_phase72_approval_gated_recommendation_acceptance.py tests/test_phase73_approval_gated_target_choice_conversion.py tests/test_phase74_approval_gated_preview_readiness.py tests/test_phase75_approval_gated_submission_handoff.py tests/test_phase76_automation_closeout.py tests/test_phase80_operator_observability.py` passed with 90 tests.
  - `.venv/bin/python -m pytest -q tests/test_phase67_recommendation_backed_submission.py tests/test_phase68_recommendation_backed_lifecycle.py tests/test_phase69_routed_workflow_inspection.py tests/test_phase610_phase6_closeout.py` passed with 20 tests.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed with 466 tests.
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py` passed with 1 test.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed with 9 tests after final docs updates.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-8.0-review.zip` created the Phase 8.0 review bundle; bundle inspection found no `.env`, virtualenvs, Git metadata, pytest caches, local DBs, SQLite files, nested archives, or Obsidian app state.

## v2026.05.01.007

- `recorded_at_utc`: `2026-05-01T12:02:56Z`
- `scope`: `Phase 7.6 controlled automation closeout safety diligence`
- `intent`: `Native entry. Closed out Phase 7 with safety-diligence regression and documentation alignment rather than adding production behavior. Added a full controlled automation closeout test that walks the accepted approval-gated same-target chain from existing recommendation through recommendation acceptance, target-choice conversion, preview/readiness, and submitted-order handoff. The test proves each stage consumes only the exact current-lineage approval, creates or reuses only its expected artifact, keeps dry-run / approval creation / generic administrative consumption / action-specific consumption / readiness / submitted-order handoff distinct, bounds `consumption_pending` so repeat calls reuse the existing submitted order without another adapter submit, and asserts no smart routing, best-binding selection, ranking/scoring, CBBO, fanout, split allocation, target reselection, route executor behavior, cross-binding/cross-venue recovery, or broad auto-submit. This phase adds no production behavior, migration, config, new action stage, new exchange behavior, route executor, or full Obsidian project-memory edit.`
- `affected_files`:
  - `tests/test_phase76_automation_closeout.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `money_flow_project_memory.md`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase76_automation_closeout.py` passed with 5 tests during focused development.
  - `.venv/bin/python -m pytest -q tests/test_phase70_routing_automation.py tests/test_phase71_routing_automation_approvals.py tests/test_phase72_approval_gated_recommendation_acceptance.py tests/test_phase73_approval_gated_target_choice_conversion.py tests/test_phase74_approval_gated_preview_readiness.py tests/test_phase75_approval_gated_submission_handoff.py tests/test_phase76_automation_closeout.py` passed with 86 tests.
  - `.venv/bin/python -m pytest -q tests/test_phase67_recommendation_backed_submission.py tests/test_phase68_recommendation_backed_lifecycle.py tests/test_phase69_routed_workflow_inspection.py tests/test_phase610_phase6_closeout.py` passed with 20 tests.
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py` passed with 22 tests.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed with 462 tests.
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py` passed with 1 test.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed with 9 tests after final docs updates.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-7.6-review.zip` created the Phase 7.6 review bundle; bundle inspection found no `.env`, virtualenvs, Git metadata, pytest caches, local DBs, SQLite files, nested archives, or Obsidian app state.

## v2026.05.01.006

- `recorded_at_utc`: `2026-05-01T09:40:47Z`
- `scope`: `Phase 7.5.1 submitted-order handoff approval-consumption truth hotpatch`
- `intent`: `Native entry. Hardened the Phase 7.5 approval-gated submitted-order handoff without adding execution scope. If the existing explicit submit path persists or safely reuses a `SubmittedOrder` but approval consumption fails afterward, the approval is now moved to `consumption_pending`, linked to the submitted order and child intent, and stamped with `submitted_order_handoff_consumption_failed`, `submitted_order_created_approval_consumption_pending`, `approval_consumption_failed_after_submitted_order`, and `manual_approval_reconciliation_required` reason/provenance truth. A repeat call with the same approval reuses the existing submitted order and attempts to complete approval consumption without calling adapter submit again. Existing adapter-in-flight / adapter-returned persistence uncertainty and submit lease behavior remain intact. This phase adds no new action hook, route executor, broad auto-submit, fanout, ranking/scoring, CBBO, target reselection, cross-binding/cross-venue recovery, new exchange behavior, migration, config, or full project-memory edit.`
- `affected_files`:
  - `core/domain/enums.py`
  - `services/routing/service.py`
  - `tests/test_phase75_approval_gated_submission_handoff.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase75_approval_gated_submission_handoff.py` passed with 24 tests.
  - `.venv/bin/python -m pytest -q tests/test_phase70_routing_automation.py tests/test_phase71_routing_automation_approvals.py tests/test_phase72_approval_gated_recommendation_acceptance.py tests/test_phase73_approval_gated_target_choice_conversion.py tests/test_phase74_approval_gated_preview_readiness.py tests/test_phase75_approval_gated_submission_handoff.py` passed with 81 tests.
  - `.venv/bin/python -m pytest -q tests/test_phase67_recommendation_backed_submission.py tests/test_phase68_recommendation_backed_lifecycle.py tests/test_phase69_routed_workflow_inspection.py tests/test_phase610_phase6_closeout.py` passed with 20 tests.
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py` passed with 22 tests.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed with 457 tests.
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py` passed with 1 test.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed with 9 tests after final docs updates.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-7.5.1-review.zip` created the Phase 7.5.1 review bundle; bundle inspection found no `.env`, virtualenvs, Git metadata, pytest caches, local DBs, SQLite files, or nested archives.

## v2026.05.01.005

- `recorded_at_utc`: `2026-05-01T08:41:37Z`
- `scope`: `Phase 7.5 approval-gated submitted-order handoff`
- `intent`: `Native entry. Added the fourth narrow approval-consuming automation action hook. One active, non-expired, current-lineage `submitted_order_handoff` approval can now be consumed to call the existing explicit child-intent submit path for the exact approved routed child `OrderIntent`, and only when current readiness, live-submit and routed-submit gates, adapter/account authorization, routed lineage/order-shape truth, and submit lease/uncertainty guards still pass. Approval is consumed only after `SubmittedOrder` persistence or safe reuse; blocked readiness/gates leave approval unconsumed with reason-coded provenance, and adapter-submit uncertainty remains manual-reconciliation-required through existing lease truth. Added `POST /api/v1/routing-automation/approvals/{approval_id}/submit` plus focused Phase 7.5 tests for success, idempotency, blocked readiness, submit-gate blocks, invalid approvals, policy/status boundaries, submit lease concurrency, uncertainty preservation, API response shape, and no SOR leakage. This phase creates no extra child intent, selects no target, reselects no target, fans out nowhere, retries nowhere, and adds no smart routing, best-binding selection, ranking/scoring, CBBO, route executor behavior, cross-binding/cross-venue recovery, broad auto-submit, migration, config, new exchange behavior, or full project-memory edit.`
- `affected_files`:
  - `services/routing/service.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase70_routing_automation.py`
  - `tests/test_phase71_routing_automation_approvals.py`
  - `tests/test_phase75_approval_gated_submission_handoff.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall services/routing/service.py tests/test_phase75_approval_gated_submission_handoff.py` passed during focused development.
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase75_approval_gated_submission_handoff.py` passed with 22 tests.
  - `.venv/bin/python -m pytest -q tests/test_phase70_routing_automation.py tests/test_phase71_routing_automation_approvals.py tests/test_phase72_approval_gated_recommendation_acceptance.py tests/test_phase73_approval_gated_target_choice_conversion.py tests/test_phase74_approval_gated_preview_readiness.py tests/test_phase75_approval_gated_submission_handoff.py` passed with 79 tests.
  - `.venv/bin/python -m pytest -q tests/test_phase67_recommendation_backed_submission.py tests/test_phase68_recommendation_backed_lifecycle.py tests/test_phase69_routed_workflow_inspection.py tests/test_phase610_phase6_closeout.py` passed with 20 tests.
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py` passed with 22 tests.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed with 455 tests.
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py` passed with 1 test.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-7.5-review.zip` created the Phase 7.5 review bundle; bundle inspection found no `.env`, virtualenvs, Git metadata, pytest caches, local DBs, SQLite files, or nested archives.

## v2026.05.01.004

- `recorded_at_utc`: `2026-05-01T07:28:41Z`
- `scope`: `Phase 7.4 approval-gated prepared-order preview/readiness`
- `intent`: `Native entry. Added the third narrow approval-consuming automation action hook. One active, non-expired, current-lineage `prepared_order_preview_and_readiness` approval can now be consumed to run the existing child-intent prepared-order preview and execution-readiness inspection path for the exact approved routed child `OrderIntent`; the action persists or reuses the readiness assessment, records the preview key, readiness id/outcome/reason codes, and consumes the approval with explicit no-submitted-order/no-exchange-submit/no-auto-submit/no-route-executor provenance. Approval authorizes inspection only and does not force readiness eligibility: blocked and phase-blocked readiness remain reason-coded. Expired, revoked, consumed-for-different-child, wrong-action, wrong-child-intent, stale-lineage, disabled, blocked, deferred, already-satisfied, dry-run-only, and manual-only cases block before action. Added `POST /api/v1/routing-automation/approvals/{approval_id}/preview-readiness` plus focused Phase 7.4 tests for success, idempotency, rollback on approval-consumption failure, invalid approvals, policy/status boundaries, readiness truth, API response shape, and no submission. This phase creates no `SubmittedOrder`, calls no adapter submit/exchange submit path, and adds no smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor, cross-binding/cross-venue recovery, auto-submit, migration, config, new exchange behavior, or full project-memory edit.`
- `affected_files`:
  - `services/routing/service.py`
  - `services/execution/service.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase74_approval_gated_preview_readiness.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase74_approval_gated_preview_readiness.py` passed with 16 tests.
  - `.venv/bin/python -m pytest -q tests/test_phase70_routing_automation.py tests/test_phase71_routing_automation_approvals.py tests/test_phase72_approval_gated_recommendation_acceptance.py tests/test_phase73_approval_gated_target_choice_conversion.py tests/test_phase74_approval_gated_preview_readiness.py` passed with 57 tests.
  - `.venv/bin/python -m pytest -q tests/test_phase64_recommendation_backed_readiness.py tests/test_operational_docs.py` passed with 18 tests.
  - `.venv/bin/python -m pytest -q tests/test_phase63_recommendation_target_choice_conversion.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py` passed with 56 tests.
  - `.venv/bin/python -m pytest -q tests/test_api.py` passed with 13 tests.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed with 433 tests.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed after final docs and Obsidian coordination updates.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-7.4-review.zip` created the Phase 7.4 review bundle; bundle inspection found 204 files and no `.env`, virtualenvs, Git metadata, pytest caches, Obsidian app state, local DBs, SQLite files, or nested ZIPs.

## v2026.05.01.003

- `recorded_at_utc`: `2026-05-01T06:45:26Z`
- `scope`: `Phase 7.3.1 approval-gated target-choice conversion test hardening`
- `intent`: `Native entry. Hardened the focused Phase 7.3 approval-gated target-choice conversion tests before Phase 7.4. Added direct negative coverage proving disabled, blocked, deferred, and already-satisfied current target-choice-conversion step states reject approval-gated conversion before new child-intent or downstream artifacts. Added direct wrong-lineage coverage for mismatched routing target recommendation id, route-readiness audit id, and desired-trade key, verifying stale-lineage truth and unconsumed approval state. No production service behavior changed: Phase 7.3.1 adds no prepared-order preview/readiness automation, submitted-order automation, exchange call, smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor, auto-submit, cross-binding/cross-venue recovery, migration, or config.`
- `affected_files`:
  - `tests/test_phase73_approval_gated_target_choice_conversion.py`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase73_approval_gated_target_choice_conversion.py` passed with 14 tests.
  - `.venv/bin/python -m pytest -q tests/test_phase70_routing_automation.py tests/test_phase71_routing_automation_approvals.py tests/test_phase72_approval_gated_recommendation_acceptance.py tests/test_phase73_approval_gated_target_choice_conversion.py` passed with 41 tests.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase63_recommendation_target_choice_conversion.py tests/test_phase56_routed_order_shape_policy.py` passed with 34 tests.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed with 417 tests.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-7.3.1-review.zip` created the Phase 7.3.1 review bundle; bundle inspection found no `.env`, virtualenvs, Git metadata, pytest caches, Obsidian app state, local DBs, SQLite files, or nested ZIPs.
## v2026.05.01.002

- `recorded_at_utc`: `2026-05-01T05:58:03Z`
- `scope`: `Phase 7.3 approval-gated target-choice conversion and Obsidian brain workflow`
- `intent`: `Native entry. Added the second narrow approval-consuming automation action hook and integrated the Obsidian strategic-memory workflow. One active, non-expired, current-lineage `target_choice_conversion` approval can now be consumed to convert the exact approved `RoutingTargetChoice` into a created or reused child `OrderIntent` through existing conversion validation/persistence helpers, then record approval consumption with actor, child-intent id, routed order-shape policy, and explicit no-prepared-order/no-readiness/no-submission provenance in one coherent session/commit. Expired, revoked, stale-lineage, wrong-action, wrong-target-choice, consumed-for-different-target-choice, dry-run-only, and manual-only cases block before child-intent creation. Added the API route `POST /api/v1/routing-automation/approvals/{approval_id}/convert-target-choice` plus focused tests for success, idempotency, rollback on approval-consumption failure, invalid approvals, policy boundaries, API response shape, and no downstream artifacts. Moved full strategic project memory into the tracked Obsidian vault at `money-flow/Project_Memory/money_flow_project_memory.md`, made the repo-root `money_flow_project_memory.md` a pointer, added required Obsidian command/current-phase/decision/coordination notes, and updated agent rules/tests so future agents read and update Obsidian without replacing repo operational docs. This phase creates/reuses only `OrderIntent`; it adds no prepared order, readiness assessment, submitted order, exchange call, smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor, auto-submit, cross-binding/cross-venue recovery, migration, or config.`
- `affected_files`:
  - `.archiveignore`
  - `.gitignore`
  - `AGENTS.md`
  - `money_flow_project_memory.md`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
  - `money-flow/Project_Memory/money_flow_project_memory.md`
  - `money-flow/40 Operations/Future Work Roadmap.md`
  - `money-flow/40 Operations/Operational Memory.md`
  - `money-flow/40 Operations/Phase 7 Focus.md`
  - `money-flow/Money Flow Command Center.md`
  - `services/routing/service.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase73_approval_gated_target_choice_conversion.py`
  - `tests/test_operational_docs.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_phase73_approval_gated_target_choice_conversion.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed.
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase72_approval_gated_recommendation_acceptance.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase70_routing_automation.py tests/test_phase71_routing_automation_approvals.py tests/test_phase72_approval_gated_recommendation_acceptance.py tests/test_phase73_approval_gated_target_choice_conversion.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase63_recommendation_target_choice_conversion.py tests/test_phase69_routed_workflow_inspection.py tests/test_api.py tests/test_operational_docs.py` passed.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed after final docs and Obsidian updates.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-7.3-review.zip` created a clean review bundle; bundle inspection found 203 files and no `.env`, virtualenvs, Git metadata, pytest caches, Obsidian app state, local DBs, SQLite files, or nested ZIPs.

## v2026.05.01.001

- `recorded_at_utc`: `2026-05-01T05:12:07Z`
- `scope`: `Phase 7.2.1 approval-gated recommendation acceptance atomicity hotpatch`
- `intent`: `Native entry. Hardened the Phase 7.2 approval-gated recommendation acceptance action so approval validation, target-choice creation or reuse, recommendation/audit target-choice marking, approval consumption, and approval provenance update occur in one coherent session/commit. The existing Phase 6.2 recommendation acceptance logic now has an internal in-session path used by both the normal operator action and the approval-gated action; approval-gated execution no longer commits a target choice before consuming the approval. If approval consumption fails after a target choice is flushed but before commit, the transaction rolls back and leaves no persisted target choice, no misleading active approval with target-choice side effects, and no recommendation target-choice-created truth. Repeated calls with the same consumed approval and recommendation still return the original target choice without changing consumed_at. The generic approval consume endpoint is documented as an administrative approval-state transition only and still does not execute the approved action. This phase creates/reuses only `RoutingTargetChoice`; it adds no child intent, prepared order, readiness assessment, submitted order, exchange call, smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor, auto-submit, cross-binding/cross-venue recovery, migration, config, or money_flow_project_memory.md update.`
- `affected_files`:
  - `services/routing/service.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase72_approval_gated_recommendation_acceptance.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall services/routing/service.py apps/api/app/api/routes.py tests/test_phase72_approval_gated_recommendation_acceptance.py` passed.
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase72_approval_gated_recommendation_acceptance.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase70_routing_automation.py tests/test_phase71_routing_automation_approvals.py tests/test_phase72_approval_gated_recommendation_acceptance.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase62_recommendation_acceptance.py tests/test_phase63_recommendation_target_choice_conversion.py tests/test_phase69_routed_workflow_inspection.py tests/test_api.py tests/test_operational_docs.py` passed.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed after final docs update.

## v2026.04.30.003

- `recorded_at_utc`: `2026-04-30T19:30:37Z`
- `scope`: `Phase 7.2 approval-gated recommendation acceptance action hook`
- `intent`: `Native entry. Added the first narrow approval-consuming automation action hook: one active, non-expired, current-lineage `recommendation_acceptance` approval can now be consumed to accept the exact approved `RoutingTargetRecommendation` into a created or reused `RoutingTargetChoice` through the existing Phase 6.2 acceptance path. The hook validates action name, approval status, expiry, revocation, consumption, recommendation id, desired-trade/audit/assessment/selected binding/account/venue/symbol lineage, and current automation step policy before acceptance; invalid, stale-lineage, revoked, expired, wrong-action, wrong-recommendation, dry-run-only, and manual-only cases block before target-choice creation. Successful consumption records the approval consumer, target choice id, target-choice-created-or-reused truth, and explicit no-child-intent/no-readiness/no-submission provenance. Added API response surfaces for `POST /api/v1/routing-automation/approvals/{approval_id}/accept-recommendation` and tests for successful consumption, idempotent repeat, invalid approvals, dry-run/manual policy blocks, and API behavior. This phase creates/reuses only `RoutingTargetChoice`; it adds no child intent, prepared order, readiness assessment, submitted order, exchange call, smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor, auto-submit, cross-binding/cross-venue recovery, migration, config, or money_flow_project_memory.md update.`
- `affected_files`:
  - `services/routing/service.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase72_approval_gated_recommendation_acceptance.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall services/routing/service.py core/domain/models.py core/interfaces/services.py core/schemas/api.py apps/api/app/api/routes.py tests/test_phase72_approval_gated_recommendation_acceptance.py` passed.
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase72_approval_gated_recommendation_acceptance.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase70_routing_automation.py tests/test_phase71_routing_automation_approvals.py tests/test_phase72_approval_gated_recommendation_acceptance.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase62_recommendation_acceptance.py tests/test_phase63_recommendation_target_choice_conversion.py tests/test_phase69_routed_workflow_inspection.py tests/test_api.py tests/test_operational_docs.py` passed.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed.

## v2026.04.30.002

- `recorded_at_utc`: `2026-04-30T18:43:44Z`
- `scope`: `Phase 7.1.2 routing automation approval approvable-step truth hotfix`
- `intent`: `Native entry. Finished the approval-truth substrate before action hooks exist. Approval creation now rejects current steps classified as `dry_run_only`, `manual_only`, `disabled`, `deferred`, `blocked`, or `already_satisfied`; only `approval_required` and explicitly `automation_eligible` steps can create active approvals. Automation approval gate-state inspection now keeps current policy truth ahead of stored approval metadata, so a current manual-only or dry-run-only step is reported as `manual_only` or `dry_run_only` rather than plain `approved` even if an old active approval row exists. Strengthened Phase 7.1 approval tests for dry-run-only rejection, manual-only rejection under custom policy input, gate-state truth under dry-run/manual current policies, and legacy approval metadata that must not make submitted-order handoff appear approved. Also hardened source/review hygiene so Git metadata and an accidentally nested local `money-flow/` note/vault artifact are excluded from review bundles, and the nested local artifact is ignored by Git. This is approval truth only: no recommendation acceptance execution, target-choice conversion execution, preview/readiness execution, submitted-order execution, exchange call, route executor behavior, smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, cross-binding/cross-venue recovery, auto-submit, new exchange behavior, migration, config, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `.archiveignore`
  - `.gitignore`
  - `services/routing/service.py`
  - `tests/test_phase71_routing_automation_approvals.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall services/routing/service.py tests/test_phase71_routing_automation_approvals.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase71_routing_automation_approvals.py` passed.
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase70_routing_automation.py tests/test_phase71_routing_automation_approvals.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase69_routed_workflow_inspection.py tests/test_phase67_recommendation_backed_submission.py tests/test_api.py tests/test_operational_docs.py` passed.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed after final docs update.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed after `.gitignore` / `.archiveignore` hygiene update.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-7.1.2-review.zip` created a clean review bundle; bundle inspection found 162 files and no Git metadata, `.env` other than `.env.example`, virtualenvs, caches, local DBs, SQLite files, logs, nested archives, or nested `money-flow/` local-note artifacts.

## v2026.04.30.001

- `recorded_at_utc`: `2026-04-30T05:40:33Z`
- `scope`: `Phase 7.1.1 routing automation approval truth hotfix`
- `intent`: `Native entry. Hardened the Phase 7.1 approval substrate before any action-taking automation exists. Approval creation and approval-gate inspection now expire active records before reuse, compute deterministic lineage fingerprints / approval scope keys from the current desired-trade/action/recommendation/audit/target-choice/child-intent/readiness/submitted-order and selected binding/account/venue/symbol facts, mark old active approvals as `stale_lineage` when their stored scope no longer matches current workflow truth, and return/create approvals only for the current lineage. Added a narrow `routing_automation_approvals` active-scope uniqueness guard so repeated or concurrent creation cannot create multiple active approvals for one desired trade, action, and current lineage scope. Approval remains separate from execution: no recommendation acceptance, target-choice conversion, preview/readiness creation, submitted-order handoff, exchange call, route executor behavior, smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, cross-binding/cross-venue recovery, auto-submit, new exchange behavior, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/schemas/api.py`
  - `db/models/trading.py`
  - `db/migrations/versions/20260430_0025_phase711_approval_truth_scope.py`
  - `services/routing/service.py`
  - `tests/test_phase71_routing_automation_approvals.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall services/routing/service.py core/domain/models.py core/schemas/api.py db/models/trading.py tests/test_phase71_routing_automation_approvals.py` passed.
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase71_routing_automation_approvals.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase70_routing_automation.py tests/test_phase71_routing_automation_approvals.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase69_routed_workflow_inspection.py tests/test_phase67_recommendation_backed_submission.py tests/test_api.py tests/test_operational_docs.py` passed.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed.
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed after docs update.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-7.1.1-review.zip` created a clean review bundle; bundle inspection found 642 files and no `.env` other than `.env.example`, virtualenvs, caches, local DBs, SQLite files, logs, or nested archives.

## v2026.04.26.004

- `recorded_at_utc`: `2026-04-26T19:32:44Z`
- `scope`: `Phase 7.1 routing automation approval and reversible gating substrate`
- `intent`: `Native entry. Added durable operator approval records and reversible action gating above the Phase 7.0 dry-run automation substrate without executing actions. Introduced approval action/status enums, typed approval/gate domain models, API schemas, a narrow `routing_automation_approvals` table, and service/API methods to create, inspect, revoke, and consume one approval for one same-target action stage. Approval records preserve policy snapshots, desired-trade/recommendation/target-choice/child-intent/readiness/submitted-order lineage where present, selected binding/account/venue/symbol facts, and no-fanout/no-CBBO/no-ranking/no-scoring/no-target-reselection/no-route-executor/no-auto-submit boundary truth. Dry-run plans now include approval gate state snapshots. Approval creation, revocation, inspection, and consumption do not accept recommendations, convert target choices, create readiness, submit orders, call exchanges, create route executor behavior, fan out, rank/score, use CBBO, reselect targets, or auto-submit. money_flow_project_memory.md was read as strategic context and not modified.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `db/models/trading.py`
  - `db/models/__init__.py`
  - `db/migrations/versions/20260426_0024_phase71_routing_automation_approvals.py`
  - `services/routing/service.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase71_routing_automation_approvals.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase71_routing_automation_approvals.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase70_routing_automation.py tests/test_phase71_routing_automation_approvals.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase69_routed_workflow_inspection.py tests/test_phase67_recommendation_backed_submission.py tests/test_api.py tests/test_operational_docs.py` passed.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed.
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py` passed.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-7.1-review.zip` created a clean review bundle.

## v2026.04.26.003

- `recorded_at_utc`: `2026-04-26T14:31:44Z`
- `scope`: `Phase 7.0 controlled routing automation substrate`
- `intent`: `Native entry. Added the first non-executing routing automation substrate above the accepted single-target recommendation-backed path. Introduced explicit automation modes (`disabled`, `dry_run_only`, `approval_required`, `explicit_automation_permitted`), policy/plan domain models, API schemas, default disabled policy inspection at `GET /api/v1/routing-automation/policy`, and dry-run plan inspection at `POST /api/v1/routing-automation/plans/by-desired-trade/{desired_trade_key}`. Plans read existing routed workflow records only, preserve desired-trade, route-readiness audit, recommendation, target-choice, child-intent, readiness, submitted-order, selected binding/account/venue/symbol lineage, classify bounded same-target steps as already satisfied, disabled, dry-run-only, approval-required, automation-eligible, manual-only, deferred, or blocked, and expose no-fanout/no-CBBO/no-ranking/no-scoring/no-target-reselection/no-route-executor/no-auto-submit boundary flags. Phase 7.0 adds no migration, config, target choice creation, child-intent conversion, readiness creation, submitted-order creation, exchange call, route executor behavior, smart routing, best-binding selection, ranking, scoring, CBBO, fanout, target reselection, cross-binding recovery, cross-venue retry, new exchange behavior, or money_flow_project_memory.md update.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `services/routing/service.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase70_routing_automation.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase70_routing_automation.py` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase69_routed_workflow_inspection.py tests/test_phase67_recommendation_backed_submission.py tests/test_api.py tests/test_operational_docs.py` passed.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed.
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py` passed.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-7.0-review.zip` created a clean review bundle.

## v2026.04.26.002

- `recorded_at_utc`: `2026-04-26T14:21:36Z`
- `scope`: `Phase 6 closeout master synchronization and memory consolidation`
- `intent`: `Native entry. Preserved the architecture-review update to money_flow_project_memory.md, removed the obsolete PHASE_5_CHANGES_SINCE_5_4.md handoff summary from the tracked repo surface, aligned REPO_TREE.md with the deletion, and replaced a machine-local absolute docs link in docs/strategy.md with a relative canonical-doc link before synchronizing the accepted Phase 6.10.3 code line into master. No product behavior, migration, config, smart routing, best-binding selection, ranking, scoring, CBBO, fanout, target reselection, route executor behavior, auto-submit, cross-binding recovery, cross-venue retry, or exchange behavior was added.`
- `affected_files`:
  - `money_flow_project_memory.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
  - `REPO_TREE.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed.
  - `git status --short --branch` verified the working tree before and after the commit/merge.
  - `git merge --ff-only phase-6.10.3` fast-forwarded `master` to the accepted Phase 6.10.3 line plus memory consolidation.

## v2026.04.26.001

- `recorded_at_utc`: `2026-04-26T05:52:07Z`
- `scope`: `Phase 6.10.3 adapter-in-flight submit uncertainty hotpatch`
- `intent`: `Native entry. Hotpatched the explicit child-intent submit lease so adapter-in-flight ambiguity is preserved before any venue adapter submit call can begin. After readiness/live/routed gates pass and the lease is acquired, the execution service now writes terminal `adapter_submit_may_have_started` with intent, readiness, venue, lease, timestamp, adapter-call, non-returned, non-persisted, and reconciliation-required metadata before invoking `adapter.submit_order()`. Ambiguous transport failures, timeouts, unknown adapter exceptions, and non-classified `VenueAdapterError` results after that mark leave the lease terminal with `adapter_submit_outcome_unknown`; future submit attempts block before adapter submission with `submission_state_uncertain`, `adapter_submit_may_have_started`, `adapter_submit_outcome_unknown`, and `manual_reconciliation_required`, even after TTL. Known pre-adapter validation/auth/preparation failures remain retryable failed lease paths, stale pre-adapter active leases remain replaceable, normal success still persists one SubmittedOrder and releases the lease as submitted, and Phase 6.10.2 `adapter_submit_persistence_unknown` behavior remains unchanged. No migration, config, smart routing, best-binding selection, ranking, scoring, CBBO, fanout, target reselection, route executor behavior, auto-submit, cross-binding recovery, cross-venue retry, new exchange behavior, broad workflow framework, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `services/execution/service.py`
  - `tests/test_phase67_recommendation_backed_submission.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase67_recommendation_backed_submission.py` passed: `11 passed`.
  - `.venv/bin/python -m pytest -q tests/test_phase68_recommendation_backed_lifecycle.py tests/test_phase69_routed_workflow_inspection.py tests/test_phase610_phase6_closeout.py tests/test_api.py tests/test_operational_docs.py` passed: `30 passed`.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed: `375 passed`.
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py` passed: `1 passed`.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed after final docs update: `8 passed`.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.10.3-review.zip` created a clean review bundle; bundle inspection found 546 files and no `.env` other than `.env.example`, virtualenvs, caches, local DBs, SQLite files, logs, or nested archives.

## v2026.04.23.002

- `recorded_at_utc`: `2026-04-23T06:16:36Z`
- `scope`: `Phase 6.10.2 submit lease uncertainty hotpatch`
- `intent`: `Native entry. Hotpatched the explicit child-intent submit lease so a successful adapter submit response followed by local SubmittedOrder persistence failure is preserved as terminal operational uncertainty instead of a normal stale active lease. The lease now records `adapter_submit_persistence_unknown` with reason `adapter_submit_returned_persistence_failed`, reconciliation metadata, adapter/submitted-order ids when available, and persistence exception details. Future submit attempts for that child intent block before adapter submission with `submission_state_uncertain`, `adapter_submit_persistence_unknown`, and `manual_reconciliation_required`, even after the lease TTL has elapsed. Normal successful submit, concurrent submit blocking, existing submitted-order idempotency, gate blocks, adapter submit failures, and stale pre-adapter active lease replacement remain unchanged. Added a minimal migration widening the lease `status` column to fit the terminal uncertainty status. No smart routing, best-binding selection, ranking, scoring, CBBO, fanout, target reselection, route executor behavior, auto-submit, cross-binding recovery, cross-venue retry, new exchange behavior, new config, broad workflow framework, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `db/models/trading.py`
  - `db/migrations/versions/20260423_0023_phase6102_submission_lease_uncertainty.py`
  - `services/execution/service.py`
  - `tests/test_phase67_recommendation_backed_submission.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase67_recommendation_backed_submission.py` passed: `10 passed`.
  - `.venv/bin/python -m pytest -q tests/test_phase68_recommendation_backed_lifecycle.py` passed: `4 passed`.
  - `.venv/bin/python -m pytest -q tests/test_phase69_routed_workflow_inspection.py` passed: `4 passed`.
  - `.venv/bin/python -m pytest -q tests/test_phase610_phase6_closeout.py` passed: `1 passed`.
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py` passed: `21 passed`.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed: `374 passed`.
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py` passed: `1 passed`.
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` passed after final docs update: `8 passed`.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.10.2-review.zip` created a clean review bundle; bundle inspection found 522 files and no `.env` other than `.env.example`, virtualenvs, caches, local DBs, SQLite files, logs, or nested archives.

## v2026.04.23.001

- `recorded_at_utc`: `2026-04-23T05:14:35Z`
- `scope`: `Phase 6.10.1 routed submit and workflow truth hotpatch`
- `intent`: `Native entry. Hotpatched the Phase 6 closeout before merge. Added a narrow persistence-backed `order_intent_submission_leases` guard so concurrent explicit submit calls for the same child intent cannot both pass through to the venue adapter before a SubmittedOrder exists; the guard is acquired after readiness/live/routed gates pass, rechecks existing submitted-order truth before adapter submission, releases on existing/success/failure paths, and does not turn SubmittedOrder into a pre-submit reservation. Preserved first-submitted-order truth on recommendation/source-audit provenance when same-target retry creates a later submitted order: `submitted_order_id` remains the first submitted order, with `first_submitted_order_id`, `first_submitted_order_created_at`, `latest_submitted_order_id`, `latest_submitted_order_checked_at`, and `submitted_order_ids` exposing retry/latest truth separately. Renamed routed workflow inspection's static `actionability_summary` / `recovery_summary` fields to `same_target_lifecycle_summary` so the read-only workflow API no longer implies real actionability or recovery evaluations. Strengthened Phase 6.7, 6.8, 6.9, and 6.10 tests for concurrent submit, retry provenance, read-only workflow response shape, and closeout boundaries. No new routing policy, smart routing, best-binding selection, ranking, scoring, CBBO, fanout, target reselection, route executor behavior, auto-submit, cross-binding recovery, cross-venue retry, new exchange behavior, config, broad workflow framework, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `db/models/trading.py`
  - `db/models/__init__.py`
  - `db/migrations/versions/20260423_0022_phase6101_submission_leases.py`
  - `core/schemas/api.py`
  - `services/execution/service.py`
  - `services/routing/service.py`
  - `tests/test_phase67_recommendation_backed_submission.py`
  - `tests/test_phase68_recommendation_backed_lifecycle.py`
  - `tests/test_phase69_routed_workflow_inspection.py`
  - `tests/test_phase610_phase6_closeout.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests scripts` passed.
  - `.venv/bin/python -m pytest -q tests/test_phase67_recommendation_backed_submission.py` passed: `8 passed`.
  - `.venv/bin/python -m pytest -q tests/test_phase68_recommendation_backed_lifecycle.py` passed: `4 passed`.
  - `.venv/bin/python -m pytest -q tests/test_phase69_routed_workflow_inspection.py` passed: `4 passed`.
  - `.venv/bin/python -m pytest -q tests/test_phase610_phase6_closeout.py` passed: `1 passed`.
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py` passed: `21 passed`.
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` passed: `372 passed`.
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py` passed: `1 passed`.
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.10.1-review.zip` created a clean review bundle; bundle inspection found 488 files and no `.env` other than `.env.example`, virtualenvs, caches, local DBs, logs, or nested archives.

## v2026.04.22.006

- `recorded_at_utc`: `2026-04-22T22:08:27Z`
- `scope`: `Phase 6.7-6.10 closeout explicit recommendation-backed routed execution`
- `intent`: `Native entry. Closed Phase 6 as controlled explicit single-target recommendation-backed routed execution without adding smart routing or automation. Recommendation-backed child intents can now create exactly one SubmittedOrder only through the existing explicit child-intent submit path after routed/live gates and readiness pass; submitted-order raw payload and typed lifecycle-lineage responses preserve desired-trade, routing assessment, route-readiness audit, routing target recommendation, target choice, child intent, readiness, selected binding/account/venue/symbol, recommendation policy, routed order-shape policy, and no-fanout/no-allocation/no-scoring/no-target-reselection/no-auto-submit flags. Recommendation/source-audit submitted-order-created truth is updated after successful explicit submit. Post-submit detail/list/actionability/recovery/reconciliation/lifecycle-event and same-target retry surfaces remain recommendation-aware while reconciliation payload collisions cannot overwrite platform-owned routed lineage or fabricate recommendation lineage on non-routed orders. Added read-only `GET /api/v1/routed-workflows/by-desired-trade/{desired_trade_key}` aggregation over existing desired trade, assessment, audit, recommendation, target-choice, child-intent, readiness, submitted-order, and lifecycle-event records; the endpoint creates no artifacts and advances no workflow state. Added Phase 6.7, 6.8, 6.9, and 6.10 tests covering gated submitted-order handoff, lifecycle/reconciliation lineage, workflow inspection, and end-to-end closeout. No migration, config, new exchange behavior, best-binding selection, ranking, scoring, CBBO, fanout, target reselection, route executor behavior, auto-submit, cross-binding recovery, cross-venue retry, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `apps/api/app/api/routes.py`
  - `core/domain/models.py`
  - `core/domain/routed_lifecycle.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `services/execution/service.py`
  - `services/routing/service.py`
  - `tests/test_phase67_recommendation_backed_submission.py`
  - `tests/test_phase68_recommendation_backed_lifecycle.py`
  - `tests/test_phase69_routed_workflow_inspection.py`
  - `tests/test_phase610_phase6_closeout.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests scripts`
  - `.venv/bin/python -m pytest -q tests/test_phase67_recommendation_backed_submission.py`
  - `.venv/bin/python -m pytest -q tests/test_phase68_recommendation_backed_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_phase69_routed_workflow_inspection.py`
  - `.venv/bin/python -m pytest -q tests/test_phase610_phase6_closeout.py`
  - `.venv/bin/python -m pytest -q tests/test_phase65_manual_routed_flow.py`
  - `.venv/bin/python -m pytest -q tests/test_phase64_recommendation_backed_readiness.py`
  - `.venv/bin/python -m pytest -q tests/test_phase63_recommendation_target_choice_conversion.py`
  - `.venv/bin/python -m pytest -q tests/test_phase62_recommendation_acceptance.py`
  - `.venv/bin/python -m pytest -q tests/test_phase600_routing_target_recommendation.py`
  - `.venv/bin/python -m pytest -q tests/test_phase5101_route_readiness_audit.py`
  - `.venv/bin/python -m pytest -q tests/test_phase54_routed_submission_handoff.py`
  - `.venv/bin/python -m pytest -q tests/test_phase55_routed_submitted_order_lineage.py`
  - `.venv/bin/python -m pytest -q tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python -c 'ephemeral test-session manual harness run-through-readiness smoke'`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6-closeout-review.zip`
  - `verified /Users/tercirafael/money-flow-phase-6-closeout-review.zip excludes .env, virtualenv, cache, nested archive, sqlite, and db artifacts`

## v2026.04.22.005

- `recorded_at_utc`: `2026-04-22T21:27:03Z`
- `scope`: `Phase 6.6 manual routed-flow timing visibility`
- `intent`: `Native entry. Added local per-step timing visibility to the Phase 6.5 manual routed-flow harness without changing routing or execution semantics. `scripts/manual_routed_flow.py` now uses monotonic timing to emit a top-level `timing_ms` object, records `elapsed_ms` on every executed step, records total harness runtime, times the local submission-confirmation block when `--submit` is requested without the danger confirmation, and keeps skipped steps omitted rather than fabricating zero-latency timings. Strengthened the manual harness tests to verify inspect-only timing, run-through-readiness timing, non-negative numeric elapsed values on each executed step, and local submit-block timing while preserving no default submission and no SubmittedOrder creation. Timing is local harness/service-call timing only; it is not production routing latency, route-executor telemetry, or exchange/network latency unless an operator explicitly triggers live submit paths. No migration, config, service-wide telemetry framework, route executor, smart routing, best-binding selection, ranking, scoring, CBBO, fanout, target reselection, auto-submit, new exchange behavior, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `scripts/manual_routed_flow.py`
  - `tests/test_phase65_manual_routed_flow.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests scripts`
  - `.venv/bin/python -m pytest -q tests/test_phase65_manual_routed_flow.py`
  - `.venv/bin/python -m pytest -q tests/test_phase64_recommendation_backed_readiness.py`
  - `.venv/bin/python -m pytest -q tests/test_phase63_recommendation_target_choice_conversion.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python -c 'ephemeral test-session manual harness run-through-readiness timing smoke'`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.6-review.zip`
  - `verified /Users/tercirafael/money-flow-phase-6.6-review.zip contains 430 files with no forbidden .env files beyond tracked .env.example, virtualenv, cache, nested archive, sqlite, or db matches`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`

## v2026.04.22.004

- `recorded_at_utc`: `2026-04-22T20:50:22Z`
- `scope`: `Phase 6.5 manual routed-flow inspection harness`
- `intent`: `Native entry. Added an internal developer/operator manual routed-flow harness without changing routing or execution semantics. The new `scripts/manual_routed_flow.py` tool starts from an existing desired trade key, can explicitly run the current controlled chain through routing assessment, route-readiness audit, target recommendation, recommendation acceptance, target-choice conversion, prepared-order preview, and execution-readiness inspection, and emits a JSON artifact trace with ids, statuses, reason codes, selected target fields, routed lineage, no-routing-intelligence flags, and submission state. Default behavior is inspection-only and creates no downstream artifacts; `--run-through-readiness` creates only the existing explicit artifacts through readiness and still skips submission. `--submit` is locally blocked unless `--i-understand-this-can-place-a-live-order` is supplied, and any confirmed submission still uses the existing execution service gates. Added direct Phase 6.5 tests proving the harness can exercise the route through readiness, exposes key artifact lineage, does not submit by default, creates no SubmittedOrder by default, and blocks submit attempts without the danger confirmation before service submission. No migration, config, API endpoint, smart routing, best-binding selection, ranking, scoring, CBBO, fanout, target reselection, route executor behavior, auto-submit, new exchange support, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `scripts/manual_routed_flow.py`
  - `tests/test_phase65_manual_routed_flow.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests scripts`
  - `.venv/bin/python -m pytest -q tests/test_phase65_manual_routed_flow.py`
  - `.venv/bin/python -m pytest -q tests/test_phase64_recommendation_backed_readiness.py`
  - `.venv/bin/python -m pytest -q tests/test_phase63_recommendation_target_choice_conversion.py`
  - `.venv/bin/python -m pytest -q tests/test_phase62_recommendation_acceptance.py`
  - `.venv/bin/python -m pytest -q tests/test_phase600_routing_target_recommendation.py`
  - `.venv/bin/python -m pytest -q tests/test_phase5101_route_readiness_audit.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py tests/test_phase510_routing_substrate_closeout.py tests/test_phase5101_route_readiness_audit.py tests/test_phase600_routing_target_recommendation.py tests/test_phase62_recommendation_acceptance.py tests/test_phase63_recommendation_target_choice_conversion.py tests/test_phase64_recommendation_backed_readiness.py tests/test_phase65_manual_routed_flow.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.5-review.zip`
  - `verified /Users/tercirafael/money-flow-phase-6.5-review.zip contains 413 files with no .env, virtualenv, cache, nested archive, sqlite, or db matches`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`

## v2026.04.22.003

- `recorded_at_utc`: `2026-04-22T20:23:37Z`
- `scope`: `Phase 6.4.1 recommendation-backed readiness truth hotpatch`
- `intent`: `Native entry. Fixed Phase 6.4 readiness truth issues without adding routing or submission scope. Routed child-intent lineage validation now blocks preview/readiness when stored routed order-shape policy is missing, malformed, or no longer matches the current OrderIntent order_type, limit_price, or reduce_only fields. Recommendation-backed quote freshness failures during preview/readiness now emit the readiness-time reason/stale-data code quote_stale_at_readiness instead of the recommendation-time code. Strengthened Phase 6.4 tests for order-type, LIMIT-price, reduce-only, missing-policy, and stale-quote readiness blockers, all before adapter preparation or submission. Cleaned stale docs that still described recommendation-to-child-intent conversion as future work; docs now state Phase 6.3 already added explicit accepted recommendation-backed target-choice conversion to one child intent and Phase 6.4/6.4.1 harden preview/readiness inspection. No migration, config, endpoint, submitted-order creation, exchange submit call, route executor behavior, fanout, allocation, ranking, scoring, CBBO, target reselection, auto-submit, new exchange support, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `services/execution/service.py`
  - `tests/test_phase64_recommendation_backed_readiness.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_phase64_recommendation_backed_readiness.py`
  - `.venv/bin/python -m pytest -q tests/test_phase53_routed_child_intent_readiness.py`
  - `.venv/bin/python -m pytest -q tests/test_phase63_recommendation_target_choice_conversion.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase54_routed_submission_handoff.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.4.1-review.zip`
  - `verified /Users/tercirafael/money-flow-phase-6.4.1-review.zip contains 393 files with no .env, virtualenv, cache, nested archive, sqlite, or db matches`

## v2026.04.22.002

- `recorded_at_utc`: `2026-04-22T19:49:16Z`
- `scope`: `Phase 6.4 recommendation-backed readiness inspection`
- `intent`: `Native entry. Implemented the controlled recommendation-backed child-intent preparation/readiness inspection handoff without adding submission behavior. Accepted recommendation-backed child intents now use the existing child-intent prepared-order preview and submission-readiness paths with stronger routed-lineage validation for source RoutingTargetRecommendation, RouteReadinessAudit, route-readiness candidate, current mandate, binding/account, active/trading-eligible symbol mapping, and stored quote-observation freshness. Prepared-order preview and execution-readiness API responses now expose routed lineage as a top-level response field so operators can inspect recommendation/audit/target-choice/order-shape lineage without parsing raw payload/provenance. Added focused Phase 6.4 tests for happy-path preview/readiness, API lineage, disabled binding/account and inactive/non-trading symbol blockers, stale quote blockers, explicit LIMIT order-shape preservation, and no SubmittedOrder/exchange-submit boundary. No migration, config, new endpoint, submitted-order creation, exchange submit call, route executor behavior, fanout, allocation, ranking, scoring, CBBO, target reselection, auto-submit, new exchange support, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `services/execution/service.py`
  - `core/schemas/api.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase64_recommendation_backed_readiness.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_phase64_recommendation_backed_readiness.py`
  - `.venv/bin/python -m pytest -q tests/test_phase53_routed_child_intent_readiness.py`
  - `.venv/bin/python -m pytest -q tests/test_phase63_recommendation_target_choice_conversion.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase54_routed_submission_handoff.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py tests/test_phase510_routing_substrate_closeout.py tests/test_phase5101_route_readiness_audit.py tests/test_phase600_routing_target_recommendation.py tests/test_phase62_recommendation_acceptance.py tests/test_phase63_recommendation_target_choice_conversion.py tests/test_phase64_recommendation_backed_readiness.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.4-review.zip`

## v2026.04.22.001

- `recorded_at_utc`: `2026-04-22T19:33:23Z`
- `scope`: `Repository source-control baseline hygiene`
- `intent`: `Native entry. Hardened source-control hygiene before creating the Phase 6.3 baseline Git commit on `master`. Expanded `.gitignore` so local secrets, virtualenvs, Python/test caches, local database/runtime state, logs, OS/editor files, build artifacts, review ZIPs, handoff archives, and optional Node artifacts are excluded while `.env.example` remains trackable. Added concise repo documentation that review bundles and handoff archives stay outside source control and future phase work should use short-lived branches from `master`. No product behavior, source refactor, migration, config expansion, endpoint, exchange behavior, routing behavior, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `.gitignore`
  - `README.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `git status`
  - `git init`
  - `git branch -M master`
  - `git check-ignore -v .env`
  - `git check-ignore -v .venv`
  - `git check-ignore -v "*.zip"`
  - `grep pass for API_KEY, SECRET, PRIVATE_KEY, PASSWORD, TOKEN, COINBASE, BINANCE, KRAKEN, OKX, HYPERLIQUID, ASTER`
  - `git add .`
  - `git status --short`
  - `git diff --cached --stat`
  - `git commit -m "Baseline Money Flow platform through Phase 6.3"`
  - `git branch --show-current`
  - `git log --oneline -1`
  - `git ls-files | grep -E '(^|/)(.env|.venv|__pycache__|.pytest_cache|.*\.zip|.*\.sqlite|.*\.db)$' || true`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`

## v2026.04.20.004

- `recorded_at_utc`: `2026-04-20T10:12:52Z`
- `scope`: `Phase 6.3 explicit accepted recommendation target-choice conversion`
- `intent`: `Native entry. Added the first controlled post-recommendation child-intent action without adding execution automation. Accepted recommendation-backed RoutingTargetChoice records can now be explicitly converted through the existing target-choice conversion path into exactly one routed child OrderIntent. Conversion validates recommendation-backed target-choice provenance, linked successful RoutingTargetRecommendation truth, source RouteReadinessAudit and RoutingAssessment lineage, stored quote freshness, desired-trade/mandate/binding/account/symbol truth, and routed order-shape policy before any new child intent is created. The child intent preserves recommendation, route-readiness audit, routing assessment, target-choice, selected binding/account/venue/symbol, recommendation policy, operator conversion timestamp, and routed order-shape lineage. Repeated conversion of the same target choice returns the existing child intent, and duplicate same-audit target-choice paths cannot create a second child intent in normal controlled flow. Recommendation/source-audit `child_intent_created` truth is updated only after a valid child intent exists. No migration, config, prepared-order creation, readiness evaluation, submitted-order creation, exchange adapter call, route executor behavior, fanout, ranking, scoring, CBBO, target reselection, auto-submit, new exchange support, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `core/domain/models.py`
  - `core/schemas/api.py`
  - `apps/api/app/api/routes.py`
  - `services/routing/service.py`
  - `tests/test_phase63_recommendation_target_choice_conversion.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase63_recommendation_target_choice_conversion.py`
  - `.venv/bin/python -m pytest -q tests/test_phase52_target_choice_conversion.py`
  - `.venv/bin/python -m pytest -q tests/test_phase62_recommendation_acceptance.py`
  - `.venv/bin/python -m pytest -q tests/test_phase600_routing_target_recommendation.py`
  - `.venv/bin/python -m pytest -q tests/test_phase5101_route_readiness_audit.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py tests/test_phase510_routing_substrate_closeout.py tests/test_phase5101_route_readiness_audit.py tests/test_phase600_routing_target_recommendation.py tests/test_phase62_recommendation_acceptance.py tests/test_phase63_recommendation_target_choice_conversion.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.3-review.zip`
  - `verified /Users/tercirafael/money-flow-phase-6.3-review.zip contains 150 files with no .env, virtualenv, cache, .DS_Store, or nested archive matches`
  - `copied /Users/tercirafael/money-flow-phase-6.3-review.zip to /Users/tercirafael/CODEX-files-MF/MF-handoffs/Phase 6/money-flow-phase-6.3-review.zip`
  - `copied /Users/tercirafael/money-flow-phase-6.3-review.zip to /Users/tercirafael/phase5_handoffs/review_bundles/money-flow-phase-6.3-review.zip`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/CODEX-files-MF/MF-handoffs/Phase 6/PHASE_5_CHANGES_SINCE_5_4.md`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/phase5_handoffs/PHASE_5_CHANGES_SINCE_5_4.md`

## v2026.04.20.003

- `recorded_at_utc`: `2026-04-20T07:11:21Z`
- `scope`: `Phase 6.2.2 recommendation acceptance same-audit validity hotpatch`
- `intent`: `Native entry. Fixed the Phase 6.2.1 same-audit idempotency truth bug without adding downstream execution behavior. Recommendation acceptance now runs a basic successful-recommendation validity preflight before same-audit idempotency can return an existing target choice. A blocked or malformed RoutingTargetRecommendation from a route-readiness audit that already has an accepted target choice now fails through the normal acceptance blocker path, remains target_choice_created=false, and is not stamped with accepted-looking same-audit idempotency provenance. Duplicate successful recommendations from the same audit still return the original target choice, preserve original recommendation/audit acceptance timestamps, and create no duplicate target choices. No migration, config, new recommendation policy, child-intent creation, prepared-order creation, readiness creation, submitted-order creation, ranking, scoring, CBBO, fanout, route executor behavior, target reselection, auto-submit, new exchange support, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `services/routing/service.py`
  - `tests/test_phase62_recommendation_acceptance.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_phase62_recommendation_acceptance.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase600_routing_target_recommendation.py`
  - `.venv/bin/python -m pytest -q tests/test_phase5101_route_readiness_audit.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py tests/test_phase510_routing_substrate_closeout.py tests/test_phase5101_route_readiness_audit.py tests/test_phase600_routing_target_recommendation.py tests/test_phase62_recommendation_acceptance.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.2.2-review.zip`
  - `verified /Users/tercirafael/money-flow-phase-6.2.2-review.zip contains 149 files with no .env, virtualenv, cache, .DS_Store, or nested archive matches`
  - `copied /Users/tercirafael/money-flow-phase-6.2.2-review.zip to /Users/tercirafael/CODEX-files-MF/MF-handoffs/Phase 6/money-flow-phase-6.2.2-review.zip`
  - `copied /Users/tercirafael/money-flow-phase-6.2.2-review.zip to /Users/tercirafael/phase5_handoffs/review_bundles/money-flow-phase-6.2.2-review.zip`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/CODEX-files-MF/MF-handoffs/Phase 6/PHASE_5_CHANGES_SINCE_5_4.md`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/phase5_handoffs/PHASE_5_CHANGES_SINCE_5_4.md`

## v2026.04.20.002

- `recorded_at_utc`: `2026-04-20T06:40:02Z`
- `scope`: `Phase 6.2.1 recommendation acceptance idempotency hotpatch`
- `intent`: `Native entry. Fixed the Phase 6.2 recommendation-acceptance idempotency and audit-time truth gaps without adding downstream execution behavior. Recommendation acceptance now checks for an existing target choice produced by any recommendation tied to the same RouteReadinessAudit before creating a new target choice. Duplicate successful recommendations from one audit return the original target choice, mark the later recommendation as target_choice_created, and record idempotent/cross-recommendation acceptance provenance instead of creating another choice. Re-accepting the same recommendation or a duplicate same-audit recommendation preserves the original recommendation/audit recommendation_accepted_at timestamp and records retry/check time separately. No migration, config, new recommendation policy, child-intent creation, prepared-order creation, readiness creation, submitted-order creation, ranking, scoring, CBBO, fanout, route executor behavior, target reselection, auto-submit, new exchange support, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `services/routing/service.py`
  - `tests/test_phase62_recommendation_acceptance.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_phase62_recommendation_acceptance.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase600_routing_target_recommendation.py`
  - `.venv/bin/python -m pytest -q tests/test_phase5101_route_readiness_audit.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py tests/test_phase510_routing_substrate_closeout.py tests/test_phase5101_route_readiness_audit.py tests/test_phase600_routing_target_recommendation.py tests/test_phase62_recommendation_acceptance.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.2.1-review.zip`
  - `verified /Users/tercirafael/money-flow-phase-6.2.1-review.zip contains 149 files with no .env, virtualenv, cache, .DS_Store, or nested archive matches`
  - `copied /Users/tercirafael/money-flow-phase-6.2.1-review.zip to /Users/tercirafael/CODEX-files-MF/MF-handoffs/Phase 6/money-flow-phase-6.2.1-review.zip`
  - `copied /Users/tercirafael/money-flow-phase-6.2.1-review.zip to /Users/tercirafael/phase5_handoffs/review_bundles/money-flow-phase-6.2.1-review.zip`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/CODEX-files-MF/MF-handoffs/Phase 6/PHASE_5_CHANGES_SINCE_5_4.md`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/phase5_handoffs/PHASE_5_CHANGES_SINCE_5_4.md`

## v2026.04.20.001

- `recorded_at_utc`: `2026-04-20T05:44:07Z`
- `scope`: `Phase 6.2 explicit recommendation acceptance into target choice`
- `intent`: `Native entry. Added the first controlled recommendation-to-target-choice workflow without adding execution automation. A successful non-executing RoutingTargetRecommendation can now be explicitly accepted by an operator into exactly one existing RoutingTargetChoice audit record. Acceptance requires the recommendation to be recommended_single_ready_candidate and non_executing, revalidates source audit freshness, recommendation freshness, stored candidate quote observation freshness, desired-trade/mandate/binding/account/symbol truth, and routing-assessment candidate lineage, records recommendation/audit/policy/selected-target lineage in target-choice provenance, and updates recommendation plus source route-readiness audit target_choice_created truth. Repeated acceptance returns the existing target choice instead of creating a duplicate. Blocked, unknown, stale, or drifted recommendations fail before target-choice creation. No migration, config, new recommendation policy, smart routing, best-binding selection, CBBO, ranking, scoring, fanout, split allocation, route executor behavior, automatic target-choice creation, child-intent creation, prepared-order creation, readiness creation, submitted-order creation, auto-submit, target reselection, cross-binding recovery, cross-venue retry/failover, new exchange support, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `apps/api/app/api/routes.py`
  - `services/routing/service.py`
  - `tests/test_phase62_recommendation_acceptance.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase62_recommendation_acceptance.py`
  - `.venv/bin/python -m pytest -q tests/test_phase600_routing_target_recommendation.py`
  - `.venv/bin/python -m pytest -q tests/test_phase5101_route_readiness_audit.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py tests/test_phase510_routing_substrate_closeout.py tests/test_phase5101_route_readiness_audit.py tests/test_phase600_routing_target_recommendation.py tests/test_phase62_recommendation_acceptance.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.2-review.zip`
  - `verified /Users/tercirafael/money-flow-phase-6.2-review.zip contains 149 files with no .env, virtualenv, cache, .DS_Store, or nested archive matches`
  - `copied /Users/tercirafael/money-flow-phase-6.2-review.zip to /Users/tercirafael/CODEX-files-MF/MF-handoffs/Phase 6/money-flow-phase-6.2-review.zip`
  - `copied /Users/tercirafael/money-flow-phase-6.2-review.zip to /Users/tercirafael/phase5_handoffs/review_bundles/money-flow-phase-6.2-review.zip`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/CODEX-files-MF/MF-handoffs/Phase 6/PHASE_5_CHANGES_SINCE_5_4.md`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/phase5_handoffs/PHASE_5_CHANGES_SINCE_5_4.md`

## v2026.04.19.011

- `recorded_at_utc`: `2026-04-19T13:20:43Z`
- `scope`: `Phase 6.1.1 recommendation-policy input and binding-priority cleanup hotpatch`
- `intent`: `Native entry. Cleaned up the Phase 6.1 deterministic binding-priority recommendation policy without adding new recommendation behavior or downstream workflow. Recommendation API input now validates `policy_name` against only `single_ready_candidate_only` or `explicit_binding_priority`, so oversized, whitespace-only, and unsupported policy names return client validation errors instead of reaching persistence; direct service calls also reject malformed or oversized policy names before any database write, while short unknown internal policy attempts remain controlled blocked records. Binding upsert semantics are now explicit: omitting `target_recommendation_priority` preserves the existing priority, `clear_target_recommendation_priority=true` intentionally clears it, and clear-plus-value requests are rejected. Strengthened Phase 6 recommendation tests for invalid policy input, direct service malformed policy rejection, priority clear/preserve semantics, and `explicit_binding_priority` blocking when the selected candidate's stored quote observation is stale at recommendation time. No migration, config, new recommendation policy, target-choice creation, child-intent creation, readiness creation, submitted-order creation, ranking, scoring, CBBO, fanout, route executor behavior, auto-submit, target reselection, new exchange support, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `apps/api/app/api/routes.py`
  - `services/runtime/context.py`
  - `services/routing/service.py`
  - `tests/test_api.py`
  - `tests/test_phase600_routing_target_recommendation.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_phase600_routing_target_recommendation.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase5101_route_readiness_audit.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py tests/test_phase510_routing_substrate_closeout.py tests/test_phase5101_route_readiness_audit.py tests/test_phase600_routing_target_recommendation.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.1.1-review.zip`
  - `verified /Users/tercirafael/money-flow-phase-6.1.1-review.zip contains 148 files with no .env, virtualenv, cache, or nested archive matches`
  - `copied /Users/tercirafael/money-flow-phase-6.1.1-review.zip to /Users/tercirafael/CODEX-files-MF/MF-handoffs/Phase 6/money-flow-phase-6.1.1-review.zip`
  - `copied /Users/tercirafael/money-flow-phase-6.1.1-review.zip to /Users/tercirafael/phase5_handoffs/review_bundles/money-flow-phase-6.1.1-review.zip`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/CODEX-files-MF/MF-handoffs/Phase 6/PHASE_5_CHANGES_SINCE_5_4.md`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/phase5_handoffs/PHASE_5_CHANGES_SINCE_5_4.md`

## v2026.04.19.010

- `recorded_at_utc`: `2026-04-19T12:30:36Z`
- `scope`: `Phase 6.1 explicit binding-priority recommendation policy`
- `intent`: `Native entry. Added one controlled deterministic recommendation policy above the Phase 5 routing substrate and Phase 6.0.x recommendation truth layer without adding execution behavior. `single_ready_candidate_only` remains the default: exactly one ready candidate can recommend, zero ready candidates block, and multiple ready candidates still block by default. Added request-level `explicit_binding_priority`, backed by nullable operator-configured `MandateAccountBinding.target_recommendation_priority`; lower positive integer priority wins only when exactly one ready candidate has the winning priority, missing priority blocks, malformed/out-of-range priority blocks, and priority ties block. The policy reuses Phase 6.0.2 current-truth safeguards before success, including audit freshness, stored candidate quote observation freshness, desired-trade truth, mandate enablement, binding/account truth, and active/trading-eligible symbol mapping truth. Added a small migration for the nullable binding priority field, exposed the field through binding API/domain surfaces, added optional recommendation `policy_name` request input, and strengthened recommendation tests for default multiple-ready blocking, explicit priority success, missing priority, tie, malformed priority, current-truth blocking after priority selection, unknown policy blocking, API compatibility, and continued absence of downstream artifacts. No smart routing, best-binding selection, price/fee/venue-quality ranking, scoring, CBBO, fanout, split allocation, route executor behavior, target-choice auto-creation, child-intent auto-creation, readiness creation, submitted-order creation, auto-submit, target reselection, cross-binding recovery, cross-venue retry/failover, new exchange support, config expansion, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `db/models/trading.py`
  - `db/migrations/versions/20260419_0021_phase61_binding_recommendation_priority.py`
  - `apps/api/app/api/routes.py`
  - `services/runtime/context.py`
  - `services/routing/service.py`
  - `tests/test_api.py`
  - `tests/test_phase600_routing_target_recommendation.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_phase600_routing_target_recommendation.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase5101_route_readiness_audit.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py tests/test_phase510_routing_substrate_closeout.py tests/test_phase5101_route_readiness_audit.py tests/test_phase600_routing_target_recommendation.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.1-review.zip`
  - `verified /Users/tercirafael/money-flow-phase-6.1-review.zip contains 148 files with no .env, virtualenv, cache, or nested archive matches`
  - `copied /Users/tercirafael/money-flow-phase-6.1-review.zip to /Users/tercirafael/CODEX-files-MF/MF-handoffs/Phase 6/money-flow-phase-6.1-review.zip`
  - `copied /Users/tercirafael/money-flow-phase-6.1-review.zip to /Users/tercirafael/phase5_handoffs/review_bundles/money-flow-phase-6.1-review.zip`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/CODEX-files-MF/MF-handoffs/Phase 6/PHASE_5_CHANGES_SINCE_5_4.md`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/phase5_handoffs/PHASE_5_CHANGES_SINCE_5_4.md`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`

## v2026.04.19.009

- `recorded_at_utc`: `2026-04-19T12:10:08Z`
- `scope`: `Phase 6.0.2 recommendation quote-freshness and audit-linkage hotpatch`
- `intent`: `Native entry. Fixed the remaining Phase 6.0/6.0.1 recommendation truth gaps without adding recommendation-policy expansion or execution behavior. `RoutingTargetRecommendation` creation now rechecks the recommended candidate's stored `fact_snapshot["quote_observed_at"]` freshness at recommendation time, using the stored `quote_freshness_threshold_seconds` when valid and the existing route-readiness freshness threshold only when that candidate threshold is absent. Missing, malformed, timezone-invalid, or stale quote observation facts block recommendation with explicit reason/stale-data codes such as `quote_freshness_unknown`, `quote_observed_at_malformed`, and `quote_stale_at_recommendation`; audit age alone is no longer enough for success. Persisting any recommendation record from a source route-readiness audit now marks `RouteReadinessAuditModel.recommendation_created=True`, including blocked recommendation records. Added direct tests for quote fresh-at-audit but stale-at-recommendation, missing/malformed quote observation facts, service/API audit `recommendation_created` truth, and continued absence of downstream artifacts. No migration, config, endpoint, smart routing, recommendation among multiple ready candidates, ranking, scoring, CBBO, fanout, target-choice creation, child-intent creation, readiness creation, submission, route executor behavior, auto-submit, target reselection, new exchange support, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `services/routing/service.py`
  - `tests/test_phase600_routing_target_recommendation.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase600_routing_target_recommendation.py`
  - `.venv/bin/python -m pytest -q tests/test_phase5101_route_readiness_audit.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py tests/test_phase510_routing_substrate_closeout.py tests/test_phase5101_route_readiness_audit.py tests/test_phase600_routing_target_recommendation.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.0.2-review.zip`
  - `verified /Users/tercirafael/money-flow-phase-6.0.2-review.zip contains 147 files with no .env, virtualenv, cache, or nested archive matches`
  - `copied /Users/tercirafael/money-flow-phase-6.0.2-review.zip to /Users/tercirafael/phase5_handoffs/review_bundles/money-flow-phase-6.0.2-review.zip`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/phase5_handoffs/PHASE_5_CHANGES_SINCE_5_4.md`

## v2026.04.19.008

- `recorded_at_utc`: `2026-04-19T08:26:25Z`
- `scope`: `Phase 6.0.1 recommendation current-truth hotpatch`
- `intent`: `Native entry. Fixed the Phase 6.0.0 `RoutingTargetRecommendation` current-truth gap without adding routing or execution behavior. Recommendation success now revalidates the current `StrategyMandate` before `recommended_single_ready_candidate`, blocking with `mandate_missing` or `mandate_inactive` when the mandate is gone or disabled after the source route-readiness audit. It also blocks stale desired-trade symbol drift with `desired_trade_symbol_mismatch` / symbol-id mismatch checks, and revalidates current venue symbol mapping active/trading-eligible truth with `symbol_inactive`, `symbol_not_trading_eligible`, or `symbol_mapping_missing_or_changed` before recording a recommended target. Blocked recommendation outputs now retain audit-level not-ready/global blocker reason codes even when zero-ready or multiple-ready candidate status is the primary outcome. Added direct regression tests for disabled mandate, inactive symbol mapping, non-trading symbol mapping, desired-trade symbol drift, and audit-level blocker visibility. No migration, config, endpoint, target-choice creation, child-intent creation, readiness creation, submission, ranking, scoring, CBBO, fanout, route plan, route executor behavior, auto-submit, target reselection, new exchange support, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `services/routing/service.py`
  - `tests/test_phase600_routing_target_recommendation.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_phase600_routing_target_recommendation.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase5101_route_readiness_audit.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py tests/test_phase510_routing_substrate_closeout.py tests/test_phase5101_route_readiness_audit.py tests/test_phase600_routing_target_recommendation.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.0.1-review.zip`
  - `verified /Users/tercirafael/money-flow-phase-6.0.1-review.zip contains 147 files with no .env, virtualenv, cache, or nested archive matches`
  - `copied /Users/tercirafael/money-flow-phase-6.0.1-review.zip to /Users/tercirafael/phase5_handoffs/review_bundles/money-flow-phase-6.0.1-review.zip`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/phase5_handoffs/PHASE_5_CHANGES_SINCE_5_4.md`

## v2026.04.19.007

- `recorded_at_utc`: `2026-04-19T07:52:23Z`
- `scope`: `Phase 6.0.0 controlled single-ready-candidate recommendation`
- `intent`: `Native entry. Added the first persisted non-executing routing target recommendation layer above the Phase 5.10.2 route-readiness audit gate. `RoutingTargetRecommendation` records are created only from an existing `RouteReadinessAudit` and use the `single_ready_candidate_only` policy: exactly one `ready_for_recommendation` candidate records that candidate as the recommended target, zero ready candidates blocks, and more than one ready candidate blocks as ambiguous without sort-order selection, ranking, scoring, best-binding selection, price comparison, CBBO, allocation, fanout, route plans, target-choice creation, child-intent creation, readiness creation, or submission. Recommendation creation re-checks audit freshness, desired-trade status/scope/action/side/quantity, current binding/account truth, and symbol mapping before recording success, and persists blocked outcomes for stale/not-ready/invalid audit or stale desired-trade/candidate truth. Added narrow API endpoints for create-from-route-readiness-audit and get-by-id plus direct tests for success, zero/multiple ready blockers, stale audit/desired-trade/binding/account blockers, API inspection, and no downstream routing artifacts.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `db/models/__init__.py`
  - `db/models/trading.py`
  - `db/migrations/versions/20260419_0020_phase600_routing_target_recommendation.py`
  - `apps/api/app/api/routes.py`
  - `services/routing/service.py`
  - `tests/test_phase600_routing_target_recommendation.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_phase600_routing_target_recommendation.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase5101_route_readiness_audit.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py tests/test_phase510_routing_substrate_closeout.py tests/test_phase5101_route_readiness_audit.py tests/test_phase600_routing_target_recommendation.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-6.0.0-review.zip`
  - `verified /Users/tercirafael/money-flow-phase-6.0.0-review.zip contains 147 files with no .env, virtualenv, cache, or nested archive matches`
  - `copied /Users/tercirafael/money-flow-phase-6.0.0-review.zip to /Users/tercirafael/phase5_handoffs/review_bundles/money-flow-phase-6.0.0-review.zip`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/phase5_handoffs/PHASE_5_CHANGES_SINCE_5_4.md`

## v2026.04.19.006

- `recorded_at_utc`: `2026-04-19T07:05:21Z`
- `scope`: `Phase 5.10.2 route-readiness audit truth hotpatch`
- `intent`: `Native entry. Fixed narrow Phase 5.10.1 route-readiness audit truth issues without adding recommendation or execution behavior. Route-readiness audits now label quote facts read from persisted routing-assessment snapshots as `derived_from_existing_assessment` instead of overclaiming a fresh `venue_query`; desired-trade missing side, missing quantity, zero quantity, and negative quantity now block recommendation-readiness through global reason codes; malformed, non-finite, zero, or negative quote prices are reason-coded and do not enter notional math; and default MARKET order-shape readiness now reports `market_order_policy_defaulted` rather than `market_order_policy_explicit`. Strengthened Phase 5.10.1 tests for quote source truth, desired-trade shape blockers, quote-price safety, default MARKET wording, API payload truth, and no downstream routing artifacts. No target recommendation, best-binding selection, smart routing, CBBO, ranking, scoring, fanout, split allocation, route executor behavior, auto-submit, target reselection, cross-binding/cross-venue recovery, new live execution behavior, new exchange support, migration, config, endpoint, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `services/routing/service.py`
  - `tests/test_phase5101_route_readiness_audit.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase5101_route_readiness_audit.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py tests/test_phase510_routing_substrate_closeout.py tests/test_phase5101_route_readiness_audit.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-5.10.2-review.zip`
  - `verified /Users/tercirafael/money-flow-phase-5.10.2-review.zip contains 145 files with no .env, virtualenv, cache, or nested archive matches`
  - `copied /Users/tercirafael/money-flow-phase-5.10.2-review.zip to /Users/tercirafael/phase5_handoffs/review_bundles/money-flow-phase-5.10.2-review.zip`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/phase5_handoffs/PHASE_5_CHANGES_SINCE_5_4.md`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`

## v2026.04.19.005

- `recorded_at_utc`: `2026-04-19T06:13:09Z`
- `scope`: `Phase 5.10.1 route-readiness data-sufficiency audit`
- `intent`: `Native entry. Added a first-class non-selecting route-readiness / data-sufficiency audit layer beside the Phase 5 routing substrate. The new persisted RouteReadinessAudit and per-candidate audit records can be created from a routing-required desired trade or an existing routing assessment, inspected by id, and exposed through narrow operator APIs without recommending, ranking, scoring, choosing, converting, preparing, assessing execution readiness, submitting, or executing anything. The audit reports overall and per-candidate statuses, missing/stale/unsupported/unavailable/policy/blocking facts, data-source labels, quote freshness truth, same-venue multi-account account-scoped facts, default routed order-shape readiness facts, and explicit no-recommendation / no-target-choice / no-child-intent / no-submission provenance. Added tests for missing and stale quotes, inactive binding/account and missing symbol mapping blockers, unsupported order-shape facts, economic/balance/fee visibility, same-venue multi-account separation, API inspection, and absence of downstream artifacts. Added a small migration for durable audit inspection. No target recommendation, best-binding selection, smart routing, CBBO, ranking, scoring, fanout, split allocation, route executor behavior, auto-submit, target reselection, cross-binding/cross-venue recovery, new exchange support, new live execution behavior, config, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `db/models/__init__.py`
  - `db/models/trading.py`
  - `db/migrations/versions/20260419_0019_phase5101_route_readiness_audit.py`
  - `apps/api/app/api/routes.py`
  - `services/routing/service.py`
  - `tests/test_phase5101_route_readiness_audit.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core/domain/enums.py core/domain/models.py db/models services/routing/service.py core/schemas/api.py apps/api/app/api/routes.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase5101_route_readiness_audit.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py tests/test_phase510_routing_substrate_closeout.py tests/test_phase5101_route_readiness_audit.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase42_execution_readiness.py tests/test_phase43_submission.py tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-5.10.1-review.zip`
  - `verified /Users/tercirafael/money-flow-phase-5.10.1-review.zip contains 145 files with no .env, virtualenv, cache, or nested archive matches`
  - `copied /Users/tercirafael/money-flow-phase-5.10.1-review.zip to /Users/tercirafael/phase5_handoffs/review_bundles/money-flow-phase-5.10.1-review.zip`
  - `copied PHASE_5_CHANGES_SINCE_5_4.md to /Users/tercirafael/phase5_handoffs/PHASE_5_CHANGES_SINCE_5_4.md`

## v2026.04.19.004

- `recorded_at_utc`: `2026-04-19T05:13:15Z`
- `scope`: `Phase 5.10 routing-substrate closeout audit`
- `intent`: `Native entry. Closed Phase 5 with a focused routing-substrate audit and regression pass without adding routing behavior. Added an end-to-end Phase 5.10 closeout test that exercises the accepted routed chain from routing-required desired trade through routing assessment, explicit target choice, exactly-one child-intent conversion, routed preview/readiness, explicit gated routed submission, submitted-order detail/list, actionability/recovery, reconciliation with a colliding update-payload routed_submission key, and lifecycle-event routed context. The test proves typed routed lineage agrees across submitted-order lineage, routed lifecycle context, actionability/recovery, reconciliation, and lifecycle-event surfaces; the selected same-venue secondary account is the only submitted target; update-payload routed_submission remains non-authoritative; and no extra child intents/submitted orders, fanout, allocation, scoring, CBBO, target reselection, route plan, route executor behavior, or auto-submit appear. Updated operational and canonical docs to mark Phase 5 as routing substrate only and closed for handoff to Phase 6 controlled single-target selection. No service behavior, endpoint, migration, config, exchange support, target selection, fanout, scoring, CBBO, route executor, auto-submit, cross-binding/cross-venue recovery, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `tests/test_phase510_routing_substrate_closeout.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_phase510_routing_substrate_closeout.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py tests/test_phase510_routing_substrate_closeout.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-5.10-review.zip`
  - `.venv/bin/python -c 'import zipfile, re; from pathlib import Path; p=Path("/Users/tercirafael/money-flow-phase-5.10-review.zip"); bad=re.compile(r"(^|/)(\\.env$|\\.venv/|__pycache__/|\\.pytest_cache/|\\.mypy_cache/|\\.ruff_cache/|\\.pgdata/|\\.pgsocket/|\\.DS_Store$)|\\.(zip|tar|tgz)$"); z=zipfile.ZipFile(p); names=z.namelist(); matches=[n for n in names if bad.search(n)]; print(f"files={len(names)}"); print("blocked_matches=" + (", ".join(matches[:20]) if matches else "none")); print(f"size={p.stat().st_size}")'`
  - `.venv/bin/python -c 'from pathlib import Path; import shutil; dst=Path("/Users/tercirafael/phase5_handoffs/review_bundles"); dst.mkdir(parents=True, exist_ok=True); target=dst / "money-flow-phase-5.10-review.zip"; shutil.copyfile("/Users/tercirafael/money-flow-phase-5.10-review.zip", target); print(target)'`
  - `.venv/bin/python -c 'from pathlib import Path; import shutil; dst=Path("/Users/tercirafael/phase5_handoffs"); dst.mkdir(parents=True, exist_ok=True); target=dst / "PHASE_5_CHANGES_SINCE_5_4.md"; shutil.copyfile("PHASE_5_CHANGES_SINCE_5_4.md", target); print(target)'`

## v2026.04.19.003

- `recorded_at_utc`: `2026-04-19T04:28:37Z`
- `scope`: `Phase 5.9.2 routed_submission namespace reservation hotpatch`
- `intent`: `Native entry. Fixed the inverse Phase 5.9.1 routed-lineage collision issue without widening routing scope. Reconciliation/lifecycle raw-payload merging now reserves top-level `routed_submission` for platform-authored routed audit lineage only: update payloads cannot create it on non-routed submitted orders, and existing routed submitted orders still keep their current platform lineage over update payload collisions. Event raw payload may retain adapter collision facts, but lifecycle-event routed context remains derived from the associated SubmittedOrder raw payload and non-routed events remain non-routed. Added direct regression coverage proving a non-routed submitted order reconciled with an update-payload `routed_submission` collision remains `routed_origin=false` with no routed lineage or lifecycle context, while venue reconciliation facts are preserved. No routing behavior, target reselection, fanout, CBBO, scoring, route executor behavior, auto-submit, cross-binding/cross-venue recovery, endpoint, migration, config, new exchange, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `services/execution/service.py`
  - `tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_phase56_routed_order_shape_policy.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-5.9.2-review.zip`
  - `.venv/bin/python -c 'import zipfile, re; from pathlib import Path; p=Path("/Users/tercirafael/money-flow-phase-5.9.2-review.zip"); bad=re.compile(r"(^|/)(\\.env$|\\.venv/|__pycache__/|\\.pytest_cache/|\\.mypy_cache/|\\.ruff_cache/|\\.pgdata/|\\.pgsocket/|\\.DS_Store$)|\\.(zip|tar|tgz)$"); z=zipfile.ZipFile(p); names=z.namelist(); matches=[n for n in names if bad.search(n)]; print(f"files={len(names)}"); print("blocked_matches=" + (", ".join(matches[:20]) if matches else "none")); print(f"size={p.stat().st_size}")'`
  - `.venv/bin/python -c 'from pathlib import Path; import shutil; dst=Path("/Users/tercirafael/phase5_handoffs/review_bundles"); dst.mkdir(parents=True, exist_ok=True); target=dst / "money-flow-phase-5.9.2-review.zip"; shutil.copyfile("/Users/tercirafael/money-flow-phase-5.9.2-review.zip", target); print(target)'`
  - `.venv/bin/python -c 'from pathlib import Path; import shutil; dst=Path("/Users/tercirafael/phase5_handoffs"); dst.mkdir(parents=True, exist_ok=True); target=dst / "PHASE_5_CHANGES_SINCE_5_4.md"; shutil.copyfile("PHASE_5_CHANGES_SINCE_5_4.md", target); print(target)'`

## v2026.04.19.002

- `recorded_at_utc`: `2026-04-19T03:37:45Z`
- `scope`: `Phase 5.9.1 routed reconciliation payload-collision hotpatch`
- `intent`: `Native entry. Fixed the Phase 5.9 routed-lineage preservation bug without widening routing scope. Reconciliation/lifecycle raw-payload merging now treats existing platform `raw_payload["routed_submission"]` as authoritative: update payloads may still add or replace venue reconciliation facts, but a colliding top-level `routed_submission` from an adapter/update payload cannot erase or mutate the platform route lineage. Lifecycle-event routed context remains derived from the associated SubmittedOrder raw payload rather than event raw payload. Added direct regression coverage proving routed reconciliation responses and lifecycle-event responses preserve original routing assessment, target choice, selected binding/account, selected venue, selected exchange symbol, and routed order-shape policy context after a collision payload. No routing behavior, target reselection, fanout, CBBO, scoring, route executor behavior, auto-submit, cross-binding/cross-venue recovery, endpoint, migration, config, new exchange, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `services/execution/service.py`
  - `tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_phase56_routed_order_shape_policy.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-5.9.1-review.zip`
  - `.venv/bin/python -c 'import zipfile, re; from pathlib import Path; p=Path("/Users/tercirafael/money-flow-phase-5.9.1-review.zip"); bad=re.compile(r"(^|/)(\\.env$|\\.venv/|__pycache__/|\\.pytest_cache/|\\.mypy_cache/|\\.ruff_cache/|\\.pgdata/|\\.pgsocket/|\\.DS_Store$)|\\.(zip|tar|tgz)$"); z=zipfile.ZipFile(p); names=z.namelist(); matches=[n for n in names if bad.search(n)]; print(f"files={len(names)}"); print("blocked_matches=" + (", ".join(matches[:20]) if matches else "none")); print(f"size={p.stat().st_size}")'`
  - `.venv/bin/python -c 'from pathlib import Path; import shutil; dst=Path("/Users/tercirafael/phase5_handoffs/review_bundles"); dst.mkdir(parents=True, exist_ok=True); target=dst / "money-flow-phase-5.9.1-review.zip"; shutil.copyfile("/Users/tercirafael/money-flow-phase-5.9.1-review.zip", target); print(target)'`
  - `.venv/bin/python -c 'from pathlib import Path; import shutil; dst=Path("/Users/tercirafael/phase5_handoffs"); dst.mkdir(parents=True, exist_ok=True); target=dst / "PHASE_5_CHANGES_SINCE_5_4.md"; shutil.copyfile("PHASE_5_CHANGES_SINCE_5_4.md", target); print(target)'`

## v2026.04.19.001

- `recorded_at_utc`: `2026-04-19T03:12:32Z`
- `scope`: `Phase 5.9 routed reconciliation and lifecycle-event audit visibility`
- `intent`: `Native entry. Deepened routed post-submit reconciliation and lifecycle audit visibility for already submitted routed child intents without adding routing behavior. Submitted-order reconciliation updates now preserve an existing `routed_submission` audit payload when venue reconciliation returns its own raw payload, so routed origin remains inspectable after reconciliation. Submitted-order lifecycle-event responses now expose read-only routed lifecycle context derived from the associated SubmittedOrder through the shared routed parser, including missing/malformed lineage facts and routed order-shape policy facts where present. Non-routed reconciliation/events do not fabricate route context, malformed routed payloads remain bounded, same-venue multi-account reconciliation context remains selected-account scoped, and Phase 5.8.2 malformed LIMIT reason-code truth remains intact. No target reselection, fanout, CBBO, scoring, route executor behavior, auto-submit, cross-binding/cross-venue recovery, new endpoint, migration, config, new exchange, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `core/domain/models.py`
  - `core/schemas/api.py`
  - `apps/api/app/api/routes.py`
  - `services/execution/service.py`
  - `tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase56_routed_order_shape_policy.py`
  - `.venv/bin/python -m pytest -q tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-5.9-review.zip`
  - `.venv/bin/python -c 'import zipfile, re; from pathlib import Path; p=Path("/Users/tercirafael/money-flow-phase-5.9-review.zip"); bad=re.compile(r"(^|/)(\\.env$|\\.venv/|__pycache__/|\\.pytest_cache/|\\.mypy_cache/|\\.ruff_cache/|\\.pgdata/|\\.pgsocket/|\\.DS_Store$)|\\.(zip|tar|tgz)$"); z=zipfile.ZipFile(p); names=z.namelist(); matches=[n for n in names if bad.search(n)]; print(f"files={len(names)}"); print("blocked_matches=" + (", ".join(matches[:20]) if matches else "none")); print(f"size={p.stat().st_size}")'`
  - `.venv/bin/python -c 'from pathlib import Path; import shutil; dst=Path("/Users/tercirafael/phase5_handoffs/review_bundles"); dst.mkdir(parents=True, exist_ok=True); target=dst / "money-flow-phase-5.9-review.zip"; shutil.copyfile("/Users/tercirafael/money-flow-phase-5.9-review.zip", target); print(target)'`
  - `.venv/bin/python -c 'from pathlib import Path; import shutil; dst=Path("/Users/tercirafael/phase5_handoffs"); dst.mkdir(parents=True, exist_ok=True); target=dst / "PHASE_5_CHANGES_SINCE_5_4.md"; shutil.copyfile("PHASE_5_CHANGES_SINCE_5_4.md", target); print(target)'`

## v2026.04.18.052

- `recorded_at_utc`: `2026-04-18T19:57:33Z`
- `scope`: `Phase 5.8.2 routed LIMIT malformed price reason-surface cleanup`
- `intent`: `Native entry. Cleaned the Phase 5.8.1 routed order-shape policy reason surface without widening routing scope. Malformed or non-finite LIMIT price input still blocks safely with malformed_limit_price and routed_order_shape_policy_blocked before child-intent creation, but no longer includes the contradictory limit_price_explicit reason code. Finite positive LIMIT input still records limit_price_explicit when accepted, including independent blocker cases where the explicit finite price is valid but another policy fact blocks conversion. No routing behavior, fanout, CBBO, auto-submit, target reselection, route executor behavior, migration, config, endpoint, new exchange, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `services/routing/service.py`
  - `tests/test_phase56_routed_order_shape_policy.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall services/routing/service.py tests/test_phase56_routed_order_shape_policy.py`
  - `.venv/bin/python -m pytest -q tests/test_phase56_routed_order_shape_policy.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase56_routed_order_shape_policy.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py`
  - `.venv/bin/python -m pytest -q tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-5.8.2-review.zip`
  - `.venv/bin/python -c 'import zipfile, re; from pathlib import Path; p=Path("/Users/tercirafael/money-flow-phase-5.8.2-review.zip"); bad=re.compile(r"(^|/)(\\.env$|\\.venv/|__pycache__/|\\.pytest_cache/|\\.mypy_cache/|\\.ruff_cache/|\\.pgdata/|\\.pgsocket/|\\.DS_Store$)|\\.(zip|tar|tgz)$"); z=zipfile.ZipFile(p); names=z.namelist(); matches=[n for n in names if bad.search(n)]; print(f"files={len(names)}"); print("blocked_matches=" + (", ".join(matches[:20]) if matches else "none"))'`
  - `.venv/bin/python -c 'from pathlib import Path; import shutil; dst=Path("/Users/tercirafael/phase5_handoffs/review_bundles"); dst.mkdir(parents=True, exist_ok=True); target=dst / "money-flow-phase-5.8.2-review.zip"; shutil.copyfile("/Users/tercirafael/money-flow-phase-5.8.2-review.zip", target); print(target)'`
  - `.venv/bin/python -c 'from pathlib import Path; import shutil; dst=Path("/Users/tercirafael/phase5_handoffs"); dst.mkdir(parents=True, exist_ok=True); target=dst / "PHASE_5_CHANGES_SINCE_5_4.md"; shutil.copyfile("PHASE_5_CHANGES_SINCE_5_4.md", target); print(target)'`

## v2026.04.18.051

- `recorded_at_utc`: `2026-04-18T19:10:58Z`
- `scope`: `Phase 5.8.1 routed LIMIT non-finite price validation hotpatch`
- `intent`: `Native entry. Fixed the Phase 5.8 P0 routed order-shape policy bug without widening routing scope. Routed conversion API input no longer models LIMIT price as a plain float, and the routing service now rejects non-finite LIMIT prices such as NaN, sNaN, Infinity, and -Infinity before any Decimal comparison or child-intent persistence. Non-finite LIMIT policy input returns blocked_order_shape_policy with malformed_limit_price and routed_order_shape_policy_blocked in direct service conversion, leaves the desired trade routing_required, and creates no OrderIntent, PreparedVenueOrder, ExecutionReadinessAssessment, or SubmittedOrder. API non-finite representations are rejected as client errors rather than 500s, while finite explicit LIMIT conversion remains unchanged. No routing behavior, fanout, CBBO, auto-submit, target reselection, route executor behavior, migration, config, new endpoint, new exchange, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `core/schemas/api.py`
  - `apps/api/app/api/routes.py`
  - `services/routing/service.py`
  - `tests/test_phase56_routed_order_shape_policy.py`
  - `tests/test_api.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `PHASE_5_CHANGES_SINCE_5_4.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core/schemas/api.py apps/api/app/api/routes.py services/routing/service.py tests/test_phase56_routed_order_shape_policy.py tests/test_api.py`
  - `.venv/bin/python -m pytest -q tests/test_phase56_routed_order_shape_policy.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py -k "routing_conversion_api or routing_assessment_and_target_choice_endpoints"`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase56_routed_order_shape_policy.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py`
  - `.venv/bin/python -m pytest -q tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-5.8.1-review.zip`
  - `.venv/bin/python -c 'import zipfile, re; from pathlib import Path; p=Path("/Users/tercirafael/money-flow-phase-5.8.1-review.zip"); bad=re.compile(r"(^|/)(\\.env$|\\.venv/|__pycache__/|\\.pytest_cache/|\\.mypy_cache/|\\.ruff_cache/|\\.pgdata/|\\.pgsocket/|\\.DS_Store$)|\\.(zip|tar|tgz)$"); z=zipfile.ZipFile(p); names=z.namelist(); matches=[n for n in names if bad.search(n)]; print(f"files={len(names)}"); print("blocked_matches=" + (", ".join(matches[:20]) if matches else "none"))'`
  - `.venv/bin/python -c 'from pathlib import Path; import shutil; dst=Path("/Users/tercirafael/phase5_handoffs/review_bundles"); dst.mkdir(parents=True, exist_ok=True); target=dst / "money-flow-phase-5.8.1-review.zip"; shutil.copyfile("/Users/tercirafael/money-flow-phase-5.8.1-review.zip", target); print(target)'`
  - `.venv/bin/python -c 'from pathlib import Path; import shutil; dst=Path("/Users/tercirafael/phase5_handoffs"); dst.mkdir(parents=True, exist_ok=True); target=dst / "PHASE_5_CHANGES_SINCE_5_4.md"; shutil.copyfile("PHASE_5_CHANGES_SINCE_5_4.md", target); print(target)'`

## v2026.04.18.050

- `recorded_at_utc`: `2026-04-18T18:35:06Z`
- `scope`: `Phase 5.8 routed order-shape policy v2`
- `intent`: `Native entry. Added explicit routed order-shape policy input and decision output for the controlled target-choice-to-child-intent conversion boundary without adding routing behavior. Conversion now accepts optional MARKET/LIMIT order-shape policy input; omitted input remains backward-compatible as MARKET / no limit price / reduce_only=false. Explicit LIMIT requires a positive limit_price and current modeled order-type support from the candidate assessment; missing, malformed, zero, negative, unsupported, MARKET+limit ambiguity, or reduce_only=true for mandate-scoped OPEN blocks before any child intent is created. Accepted and blocked order-shape decisions are visible in conversion provenance, and accepted decisions are persisted in child-intent provenance. Repeated conversion remains idempotent, and a different policy after conversion cannot create a second child intent or silently mutate the existing one. No auto-submit, target reselection, fanout, route executor, best-binding selection, smart routing, CBBO, venue ranking, execution-quality scoring, migration, config, new exchange, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `apps/api/app/api/routes.py`
  - `services/routing/service.py`
  - `tests/test_phase56_routed_order_shape_policy.py`
  - `tests/test_phase57_routed_post_submit_lifecycle.py`
  - `tests/test_api.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core/domain/enums.py core/domain/models.py core/interfaces/services.py core/schemas/api.py apps/api/app/api/routes.py services/routing/service.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py tests/test_api.py`
  - `.venv/bin/python -m pytest -q tests/test_phase56_routed_order_shape_policy.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase56_routed_order_shape_policy.py`
  - `.venv/bin/python -m pytest -q tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-5.8-review.zip`
  - `.venv/bin/python -c 'import zipfile, re; p="/Users/tercirafael/money-flow-phase-5.8-review.zip"; bad=re.compile(r"(^|/)(\\.env$|\\.venv/|__pycache__/|\\.pytest_cache/|\\.mypy_cache/|\\.ruff_cache/|\\.pgdata/|\\.pgsocket/|\\.DS_Store$)|\\.(zip|tar|tgz)$"); z=zipfile.ZipFile(p); names=z.namelist(); matches=[n for n in names if bad.search(n)]; print(f"files={len(names)}"); print("blocked_matches=" + (", ".join(matches[:20]) if matches else "none"))'`
  - `.venv/bin/python -c 'from pathlib import Path; import shutil; dst=Path("/Users/tercirafael/phase5_handoffs/review_bundles"); dst.mkdir(parents=True, exist_ok=True); target=dst / "money-flow-phase-5.8-review.zip"; shutil.copyfile("/Users/tercirafael/money-flow-phase-5.8-review.zip", target); print(target)'`
  - `.venv/bin/python -c 'from pathlib import Path; import re; root=Path("/Users/tercirafael/phase5_handoffs"); bad=re.compile(r"(^|/)(\\.env$|\\.venv/|__pycache__/|\\.pytest_cache/|\\.mypy_cache/|\\.ruff_cache/|\\.pgdata/|\\.pgsocket/|\\.DS_Store$)"); matches=[]; [matches.append(str(p.relative_to(root))) for p in root.rglob("*") if bad.search(str(p.relative_to(root)))]; print("handoff_forbidden_matches=" + (", ".join(matches[:20]) if matches else "none"))'`

## v2026.04.18.049

- `recorded_at_utc`: `2026-04-18T18:07:25Z`
- `scope`: `Phase 5.7.1 routed same-target retry lineage and parser deduplication hotpatch`
- `intent`: `Native entry. Fixed the Phase 5.7 review issues without widening routing scope. Same-target retry of a routed submitted order now stamps the existing routed lineage onto the retried SubmittedOrder before persistence, so routed retry results remain inspectable as routed-origin while preserving recovery_parent_submitted_order_id provenance and same-target / same-account / same-venue retry semantics. Non-routed same-target retry still does not fabricate routed lineage. Routed submitted-order lineage/lifecycle parsing was collapsed into one shared domain helper used by both execution service and API response mapping, preserving missing/malformed lineage handling and routed order-shape policy validation without duplicate parser logic. No target reselection, fanout, route executor behavior, auto-submit, CBBO, scoring, LIMIT/slippage expansion, migration, config, endpoint, new exchange, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `core/domain/routed_lifecycle.py`
  - `services/execution/service.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase57_routed_post_submit_lifecycle.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core/domain/routed_lifecycle.py services/execution/service.py apps/api/app/api/routes.py tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_api.py tests/test_operational_docs.py tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-5.7.1-review.zip`
  - `.venv/bin/python -c 'import zipfile, re; p="/Users/tercirafael/money-flow-phase-5.7.1-review.zip"; bad=re.compile(r"(^|/)(\\.env$|\\.venv/|__pycache__/|\\.pytest_cache/|\\.mypy_cache/|\\.ruff_cache/|\\.pgdata/|\\.pgsocket/|\\.DS_Store$)|\\.(zip|tar|tgz)$"); z=zipfile.ZipFile(p); names=z.namelist(); matches=[n for n in names if bad.search(n)]; print(f"files={len(names)}"); print("blocked_matches=" + (", ".join(matches[:20]) if matches else "none"))'`
  - `.venv/bin/python -c 'from pathlib import Path; import shutil; dst=Path("/Users/tercirafael/phase5_handoffs/review_bundles"); dst.mkdir(parents=True, exist_ok=True); target=dst / "money-flow-phase-5.7.1-review.zip"; shutil.copyfile("/Users/tercirafael/money-flow-phase-5.7.1-review.zip", target); print(target)'`
  - `.venv/bin/python -c 'from pathlib import Path; import re; root=Path("/Users/tercirafael/phase5_handoffs"); bad=re.compile(r"(^|/)(\\.env$|\\.venv/|__pycache__/|\\.pytest_cache/|\\.mypy_cache/|\\.ruff_cache/|\\.pgdata/|\\.pgsocket/|\\.DS_Store$)"); matches=[]; [matches.append(str(p.relative_to(root))) for p in root.rglob("*") if bad.search(str(p.relative_to(root)))]; print("handoff_forbidden_matches=" + (", ".join(matches[:20]) if matches else "none"))'`

## v2026.04.18.048

- `recorded_at_utc`: `2026-04-18T17:28:56Z`
- `scope`: `Phase 5.7 routed post-submit lifecycle/actionability inspection`
- `intent`: `Native entry. Added the first routed post-submit lifecycle/actionability inspection layer for already submitted routed child intents without adding routing behavior. Submitted-order detail/list responses now expose read-only routed_lifecycle_context alongside routed lineage; recovery recommendation, recovery execution response, and actionability responses expose the same selected route context so operators can inspect desired-trade, routing assessment, target-choice, selected binding/account, selected venue, selected exchange symbol, readiness, and routed order-shape policy facts without parsing raw payload manually. Routed recovery/actionability remains same-target, same-account, and same-venue only; malformed routed payloads stay bounded with missing/malformed lineage facts; non-routed submitted orders do not fabricate routed context. No auto-submit, fanout, CBBO, venue ranking/scoring, target reselection, route executor behavior, LIMIT/slippage routed order-shape expansion, cross-binding recovery, cross-venue retry/failover, new exchange, migration, config change, endpoint, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `core/domain/models.py`
  - `core/schemas/api.py`
  - `services/execution/service.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase57_routed_post_submit_lifecycle.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core/domain/models.py core/schemas/api.py services/execution/service.py apps/api/app/api/routes.py`
  - `.venv/bin/python -m pytest -q tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py tests/test_phase57_routed_post_submit_lifecycle.py`
  - `.venv/bin/python -m pytest -q tests/test_phase42_execution_readiness.py tests/test_phase43_submission.py tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-5.7-review.zip`
  - `.venv/bin/python -c 'import zipfile, re; p="/Users/tercirafael/money-flow-phase-5.7-review.zip"; bad=re.compile(r"(^|/)(\\.env$|\\.venv/|__pycache__/|\\.pytest_cache/|\\.mypy_cache/|\\.ruff_cache/|\\.pgdata/|\\.pgsocket/|\\.DS_Store$)|\\.(zip|tar|tgz)$"); z=zipfile.ZipFile(p); names=z.namelist(); matches=[n for n in names if bad.search(n)]; print(f"files={len(names)}"); print("blocked_matches=" + (", ".join(matches[:20]) if matches else "none"))'`
  - `.venv/bin/python -c 'from pathlib import Path; import shutil; dst=Path("/Users/tercirafael/phase5_handoffs/review_bundles"); dst.mkdir(parents=True, exist_ok=True); target=dst / "money-flow-phase-5.7-review.zip"; shutil.copyfile("/Users/tercirafael/money-flow-phase-5.7-review.zip", target); print(target)'`
  - `.venv/bin/python -c 'from pathlib import Path; import re; root=Path("/Users/tercirafael/phase5_handoffs"); bad=re.compile(r"(^|/)(\\.env$|\\.venv/|__pycache__/|\\.pytest_cache/|\\.mypy_cache/|\\.ruff_cache/|\\.pgdata/|\\.pgsocket/|\\.DS_Store$)"); matches=[]; [matches.append(str(p.relative_to(root))) for p in root.rglob("*") if bad.search(str(p.relative_to(root)))]; print("handoff_forbidden_matches=" + (", ".join(matches[:20]) if matches else "none"))'`

## v2026.04.18.047

- `recorded_at_utc`: `2026-04-18T16:47:33Z`
- `scope`: `Phase 5.6 routed order-shape policy and lineage malformed-type truth`
- `intent`: `Native entry. Fixed the Phase 5.5 routed submitted-order lineage P2 issue by marking wrong-typed routed lineage fields as malformed, exposing malformed_lineage_fields alongside missing_lineage_fields while keeping submitted-order list/detail responses bounded and non-crashing. Added the first explicit routed order-shape policy for the current target-choice conversion path: converted routed child intents now get MARKET / no limit price / reduce_only=false from a policy-backed RoutedOrderShapeDecision with visible child-intent provenance instead of an implicit hardcoded default. LIMIT routed order-shape policy, routed limit-price source, and slippage guard semantics remain deferred. No smart routing, target reselection, best-binding selection, CBBO, venue ranking, price/quality scoring, fanout, route executor behavior, auto-submit, cross-binding recovery, cross-venue retry/failover, new exchange, migration, config change, API endpoint, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `core/schemas/api.py`
  - `apps/api/app/api/routes.py`
  - `services/routing/service.py`
  - `tests/test_phase55_routed_submitted_order_lineage.py`
  - `tests/test_phase56_routed_order_shape_policy.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core/schemas/api.py apps/api/app/api/routes.py services/routing/service.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py`
  - `.venv/bin/python -m pytest -q tests/test_phase55_routed_submitted_order_lineage.py -k "malformed or wrong_typed or non_routed"`
  - `.venv/bin/python -m pytest -q tests/test_phase55_routed_submitted_order_lineage.py`
  - `.venv/bin/python -m pytest -q tests/test_phase56_routed_order_shape_policy.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py tests/test_phase56_routed_order_shape_policy.py`
  - `.venv/bin/python -m pytest -q tests/test_phase42_execution_readiness.py tests/test_phase43_submission.py tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-5.6-review.zip`
  - `.venv/bin/python -c 'import zipfile, re; p="/Users/tercirafael/money-flow-phase-5.6-review.zip"; bad=re.compile(r"(^|/)(\\.env$|\\.venv/|__pycache__/|\\.pytest_cache/|\\.mypy_cache/|\\.ruff_cache/|\\.pgdata/|\\.pgsocket/|\\.DS_Store$)|\\.(zip|tar|tgz)$"); z=zipfile.ZipFile(p); names=z.namelist(); matches=[n for n in names if bad.search(n)]; print(f"files={len(names)}"); print("blocked_matches=" + (", ".join(matches[:20]) if matches else "none"))'`

## v2026.04.18.046

- `recorded_at_utc`: `2026-04-18T15:53:17Z`
- `scope`: `Phase 5.5 routed submitted-order lineage inspection`
- `intent`: `Native entry. Added read-only routed submitted-order lineage inspection without adding routing behavior. SubmittedOrder API responses now expose derived routed-origin lineage from existing raw_payload["routed_submission"], including desired-trade, routing assessment, routing target-choice, selected binding/account, selected venue, selected exchange symbol, readiness evaluation, and no-auto-submit / no-fanout / no-scoring / no-target-reselection audit flags. Non-routed submitted orders do not fabricate routing ids, and malformed routed payloads are bounded with route_lineage_malformed / missing_lineage_fields rather than breaking list/detail responses. Documented routed order-shape policy as deferred while preserving the current controlled target-choice conversion default of market, no limit price, and non-reduce-only. No migration, config change, endpoint expansion, target reselection, fanout, scoring, CBBO, auto-submit, route executor behavior, new exchange, or money_flow_project_memory.md update was added.`
- `affected_files`:
  - `core/schemas/api.py`
  - `apps/api/app/api/routes.py`
  - `services/routing/service.py`
  - `tests/test_phase55_routed_submitted_order_lineage.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core/schemas/api.py apps/api/app/api/routes.py tests/test_phase55_routed_submitted_order_lineage.py`
  - `.venv/bin/python -m pytest -q tests/test_phase55_routed_submitted_order_lineage.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase54_routed_submission_handoff.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py tests/test_phase55_routed_submitted_order_lineage.py`
  - `.venv/bin/python -m pytest -q tests/test_phase42_execution_readiness.py tests/test_phase43_submission.py tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-5.5-review.zip`
  - `.venv/bin/python -c 'import zipfile, re; p="/Users/tercirafael/money-flow-phase-5.5-review.zip"; bad=re.compile(r"(^|/)(\\.env$|\\.venv/|__pycache__/|\\.pytest_cache/|\\.mypy_cache/|\\.ruff_cache/|\\.pgdata/|\\.pgsocket/|\\.DS_Store$)|\\.(zip|tar|tgz)$"); z=zipfile.ZipFile(p); names=z.namelist(); matches=[n for n in names if bad.search(n)]; print(f"files={len(names)}"); print("blocked_matches=" + (", ".join(matches[:20]) if matches else "none"))'`

## v2026.04.18.045

- `recorded_at_utc`: `2026-04-18T14:43:49Z`
- `scope`: `Operational handoff bundle workflow`
- `intent`: `Native entry. Persisted the operator handoff requirement that each completed phase must produce a clean review ZIP in /Users/tercirafael/ using scripts/create_review_bundle.py and .archiveignore. This keeps phase handoff archives deterministic and avoids including .env files, keys, local virtualenvs, caches, generated archives, database/socket data, or other unnecessary local artifacts. No application behavior, routing scope, API endpoint, migration, or exchange behavior was changed.`
- `affected_files`:
  - `AGENTS.md`
  - `CHANGELOG.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-phase-5.4.1-cleanup-review.zip`
  - `.venv/bin/python -c 'import zipfile, re; p="/Users/tercirafael/money-flow-phase-5.4.1-cleanup-review.zip"; bad=re.compile(r"(^|/)(\\.env$|\\.venv/|__pycache__/|\\.pytest_cache/|\\.mypy_cache/|\\.ruff_cache/|\\.pgdata/|\\.pgsocket/|\\.DS_Store$)|\\.(zip|tar|tgz)$"); z=zipfile.ZipFile(p); names=z.namelist(); matches=[n for n in names if bad.search(n)]; print(f"files={len(names)}"); print("blocked_matches=" + (", ".join(matches[:20]) if matches else "none"))'`

## v2026.04.18.044

- `recorded_at_utc`: `2026-04-18T14:25:05Z`
- `scope`: `Phase 5.4.1 routed submission dual-gate truth cleanup`
- `intent`: `Native entry. Fixed the remaining Phase 5.4.1 routed phase-gate truth inconsistency without adding routing scope. Routed child-intent readiness now records both routed_submission_deferred and phase_live_submit_deferred when both the separate routed-submit gate and the normal live-submit gate are disabled, so later submit-block provenance truthfully records routed_submission_deferred=true, live_submission_deferred=true, routed_submission_enabled=false, and live_submission_enabled=false. Phase-blocked routed submit attempts still preserve the child intent status, avoid last_submission_failure, skip adapter submission, and create no SubmittedOrder. No smart routing, target reselection, best-binding selection, CBBO, venue ranking, price/quality scoring, fanout, route executor behavior, auto-submit, new endpoint, migration, or new exchange behavior was added.`
- `affected_files`:
  - `services/execution/service.py`
  - `tests/test_phase54_routed_submission_handoff.py`
  - `CHANGELOG.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall services/execution/service.py tests/test_phase54_routed_submission_handoff.py`
  - `.venv/bin/python -m pytest -q tests/test_phase54_routed_submission_handoff.py -k "both_gates or routed_submission_disabled or live_gate or routed_submission_enabled_creates"`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase54_routed_submission_handoff.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py`
  - `.venv/bin/python -m pytest -q tests/test_phase42_execution_readiness.py tests/test_phase43_submission.py tests/test_api.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`

## v2026.04.18.043

- `recorded_at_utc`: `2026-04-18T12:53:28Z`
- `scope`: `Phase 5.4.1 routed submission phase-boundary truth hotpatch`
- `intent`: `Native entry. Fixed two Phase 5.4 routed-submission truth leaks without adding routing scope. Routed child-intent submit attempts blocked by phase boundaries now preserve child-intent status and record last_submission_block for both routed_submission_deferred and phase_live_submit_deferred, avoiding misleading submission_failed status and last_submission_failure provenance when no adapter submission was attempted. Routed prepared-order preview payloads now remain non-submitting and explicit-submit-only while reporting the actual routed/live gate state; submission_deferred is true only when one or both phase gates still block explicit routed submission. No smart routing, target reselection, best-binding selection, CBBO, venue ranking, price/quality scoring, fanout, route executor behavior, auto-submit, new exchange, migration, or new API endpoint was added.`
- `affected_files`:
  - `services/execution/service.py`
  - `tests/test_phase54_routed_submission_handoff.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/python -m pytest -q tests/test_phase54_routed_submission_handoff.py`
  - `.venv/bin/python -m compileall services/execution/service.py tests/test_phase54_routed_submission_handoff.py`
  - `.venv/bin/python -m pytest -q tests/test_phase53_routed_child_intent_readiness.py`
  - `.venv/bin/python -m pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py`
  - `.venv/bin/python -m pytest -q tests/test_phase42_execution_readiness.py tests/test_phase43_submission.py tests/test_api.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_phase43_submission.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`

## v2026.04.18.042

- `recorded_at_utc`: `2026-04-18T12:18:30Z`
- `scope`: `Phase 5.4 explicit routed submission handoff`
- `intent`: `Native entry. Added the first controlled explicit routed submission handoff without adding smart routing or target reselection. A converted routed child intent now remains phase-blocked with routed_submission_deferred while the new EXECUTION_ROUTED_SUBMISSION_PHASE_ENABLED gate is false; disabled routed submit attempts are recorded as phase-boundary blocks without marking the child intent submission_failed. When the normal live-submit gate and the separate routed-submit gate are both enabled, an explicit submit action can submit only the already selected routed child intent after Phase 5.3.1 route-lineage validation and normal readiness pass. Successful routed submission creates exactly one SubmittedOrder through the existing venue submit path and preserves desired-trade, routing assessment, target-choice, selected binding/account, selected venue, selected exchange symbol, and readiness lineage in submitted-order raw payload. No auto-submit, fanout, split allocation, CBBO, venue ranking, price/quality scoring, target reselection, route executor, new exchange, or schema migration was added.`
- `affected_files`:
  - `core/config/settings.py`
  - `core/schemas/api.py`
  - `services/execution/service.py`
  - `.env.example`
  - `tests/test_config.py`
  - `tests/test_phase54_routed_submission_handoff.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase54_routed_submission_handoff.py`
  - `.venv/bin/pytest -q tests/test_phase53_routed_child_intent_readiness.py`
  - `.venv/bin/pytest -q tests/test_phase42_execution_readiness.py tests/test_phase43_submission.py`
  - `.venv/bin/pytest -q tests/test_phase42_execution_readiness.py tests/test_phase43_submission.py tests/test_api.py tests/test_interfaces.py tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_config.py`
  - `.venv/bin/pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py`
  - `.venv/bin/pytest -q tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_phase43_submission.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py tests/test_phase54_routed_submission_handoff.py`

## v2026.04.18.041

- `recorded_at_utc`: `2026-04-18T11:23:19Z`
- `scope`: `Phase 5.3.1 routed child-intent readiness lineage hardening`
- `intent`: `Native entry. Hardened the accepted Phase 5.3 routed child-intent preparation/readiness boundary without adding routed submission or new routing behavior. Routed lineage validation now blocks selected-target provenance drift across binding/account/venue/exchange-symbol fields, child-intent client/mandate identity drift, target-choice desired-trade linkage drift, and venue-account client mismatch before adapter preparation. Added direct regression coverage proving provenance drift, intent ownership drift, target-choice desired-trade drift, and explicit routed submit attempts are blocked before adapter preparation/submission; valid routed readiness remains phase-blocked with routed_submission_deferred. No routed submission, route executor, fanout, CBBO, scoring, target reselection, schema migration, new exchange, or auto-submit behavior was added.`
- `affected_files`:
  - `services/execution/service.py`
  - `tests/test_phase53_routed_child_intent_readiness.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/pytest -q tests/test_phase53_routed_child_intent_readiness.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py`
  - `.venv/bin/pytest -q tests/test_phase42_execution_readiness.py tests/test_api.py tests/test_interfaces.py tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py`

## v2026.04.18.040

- `recorded_at_utc`: `2026-04-18T10:44:09Z`
- `scope`: `Phase 5.3 routed child-intent preparation/readiness handoff`
- `intent`: `Native entry. Added the controlled Phase 5.3 handoff that lets child intents created from explicit routing target-choice conversion enter the existing prepared-order preview and execution-readiness inspection paths without creating submitted orders. Routed preview/readiness now validates route-origin lineage from OrderIntent provenance, the current source desired trade, routing assessment, target choice, selected candidate, binding, venue account, and symbol mapping before preparing or assessing; stale desired-trade status, stale binding/account truth, or mismatched route lineage returns blocked preview/readiness facts with explicit reason codes. Valid routed readiness preserves routing assessment / target-choice lineage in provenance and remains phase-blocked with routed_submission_deferred. No live routed submission, extra child intent, fanout, split allocation, CBBO, price/quality scoring, venue ranking, target reselection, route executor, route plan, migration, or new exchange behavior was added.`
- `affected_files`:
  - `services/execution/service.py`
  - `tests/test_phase53_routed_child_intent_readiness.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall services/execution/service.py`
  - `.venv/bin/pytest -q tests/test_phase52_target_choice_conversion.py`
  - `.venv/bin/pytest -q tests/test_phase53_routed_child_intent_readiness.py`
  - `.venv/bin/pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py`
  - `.venv/bin/pytest -q tests/test_phase42_execution_readiness.py tests/test_api.py tests/test_interfaces.py`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py tests/test_phase53_routed_child_intent_readiness.py`

## v2026.04.18.039

- `recorded_at_utc`: `2026-04-18T10:14:13Z`
- `scope`: `Phase 5.2.1 target-choice conversion lineage hardening`
- `intent`: `Native entry. Hardened the Phase 5.2 target-choice-to-child-intent conversion path before Phase 5.3 by validating routing assessment id/ref/environment consistency, desired-trade client/mandate/source-policy/planning-source identity, and selected binding mandate ownership before any OrderIntent can be created. Added direct blocker tests for assessment id/environment drift, desired-trade ownership drift, binding mandate drift, missing desired-trade linkage, symbol-mapping drift, assessment status drift, incomplete target-choice fields, and existing happy-path/idempotency behavior. No routed preparation, readiness assessment, submitted order, submission, fanout, scoring, CBBO, target reselection, route-plan, route-executor, migration, or new routing behavior was added.`
- `affected_files`:
  - `services/routing/service.py`
  - `tests/test_phase52_target_choice_conversion.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase52_target_choice_conversion.py`
  - `.venv/bin/pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py`
  - `.venv/bin/pytest -q tests/test_api.py tests/test_interfaces.py`
  - `.venv/bin/pytest -q tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py`

## v2026.04.18.038

- `recorded_at_utc`: `2026-04-18T09:49:12Z`
- `scope`: `Phase 5.2 controlled target-choice-to-child-intent conversion`
- `intent`: `Native entry. Added the first controlled conversion step from an explicit recorded RoutingTargetChoice to exactly one binding/account-targeted OrderIntent. The conversion revalidates current target-choice, routing assessment, candidate, desired-trade, binding, venue-account, and symbol-mapping truth before creating a child intent; preserves routing assessment / target-choice / selected binding-account lineage in OrderIntent provenance; marks the source desired trade routed only to mean a child intent now exists; and is idempotent so repeated conversion of the same target choice returns the existing child intent instead of creating duplicates. No prepared venue order, execution-readiness assessment, submitted order, submission, fanout, split allocation, CBBO, price/quality scoring, target reselection, or smart routing behavior was added.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `services/routing/service.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase52_target_choice_conversion.py`
  - `tests/test_api.py`
  - `tests/test_interfaces.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase50_routing_substrate.py`
  - `.venv/bin/pytest -q tests/test_phase51_routing_target_choice.py`
  - `.venv/bin/pytest -q tests/test_phase52_target_choice_conversion.py`
  - `.venv/bin/pytest -q tests/test_api.py tests/test_interfaces.py`
  - `.venv/bin/pytest -q tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py tests/test_phase52_target_choice_conversion.py`

## v2026.04.18.037

- `recorded_at_utc`: `2026-04-18T08:46:44Z`
- `scope`: `Phase 5.1.1 target-choice desired-trade truth hotpatch`
- `intent`: `Native entry. Tightened the Phase 5.1 non-executing target-choice substrate so a successful RoutingTargetChoice now revalidates current MandateDesiredTrade truth before recording success: the source desired trade must still exist, remain routing_required, remain mandate-scoped, remain an open action, and remain unbound to any target binding/account. Stale desired-trade drift now persists blocked_stale_assessment audit facts with explicit desired_trade_* reason codes while preserving existing assessment/candidate/binding/account stale checks. Wording was narrowed from operator-approved to operator-requested / explicit audit metadata because no auth or approval-policy enforcement exists. No child-intent conversion, execution readiness, submission, fanout, scoring, CBBO, or routing execution was added.`
- `affected_files`:
  - `services/routing/service.py`
  - `tests/test_phase51_routing_target_choice.py`
  - `core/schemas/api.py`
  - `db/models/trading.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase51_routing_target_choice.py`
  - `.venv/bin/pytest -q tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py`
  - `.venv/bin/pytest -q tests/test_api.py tests/test_interfaces.py`
  - `.venv/bin/pytest -q tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py`

## v2026.04.18.036

- `recorded_at_utc`: `2026-04-18T08:16:40Z`
- `scope`: `Phase 5.1 non-executing routing target-choice substrate`
- `intent`: `Native entry. Cleaned up Phase 5.0 candidate semantics so RoutingCandidateAssessment.assessment_id always carries the persisted routing assessment id rather than the routing request id, then added the controlled Phase 5.1 target-choice layer: RoutingTargetChoice domain/API/persistence surfaces, a routing_target_choices audit table, operator-facing target-choice endpoints, explicit assessment/candidate/binding/account validation, recorded and blocked target-choice statuses, and tests proving target choice is non-executing. Target choice leaves MandateDesiredTrade.status at routing_required and does not create OrderIntent, PreparedVenueOrder, ExecutionReadinessAssessment, SubmittedOrder, fanout, allocation, venue scoring, CBBO, or submission behavior.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `db/models/trading.py`
  - `db/models/__init__.py`
  - `db/migrations/versions/20260418_0018_phase51_routing_target_choice.py`
  - `services/routing/service.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase50_routing_substrate.py`
  - `tests/test_phase51_routing_target_choice.py`
  - `tests/test_api.py`
  - `tests/test_interfaces.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase50_routing_substrate.py`
  - `.venv/bin/pytest -q tests/test_phase51_routing_target_choice.py`
  - `.venv/bin/pytest -q tests/test_api.py tests/test_interfaces.py`
  - `.venv/bin/pytest -q tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py tests/test_phase50_routing_substrate.py tests/test_phase51_routing_target_choice.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`

## v2026.04.16.035

- `recorded_at_utc`: `2026-04-16T19:24:34Z`
- `scope`: `Phase 5.0 non-executing routing assessment substrate`
- `intent`: `Native entry. Added the first controlled routing substrate above the current execution layer without implementing target choice or live routing execution. Phase 5.0 introduces RoutingRequest, RoutingAssessment, and RoutingCandidateAssessment domain/API surfaces; persists routing_assessments and routing_assessment_candidates as assessment facts only; exposes non-executing routing-assessment creation/inspection endpoints for routing-required mandate-scoped open desired trades; enumerates eligible_for_future_selection and ineligible_for_future_selection binding candidates with explicit reason codes and missing-data facts; preserves same-venue multi-account candidate inventory; and adds tests proving assessments do not create OrderIntent or SubmittedOrder records and do not expose target-choice, ranking, scoring, fanout, or submission fields.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `db/models/trading.py`
  - `db/models/__init__.py`
  - `db/migrations/versions/20260417_0017_phase50_routing_assessment_substrate.py`
  - `services/routing/__init__.py`
  - `services/routing/service.py`
  - `apps/api/app/dependencies.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase50_routing_substrate.py`
  - `tests/test_api.py`
  - `tests/test_interfaces.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase50_routing_substrate.py`
  - `.venv/bin/pytest -q tests/test_api.py tests/test_interfaces.py`
  - `.venv/bin/pytest -q tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_api.py tests/test_interfaces.py tests/test_phase50_routing_substrate.py`
  - `.venv/bin/pytest -q tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py tests/test_phase50_routing_substrate.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`

## v2026.04.16.034

- `recorded_at_utc`: `2026-04-16T18:16:49Z`
- `scope`: `Phase 4.10.2 scoped retry-fill evidence hotpatch`
- `intent`: `Native entry. Removed the unsafe submitted-order private-fill convenience wrapper from the base, Aster, Binance, and Hyperliquid adapters so Aster/Binance same-account/same-symbol ambiguous retry evidence cannot be collapsed into plain submitted-order fills after losing evidence_scope. Kept retry safety unchanged by preserving ambiguous evidence inside SubmittedOrderPrivateFillEvidence, kept exact exchange-order-id matches order_scoped, tightened zero-match exact-id messages so they no longer claim a match occurred, and added direct regression coverage for Aster/Binance ambiguity leakage, order-scoped fills, zero-match messages, and unchanged retry blocking behavior. No routing, stream framework, target selection, fanout, native amend expansion, new exchange, migration, or orchestration action was added.`
- `affected_files`:
  - `services/exchange/base.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/binance/adapter.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `tests/test_phase45_execution_lifecycle.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/pytest -q tests/test_phase45_execution_lifecycle.py -k "retry or private_state or open_positions or hyperliquid or binance or aster"`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`

## v2026.04.16.033

- `recorded_at_utc`: `2026-04-16T18:01:04Z`
- `scope`: `Phase 4.10.1 retry-evidence time-bound and Hyperliquid mark-price truth hotpatch`
- `intent`: `Native entry. Closed the remaining Phase 4.10 review issues without widening scope: Hyperliquid direct open-position parsing no longer emits mark_price=0 when clearinghouseState omits markPx and instead derives from positionValue / abs(szi) only when possible; Aster and Binance same-target retry private-fill checks now pass startTime from SubmittedOrder.submitted_at and defensively ignore pre-submit same-symbol fills while still blocking submitted-at-or-after ambiguity; exact exchange-order-id matches remain order_scoped; and Binance private-trade query failures are now directly covered so retry_same_target blocks before any new SubmittedOrder can be created. No routing, stream framework, target selection, fanout, new exchange, or orchestration action was added.`
- `affected_files`:
  - `services/exchange/hyperliquid/adapter.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/binance/adapter.py`
  - `services/execution/service.py`
  - `tests/test_phase45_execution_lifecycle.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/pytest -q tests/test_phase45_execution_lifecycle.py -k "retry or private_state or open_positions or hyperliquid or binance or aster"`
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_operational_docs.py`

## v2026.04.16.032

- `recorded_at_utc`: `2026-04-16T15:25:15Z`
- `scope`: `Phase 4.10.0 final below-routing retry-evidence truth cleanup and Hyperliquid direct position parity`
- `intent`: `Native entry. Closed the remaining Phase 4.9 truth drift by making Aster/Binance retry private-fill evidence explicitly scope-aware: when a rejected submitted order has no exchange order id, direct private trade evidence is now recorded and surfaced as same-account/same-symbol ambiguity instead of targeted order fill proof, and failed direct fill-evidence queries now block retry rather than proceeding optimistically. Deepened one code/test-proven private-state path by moving Hyperliquid open-position visibility to direct account-targeted clearinghouseState polling where account context exists, while preserving persistence fallback, keeping adapter-level user streams unimplemented, leaving Aster/Binance native amend unsupported, and avoiding routing, target selection, CBBO, fanout, or new exchanges.`
- `affected_files`:
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `services/exchange/base.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/binance/adapter.py`
  - `services/execution/service.py`
  - `tests/test_phase45_execution_lifecycle.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/python -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase45_execution_lifecycle.py -k 'retry or private_state or open_positions or hyperliquid'`
  - `.venv/bin/pytest -q tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_operational_docs.py`

## v2026.04.16.031

- `recorded_at_utc`: `2026-04-15T20:06:12Z`
- `scope`: `Phase 4.9 below-routing private-state parity, scoped Kraken amend, and deeper same-target retry safety`
- `intent`: `Native entry. Deepened the execution substrate below routing without widening into routing by moving Hyperliquid private open-order truth onto direct account-targeted venue query, adding direct private trade checks for Aster and Binance to harden same-target retry safety, broadening native amend parity to Kraken spot limit orders only, exposing per-surface runtime source truth on private-state operator endpoints, and updating docs/repo-memory to describe the narrower code/test-proven six-venue matrix honestly. Phase 4.10.0 later narrowed the Aster/Binance retry-fill wording to same-account/same-symbol ambiguity when no exchange order id exists.`
- `affected_files`:
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `services/exchange/base.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/binance/adapter.py`
  - `services/exchange/kraken/adapter.py`
  - `services/execution/service.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_api.py`
  - `tests/test_phase45_execution_lifecycle.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase45_execution_lifecycle.py -k 'private_state or open_orders or recent_fills or retry or amend or kraken or hyperliquid'`
  - `.venv/bin/pytest -q tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`

## v2026.04.16.030

- `recorded_at_utc`: `2026-04-15T18:51:33Z`
- `scope`: `Phase 4.8.1 private-state truth boundary hotfix`
- `intent`: `Native entry. Corrected the remaining 4.8 boundary-truth issues without widening scope by separating venue-private open-order snapshots from platform SubmittedOrder identity end to end, removing fabricated live-* submitted-order ids from private open-order surfaces, making private-state source/availability fields describe the runtime path actually used for each summary call, narrowing /session-state to explicit adapter/runtime connection bookkeeping, and realigning tests/docs/repo-memory around that sharper below-routing private-state boundary while preserving all accepted 4.7.1 execution behavior and accepted 4.8 private-state depth that remains truthful.`
- `affected_files`:
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `services/exchange/base.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/binance/adapter.py`
  - `services/exchange/coinbase/adapter.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `services/exchange/kraken/adapter.py`
  - `services/exchange/okx/adapter.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_api.py`
  - `tests/test_phase45_execution_lifecycle.py`
  - `tests/test_operational_docs.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_api.py tests/test_phase45_execution_lifecycle.py -k 'private_state or open_orders or recent_fills or session_state or hyperliquid_recent_fills or binance_private_open_orders or okx_recent_fills'`
  - `.venv/bin/pytest -q tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py tests/test_api.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`

## v2026.04.13.029

- `recorded_at_utc`: `2026-04-13T05:40:04Z`
- `scope`: `Phase 4.8 polling-first private-state and deeper venue/account order-state truth below routing`
- `intent`: `Native entry. Deepened the execution substrate below routing by adding explicit polling-first private-state truth surfaces for session state, open orders, recent fills, and open positions; extending direct account-targeted private open-order polling to Aster/Binance/OKX/Coinbase Advanced Trade/Kraken; extending direct recent-fill polling to Hyperliquid/OKX/Coinbase Advanced Trade/Kraken; keeping user-stream parity explicit rather than implied; and tightening tests/docs around the narrower code/test-proven per-venue matrix without adding routing, target reselection, or new execution semantics above SubmittedOrder.`
- `affected_files`:
  - `core/domain/models.py`
  - `core/schemas/api.py`
  - `services/exchange/base.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/binance/adapter.py`
  - `services/exchange/coinbase/adapter.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `services/exchange/kraken/adapter.py`
  - `services/exchange/okx/adapter.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_api.py`
  - `tests/test_phase401_trade_planning.py`
  - `tests/test_phase411_venue_preparation.py`
  - `tests/test_phase41_risk.py`
  - `tests/test_phase42_execution_readiness.py`
  - `tests/test_phase45_execution_lifecycle.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_api.py tests/test_phase45_execution_lifecycle.py`
  - `.venv/bin/pytest -q tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_operational_docs.py`

## v2026.04.13.028

- `recorded_at_utc`: `2026-04-13T04:01:26Z`
- `scope`: `Phase 4.7.1 canonical-doc and repo-memory stale draft-reference cleanup`
- `intent`: `Native entry. Removed the remaining stale references to deleted draft architecture/strategy docs from the canonical docs and repo-memory surfaces, kept the canonical documents self-contained, and added an operational-doc guard so future changes fail if they reintroduce references to nonexistent *_updated.md or *_preserve_refresh.md files.`
- `affected_files`:
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `REPO_TREE.md`
  - `CHANGELOG.md`
  - `tests/test_operational_docs.py`
- `validation_performed`:
  - `.venv/bin/pytest -q tests/test_operational_docs.py`

## v2026.04.13.027

- `recorded_at_utc`: `2026-04-13T01:36:14Z`
- `scope`: `Phase 4.7.1 submitted-order fill-merge truth and cancel-vs-amend capability-surface hotfix`
- `intent`: `Native entry. Fixed the remaining 4.7 review blockers without widening scope by preserving terminal and cancel-pending submitted-order truth when persisted fill evidence is merged into lifecycle updates, correcting Hyperliquid exchange-status and capability surfaces so they report the current proven cancel/amend support truthfully, splitting the misleading public cancel/amend capability surface into explicit cancel and amend fields, and realigning the canonical docs and tests around the narrower code/test-proven post-4.7 boundary.`
- `affected_files`:
  - `core/domain/models.py`
  - `core/schemas/api.py`
  - `services/exchange/base.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/binance/adapter.py`
  - `services/exchange/okx/adapter.py`
  - `services/exchange/coinbase/adapter.py`
  - `services/exchange/kraken/adapter.py`
  - `services/execution/service.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_api.py`
  - `tests/test_phase401_trade_planning.py`
  - `tests/test_phase41_risk.py`
  - `tests/test_phase411_venue_preparation.py`
  - `tests/test_phase42_execution_readiness.py`
  - `tests/test_phase45_execution_lifecycle.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `CHANGELOG.md`
- `validation_performed`:
  - `python3 -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase45_execution_lifecycle.py tests/test_phase44_submission_lifecycle.py tests/test_phase42_execution_readiness.py tests/test_api.py tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_interfaces.py`

## v2026.04.13.026

- `recorded_at_utc`: `2026-04-13T01:04:08Z`
- `scope`: `Canonical docs consolidation for architecture and strategy at current head`
- `intent`: `Native entry. Consolidated the architecture and strategy documentation into one current canonical source of truth for each topic by rewriting docs/architecture.md and docs/strategy.md around the actual 4.7 boundary, removing stale phase-forward wording, and updating repo-memory so future work treated those canonical docs as the only live architecture/strategy references.`
- `affected_files`:
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
- `validation_performed`:
  - `.venv/bin/pytest -q tests/test_operational_docs.py`

## v2026.04.13.025

- `recorded_at_utc`: `2026-04-12T17:21:48Z`
- `scope`: `Phase 4.7 deeper post-submit cancel/amend parity and reconciliation truth below routing`
- `intent`: `Native entry. Extended the post-submit execution layer without crossing into routing by adding truthful Hyperliquid cancel acknowledgement and native limit-order amend for the current perpetual scope, adding native Coinbase Advanced Trade amend for the current spot limit-order scope, tightening Hyperliquid reconciliation so canceled zero-remaining orders no longer misclassify as filled without fill evidence, deepening Aster canceled/expired-after-partial-fill truth and Kraken cancel acknowledgement truth, and broadening recovery/actionability semantics so amend acknowledgement now drives explicit reconcile-now follow-up while docs and repo-memory stay aligned with the narrower code/test-proven venue matrix.`
- `affected_files`:
  - `services/exchange/hyperliquid/adapter.py`
  - `services/exchange/coinbase/adapter.py`
  - `services/exchange/kraken/adapter.py`
  - `services/exchange/okx/adapter.py`
  - `services/exchange/aster/adapter.py`
  - `services/execution/service.py`
  - `tests/test_phase44_submission_lifecycle.py`
  - `tests/test_phase45_execution_lifecycle.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall services/exchange/hyperliquid/adapter.py services/exchange/coinbase/adapter.py services/exchange/kraken/adapter.py services/exchange/okx/adapter.py services/exchange/aster/adapter.py services/execution/service.py tests/test_phase44_submission_lifecycle.py tests/test_phase45_execution_lifecycle.py`
  - `.venv/bin/pytest -q tests/test_phase45_execution_lifecycle.py -k 'hyperliquid or amend or kraken or aster_canceled or recovery_execute_reconciles_amend'`
  - `.venv/bin/pytest -q tests/test_phase45_execution_lifecycle.py tests/test_phase44_submission_lifecycle.py tests/test_api.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`

## v2026.04.09.024

- `recorded_at_utc`: `2026-04-08T20:05:37Z`
- `scope`: `Phase 4.6.1 same-target retry client-order-id truth hotpatch`
- `intent`: `Native entry. Closed the remaining narrow 4.6 execution-truth gap by making same-target retry venue-scoped around strict client-order-id reuse semantics: Aster and Binance now generate a fresh retry client order id instead of silently reusing the original deterministic submission id, existing OKX retry behavior remains intact, retry/account-targeting tests were strengthened accordingly, and docs/repo-memory wording was narrowed to only the recovery parity the code and tests now prove.`
- `affected_files`:
  - `services/exchange/base.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/binance/adapter.py`
  - `services/execution/service.py`
  - `tests/test_phase45_execution_lifecycle.py`
  - `README.md`
  - `docs/architecture.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall services tests`
  - `.venv/bin/pytest -q tests/test_phase45_execution_lifecycle.py -k 'retry'`

## v2026.04.09.023

- `recorded_at_utc`: `2026-04-08T18:21:54Z`
- `scope`: `Phase 4.6 bounded post-submit orchestration, retry safety, and selective amend depth`
- `intent`: `Native entry. Extended the post-submit execution layer without crossing into routing by adding explicit same-target recovery execution on top of the existing recovery recommendations, conservative retry safety checks that block when duplicate exposure cannot be ruled out, native OKX limit-order amend for the current scoped path, expanded lifecycle-event audit history for recovery/amend actions, and matching operator API surfaces/docs while keeping Hyperliquid cancel/amend and broader amend parity explicitly deferred.`
- `affected_files`:
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `services/exchange/base.py`
  - `services/exchange/okx/adapter.py`
  - `services/execution/service.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase45_execution_lifecycle.py`
  - `tests/test_interfaces.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase45_execution_lifecycle.py tests/test_interfaces.py`
  - `.venv/bin/pytest -q tests/test_api.py tests/test_phase44_submission_lifecycle.py tests/test_phase43_submission.py tests/test_phase42_execution_readiness.py tests/test_config.py tests/test_operational_docs.py`

## v2026.04.08.022

- `recorded_at_utc`: `2026-04-08T13:34:27Z`
- `scope`: `Phase 4.5.1 review-bundle hygiene enforcement`
- `intent`: `Native entry. Finished the remaining 4.5.1 archive-hygiene condition by adding a deterministic review-bundle creation script that reads .archiveignore, prunes ignored local-artifact trees during the walk, and produces a real ZIP whose contents are now test-verified to exclude local developer artifacts such as .env, .venv, .pgdata, .pgsocket, .pytest_cache, .DS_Store, and __MACOSX without touching any execution logic.`
- `affected_files`:
  - `scripts/create_review_bundle.py`
  - `.archiveignore`
  - `tests/test_operational_docs.py`
  - `README.md`
  - `REPO_TREE.md`
  - `CHANGELOG.md`
- `validation_performed`:
  - `.venv/bin/pytest -q tests/test_operational_docs.py`
  - `python3 -m compileall scripts tests`

## v2026.04.08.021

- `recorded_at_utc`: `2026-04-08T12:09:00Z`
- `scope`: `Phase 4.5.1 cancel lifecycle truth hotfix`
- `intent`: `Native entry. Corrected the narrow cancel-lifecycle overclaim from Phase 4.5 by introducing explicit intermediate submitted-order states for cancel request and cancel acknowledgement, making OKX and Coinbase Advanced Trade cancellation success remain non-terminal until later reconciliation confirms final canceled state, persisting lifecycle events for those stages, and realigning docs/archive hygiene notes with the corrected post-submit truth without broadening scope into routing, fanout, amend execution, or orchestration.`
- `affected_files`:
  - `core/domain/enums.py`
  - `services/exchange/base.py`
  - `services/exchange/okx/adapter.py`
  - `services/exchange/coinbase/adapter.py`
  - `services/execution/service.py`
  - `db/migrations/versions/20260408_0016_phase451_cancel_lifecycle_truth.py`
  - `tests/test_phase45_execution_lifecycle.py`
  - `tests/test_operational_docs.py`
  - `.archiveignore`
  - `README.md`
  - `docs/architecture.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
- `validation_performed`:
  - `python3 -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase45_execution_lifecycle.py`
  - `.venv/bin/pytest -q tests/test_phase45_execution_lifecycle.py tests/test_phase44_submission_lifecycle.py tests/test_api.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`
  - `/bin/zsh -lc "TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py"`

## v2026.04.08.020

- `recorded_at_utc`: `2026-04-08T06:18:00Z`
- `scope`: `Phase 4.5 deeper submitted-order lifecycle parity, recovery guidance, live cancel, and hygiene hardening`
- `intent`: `Native entry. Extended the post-submit execution layer by adding venue-by-venue reconciliation beyond the existing Hyperliquid-first path, explicit submitted-order recovery recommendations, truthful live cancel execution for the currently supportable HTTP venues while keeping Hyperliquid cancel explicitly blocked, operator-facing recovery/actionability/cancel APIs, hermetic pytest isolation from workspace .env files, and review/archive hygiene via a dedicated .archiveignore surface without broadening scope into routing, mandate-scoped open target selection, or broad amend execution claims.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `services/exchange/base.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/okx/adapter.py`
  - `services/exchange/coinbase/adapter.py`
  - `services/exchange/binance/adapter.py`
  - `services/exchange/kraken/adapter.py`
  - `services/execution/service.py`
  - `apps/api/app/api/routes.py`
  - `tests/conftest.py`
  - `tests/test_phase3_strategy.py`
  - `tests/test_phase45_execution_lifecycle.py`
  - `tests/test_interfaces.py`
  - `tests/test_config.py`
  - `tests/test_operational_docs.py`
  - `.archiveignore`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase45_execution_lifecycle.py tests/test_phase44_submission_lifecycle.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_phase45_execution_lifecycle.py tests/test_phase44_submission_lifecycle.py tests/test_phase43_submission.py tests/test_phase431_submission_truth.py tests/test_phase42_execution_readiness.py tests/test_phase411_venue_preparation.py tests/test_phase4a_venues.py tests/test_api.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`

## v2026.04.08.019

- `recorded_at_utc`: `2026-04-07T19:56:29Z`
- `scope`: `Phase 4.4.1 narrow submitted-order lifecycle truth fixes`
- `intent`: `Native entry. Corrected the remaining 4.4 lifecycle blockers by making Hyperliquid reconciliation combine open-order truth with fill truth before finalizing status, aligning immediate venue rejection so child intents no longer remain submitted when the venue rejected at submit time, tightening lifecycle-event coverage around those cases, and updating operator docs to describe the corrected execution-lifecycle truth without broadening scope into routing or cancel/amend behavior.`
- `affected_files`:
  - `services/exchange/base.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `services/execution/service.py`
  - `tests/test_phase44_submission_lifecycle.py`
  - `README.md`
  - `docs/architecture.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase44_submission_lifecycle.py`
  - `.venv/bin/pytest -q tests/test_phase43_submission.py tests/test_phase431_submission_truth.py tests/test_phase42_execution_readiness.py tests/test_phase44_submission_lifecycle.py tests/test_api.py tests/test_interfaces.py tests/test_operational_docs.py`

## v2026.04.08.018

- `recorded_at_utc`: `2026-04-07T18:34:35Z`
- `scope`: `Phase 4.4 submitted-order lifecycle, reconciliation, and cancel/amend groundwork`
- `intent`: `Native entry. Added the first real post-submit execution lifecycle above the existing truthful submit boundary by extending submitted-order state with explicit reconciliation status and lifecycle rollups, persisting submitted-order lifecycle events for auditability, wiring execution-service reconciliation and single-target post-submit orchestration, adding the first Hyperliquid venue-truth reconciliation path plus honest lifecycle-unavailable handling for thinner venues, exposing submitted-order lifecycle inspection APIs, and updating docs/tests to describe the new 4.4 boundary without implying routing or live cancel/amend behavior.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `db/models/trading.py`
  - `db/models/__init__.py`
  - `db/migrations/versions/20260408_0015_phase44_post_submit_lifecycle.py`
  - `services/exchange/base.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `services/execution/service.py`
  - `services/portfolio/service.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_interfaces.py`
  - `tests/test_phase44_submission_lifecycle.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase43_submission.py tests/test_phase431_submission_truth.py tests/test_phase44_submission_lifecycle.py tests/test_api.py tests/test_interfaces.py`
  - `.venv/bin/pytest -q tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_phase43_submission.py tests/test_phase431_submission_truth.py tests/test_phase44_submission_lifecycle.py tests/test_phase4a_venues.py tests/test_phase41_risk.py tests/test_phase401_trade_planning.py tests/test_api.py tests/test_interfaces.py tests/test_config.py tests/test_operational_docs.py`

## v2026.04.07.017

- `recorded_at_utc`: `2026-04-07T16:50:46Z`
- `scope`: `Phase 4.3.3 exact submit-body fidelity and final execution-truth cleanup`
- `intent`: `Native entry. Closed the remaining narrow execution-truth gap by adding exact JSON/form submission helpers so the signed payload representation and transmitted payload representation match for the claimed venue submit scopes, tightening submission-truth tests around raw transmitted bodies and same-venue account targeting, and narrowing docs/capability wording to code/test-proven submit-path truth without implying broader live-validation than the repo actually has.`
- `affected_files`:
  - `services/exchange/base.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/binance/adapter.py`
  - `services/exchange/okx/adapter.py`
  - `services/exchange/coinbase/adapter.py`
  - `services/exchange/kraken/adapter.py`
  - `tests/test_phase43_submission.py`
  - `tests/test_phase431_submission_truth.py`
  - `README.md`
  - `docs/architecture.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `.venv/bin/pytest -q tests/test_phase431_submission_truth.py tests/test_phase43_submission.py`
  - `python3 -m compileall services tests core`
  - `.venv/bin/pytest -q tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_phase43_submission.py tests/test_phase431_submission_truth.py tests/test_phase4a_venues.py tests/test_config.py tests/test_api.py tests/test_interfaces.py tests/test_operational_docs.py`

## v2026.04.07.016

- `recorded_at_utc`: `2026-04-07T10:13:16Z`
- `scope`: `Phase 4.3.2 execution-truth fixes and scoped auth/account-targeting hardening`
- `intent`: `Native entry. Corrected the remaining 4.3.1 execution-truth gaps by making credential resolution explicit instead of treating reference labels as raw secret material, fixing Coinbase Advanced Trade to use the documented JWT bearer auth model, moving Hyperliquid to an SDK-faithful L1 signing flow, tightening Aster/OKX/Binance/Kraken account-targeted signing and account-snapshot behavior, adding stronger auth/signing/account-targeting tests, and realigning docs/config guidance with the actual submission boundary at head.`
- `affected_files`:
  - `core/config/settings.py`
  - `services/exchange/base.py`
  - `services/exchange/coinbase/jwt_auth.py`
  - `services/exchange/coinbase/adapter.py`
  - `services/exchange/hyperliquid/signing.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/okx/adapter.py`
  - `services/exchange/binance/adapter.py`
  - `services/exchange/kraken/adapter.py`
  - `pyproject.toml`
  - `tests/test_phase411_venue_preparation.py`
  - `tests/test_phase43_submission.py`
  - `tests/test_phase431_submission_truth.py`
  - `tests/test_phase4a_venues.py`
  - `.env.example`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall services tests core`
  - `.venv/bin/pytest -q tests/test_phase431_submission_truth.py tests/test_phase43_submission.py tests/test_phase4a_venues.py tests/test_config.py`
  - `.venv/bin/pytest -q tests/test_phase42_execution_readiness.py tests/test_phase411_venue_preparation.py tests/test_api.py tests/test_interfaces.py tests/test_operational_docs.py tests/test_phase431_submission_truth.py tests/test_phase43_submission.py tests/test_phase4a_venues.py tests/test_config.py`

## v2026.04.07.015

- `recorded_at_utc`: `2026-04-07T07:46:11Z`
- `scope`: `Phase 4.3.1 truthful account-targeted submission and Binance/Kraken maturity`
- `intent`: `Native entry. Corrected the overclaimed 4.3 submission boundary by moving submit-path truth into venue-specific authenticated adapters, making submission resolve the targeted VenueAccount instead of a venue-global integration account, adding Binance and Kraken to the current execution-preparable maturity branch with scoped preview/preflight and submit support, and realigning tests/docs with code reality.`
- `affected_files`:
  - `core/config/settings.py`
  - `services/exchange/base.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/okx/adapter.py`
  - `services/exchange/coinbase/adapter.py`
  - `services/exchange/registry.py`
  - `services/exchange/binance/__init__.py`
  - `services/exchange/binance/adapter.py`
  - `services/exchange/kraken/__init__.py`
  - `services/exchange/kraken/adapter.py`
  - `tests/test_config.py`
  - `tests/test_phase4a_venues.py`
  - `tests/test_phase43_submission.py`
  - `tests/test_phase431_submission_truth.py`
  - `.env.example`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall core services tests`
  - `.venv/bin/pytest -q tests/test_phase431_submission_truth.py tests/test_phase43_submission.py tests/test_phase42_execution_readiness.py tests/test_phase4a_venues.py tests/test_config.py`
  - `.venv/bin/pytest -q tests/test_config.py tests/test_interfaces.py tests/test_api.py tests/test_phase4a_venues.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_phase43_submission.py tests/test_phase431_submission_truth.py tests/test_operational_docs.py`

## v2026.04.07.014

- `recorded_at_utc`: `2026-04-06T20:25:57Z`
- `scope`: `Phase 4.3 live-submission path and submitted-order truth`
- `intent`: `Native entry. Added the first explicit live-submission transition from prepared child intent to persisted submitted-order truth, implemented real submit-order adapter paths for the current venue set, added per-venue submission enablement controls, widened execution/API surfaces for submitted orders, and preserved the readiness gate as the mandatory precondition to any submission attempt.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/config/settings.py`
  - `core/schemas/api.py`
  - `db/migrations/versions/20260407_0014_phase43_submission_lifecycle.py`
  - `services/exchange/base.py`
  - `services/exchange/registry.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/okx/adapter.py`
  - `services/exchange/coinbase/adapter.py`
  - `services/execution/service.py`
  - `services/portfolio/service.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase43_submission.py`
  - `tests/test_phase4a_venues.py`
  - `tests/test_interfaces.py`
  - `tests/test_config.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `.env.example`
- `validation_performed`:
  - `python3 -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase43_submission.py tests/test_phase4a_venues.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_interfaces.py tests/test_config.py tests/test_api.py`

## v2026.04.03.001

- `recorded_at_utc`: `2026-04-03T19:10:00Z`
- `scope`: `Phase 1 scaffold`
- `intent`: `Reconstructed entry. Established the initial production-minded scaffold for a Hyperliquid-first multi-strategy trading platform.`
- `affected_files`:
  - `README.md`
  - `docs/architecture.md`
  - `apps/api/`
  - `core/`
  - `db/`
  - `services/`
  - `tests/`
- `validation_performed`:
  - `Reconstructed from repo structure and later phase documentation. No original phase-time changelog entry existed.`

## v2026.04.03.002

- `recorded_at_utc`: `2026-04-03T19:11:00Z`
- `scope`: `Phase 1.1 cleanup`
- `intent`: `Reconstructed entry. Hardened Phase 1 documentation, config, Hyperliquid contract coverage, and smoke validation.`
- `affected_files`:
  - `README.md`
  - `docs/architecture.md`
  - `core/config/settings.py`
  - `core/interfaces/hyperliquid.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `tests/test_api.py`
  - `tests/test_config.py`
  - `tests/test_interfaces.py`
  - `tests/test_migrations.py`
- `validation_performed`:
  - `Reconstructed from repo state and prior phase summaries.`

## v2026.04.03.003

- `recorded_at_utc`: `2026-04-03T19:12:00Z`
- `scope`: `Phase 2 exchange/data/state foundation`
- `intent`: `Reconstructed entry. Added Hyperliquid exchange integration boundaries, market-data ingestion foundation, reconciliation, persistence wiring, and operator endpoints.`
- `affected_files`:
  - `services/exchange/hyperliquid/adapter.py`
  - `services/market_data/service.py`
  - `services/portfolio/service.py`
  - `db/models/trading.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_phase2_services.py`
- `validation_performed`:
  - `Reconstructed from implemented code and Phase 2 handoff summary.`

## v2026.04.03.004

- `recorded_at_utc`: `2026-04-03T19:13:00Z`
- `scope`: `Phase 2.1 hardening`
- `intent`: `Reconstructed entry. Hardened instrument normalization, venue readiness, checkpoint semantics, exchange truth vs attribution separation, and execution-quality data foundations.`
- `affected_files`:
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `db/models/trading.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `services/market_data/service.py`
  - `services/portfolio/service.py`
  - `db/migrations/versions/20260402_0003_phase21_hardening.py`
- `validation_performed`:
  - `Reconstructed from repo state and prior phase documentation.`

## v2026.04.03.005

- `recorded_at_utc`: `2026-04-03T19:14:00Z`
- `scope`: `Phase 3 indicator and strategy layer`
- `intent`: `Reconstructed entry. Added deterministic indicator computation, persisted indicator snapshots, the modular strategy framework, and Money Flow sleeves for 15m/1h/4h.`
- `affected_files`:
  - `services/indicators/service.py`
  - `services/strategy/base.py`
  - `services/strategy/engine.py`
  - `services/strategy/money_flow.py`
  - `docs/strategy.md`
  - `tests/test_phase3_strategy.py`
- `validation_performed`:
  - `Reconstructed from implemented code and prior phase summary.`

## v2026.04.03.006

- `recorded_at_utc`: `2026-04-03T19:15:00Z`
- `scope`: `Phase 3.1 strategy hardening`
- `intent`: `Reconstructed entry. Hardened instrument identity semantics, stale-indicator rejection, decision idempotency, Money Flow exit logic, portfolio summary semantics, and builder-asset policy.`
- `affected_files`:
  - `core/domain/models.py`
  - `core/config/settings.py`
  - `db/models/trading.py`
  - `db/migrations/versions/20260403_0005_phase31_strategy_hardening.py`
  - `services/strategy/engine.py`
  - `services/strategy/money_flow.py`
  - `services/portfolio/service.py`
  - `tests/test_phase2_services.py`
  - `tests/test_phase3_strategy.py`
- `validation_performed`:
  - `Reconstructed from implemented code and Phase 3.1 completion summary.`

## v2026.04.03.007

- `recorded_at_utc`: `2026-04-03T19:16:00Z`
- `scope`: `Phase 3.2 documentation governance`
- `intent`: `Native entry. Added operational-memory docs, standardized changelog governance, required startup/shutdown doc workflow, and lightweight validation for documentation presence and references.`
- `affected_files`:
  - `AGENTS.md`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `tests/test_operational_docs.py`
- `validation_performed`:
  - `python3 -m compileall tests`
  - `.venv/bin/pytest -q tests/test_operational_docs.py`

## v2026.04.04.008

- `recorded_at_utc`: `2026-04-04T07:08:00Z`
- `scope`: `Phase 3.3 client/account/deployment hierarchy hardening`
- `intent`: `Native entry. Replaced the remaining single-account assumptions with first-class client, venue account, strategy deployment, and deployment-scoped sleeve configuration models; wired the active deployment context through portfolio, strategy, API, and migration/backfill paths so Phase 4 can operate on account/deployment-scoped state.`
- `affected_files`:
  - `core/config/settings.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `db/models/trading.py`
  - `db/models/__init__.py`
  - `db/migrations/versions/20260404_0006_phase33_client_account_deployment.py`
  - `services/runtime/context.py`
  - `services/portfolio/service.py`
  - `services/strategy/engine.py`
  - `services/strategy/money_flow.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `apps/api/app/dependencies.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_config.py`
  - `tests/test_api.py`
  - `tests/test_phase3_strategy.py`
  - `tests/test_phase33_hierarchy.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `.env.example`
- `validation_performed`:
  - `python3 -m compileall apps core db services tests`
  - `.venv/bin/pytest -q`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase33 .venv/bin/pytest -q tests/test_migrations.py`

## v2026.04.05.009

- `recorded_at_utc`: `2026-04-05T03:55:00Z`
- `scope`: `Phase 3.4 mandate hierarchy refactor`
- `intent`: `Native entry. Replaced the deployment-top runtime model with a mandate-top hierarchy so one logical strategy umbrella can span many venue accounts through bindings, while keeping VenueAccount as the exchange-truth boundary and preparing Phase 4 for mandate/binding-scoped risk and intents.`
- `affected_files`:
  - `core/config/settings.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `db/models/trading.py`
  - `db/models/__init__.py`
  - `db/migrations/versions/20260405_0007_phase34_mandate_hierarchy.py`
  - `services/runtime/context.py`
  - `services/strategy/engine.py`
  - `services/strategy/money_flow.py`
  - `services/portfolio/service.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `apps/api/app/api/routes.py`
  - `.env.example`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `tests/test_api.py`
  - `tests/test_config.py`
  - `tests/test_phase34_mandates.py`
- `validation_performed`:
  - `python3 -m compileall apps core db services tests`
  - `.venv/bin/pytest -q tests/test_interfaces.py tests/test_phase2_services.py tests/test_config.py tests/test_api.py tests/test_phase3_strategy.py tests/test_phase34_mandates.py tests/test_operational_docs.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`

## v2026.04.05.010

- `recorded_at_utc`: `2026-04-05T11:45:00Z`
- `scope`: `Phase 3.5 mandate hierarchy cleanup and consolidation`
- `intent`: `Native entry. Removed active deployment-era baggage from the mandate/binding/component model, dropped legacy deployment tables and columns from the active schema, removed the deployment-key runtime fallback, tightened tests around many-mandates-per-client and reusable accounts, and updated repo/docs language to describe the platform as signal generation plus future routing/execution preparation.`
- `affected_files`:
  - `core/config/settings.py`
  - `db/models/trading.py`
  - `db/models/__init__.py`
  - `db/migrations/versions/20260405_0008_phase35_cleanup_legacy_deployments.py`
  - `services/strategy/engine.py`
  - `apps/api/app/dependencies.py`
  - `tests/test_config.py`
  - `tests/test_phase3_strategy.py`
  - `tests/test_phase34_mandates.py`
  - `tests/test_phase35_cleanup.py`
  - `.gitignore`
  - `.env.example`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall apps core db services tests`
  - `.venv/bin/pytest -q tests/test_config.py tests/test_api.py tests/test_phase3_strategy.py tests/test_phase34_mandates.py tests/test_phase35_cleanup.py tests/test_operational_docs.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`

## v2026.04.05.011

- `recorded_at_utc`: `2026-04-05T15:50:00Z`
- `scope`: `Phase 4A multi-venue read-only adapter hardening`
- `intent`: `Native entry. Added first-class read-only / QA adapters for Aster, OKX, and Coinbase Advanced Trade, introduced a venue registry and multi-venue QA inspection endpoints, widened the shared capability/status/account-connectivity model, and fixed the symbol uniqueness model so one venue can carry multiple product mappings for the same canonical asset.`
- `affected_files`:
  - `core/config/settings.py`
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `services/exchange/base.py`
  - `services/exchange/common.py`
  - `services/exchange/registry.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/okx/adapter.py`
  - `services/exchange/coinbase/adapter.py`
  - `apps/api/app/dependencies.py`
  - `apps/api/app/api/routes.py`
  - `db/models/trading.py`
  - `db/migrations/versions/20260405_0009_phase4a_symbol_uniqueness.py`
  - `.env.example`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
  - `tests/test_config.py`
  - `tests/test_api.py`
  - `tests/test_phase4a_venues.py`
- `validation_performed`:
  - `python3 -m compileall apps core db services tests`
  - `.venv/bin/pytest -q tests/test_config.py tests/test_api.py tests/test_phase2_services.py tests/test_phase3_strategy.py tests/test_phase34_mandates.py tests/test_phase35_cleanup.py tests/test_phase4a_venues.py tests/test_operational_docs.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`

## v2026.04.05.012

- `recorded_at_utc`: `2026-04-05T16:59:53Z`
- `scope`: `Phase 4.0.1 mandate desired-trade and routing-candidate boundary`
- `intent`: `Native entry. Added the mandate-level desired-trade boundary above downstream child intents, introduced derived routing-candidate and normalized quote inspection models/services, clarified `OrderIntent` as the future binding/account-targeted child-intent object, and added planning inspection endpoints so Phase 4B can build risk approval on the correct architectural split.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `db/models/trading.py`
  - `db/models/__init__.py`
  - `db/migrations/versions/20260405_0010_phase401_mandate_desired_trade_boundary.py`
  - `services/planning/service.py`
  - `services/execution/service.py`
  - `apps/api/app/dependencies.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_api.py`
  - `tests/test_phase401_trade_planning.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall apps core db services tests`
  - `.venv/bin/pytest -q tests/test_api.py tests/test_phase401_trade_planning.py tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_config.py tests/test_phase3_strategy.py tests/test_phase34_mandates.py tests/test_phase35_cleanup.py tests/test_phase4a_venues.py tests/test_interfaces.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`

## v2026.04.05.013

- `recorded_at_utc`: `2026-04-05T19:38:42Z`
- `scope`: `Phase 4.0.2 source-policy and desired-trade boundary hardening`
- `intent`: `Native entry. Added first-class mandate market-data source policy, hardened mandate desired-trade aggregation/idempotency and convertibility rules, refactored shared risk/execution interfaces off the old direct decision->intent teaching path, tightened planning around canonical instrument identity, and updated the docs to describe the explicit split between planning/source venue, desired trades, routing candidates, and future child intents.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/config/settings.py`
  - `core/schemas/api.py`
  - `db/models/trading.py`
  - `db/models/__init__.py`
  - `db/migrations/versions/20260406_0011_phase402_source_policy_and_trade_aggregation.py`
  - `services/runtime/context.py`
  - `services/planning/service.py`
  - `services/strategy/engine.py`
  - `services/strategy/money_flow.py`
  - `services/risk/engine.py`
  - `services/execution/service.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_config.py`
  - `tests/test_interfaces.py`
  - `tests/test_api.py`
  - `tests/test_phase401_trade_planning.py`
  - `.env.example`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall apps core db services tests`
  - `.venv/bin/pytest -q tests/test_config.py tests/test_interfaces.py tests/test_api.py tests/test_phase2_services.py tests/test_phase3_strategy.py tests/test_phase34_mandates.py tests/test_phase35_cleanup.py tests/test_phase4a_venues.py tests/test_phase401_trade_planning.py tests/test_operational_docs.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`

## v2026.04.06.014

- `recorded_at_utc`: `2026-04-06T10:49:23Z`
- `scope`: `Phase 4.1 risk evaluation, desired-trade approval, and selective child-intent preparation`
- `intent`: `Native entry. Added the first real risk-evaluation layer over persisted strategy decisions using convertibility and mandate source-policy context, introduced explicit approved/rejected/routing-required desired-trade lifecycle handling, created binding/account-targeted child intents only for naturally binding-scoped actions when the target is already known, and updated the docs/API around the desired-trade-first architecture.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/config/settings.py`
  - `core/schemas/api.py`
  - `services/planning/service.py`
  - `services/risk/engine.py`
  - `services/execution/service.py`
  - `apps/api/app/dependencies.py`
  - `apps/api/app/api/routes.py`
  - `db/models/trading.py`
  - `db/models/__init__.py`
  - `db/migrations/versions/20260406_0012_phase41_risk_approval_and_child_intents.py`
  - `tests/test_interfaces.py`
  - `tests/test_api.py`
  - `tests/test_phase41_risk.py`
  - `.env.example`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall apps core db services tests`
  - `.venv/bin/pytest -q tests/test_interfaces.py tests/test_api.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py`
  - `.venv/bin/pytest -q tests/test_config.py tests/test_interfaces.py tests/test_api.py tests/test_phase2_services.py tests/test_phase3_strategy.py tests/test_phase34_mandates.py tests/test_phase35_cleanup.py tests/test_phase4a_venues.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_operational_docs.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`

## v2026.04.06.015

- `recorded_at_utc`: `2026-04-06T13:56:49Z`
- `scope`: `Phase 4.1.1 venue maturity and prepared-order preflight hardening`
- `intent`: `Native entry. Matured Hyperliquid, Aster, OKX, and Coinbase Advanced Trade from weak QA-only posture into explicit execution-preparable integrations for this phase, added venue-native prepared-order preview/preflight below child intents, widened venue capability and private-state inspection truth, and updated the docs to distinguish prepared from submission-ready while keeping future new venues free to remain qa_read_only.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/schemas/api.py`
  - `services/exchange/base.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/okx/adapter.py`
  - `services/exchange/coinbase/adapter.py`
  - `services/exchange/registry.py`
  - `services/planning/service.py`
  - `services/execution/service.py`
  - `services/risk/engine.py`
  - `apps/api/app/dependencies.py`
  - `apps/api/app/api/routes.py`
  - `tests/test_interfaces.py`
  - `tests/test_phase4a_venues.py`
  - `tests/test_phase401_trade_planning.py`
  - `tests/test_phase41_risk.py`
  - `tests/test_phase411_venue_preparation.py`
  - `tests/test_api.py`
  - `tests/test_config.py`
  - `.env.example`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase411_venue_preparation.py tests/test_phase4a_venues.py tests/test_phase41_risk.py tests/test_api.py tests/test_interfaces.py tests/test_phase401_trade_planning.py tests/test_config.py`
  - `.venv/bin/pytest -q tests/test_interfaces.py tests/test_phase4a_venues.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_api.py tests/test_config.py tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_config.py tests/test_interfaces.py tests/test_api.py tests/test_phase2_services.py tests/test_phase3_strategy.py tests/test_phase34_mandates.py tests/test_phase35_cleanup.py tests/test_phase4a_venues.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_operational_docs.py`
  - `No Alembic migration added. Prepared-order previews remain derived/ephemeral in Phase 4.1.1.`

## v2026.04.06.016

- `recorded_at_utc`: `2026-04-06T16:46:09Z`
- `scope`: `Phase 4.2 execution-readiness gating above prepared child intents`
- `intent`: `Native entry. Added a first-class persisted execution-readiness assessment above prepared child intents, separated venue semantic support from adapter submission implementation and environment/account authorization truth, exposed readiness inspection endpoints, and updated the repo/docs to distinguish prepared child intents from submission-eligible or phase-blocked intents without enabling live submission.`
- `affected_files`:
  - `core/domain/enums.py`
  - `core/domain/models.py`
  - `core/interfaces/services.py`
  - `core/config/settings.py`
  - `core/schemas/api.py`
  - `services/exchange/base.py`
  - `services/exchange/registry.py`
  - `services/exchange/hyperliquid/adapter.py`
  - `services/exchange/aster/adapter.py`
  - `services/exchange/okx/adapter.py`
  - `services/exchange/coinbase/adapter.py`
  - `services/planning/service.py`
  - `services/execution/service.py`
  - `apps/api/app/api/routes.py`
  - `db/models/trading.py`
  - `db/models/__init__.py`
  - `db/migrations/versions/20260406_0013_phase42_execution_readiness_gate.py`
  - `tests/test_interfaces.py`
  - `tests/test_config.py`
  - `tests/test_api.py`
  - `tests/test_phase4a_venues.py`
  - `tests/test_phase401_trade_planning.py`
  - `tests/test_phase41_risk.py`
  - `tests/test_phase411_venue_preparation.py`
  - `tests/test_phase42_execution_readiness.py`
  - `.env.example`
  - `README.md`
  - `docs/architecture.md`
  - `docs/strategy.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall core services apps tests`
  - `.venv/bin/pytest -q tests/test_phase42_execution_readiness.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase401_trade_planning.py tests/test_api.py tests/test_config.py tests/test_interfaces.py`
  - `.venv/bin/pytest -q tests/test_config.py tests/test_interfaces.py tests/test_api.py tests/test_phase2_services.py tests/test_phase3_strategy.py tests/test_phase34_mandates.py tests/test_phase35_cleanup.py tests/test_phase4a_venues.py tests/test_phase401_trade_planning.py tests/test_phase41_risk.py tests/test_phase411_venue_preparation.py tests/test_phase42_execution_readiness.py tests/test_operational_docs.py`
  - `TEST_DATABASE_URL=postgresql+psycopg://tercirafael@127.0.0.1:55432/money_flow_phase34 .venv/bin/pytest -q tests/test_migrations.py`

## v2026.04.06.017

- `recorded_at_utc`: `2026-04-06T19:30:23Z`
- `scope`: `Phase 4.2.1 execution-readiness semantic hardening and strategic-memory governance`
- `intent`: `Native entry. Corrected readiness handling so `live_enabled` support advances beyond venue-level gating, enforced binding/account active-state policy in readiness evaluation, tightened the capability-vs-adapter-vs-authorization-vs-phase test matrix, and added `money_flow_project_memory.md` as required read-only pre-task strategic context in repo governance.`
- `affected_files`:
  - `services/execution/service.py`
  - `tests/test_phase42_execution_readiness.py`
  - `tests/test_operational_docs.py`
  - `AGENTS.md`
  - `README.md`
  - `REPO_TREE.md`
  - `KNOWN_ISSUES.md`
  - `TODO.md`
- `validation_performed`:
  - `python3 -m compileall services tests`
  - `.venv/bin/pytest -q tests/test_phase42_execution_readiness.py tests/test_operational_docs.py`
  - `.venv/bin/pytest -q tests/test_api.py tests/test_config.py tests/test_interfaces.py tests/test_phase411_venue_preparation.py tests/test_phase41_risk.py tests/test_phase401_trade_planning.py tests/test_phase42_execution_readiness.py tests/test_operational_docs.py`
