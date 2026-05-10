# UAT0 Safety Runtime Hardening

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

UAT0 safety/security/runtime audit is complete. UAT0.1 API auth/authz and runtime lockout hardening is complete. UAT0.2 adapter runtime-policy, read-only allowlist, and representative redaction hardening is complete. UAT0.3 top-20 universe and drawdown readiness preflight is complete. UAT1 public read-only connectivity may proceed under strict constraints.

## Result

UAT0 did not implement UAT1, UAT2, UAT3, sandbox orders, paper trading, live trading, exchange calls, API-key use, routing expansion, Money Flow rule changes, or evidence-pack generation.

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

Founder/operator report:

- `docs/uat0_safety_security_runtime_hardening.md`
- `docs/uat0_1_api_auth_runtime_lockout.md`
- `docs/uat0_2_adapter_runtime_policy_and_redaction.md`
- `docs/uat0_3_top20_universe_and_drawdown_readiness.md`

## Evidence Candidate vs Observation Universe

Frozen evidence candidate:

- `money_flow_hyperliquid_eth_1h_baseline_uat_candidate`
- Hyperliquid ETH USDC perpetual
- `sleeve_1h`
- current baseline Money Flow rules
- observation / shadow first

Future UAT observation is not ETH-only. UAT1/UAT2 should cover top 20 high-volume crypto assets supported by the selected UAT venue/environment. Top-20 inclusion is not strategy approval.

Future UAT2 shadow timing must compare `next_candle_open` and `next_candle_close`. `same_candle_close_research_only` remains research-only.

## Blocker Matrix Summary

| Blocker | Current Status | Severity |
| --- | --- | --- |
| API authentication / authorization readiness | implemented | P0 closed by UAT0.1 |
| Live endpoint lockout / endpoint safety | implemented_baseline | P0 closed by UAT0.1 |
| Key and secret hygiene | implemented_baseline | P1 partially closed by UAT0.2 representative redaction tests |
| No secrets in logs / errors | needs_verification | P1 broader structured log/API error review remains |
| Fail-safe UAT/read-only/shadow/live mode separation | implemented_baseline | P1 adapter guard baseline closed by UAT0.2 |
| Sandbox/testnet environment gating | needs_verification | P1 Hyperliquid allowlist exists; endpoint URL/sandbox behavior remains UAT1 verification |
| Risk limit enforcement | needs_verification | P1 |
| Runtime drawdown calculation and monitoring | implemented_design | P1 closed enough for UAT1; UAT2/UAT3 wiring remains |
| Kill switch / disable switch | needs_verification | P1 |
| Debug stack traces not exposed to users | needs_verification | P1 |
| Audit logging | needs_verification | P1 |
| Top-20 symbol / market identity resolution | implemented_fixture_policy | P1 closed enough for UAT1; public-source/venue metadata verification remains UAT1 work |
| Operator confirmation gates | implemented, needs UAT3 verification | P2 |
| Duplicate order prevention | implemented, needs UAT3 verification | P2 |
| Submit lease / uncertainty handling remains active | implemented, needs UAT3 verification | P2 |

## UAT1 Readiness

`UAT1 read-only connectivity may proceed`.

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
