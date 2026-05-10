from __future__ import annotations

from pathlib import Path


REPORT = Path("docs/uat0_safety_security_runtime_hardening.md")


def test_uat0_report_exists_and_keeps_non_trading_boundaries() -> None:
    report = REPORT.read_text()

    assert "# UAT0 Safety / Security / Runtime Hardening" in report
    assert "Paper trading is not approved" in report
    assert "Live trading is not approved" in report
    assert "Exchange order submission is not approved" in report
    assert "not paper-trading authorization" in report
    assert "not live-trading authorization" in report
    assert "not exchange order-submission authorization" in report
    assert "No exchange calls were made" in report
    assert "No orders were submitted" in report
    assert "No Money Flow rules changed" in report


def test_uat0_report_freezes_evidence_candidate_and_top20_policy() -> None:
    report = REPORT.read_text()

    assert "Evidence Candidate" in report
    assert "UAT Observation Universe" in report
    assert "money_flow_hyperliquid_eth_1h_baseline_uat_candidate" in report
    assert "top 20 high-volume crypto assets supported by the selected UAT venue/environment" in report
    assert "The UAT observation universe is not a list of approved strategy candidates" in report
    for reason_code in [
        "unsupported_by_venue",
        "unsupported_market_type",
        "missing_market_identity",
        "quote_asset_mismatch",
        "settlement_asset_mismatch",
        "insufficient_public_market_data",
        "not_enabled_for_uat",
    ]:
        assert reason_code in report


def test_uat0_shadow_fill_timing_policy_is_explicit() -> None:
    report = REPORT.read_text()

    assert "UAT Shadow Fill-Timing Policy" in report
    assert "next_candle_open" in report
    assert "next_candle_close" in report
    assert "same_candle_close_research_only" in report
    assert "remains research-only" in report


def test_uat0_blocker_matrix_and_readiness_decision_are_conservative() -> None:
    report = REPORT.read_text()

    assert "UAT0 Blocker Matrix" in report
    assert "API auth" in report
    assert "`implemented` | P0 closed by UAT0.1" in report
    assert "Live endpoint lockout" in report
    assert "`implemented` | P0 closed by UAT0.1 / adapter baseline closed by UAT0.2" in report
    assert "UAT1 is blocked" in report
    assert "Sensitive `/api/v1` routes now require scoped bearer auth" in report
    assert "closes the adapter-level runtime-policy enforcement baseline" in report


def test_uat0_exchange_endpoint_table_covers_supported_venues() -> None:
    report = REPORT.read_text()

    for venue in [
        "Hyperliquid",
        "Aster",
        "Binance",
        "OKX",
        "Coinbase Advanced Trade",
        "Kraken",
    ]:
        assert venue in report


def test_uat0_current_notes_reflect_blocked_uat1_truth() -> None:
    current_phase = Path("money-flow/01_Current_Phase.md").read_text()
    command_center = Path("money-flow/00_Money_Flow_Command_Center.md").read_text()
    uat_roadmap = Path("money-flow/00 Maps/UAT Roadmap.md").read_text()

    for note in (current_phase, command_center, uat_roadmap):
        assert "UAT0" in note
        assert "UAT1 is blocked" in note
        assert "top 20" in note
        assert "next_candle_open" in note
        assert "next_candle_close" in note
        assert "same_candle_close_research_only" in note
