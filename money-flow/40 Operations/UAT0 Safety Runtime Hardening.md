# UAT0 Safety Runtime Hardening

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

UAT0 safety/security/runtime audit is complete. UAT0.1 API auth/authz and runtime lockout hardening is complete. UAT1 is blocked.

## Result

UAT0 did not implement UAT1, UAT2, UAT3, sandbox orders, paper trading, live trading, exchange calls, API-key use, routing expansion, Money Flow rule changes, or evidence-pack generation.

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

Founder/operator report:

- `docs/uat0_safety_security_runtime_hardening.md`
- `docs/uat0_1_api_auth_runtime_lockout.md`

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
| Key and secret hygiene | needs_verification | P1 |
| No secrets in logs / errors | needs_verification | P1 |
| Fail-safe UAT/read-only/shadow/live mode separation | implemented_baseline | P1 |
| Sandbox/testnet environment gating | needs_verification | P1 |
| Risk limit enforcement | needs_verification | P1 |
| Runtime drawdown calculation and monitoring | missing | P1 |
| Kill switch / disable switch | needs_verification | P1 |
| Debug stack traces not exposed to users | needs_verification | P1 |
| Audit logging | needs_verification | P1 |
| Top-20 symbol / market identity resolution | needs_verification | P1 |
| Operator confirmation gates | implemented, needs UAT3 verification | P2 |
| Duplicate order prevention | implemented, needs UAT3 verification | P2 |
| Submit lease / uncertainty handling remains active | implemented, needs UAT3 verification | P2 |

## UAT1 Readiness

`UAT1 is blocked`.

Closed by UAT0.1:

- protect sensitive API routes with scoped bearer authentication and authorization;
- add central fail-safe runtime policy and live/order/private endpoint lockout flags;

Required before UAT1:

- verify adapter-level enforcement of runtime policy;
- verify no-secret logging, no-secret API errors, and sanitized tracebacks;
- define selected-venue sandbox/read-only endpoint policy;
- implement top-20 public source selection and market identity resolution.

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
