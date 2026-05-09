from __future__ import annotations

from pathlib import Path


REPORT_PATH = Path("docs/strategy_validation_sv1_18_evidence_closeout_and_uat_candidate_freeze.md")


def _report() -> str:
    return REPORT_PATH.read_text()


def test_sv118_freezes_exact_uat_observation_candidate() -> None:
    report = _report()

    assert "money_flow_hyperliquid_eth_1h_baseline_uat_candidate" in report
    assert "| Venue | Hyperliquid |" in report
    assert "| Product | USDC perpetual |" in report
    assert "| Symbol | ETH |" in report
    assert "| Component | `sleeve_1h` |" in report
    assert "| Strategy rules | Current baseline Money Flow rules |" in report
    assert "| Position behavior for UAT | Observation / shadow first |" in report
    assert "| Execution in SV1.18 | None |" in report


def test_sv118_excluded_candidate_table_is_explicit() -> None:
    report = _report()

    assert "## Excluded Candidates" in report
    for expected in [
        "| 15m sleeve |",
        "| 4h sleeve |",
        "| BTC 1h |",
        "| SOL 1h |",
        "| Lower-RSI variants |",
        "| Market-structure variants |",
        "| Aster / Binance |",
        "| OKX / Coinbase / Kraken |",
    ]:
        assert expected in report


def test_sv118_uat_purpose_and_pass_fail_criteria_exist() -> None:
    report = _report()

    assert "UAT is plumbing and behavior validation" in report
    assert "It is not performance validation" in report
    assert "## UAT Pass Criteria" in report
    assert "## UAT Fail Criteria" in report
    assert "No unapproved order submission path is reachable" in report
    assert "Live endpoint can be reached accidentally from sandbox mode" in report


def test_sv118_uat0_blocker_checklist_exists() -> None:
    report = _report()

    assert "## UAT0 Safety / Security / Runtime Hardening" in report
    for expected in [
        "API authentication / authorization readiness",
        "Key and secret hygiene",
        "Fail-safe live/demo mode separation",
        "Sandbox/testnet environment gating",
        "Risk limit enforcement",
        "Drawdown calculation and monitoring",
        "Kill switch / disable switch",
        "No live endpoint access in sandbox mode",
    ]:
        assert expected in report


def test_sv118_report_avoids_proof_and_trading_authorization_language() -> None:
    report = _report().lower()

    forbidden_phrases = [
        "proven profitable",
        "approved for paper trading",
        "paper trading approved",
        "ready for live trading",
        "recommended strategy",
        "optimal strategy",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in report
    assert "paper trading remains deferred" in report
    assert "live trading remains deferred" in report


def test_sv118_boundary_flags_confirm_no_live_artifacts() -> None:
    report = _report()

    assert "`creates_live_artifacts`: `false`" in report
    assert "`creates_routing_artifacts`: `false`" in report
    assert "`calls_exchange_adapters`: `false`" in report
    assert "`uses_api_keys`: `false`" in report
    assert "`generates_evidence_packs`: `false`" in report


def test_sv118_closeout_is_not_wired_into_production_money_flow_rules() -> None:
    source = Path("services/strategy/money_flow.py").read_text()

    assert "money_flow_hyperliquid_eth_1h_baseline_uat_candidate" not in source
    assert "SV1.18" not in source
    assert "uat_candidate" not in source
