"""Build the PT-RT1.1 probes-disabled dry-run report.

The builder is intentionally conservative: if the ignored 24-hour runtime
artifact directory is absent or incomplete, the committed report is blocked
rather than fabricating runtime stability.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


RUNTIME_DIR = Path("reports/paper_runtime/pt_rt1_1_24h_dry_run")
REPORT_PATH = Path("docs/pt_rt1_1_24h_probes_disabled_dry_run.md")
SUMMARY_PATH = Path("docs/pt_rt1_1_24h_probes_disabled_dry_run_summary.json")

REQUIRED_RUNTIME_FILES = (
    "state.json",
    "decisions.jsonl",
    "trades.jsonl",
    "equity_curves.json",
    "data_health.json",
    "runtime_audit.jsonl",
    "summary.json",
)

STRATEGY_LANES = (
    "money_flow_v1_2_baseline",
    "avoid_low_rolling_range_50",
    "avoid_low_rolling_range_20",
    "mf_orig_1d_stage2_breakout_resistance_full_equity",
)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_runtime_summary(runtime_dir: Path) -> dict[str, Any] | None:
    path = runtime_dir / "summary.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {
            "status": "blocked",
            "reason_codes": ["runtime_summary_json_invalid"],
        }
    return payload if isinstance(payload, dict) else {"status": "blocked", "reason_codes": ["runtime_summary_not_object"]}


def build_summary(*, runtime_dir: Path = RUNTIME_DIR, recorded_at_utc: str | None = None) -> dict[str, Any]:
    recorded_at_utc = recorded_at_utc or _utc_now()
    runtime_files = {path.name for path in runtime_dir.iterdir()} if runtime_dir.exists() else set()
    missing_runtime_files = [name for name in REQUIRED_RUNTIME_FILES if name not in runtime_files]
    runtime_summary = _load_runtime_summary(runtime_dir)
    runtime_artifacts_present = runtime_dir.exists() and not missing_runtime_files and runtime_summary is not None

    runtime_duration_ok = bool(runtime_summary and runtime_summary.get("duration_hours", 0) >= 24)
    runtime_summary_passed = bool(runtime_summary and runtime_summary.get("dry_run_passed") is True)

    if runtime_artifacts_present and runtime_duration_ok and runtime_summary_passed:
        status = "verified"
        decision = "PT-RT1.2 may proceed"
        decision_reason_codes = ["dry_run_24h_artifacts_present"]
    else:
        status = "blocked"
        decision = "PT-RT1.2 blocked"
        decision_reason_codes = ["pt_rt1_1_24h_runtime_artifacts_missing"]
        if runtime_dir.exists() and missing_runtime_files:
            decision_reason_codes.append("pt_rt1_1_24h_runtime_artifacts_incomplete")
        if runtime_summary is not None and runtime_summary.get("duration_hours", 0) < 24:
            decision_reason_codes.append("dry_run_duration_less_than_24h")
        if runtime_artifacts_present and runtime_duration_ok and not runtime_summary_passed:
            decision_reason_codes.append("dry_run_summary_pass_flag_missing")

    duration_hours = runtime_summary.get("duration_hours", 0) if runtime_summary else 0
    start_time = runtime_summary.get("start_time_utc") if runtime_summary else None
    end_time = runtime_summary.get("end_time_utc") if runtime_summary else None

    return {
        "phase": "PT-RT1.1",
        "report": "pt_rt1_1_24h_probes_disabled_dry_run",
        "recorded_at_utc": recorded_at_utc,
        "status": status,
        "decision": decision,
        "decision_reason_codes": decision_reason_codes,
        "runtime_artifact_dir": str(runtime_dir),
        "runtime_artifact_dir_exists": runtime_dir.exists(),
        "required_runtime_files": list(REQUIRED_RUNTIME_FILES),
        "missing_runtime_files": missing_runtime_files,
        "dry_run": {
            "start_time_utc": start_time,
            "end_time_utc": end_time,
            "duration_hours_observed": duration_hours,
            "required_duration_hours": 24,
            "runtime_summary_present": runtime_summary is not None,
        },
        "runtime_config": {
            "PT_RT1_TESTNET_PROBES_ENABLED": False,
            "PT_RT1_TESTNET_KILL_SWITCH": True,
            "PT_RT1_TESTNET_DAILY_PROBE_CAP": 0,
            "strategy_truth": "Hyperliquid public mainnet data only",
            "forbidden": [
                "testnet_prices_as_strategy_truth",
                "private_signed_endpoints",
                "order_endpoints",
                "api_keys",
                "account_balances",
                "sandbox_testnet_fills_as_strategy_pnl",
            ],
        },
        "strategy_lanes_observed": list(STRATEGY_LANES),
        "data_health_results": {
            "verdict": "not_verified_runtime_absent" if status == "blocked" else "verified_from_runtime_summary",
            "public_fetch_success_count": runtime_summary.get("public_fetch_success_count") if runtime_summary else None,
            "public_fetch_failure_count": runtime_summary.get("public_fetch_failure_count") if runtime_summary else None,
            "stale_symbols": runtime_summary.get("stale_symbols", []) if runtime_summary else [],
            "missing_candle_gaps": runtime_summary.get("missing_candle_gaps") if runtime_summary else None,
            "out_of_order_candles": runtime_summary.get("out_of_order_candles") if runtime_summary else None,
            "incomplete_candle_skips": runtime_summary.get("incomplete_candle_skips") if runtime_summary else None,
            "indicator_unavailable_counts": runtime_summary.get("indicator_unavailable_counts", {}) if runtime_summary else {},
            "data_unavailable_decisions": runtime_summary.get("data_unavailable_decisions") if runtime_summary else None,
        },
        "duplicate_signal_summary": {
            "verdict": "not_verified_runtime_absent" if status == "blocked" else "verified_from_runtime_summary",
            "reported": bool(runtime_summary and runtime_summary.get("duplicate_signal_summary")),
            "duplicate_ignored_count": runtime_summary.get("duplicate_ignored_count") if runtime_summary else None,
        },
        "ledger_summary": {
            "verdict": "not_verified_runtime_absent" if status == "blocked" else "verified_from_runtime_summary",
            "required_starting_equity_usdc_per_lane": "10000",
            "invariants_required": [
                "equity_does_not_reset_after_trades",
                "closed_trade_pnl_changes_realized_equity",
                "open_trade_pnl_changes_unrealized_pnl",
                "total_equity_equals_realized_equity_plus_unrealized_pnl",
            ],
            "lanes": runtime_summary.get("ledger_summary", {}) if runtime_summary else {},
        },
        "dashboard_verification": {
            "verdict": "not_verified_runtime_absent",
            "paper_observation_view_exists": True,
            "requires_manual_browser_review_after_runtime": True,
            "no_order_controls_expected": True,
            "labels_required": [
                "paper observation only",
                "public mainnet data is strategy truth",
                "testnet probes disabled",
                "not real capital",
                "no live trading",
            ],
        },
        "no_order_boundary_verification": {
            "testnet_probes_disabled": True,
            "kill_switch_active": True,
            "daily_probe_cap_zero": True,
            "orders_submitted": False,
            "private_signed_order_endpoints_called": False,
            "api_keys_used": False,
            "order_intent_created": False,
            "prepared_venue_order_created": False,
            "submitted_order_created": False,
            "live_endpoint_used": False,
            "production_execution_artifact_created": False,
            "basis": "static_PT_RT1_policy_and_no_PT_RT1_1_runtime_artifacts",
        },
        "issues_found": [
            {
                "severity": "P1",
                "issue": "pt_rt1_1_24h_runtime_artifacts_missing",
                "impact": "Cannot validate market-data refresh, closed-candle gating, ledgers, duplicate prevention, or dashboard runtime behavior.",
                "required_fix": "Run the PT-RT1 24-hour probes-disabled dry-run and retain ignored artifacts under reports/paper_runtime/pt_rt1_1_24h_dry_run/.",
                "blocks_pt_rt1_2": True,
            }
        ]
        if status == "blocked"
        else [],
        "boundaries": {
            "production_money_flow_rules_changed": False,
            "historical_evidence_packs_regenerated": False,
            "testnet_probes_enabled": False,
            "live_trading_approved": False,
            "paper_trading_approved_as_production": False,
            "sor_fanout_cbbo_added": False,
        },
    }


def render_report(summary: dict[str, Any]) -> str:
    lanes = "\n".join(f"- `{lane}`" for lane in summary["strategy_lanes_observed"])
    missing = ", ".join(summary["missing_runtime_files"]) or "none"
    issues = summary["issues_found"]
    issue_rows = "\n".join(
        f"| {item['severity']} | `{item['issue']}` | {item['impact']} | {item['required_fix']} |"
        for item in issues
    ) or "| none | none | none | none |"
    no_order = summary["no_order_boundary_verification"]
    config = summary["runtime_config"]
    data = summary["data_health_results"]
    ledger = summary["ledger_summary"]
    duplicate = summary["duplicate_signal_summary"]
    dashboard = summary["dashboard_verification"]

    return f"""# PT-RT1.1 24-Hour Probes-Disabled Dry Run

## Summary

Status: {summary['status']}

Decision: **{summary['decision']}**

PT-RT1.1 is an observation/validation phase for the PT-RT1 public-mainnet paper-observation runtime. The required 24-hour runtime artifact directory was checked at:

`{summary['runtime_artifact_dir']}`

Artifact directory exists: `{str(summary['runtime_artifact_dir_exists']).lower()}`

Missing required runtime files: `{missing}`

Because the 24-hour runtime artifacts are absent, this report does **not** claim that public market-data refresh, closed-candle gating, synthetic paper ledgers, duplicate prevention, or dashboard runtime behavior passed. PT-RT1.2 remains blocked until a real 24-hour probes-disabled run is executed and summarized.

## Runtime Config

| Setting | Required / Observed |
|---|---:|
| `PT_RT1_TESTNET_PROBES_ENABLED` | `{str(config['PT_RT1_TESTNET_PROBES_ENABLED']).lower()}` |
| `PT_RT1_TESTNET_KILL_SWITCH` | `{str(config['PT_RT1_TESTNET_KILL_SWITCH']).lower()}` |
| `PT_RT1_TESTNET_DAILY_PROBE_CAP` | `{config['PT_RT1_TESTNET_DAILY_PROBE_CAP']}` |
| Strategy truth | {config['strategy_truth']} |

Forbidden in this dry run: testnet prices as strategy truth, private/signed endpoints, order endpoints, API keys, account balances, and sandbox/testnet fills as strategy PnL.

## Start / End Time

| Field | Value |
|---|---:|
| Start time | `{summary['dry_run']['start_time_utc'] or 'not_available'}` |
| End time | `{summary['dry_run']['end_time_utc'] or 'not_available'}` |
| Observed duration hours | `{summary['dry_run']['duration_hours_observed']}` |
| Required duration hours | `{summary['dry_run']['required_duration_hours']}` |

## Strategy Lanes

Expected lanes:

{lanes}

All lanes must start at synthetic `10000 USDC` and compound wins/losses forward during the actual dry run.

## Data-Health Results

Verdict: `{data['verdict']}`

Runtime counters are not available because the 24-hour artifact set is absent. The next run must report public fetch successes/failures, stale symbols, missing candle gaps, out-of-order candles, incomplete candle skips, indicator-unavailable counts, and data-unavailable decisions.

## Decisions / Trades Summary

Status: `not_verified_runtime_absent`

No committed runtime decisions or trades are included in this report. Runtime decisions/trades must remain ignored under `reports/paper_runtime/pt_rt1_1_24h_dry_run/` and summarized here only after the real run completes.

## Ledger Summary

Verdict: `{ledger['verdict']}`

Required invariants:

- `equity_does_not_reset_after_trades`
- `closed_trade_pnl_changes_realized_equity`
- `open_trade_pnl_changes_unrealized_pnl`
- `total_equity_equals_realized_equity_plus_unrealized_pnl`

The invariants are not runtime-verified for PT-RT1.1 yet because no dry-run artifacts exist.

## Duplicate-Signal Summary

Verdict: `{duplicate['verdict']}`

The dry run must report signal keys, first-seen timestamps, duplicate counts, and `duplicate_ignored` counts. No duplicate paper position from the same signal candle may be created.

## Dashboard Verification

Verdict: `{dashboard['verdict']}`

Static PT-RT1 dashboard support exists, but the Paper Observation dashboard was not verified against a completed 24-hour runtime artifact set. The next dry run must verify that the dashboard shows top-20 scanner state, public-mainnet data health, lane comparison, synthetic equity curves, open/closed synthetic trades, drawdown/losing streaks, testnet probes disabled, and no order controls.

## No-Order / No-Live Verification

| Boundary | Status |
|---|---:|
| Testnet probes disabled | `{str(no_order['testnet_probes_disabled']).lower()}` |
| Kill switch active | `{str(no_order['kill_switch_active']).lower()}` |
| Daily probe cap zero | `{str(no_order['daily_probe_cap_zero']).lower()}` |
| Orders submitted | `{str(no_order['orders_submitted']).lower()}` |
| Private/signed/order endpoints called | `{str(no_order['private_signed_order_endpoints_called']).lower()}` |
| API keys used | `{str(no_order['api_keys_used']).lower()}` |
| `OrderIntent` created | `{str(no_order['order_intent_created']).lower()}` |
| `PreparedVenueOrder` created | `{str(no_order['prepared_venue_order_created']).lower()}` |
| `SubmittedOrder` created | `{str(no_order['submitted_order_created']).lower()}` |
| Live endpoint used | `{str(no_order['live_endpoint_used']).lower()}` |

Basis: `{no_order['basis']}`

## Issues Found

| Severity | Issue | Impact | Required fix |
|---|---|---|---|
{issue_rows}

## Go / No-Go For PT-RT1.2

**{summary['decision']}**

PT-RT1.2 may proceed only after a real 24-hour probes-disabled dry run demonstrates stable public mainnet data refresh, correct paper-ledger updates, no duplicate-signal bug, working data-health gates, readable dashboard runtime state, disabled testnet probes, and no private/signed/order endpoint calls.
"""


def main() -> None:
    summary = build_summary()
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    REPORT_PATH.write_text(render_report(summary))


if __name__ == "__main__":
    main()
