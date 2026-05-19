# SUBAGENTS1 Money Flow Codex Workflow

## Executive Summary

SUBAGENTS1 adds three project-scoped Codex subagents under `.codex/agents/`:

- `runtime_reviewer`
- `dashboard_reviewer`
- `quant_reviewer`

This is a workflow/governance phase. It changes no strategy code, runtime behavior, dashboard behavior, evidence packs, exchange endpoints, testnet transport policy, live trading approval, or production approval.

## Why Subagents Were Added

Money Flow has grown into a system with separate runtime, dashboard, and quant-review concerns. A single builder session can miss review-specific details, especially during active PT-RT paper observation. The new subagents give the founder and future Codex sessions focused reviewers that can inspect artifacts and return bounded findings before the main session changes anything.

## Agent Files Created

- `.codex/agents/runtime_reviewer.toml`
- `.codex/agents/dashboard_reviewer.toml`
- `.codex/agents/quant_reviewer.toml`
- `.codex/config.toml`

## Agent Responsibilities

| agent | responsibility |
| --- | --- |
| `runtime_reviewer` | PT-RT runtime safety, candle-close scheduling, warm-start gating, duplicate prevention, synthetic ledger invariants, MTM, data health, and testnet lifecycle separation. |
| `dashboard_reviewer` | Founder dashboard clarity, tab taxonomy, active vs archived rows, markers, stale labels, misleading metrics, and testnet/synthetic-PnL separation. |
| `quant_reviewer` | Paper-trade quality, lane comparison, late entries, RSI-cooldown/impulse entries, no-trade reasons, symbol/timeframe concentration, and hypotheses for later evidence testing. |

## Read-Only Default Policy

Each agent file uses `sandbox_mode = "read-only"` and developer instructions stating the agent is read-only unless the parent explicitly asks for a patch. These first three agents are intended for review/triage, not parallel write-heavy implementation.

If a local Codex version does not support project-local `sandbox_mode = "read-only"`, the instructions still state the read-only policy and tests validate that the policy text remains present.

## Current Money Flow Boundaries Embedded

- Current surface: `Paper Trading`.
- Current runtime: PT-RT1.5.x / PT-RT1.5.3 current truth.
- Active paper timeframes: `1h`, `4h`, `1d`.
- Paused timeframe: `15m`.
- Strategy truth: public Hyperliquid mainnet candles.
- Synthetic PnL truth: internal paper ledgers.
- Testnet transport: Hyperliquid testnet only, Money Flow v1.2 baseline only, fixed 25 USDC, gated.
- Candidate / MF-ORIG / wildcard lanes: synthetic-only.
- Testnet fills do not update synthetic PnL.
- Live trading is not approved.
- No strategy is production-approved.

## How To Invoke Subagents

Use the project agent names in a main Codex prompt, for example:

```text
Spawn runtime_reviewer, dashboard_reviewer, and quant_reviewer.
Review the current PT-RT artifacts and dashboard state.
Stay read-only and return findings with exact files inspected.
```

Detailed prompts live in `docs/codex_subagents_money_flow_workflow.md`.

## How To Avoid Parallel Write Conflicts

- Keep subagents read-only by default.
- Do not use them for broad implementation unless a later phase explicitly changes their role.
- Add or update a row in `money-flow/05_Agent_Coordination.md` before substantial parent-session edits.
- If future write-capable workers are added, assign disjoint file ownership and make each worker list touched files.

## Validation Run

SUBAGENTS1 validation:

- `.venv/bin/python -m json.tool docs/subagents1_money_flow_codex_workflow_summary.json`: passed.
- `.venv/bin/python -m pytest -q tests/test_codex_subagents.py`: 5 passed.
- `.venv/bin/python -m pytest -q tests/test_operational_docs.py`: 19 passed.
- `.venv/bin/python -m compileall core services apps tests scripts`: passed.
- `git diff --check`: passed.
- `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py`: 1083 passed, 1 failed.
- `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-subagents1-review.zip`: created review bundle.
- Review bundle excluded-path scan: passed.
- Review bundle private-key/Bearer-token pattern scan: passed.

The full non-migration residual is outside SUBAGENTS1 scope: `tests/test_pt_rt1_5_week1_reset_scheduler_transport.py::test_pt_rt1_5_summary_policy_and_runner_command_are_boundary_labeled` expects the stale `pt_rt1_5_week1_active` dashboard string. SUBAGENTS1 does not change dashboard runtime behavior, so this phase records the residual rather than modifying PT-RT dashboard tests.

Review bundle: `/Users/tercirafael/money-flow-subagents1-review.zip`

## Remaining Follow-Up

- Use the three reviewers during the next runtime/dashboard/quant triage.
- Keep the first three subagents read-only until the founder explicitly scopes write-capable builder agents.
- If Codex project-local agent syntax changes, update tests and this workflow doc rather than silently weakening the guardrails.
