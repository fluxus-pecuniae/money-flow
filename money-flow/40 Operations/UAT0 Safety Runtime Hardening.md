# UAT0 Safety Runtime Hardening

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

UAT0 is the next proposed phase. It has not started.

## Objective

Make the platform safe enough for later sandbox/read-only connectivity and shadow observation.

## Checklist

| Blocker | Current Status |
| --- | --- |
| API authentication / authorization readiness | needs verification |
| Key and secret hygiene | needs verification |
| No secrets in logs | needs verification |
| Fail-safe live/demo separation | needs verification |
| Sandbox/testnet environment gating | missing or unverified |
| Risk limit enforcement | needs verification |
| Drawdown calculation and monitoring | needs verification |
| Kill switch / disable switch | needs verification |
| Debug stack traces not exposed to users | needs verification |
| Audit logging | partially implemented, needs UAT verification |
| Operator confirmation gates | partially implemented, needs UAT verification |
| Duplicate order prevention | partially implemented, needs UAT verification |
| Submit lease / uncertainty handling remains active | partially implemented, needs UAT verification |
| No private endpoint calls before explicit UAT phase | process gate required |
| No live endpoint access in sandbox mode | missing or unverified |

## Forbidden In UAT0

- Private exchange calls.
- Signed endpoint calls.
- API keys.
- Exchange order endpoints.
- Paper trades.
- Live trades.
- Routing expansion.
- Money Flow rule changes.

## Success Criteria

UAT0 succeeds only when the checklist is verified or explicitly accepted by the founder for a later gated UAT phase.
