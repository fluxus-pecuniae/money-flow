# Codex Subagents Money Flow Workflow

## Purpose

Money Flow now has three project-scoped Codex subagents for bounded read-only review work:

- `runtime_reviewer`
- `dashboard_reviewer`
- `quant_reviewer`

They separate runtime safety review, founder dashboard review, and quantitative signal-quality review from the main builder session. They are helpers for triage and synthesis, not independent implementers by default.

## Why Subagents Were Added

The project has several review surfaces that benefit from different lenses:

- PT-RT runtime artifacts need safety, scheduling, ledger, and testnet-boundary review.
- The dashboard needs founder-readable UX review without changing the research meaning.
- Paper trades and lane results need quant interpretation without approving a production strategy.

Subagents make those reviews more focused while keeping the main session responsible for coordination, edits, validation, and final handoff.

## Available Subagents

| subagent | default mode | use when |
| --- | --- | --- |
| `runtime_reviewer` | read-only | Reviewing PT-RT runtime artifacts, candle-close scheduling, warm-start gates, duplicate prevention, synthetic ledgers, MTM, data health, and testnet lifecycle separation. |
| `dashboard_reviewer` | read-only | Reviewing Paper Trading / Historical Replay / Evidence / The Lab / Audit / Strategy dashboard clarity, stale labels, misleading metrics, markers, and tab taxonomy. |
| `quant_reviewer` | read-only | Reviewing paper-trade quality, lane comparison, late entries, RSI-cooldown entries, impulse entries, no-trade reasons, symbol/timeframe concentration, and evidence interpretation. |

## Current Boundaries Embedded In The Agents

- Paper Trading is the main weekly surface.
- Active paper timeframes are `1h`, `4h`, and `1d`.
- `15m` is paused.
- Public Hyperliquid mainnet candles are strategy truth.
- Synthetic paper ledgers are PnL truth.
- Hyperliquid testnet transport is fixed 25 USDC, Money Flow v1.2 baseline-only, and gated.
- Candidate, MF-ORIG, and wildcard lanes are synthetic-only.
- Testnet fills do not update synthetic PnL.
- Live trading is not approved.
- No strategy is production-approved.

## Read-Only Default Rule

All three initial subagents are configured with `sandbox_mode = "read-only"` and instructions that they must stay read-only unless the parent explicitly asks for a patch. They should normally inspect files, summarize evidence, classify findings, and recommend next actions.

Do not use these subagents for parallel write-heavy implementation. If a future phase needs write-capable agents, define a separate phase and split file ownership carefully.

## How To Invoke Them

Ask the main Codex session to spawn one or more project subagents by name and keep the task bounded. The main session should wait for their findings, consolidate them, and decide whether any code/docs changes are in scope.

## Example Prompts

### Full Triage

```text
Spawn runtime_reviewer, dashboard_reviewer, and quant_reviewer.

Task:
Review the current PT-RT1.5.x Week 1 active runtime artifacts and dashboard state.

Stay read-only.
Each subagent should return:
1. verdict
2. top findings
3. severity list
4. exact files/logs inspected
5. recommended next action

Wait for all subagents and consolidate the result.
```

### Runtime-Only

```text
Spawn runtime_reviewer.

Task:
Review whether the current runtime is still producing startup-valid opens, duplicate closed-candle decisions, 15m active-week entries, or synthetic PnL/testnet lifecycle contamination.

Stay read-only.
Return P0/P1/P2/P3 findings.
```

### Dashboard-Only

```text
Spawn dashboard_reviewer.

Task:
Review the Paper Trading tab for founder readability. Check active vs archived rows, watchlist compactness, open/closed trade tables, signal stream labels, testnet lifecycle separation, and chart-marker meaning.

Stay read-only.
Return confusing labels and low-risk fixes.
```

### Quant-Only

```text
Spawn quant_reviewer.

Task:
Review the latest Week 1 paper trades. Tag late entries, RSI-cooldown entries, large-impulse entries, MACD-fading entries, bad exits, no-trade reasons, and lane concentration.

Stay read-only.
Do not propose production approval.
```

## Combining Multiple Codex Sessions

When more than one Codex session is active:

- Check `money-flow/05_Agent_Coordination.md` before starting.
- Add or update a coordination row before substantial work.
- Keep subagent work read-only unless the owning session explicitly assigns a patch.
- Avoid asking multiple sessions or subagents to edit the same files.
- Treat subagent findings as review inputs; the parent session remains responsible for final changes and validation.

## What Subagents Must Not Do

- Do not change Money Flow production rules.
- Do not change runtime behavior.
- Do not change dashboard behavior unless a parent session explicitly scopes a patch.
- Do not submit orders.
- Do not call exchange endpoints.
- Do not use API keys.
- Do not enable or disable testnet transport.
- Do not regenerate evidence packs.
- Do not run new backtests.
- Do not approve live trading.
- Do not approve any strategy for production.

## Parallel Write Conflict Avoidance

Subagents should be used for exploration, test review, artifact inspection, and summarization. If a future phase intentionally delegates implementation, assign disjoint file ownership and make each write-capable worker update `money-flow/05_Agent_Coordination.md` before editing.
