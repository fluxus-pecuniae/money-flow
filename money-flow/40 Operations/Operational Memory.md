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

- Current implemented milestone: `UAT3.1` first sandbox/testnet lifecycle probe complete.
- Strategy Validation SV1 is closed for now.
- Next proposed phase: `UAT3.2` additional sandbox lifecycle testing may be scoped only with separate approval and sandbox account/API-wallet configuration review.
- UAT1 public read-only connectivity is complete under strict no-private/no-signed/no-order/no-API-key constraints.
- UAT1 verified allowed public Hyperliquid info types, fetched a no-key public top-volume source, and resolved observation-only Hyperliquid supported assets.
- UAT1.1 adds operator-visible shadow drawdown state, shadow signal audit surfaces, and representative structured redaction verification.
- UAT2 evaluated the UAT1 Hyperliquid observation universe across `sleeve_15m`, `sleeve_1h`, and `sleeve_4h` using public read-only candles and shadow audit records only.
- UAT2.1 made the UAT2 shadow run visible in the dashboard without adding approval/order controls.
- UAT3.0 defines the sandbox-order design, founder approval template, sandbox runtime policy, sandbox drawdown feed requirements, approval lifecycle, submit-lease/duplicate-prevention design, and risk gate design.
- UAT3.0.1 adds fixture-only readiness validators for fail-closed sandbox runtime policy, sandbox artifact labels, actual-submission approval scope, sandbox risk gates, sandbox drawdown feed fixtures, and submit-lease duplicate-prevention checks.
- UAT3.0.2 adds full runtime-policy blocker propagation, non-positive sandbox numeric validation, and a unified fixture-only dry-run sandbox gate preflight.
- UAT3.0.3 adds sandbox artifact label boundary helpers for persistence/API/dashboard/report surfaces and a dry-run executable gate service that composes runtime, label, approval, risk, drawdown, and submit-lease checks without side effects.
- UAT3.0.4 adds private read-only sandbox account policy, credential approval/boundary validation, endpoint category separation, redaction, and sandbox account drawdown feed modeling.
- UAT3.0.5 validates exact private-read-only approval and sandbox/testnet credential boundaries, performs one Hyperliquid testnet read-only account-state request, and verifies `sandbox_drawdown_feed_live_fed_verified`; no API key/private key or order endpoint was used.
- UAT3.0.6 wires the future sandbox submit path in dry-run mode through a non-persistent submission plan plus actual-submission approval, live-fed drawdown, approval scope, risk, submit-lease duplicate prevention, endpoint classification, and sandbox label checks; no artifacts are created and no exchange is called.
- UAT3.1 verified exact founder/operator approval, made one Hyperliquid testnet ETH post-only limit attempt under 10 USDC notional, received a sanitized user/API-wallet-not-found rejection, required no cancel, reconciled no open order, and created no production execution artifacts.
- Frozen evidence candidate: Hyperliquid ETH `sleeve_1h` baseline current Money Flow rules.
- Future UAT observation universe: top-20 high-volume supported assets for behavior validation only.
- Paper trading is not approved.
- Live trading is not approved.
- Additional exchange order submission is not approved.
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
