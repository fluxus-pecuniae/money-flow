# UAT0 Safety Runtime Hardening

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

UAT0 safety/security/runtime audit is complete. UAT0.1 API auth/authz and runtime lockout hardening is complete. UAT0.2 adapter runtime-policy, read-only allowlist, and representative redaction hardening is complete. UAT0.3 top-20 universe and drawdown readiness preflight is complete. UAT1 public read-only connectivity and top-20 universe resolution is complete. UAT1.1 shadow readiness is complete. UAT2 bounded no-order shadow strategy observation is complete. UAT2.1 dashboard visualization is complete. UAT3.0 sandbox-order design/readiness is complete. UAT3.0.1 sandbox runtime / approval / risk readiness hardening is complete. UAT3.0.2 sandbox gate integration dry-run / policy hardening is complete. UAT3.0.3 sandbox gate wiring / label-enforcement hardening is complete. UAT3.0.4 sandbox private read-only drawdown readiness is complete. UAT3.0.5 sandbox/testnet private read-only drawdown verification is complete. UAT3.1 actual sandbox order submission remains blocked.

## Result

UAT0 did not implement UAT1, UAT2, UAT3, sandbox orders, paper trading, live trading, exchange calls, API-key use, routing expansion, Money Flow rule changes, or evidence-pack generation.

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

Founder/operator report:

- `docs/uat0_safety_security_runtime_hardening.md`
- `docs/uat0_1_api_auth_runtime_lockout.md`
- `docs/uat0_2_adapter_runtime_policy_and_redaction.md`
- `docs/uat0_3_top20_universe_and_drawdown_readiness.md`
- `docs/uat1_public_read_only_connectivity_and_top20_universe.md`
- `docs/uat1_1_shadow_signal_audit_and_drawdown_readiness.md`
- `docs/uat2_shadow_strategy_top20_observation.md`
- `docs/uat2_1_dashboard_visualization_and_approval_readiness.md`
- `docs/uat3_0_sandbox_order_design_and_readiness.md`
- `docs/uat3_0_1_sandbox_runtime_approval_risk_readiness.md`
- `docs/uat3_0_2_sandbox_gate_integration_dry_run.md`
- `docs/uat3_0_3_sandbox_gate_wiring_and_label_enforcement.md`
- `docs/uat3_0_4_sandbox_private_read_only_drawdown.md`
- `docs/uat3_0_5_sandbox_private_read_only_drawdown_verification.md`

## Evidence Candidate vs Observation Universe

Frozen evidence candidate:

- `money_flow_hyperliquid_eth_1h_baseline_uat_candidate`
- Hyperliquid ETH USDC perpetual
- `sleeve_1h`
- current baseline Money Flow rules
- observation / shadow first

Future UAT observation is not ETH-only. UAT1/UAT2 should cover top 20 high-volume crypto assets supported by the selected UAT venue/environment. Top-20 inclusion is not strategy approval.

UAT2 shadow timing compared `next_candle_open` and `next_candle_close`. `same_candle_close_research_only` remains research-only.

## Blocker Matrix Summary

| Blocker | Current Status | Severity |
| --- | --- | --- |
| API authentication / authorization readiness | implemented | P0 closed by UAT0.1 |
| Live endpoint lockout / endpoint safety | implemented_baseline | P0 closed by UAT0.1 |
| Key and secret hygiene | implemented_baseline | P1 partially closed by UAT0.2 representative redaction tests |
| No secrets in logs / errors | implemented_representative | P1 representative API-error / structured-log verification closed by UAT1.1; deployment smoke tests remain |
| Fail-safe UAT/read-only/shadow/live mode separation | implemented_baseline | P1 adapter guard baseline closed by UAT0.2 |
| Sandbox/testnet environment gating | needs_verification | P1 Hyperliquid allowlist exists; endpoint URL/sandbox behavior remains UAT1 verification |
| Hyperliquid public read-only endpoint behavior | verified_public_only | P1 closed by UAT1 |
| Risk limit enforcement | needs_verification | P1 |
| Runtime drawdown calculation and monitoring | implemented_shadow_visibility | P1 closed for UAT2 shadow by UAT1.1; UAT3.1 sandbox account feed wiring remains |
| Kill switch / disable switch | needs_verification | P1 |
| Debug stack traces not exposed to users | needs_verification | P1 |
| Audit logging | implemented_shadow_audit_surface | P1 closed for UAT2 shadow by UAT1.1; UAT3 lifecycle audit verification remains |
| Top-20 symbol / market identity resolution | verified_public_only | P1 public-source/venue metadata verification closed by UAT1 |
| Operator confirmation gates | implemented, needs UAT3 verification | P2 |
| Duplicate order prevention | implemented, needs UAT3 verification | P2 |
| Submit lease / uncertainty handling remains active | implemented, needs UAT3 verification | P2 |

## UAT1 Readiness

`UAT1 read-only connectivity may proceed`.

UAT1 is now complete. UAT1.1 is now complete. UAT2 is now complete. UAT2.1 is now complete. UAT3.0 design/readiness is now complete. UAT3.0.1 fixture/readiness hardening is now complete. UAT3.0.2 dry-run gate hardening is now complete. UAT3.0.3 dry-run executable gate wiring and label-enforcement hardening is now complete. UAT3.0.4 private read-only sandbox drawdown readiness is now complete. UAT3.0.5 sandbox/testnet private read-only drawdown verification is now complete. `UAT3.1 is blocked`.

Closed by UAT0.1:

- protect sensitive API routes with scoped bearer authentication and authorization;
- add central fail-safe runtime policy and live/order/private endpoint lockout flags;

Closed or partially closed by UAT0.2:

- adapter private/signed/order methods are guarded by runtime policy before transport;
- public read-only methods are classified for future UAT1;
- Hyperliquid future-UAT1 read-only allowlist artifact exists;
- bearer/API-key/secret/password/DB URL redaction helper behavior is tested;

Closed by UAT0.3:

- fixture-tested top-20 public source / Hyperliquid market-intersection resolver policy;
- Hyperliquid public read-only info-type allowlist for `meta`, `metaAndAssetCtxs`, `allMids`, `l2Book`, `candleSnapshot`, and `fundingHistory`;
- fixture-tested runtime drawdown monitor policy/model.

Required in UAT1:

- verify Hyperliquid public read-only endpoint URLs and sandbox/testnet behavior without private/order access;
- fetch public top-20 source data without private keys or signed endpoints;
- fetch public Hyperliquid metadata only through allowlisted public read-only categories;
- run the resolver with real public metadata and preserve observation-only / not-strategy-approved labels.

Closed by UAT1:

- explicit public-read-only network mode was required;
- Hyperliquid public read-only info types returned HTTP 200 with usable response shapes;
- CoinGecko public markets was fetched without API keys;
- the generated UAT1 report resolved 15 included Hyperliquid observation candidates and 5 excluded assets;
- no private/signed/order endpoints, API keys, order submissions, strategy decisions, order intents, submitted orders, paper/live behavior, evidence packs, or Money Flow rule changes were created.

Closed by UAT1.1:

- model/report-only shadow signal audit records exist;
- `next_candle_open` and `next_candle_close` are represented for future UAT2;
- `same_candle_close_research_only` remains research-only;
- operator-visible `shadow_simulated_drawdown` / `not_live_account_drawdown` state exists;
- UAT1 universe snapshot loading is available for UAT2;
- representative API-error / structured-log redaction verification exists;
- no strategy decisions, order intents, submitted orders, approvals, private/signed/order endpoints, API keys, paper/live behavior, evidence packs, or Money Flow rule changes were created.

Closed by UAT2:

- explicit UAT2 shadow mode and public-read-only flags were required;
- UAT1 universe snapshot was evaluated across `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`;
- 45 shadow audit records were created: 11 `would_open`, 34 `no_trade`, 0 `invalid`, and 0 `risk_blocked`;
- `next_candle_open` and `next_candle_close` were represented; `same_candle_close_research_only` remained research-only;
- shadow drawdown was labeled `shadow_simulated_drawdown` / `not_live_account_drawdown`;
- no private/signed/order endpoints, API keys, order submissions, strategy decisions, order intents, submitted orders, approvals, paper/live behavior, evidence packs, routing artifacts, or Money Flow rule changes were created.

Closed by UAT2.1:

- the existing static dashboard now loads the UAT2 summary JSON;
- UAT2 summary cards, a filterable signal matrix, would-open review, no-trade reason breakdowns, ETH candidate truth, timing assumptions, not-live-account drawdown, boundary flags, and UAT3 blockers are visible;
- no approval action, order submission path, paper/live behavior, routing behavior, evidence pack, or Money Flow rule change was added.

Closed by UAT3.0:

- future initial sandbox-order subset is defined as Hyperliquid ETH USDC perpetual `sleeve_1h` current baseline rules only;
- founder/operator approval template, sandbox runtime policy, sandbox account drawdown feed requirements, approval-gated lifecycle, sandbox artifact labeling, submit-lease / duplicate-prevention design, approval gate design, and risk gate design are documented;
- dashboard UAT view includes an informational UAT3.0 design/readiness panel;
- no order intent, submitted order, executable approval, private/signed endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was added.

Closed by UAT3.0.1:

- fixture-only `SandboxRuntimePolicy` exists and defaults fail-closed;
- sandbox artifact-label validation exists and requires sandbox/testnet/not-live/not-paper/no-real-capital labels;
- future actual-submission approval wording is sharpened and fixture approval-scope validation exists;
- fixture sandbox risk gate evaluator, sandbox drawdown feed fixture, and submit-lease duplicate-prevention checks exist;
- dashboard UAT view reports the UAT3.0.1 readiness primitives as fixture/readiness only;
- no order intent, submitted order, executable approval, private/signed endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was added.

Closed by UAT3.0.2:

- all sandbox runtime-policy blockers propagate into sandbox risk/preflight reason codes;
- approval scope, risk limits, risk request, and drawdown fixture inputs reject invalid non-positive sandbox numeric values;
- unified fixture-only sandbox gate preflight combines runtime policy, artifact labels, approval scope, risk gates, drawdown feed status, submit preflight, founder/operator actual-submission approval, and artifact-label persistence status;
- dashboard UAT view reports unified dry-run preflight and full runtime blocker propagation status;
- no order intent, submitted order, executable approval, private/signed endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was added.

Closed by UAT3.0.3:

- sandbox artifact label boundary helpers enforce required sandbox/testnet/not-live/not-paper/no-real-capital labels before future persistence, API serialization, dashboard display, and report generation boundaries;
- a dry-run executable gate service composes runtime policy, boundary labels, approval scope, risk gates, drawdown feed status, and submit-lease duplicate-prevention checks;
- runtime policy semantics now distinguish broad/global exchange order submission from sandbox/testnet-only submission gating;
- dashboard UAT view reports boundary-label enforcement and dry-run executable gate wiring status;
- no order intent, prepared order, submitted order, executable approval, private/signed/order endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was added.

Closed by UAT3.0.4:

- fail-closed private read-only sandbox account policy exists;
- exact founder/operator credential approval validation exists;
- credential boundary validation and redaction helpers exist;
- private read-only account/balance/position/equity categories are separated from order/cancel/amend/retry/live-private categories;
- sandbox account drawdown feed modeling exists with `sandbox_account` and `not_live_account` labels;
- explicit credential approval was absent, so no API keys were used and no private endpoints were called;
- no order intent, prepared order, submitted order, executable approval, order/cancel/amend/retry endpoint call, live API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was added.

Closed by UAT3.0.5:

- exact UAT3.0.5 founder/operator private-read-only approval text is validated;
- sandbox/testnet credential environment status is inspectable without retaining private key values;
- live Hyperliquid endpoint URLs are blocked by sandbox/testnet boundary validation;
- Hyperliquid sandbox account-state payload parsing can produce a `sandbox_account` / `not_live_account` drawdown feed from caller-supplied sandbox account truth;
- local sandbox/testnet credential env vars were missing, so no credentials were loaded, no API keys were used, no private endpoints were called, and live-fed sandbox drawdown remains blocked;
- order/cancel/amend/retry endpoints remain blocked even when private read-only categories are modeled;
- no order intent, prepared order, submitted order, executable approval, order/cancel/amend/retry endpoint call, live API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was added.

Remaining before UAT3.1:

- explicit founder/operator approval for actual sandbox submission;
- live-fed sandbox account drawdown from sandbox/testnet account truth;
- real sandbox submit path wiring;
- executable approval-scope gate wiring to persistence;
- risk gate wiring to the actual future sandbox submit path;
- submit-lease integration verification;
- explicit founder/operator approval for actual sandbox submission.

## Forbidden Until Later Gated Phases

- Private exchange calls.
- Signed endpoint calls.
- API keys against real exchanges.
- Exchange order endpoints.
- Paper trades.
- Live trades.
- Routing expansion.
- Money Flow rule changes.
- Automatic top-20 order submission.
