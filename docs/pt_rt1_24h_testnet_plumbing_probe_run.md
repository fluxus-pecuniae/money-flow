# PT-RT1 24-Hour Testnet Plumbing Probe Run

## Goal

Run scanner-linked Hyperliquid testnet plumbing probes under hard gates after exact approval.

This validates plumbing only:

- account targeting
- precision formatting
- post-only submit shape
- cancel/reconcile lifecycle
- audit logging
- cap enforcement
- kill-switch behavior

Testnet probes are not strategy truth. Testnet fills must not update strategy paper PnL.

## Exact Approval Text

The probe path must remain blocked unless this exact approval text is captured:

```text
I APPROVE PT-RT1 TESTNET PLUMBING PROBES ONLY. HYPERLIQUID TESTNET ONLY. POST-ONLY UNDER 10 USDC DEFAULT NOTIONAL. CANCEL/RECONCILE REQUIRED. TESTNET FILLS MUST NOT UPDATE STRATEGY PAPER PNL. LIVE TRADING IS NOT APPROVED.
```

## Required Starting State

- `PT_RT1_TESTNET_PROBES_ENABLED=true`.
- `PT_RT1_TESTNET_KILL_SWITCH=false`.
- Daily cap is set to `1` unless explicitly changed in a later approved phase.
- Probe notional is under `10 USDC`.
- Endpoint is Hyperliquid testnet only.
- No live endpoint is configured.
- Account targeting is resolved.
- Main/user mode omits `vaultAddress`.
- Subaccount/vault mode uses `vaultAddress` only when explicit.
- Symbol precision is validated from testnet metadata.
- No unknown/open prior probe state exists.

## Steps

1. Confirm exact approval text is present.
2. Confirm endpoint is testnet.
3. Confirm no live endpoint is configured.
4. Confirm kill switch is off.
5. Confirm daily cap remaining count is positive.
6. Confirm scanner signal is eligible.
7. Confirm notional is under cap.
8. Build post-only `Alo` order shape.
9. Submit only if every gate passes.
10. If accepted/open, cancel immediately.
11. Reconcile open orders.
12. Write a testnet-only lifecycle audit row.
13. Confirm testnet fill status does not update strategy paper PnL.

## Success Criteria

- Approval captured.
- Probe gate blocks unless all conditions are true.
- Cap is enforced.
- Kill switch blocks when enabled.
- Testnet post-only order is attempted only when eligible.
- Cancel/reconcile is required.
- No unknown open state remains.
- Testnet lifecycle audit is written.
- Testnet fills do not change paper PnL.
- No live endpoint is touched.

## Failure Criteria

- Probe path attempts live endpoint.
- Probe path runs without exact approval.
- Probe path runs while kill switch is active.
- Probe notional is at or above cap.
- Accepted/open order is not canceled/reconciled.
- Unknown state does not block future probes.
- Any testnet fill changes strategy paper PnL.
