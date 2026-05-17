from __future__ import annotations

import json
from pathlib import Path


REPORT = Path("docs/pt_rt1_1c_24h_runtime_collection_start.md")
SUMMARY = Path("docs/pt_rt1_1c_24h_runtime_collection_start_summary.json")


def _summary() -> dict:
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


def test_pt_rt1_1c_start_report_and_summary_exist() -> None:
    assert REPORT.exists()
    assert SUMMARY.exists()
    report = REPORT.read_text(encoding="utf-8")
    summary = _summary()

    assert "PT-RT1.1C 24-Hour Runtime Collection Start" in report
    assert summary["phase"] == "PT-RT1.1C"
    assert summary["status"] == "runtime_collection_started"
    assert summary["next_phase_decision"] == "PT-RT1.1D may evaluate 24-hour runtime artifacts after completion"


def test_pt_rt1_1c_runtime_command_and_output_directory() -> None:
    report = REPORT.read_text(encoding="utf-8")
    summary = _summary()
    command = summary["runtime_command"]

    assert "--duration-hours 24" in command
    assert "--disable-testnet-probes" in command
    assert "--public-mainnet-only" in command
    assert summary["output_directory"] == "reports/paper_runtime/pt_rt1_1c_24h_dry_run"
    assert "reports/paper_runtime/pt_rt1_1c_24h_dry_run" in report
    assert summary["runtime_artifacts_ignored"] is True
    assert "reports/paper_runtime/" in Path(".gitignore").read_text(encoding="utf-8")


def test_pt_rt1_1c_strategy_lanes_and_universe_are_listed() -> None:
    summary = _summary()
    report = REPORT.read_text(encoding="utf-8")

    assert len(summary["strategy_lanes"]) == 10
    for lane_id in [
        "money_flow_v1_2_baseline",
        "avoid_low_rolling_range_20",
        "avoid_low_rolling_range_50",
        "mf_orig_stage_filter_only_full_equity",
        "mf_orig_stage2_pullback_reclaim_full_equity",
        "mf_orig_1d_stage2_5_20_crossover_full_equity",
        "mf_orig_1d_stage2_breakout_resistance_full_equity",
        "wildcard_btc_regime_guard",
        "wildcard_multi_timeframe_alignment",
        "wildcard_volatility_expansion_breakout",
    ]:
        assert lane_id in summary["strategy_lanes"]
        assert lane_id in report

    assert len(summary["requested_universe"]) == 25
    assert "TRON" in summary["requested_universe"]
    assert "PEPE" in summary["requested_universe"]
    assert "OKB" in summary["requested_universe"]


def test_pt_rt1_1c_blocked_symbols_and_reason_codes_are_visible() -> None:
    summary = _summary()
    blocked = {row["requested_symbol"]: row for row in summary["watchlist_first_cycle"]["blocked_symbols"]}

    assert summary["watchlist_first_cycle"]["resolved_rows"] == 25
    assert summary["watchlist_first_cycle"]["eligible_rows"] == 23
    assert summary["watchlist_first_cycle"]["blocked_rows"] == 2
    assert blocked["PEPE"]["resolved_venue_symbol"] == "kPEPE"
    assert "pepe_kpepe_unit_semantics_deferred" in blocked["PEPE"]["reason_codes"]
    assert blocked["OKB"]["resolved_venue_symbol"] == "OKB"
    assert "okb_support_not_confirmed" in blocked["OKB"]["reason_codes"]


def test_pt_rt1_1c_boundaries_and_dashboard_handoff() -> None:
    summary = _summary()
    report = REPORT.read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")

    boundaries = summary["boundaries"]
    assert boundaries["testnet_probes_enabled"] is False
    assert boundaries["testnet_kill_switch_active"] is True
    assert boundaries["daily_probe_cap_zero"] is True
    assert boundaries["orders_submitted"] is False
    assert boundaries["private_signed_order_endpoints_called_from_strategy_truth"] is False
    assert boundaries["api_keys_used_for_strategy_truth"] is False
    assert boundaries["production_money_flow_rules_changed"] is False
    assert boundaries["live_trading_approved"] is False
    assert summary["dashboard_url"] == "http://127.0.0.1:8765/apps/dashboard/index.html"
    assert "PT-RT1.1D may evaluate 24-hour runtime artifacts after completion" in report
    assert "../../reports/paper_runtime/pt_rt1_5_2_week1_active/summary.json" in js
    assert "../../reports/paper_runtime/pt_rt1_5_2_transport_smoke/summary.json" in js
    assert "../../reports/paper_runtime/pt_rt1_5_1_smoke/summary.json" not in js
    assert "../../reports/paper_runtime/pt_rt1_1c_24h_dry_run/summary.json" not in js
    assert "No strategy is production-approved." in report
    assert "Live trading is not approved." in report
