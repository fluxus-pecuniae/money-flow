from __future__ import annotations

import json
from pathlib import Path


def test_pt_rt1_1a_report_and_summary_exist() -> None:
    report = Path("docs/pt_rt1_1a_expanded_universe_and_strategy_lanes.md")
    summary = Path("docs/pt_rt1_1a_expanded_universe_and_strategy_lanes_summary.json")

    assert report.exists()
    assert summary.exists()
    assert "PT-RT1.1B may connect public mainnet data and prepare PT-RT1.1C" in report.read_text(encoding="utf-8")
    assert json.loads(summary.read_text(encoding="utf-8"))["phase"] == "PT-RT1.1A"


def test_pt_rt1_1a_summary_declares_boundaries_and_expansion() -> None:
    summary = json.loads(Path("docs/pt_rt1_1a_expanded_universe_and_strategy_lanes_summary.json").read_text(encoding="utf-8"))

    assert len(summary["strategy_lanes"]) == 10
    assert "wildcard_btc_regime_guard" in summary["strategy_lanes"]
    assert "wildcard_multi_timeframe_alignment" in summary["strategy_lanes"]
    assert "wildcard_volatility_expansion_breakout" in summary["strategy_lanes"]
    assert summary["alias_mappings"]["TRON"] == "TRX"
    assert summary["alias_mappings"]["PEPE"] == "kPEPE"
    assert summary["blocked_symbol_policy"]["PEPE"] == "blocked_by_default_pepe_kpepe_unit_semantics_deferred"
    assert "OKB" in summary["blocked_symbol_policy"]
    assert "POL" in summary["blocked_symbol_policy"]
    assert summary["testnet_probe_policy"]["enabled_by_default"] is False
    assert summary["testnet_probe_policy"]["kill_switch_default"] is True
    assert summary["testnet_probe_policy"]["testnet_fills_update_strategy_pnl"] is False
    assert summary["boundaries"]["runtime_collection_started"] is False
    assert summary["boundaries"]["production_money_flow_rules_changed"] is False
    assert summary["boundaries"]["orders_submitted"] is False
    assert summary["boundaries"]["live_trading_approved"] is False
    assert summary["next_phase"] == "PT-RT1.1B connects public mainnet data and prepares PT-RT1.1C 24-hour probes-disabled runtime collection"


def test_pt_rt1_1a_existing_summary_is_dashboard_ready() -> None:
    summary = json.loads(Path("docs/pt_rt1_real_time_paper_observation_and_testnet_plumbing_summary.json").read_text(encoding="utf-8"))

    assert summary["revision"] == "PT-RT1.1A"
    assert len(summary["strategy_lanes"]) == 10
    assert summary["dashboard_status"]["strategy_lanes_visible"] == 10
    assert summary["dashboard_status"]["blocked_symbols_visible"] is True
    assert summary["dashboard_status"]["wildcard_diagnostics_visible"] is True
    assert any(row["requested_symbol"] == "PEPE" and row["blocked"] for row in summary["scanner_universe"])
    assert any(row["requested_symbol"] == "OKB" and row["blocked"] for row in summary["scanner_universe"])
    assert any(row["requested_symbol"] == "TRON" and row["resolved_venue_symbol"] == "TRX" for row in summary["scanner_universe"])
    assert summary["latest_readiness_phase"] == "PT-RT1.1B"
    assert summary["dashboard_status"]["public_mainnet_connection_status_visible"] is True
    assert summary["next_phase"]["decision"] == "PT-RT1.1C may start 24-hour probes-disabled runtime collection"
