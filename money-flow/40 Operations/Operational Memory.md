# Operational Memory

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

## Canonical Repo Memory

Required repo operational docs:

- `AGENTS.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`

## Obsidian Strategic Brain

Required Obsidian notes:

- [[00_Money_Flow_Command_Center|Money Flow Command Center]]
- [[01_Current_Phase|Current Phase]]
- [[03_Decision_Log|Decision Log]]
- [[05_Agent_Coordination|Agent Coordination]]
- [[Project_Memory/money_flow_project_memory|Project Memory]]

## Working Rule

Before substantial work, read the repo memory and Obsidian brain. Before editing overlapping files, update your own coordination row. After work, update docs/Obsidian and mark your row `done` or `blocked`.

## Current Important Memory Facts

- Current implemented milestone: `UAT3.0` sandbox order design/readiness complete.
- Strategy Validation SV1 is closed for now.
- Next proposed phase: `UAT3.1` first approval-gated sandbox order remains blocked until explicit founder/operator approval, sandbox runtime policy, sandbox account drawdown feed, approval scope verification, submit-lease lifecycle verification, risk gates, and sandbox artifact labeling are implemented/tested.
- UAT1 public read-only connectivity is complete under strict no-private/no-signed/no-order/no-API-key constraints.
- UAT1 verified allowed public Hyperliquid info types, fetched a no-key public top-volume source, and resolved observation-only Hyperliquid supported assets.
- UAT1.1 adds operator-visible shadow drawdown state, shadow signal audit surfaces, and representative structured redaction verification.
- UAT2 evaluated the UAT1 Hyperliquid observation universe across `sleeve_15m`, `sleeve_1h`, and `sleeve_4h` using public read-only candles and shadow audit records only.
- UAT2.1 made the UAT2 shadow run visible in the dashboard without adding approval/order controls.
- UAT3.0 defines the sandbox-order design, founder approval template, sandbox runtime policy, sandbox drawdown feed requirements, approval lifecycle, submit-lease/duplicate-prevention design, and risk gate design.
- UAT3.1 actual sandbox order submission remains blocked.
- Frozen evidence candidate: Hyperliquid ETH `sleeve_1h` baseline current Money Flow rules.
- Future UAT observation universe: top-20 high-volume supported assets for behavior validation only.
- Paper trading is not approved.
- Live trading is not approved.
- Exchange order submission is not approved.
- Phase 8 is historical/operator-control context, not the current next phase.

## Drift Rules

Do not create duplicate command centers or competing current-phase notes.

Do not leave completed phases marked active.

Do not describe future phases as implemented.

## Related Notes

- [[00 Maps/Current State Dashboard]]
- [[00 Maps/Strategy Validation Map]]
- [[00 Maps/UAT Roadmap]]
- [[40 Operations/Agent Workflow]]
- [[40 Operations/Review Bundle Hygiene]]
