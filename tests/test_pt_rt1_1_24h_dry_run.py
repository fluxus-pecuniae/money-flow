from __future__ import annotations

import json
from pathlib import Path

from scripts.build_pt_rt1_1_dry_run_report import build_summary


REPORT_PATH = Path("docs/pt_rt1_1_24h_probes_disabled_dry_run.md")
SUMMARY_PATH = Path("docs/pt_rt1_1_24h_probes_disabled_dry_run_summary.json")


def _summary() -> dict:
    return json.loads(SUMMARY_PATH.read_text())


def test_pt_rt1_1_report_and_summary_exist() -> None:
    assert REPORT_PATH.exists()
    assert SUMMARY_PATH.exists()
    assert "PT-RT1.1 24-Hour Probes-Disabled Dry Run" in REPORT_PATH.read_text()


def test_pt_rt1_1_enforces_probes_disabled_config_and_blocks_pt_rt1_2_without_artifacts() -> None:
    payload = _summary()

    assert payload["phase"] == "PT-RT1.1"
    assert payload["status"] == "blocked"
    assert payload["decision"] == "PT-RT1.2 blocked"
    assert "pt_rt1_1_24h_runtime_artifacts_missing" in payload["decision_reason_codes"]
    assert payload["runtime_config"]["PT_RT1_TESTNET_PROBES_ENABLED"] is False
    assert payload["runtime_config"]["PT_RT1_TESTNET_KILL_SWITCH"] is True
    assert payload["runtime_config"]["PT_RT1_TESTNET_DAILY_PROBE_CAP"] == 0
    assert payload["no_order_boundary_verification"]["testnet_probes_disabled"] is True
    assert payload["no_order_boundary_verification"]["kill_switch_active"] is True
    assert payload["no_order_boundary_verification"]["daily_probe_cap_zero"] is True


def test_pt_rt1_1_public_mainnet_truth_and_forbidden_endpoint_boundaries_are_reported() -> None:
    payload = _summary()
    forbidden = set(payload["runtime_config"]["forbidden"])
    boundary = payload["no_order_boundary_verification"]

    assert payload["runtime_config"]["strategy_truth"] == "Hyperliquid public mainnet data only"
    assert "testnet_prices_as_strategy_truth" in forbidden
    assert "private_signed_endpoints" in forbidden
    assert "order_endpoints" in forbidden
    assert "api_keys" in forbidden
    assert boundary["orders_submitted"] is False
    assert boundary["private_signed_order_endpoints_called"] is False
    assert boundary["api_keys_used"] is False
    assert boundary["order_intent_created"] is False
    assert boundary["prepared_venue_order_created"] is False
    assert boundary["submitted_order_created"] is False
    assert boundary["live_endpoint_used"] is False


def test_pt_rt1_1_duplicate_ledger_and_data_health_sections_are_explicitly_not_verified_without_runtime() -> None:
    payload = _summary()

    assert payload["data_health_results"]["verdict"] == "not_verified_runtime_absent"
    assert payload["duplicate_signal_summary"]["verdict"] == "not_verified_runtime_absent"
    assert payload["duplicate_signal_summary"]["reported"] is False
    assert payload["ledger_summary"]["verdict"] == "not_verified_runtime_absent"
    assert payload["ledger_summary"]["required_starting_equity_usdc_per_lane"] == "10000"
    assert "total_equity_equals_realized_equity_plus_unrealized_pnl" in payload["ledger_summary"]["invariants_required"]


def test_pt_rt1_1_strategy_lanes_and_dashboard_labels_are_reported() -> None:
    payload = _summary()

    assert set(payload["strategy_lanes_observed"]) == {
        "money_flow_v1_2_baseline",
        "avoid_low_rolling_range_50",
        "avoid_low_rolling_range_20",
        "mf_orig_1d_stage2_breakout_resistance_full_equity",
    }
    assert payload["dashboard_verification"]["paper_observation_view_exists"] is True
    assert payload["dashboard_verification"]["no_order_controls_expected"] is True
    assert "public mainnet data is strategy truth" in payload["dashboard_verification"]["labels_required"]
    assert "testnet probes disabled" in payload["dashboard_verification"]["labels_required"]


def test_pt_rt1_1_builder_can_mark_complete_artifacts_as_verified(tmp_path: Path) -> None:
    for name in (
        "state.json",
        "decisions.jsonl",
        "trades.jsonl",
        "equity_curves.json",
        "data_health.json",
        "runtime_audit.jsonl",
    ):
        (tmp_path / name).write_text("{}\n")
    (tmp_path / "summary.json").write_text(
        json.dumps(
            {
                "duration_hours": 24,
                "dry_run_passed": True,
                "start_time_utc": "2026-05-14T00:00:00Z",
                "end_time_utc": "2026-05-15T00:00:00Z",
                "public_fetch_success_count": 10,
                "public_fetch_failure_count": 0,
                "duplicate_signal_summary": {"ETH|1h|entry": {"duplicate_ignored": 1}},
                "duplicate_ignored_count": 1,
                "ledger_summary": {"money_flow_v1_2_baseline": {"starting_equity": "10000"}},
            }
        )
        + "\n"
    )

    payload = build_summary(runtime_dir=tmp_path, recorded_at_utc="2026-05-15T00:01:00Z")

    assert payload["status"] == "verified"
    assert payload["decision"] == "PT-RT1.2 may proceed"
    assert payload["missing_runtime_files"] == []
    assert payload["data_health_results"]["public_fetch_success_count"] == 10
    assert payload["duplicate_signal_summary"]["duplicate_ignored_count"] == 1


def test_pt_rt1_1_builder_requires_explicit_runtime_pass_flag(tmp_path: Path) -> None:
    for name in (
        "state.json",
        "decisions.jsonl",
        "trades.jsonl",
        "equity_curves.json",
        "data_health.json",
        "runtime_audit.jsonl",
    ):
        (tmp_path / name).write_text("{}\n")
    (tmp_path / "summary.json").write_text(
        json.dumps(
            {
                "duration_hours": 24,
                "start_time_utc": "2026-05-14T00:00:00Z",
                "end_time_utc": "2026-05-15T00:00:00Z",
            }
        )
        + "\n"
    )

    payload = build_summary(runtime_dir=tmp_path, recorded_at_utc="2026-05-15T00:01:00Z")

    assert payload["status"] == "blocked"
    assert payload["decision"] == "PT-RT1.2 blocked"
    assert "dry_run_summary_pass_flag_missing" in payload["decision_reason_codes"]
