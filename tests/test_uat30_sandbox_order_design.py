from __future__ import annotations

from pathlib import Path


REPORT = Path("docs/uat3_0_sandbox_order_design_and_readiness.md")


def _report() -> str:
    return REPORT.read_text(encoding="utf-8")


def test_uat30_report_exists_and_keeps_design_only_boundaries() -> None:
    report = _report()

    assert "# UAT3.0 Sandbox Order Design And Approval/Lifecycle Readiness" in report
    assert "UAT3.0 is a design and readiness phase" in report
    assert "does not submit orders" in report
    assert "does not call private or signed endpoints" in report
    assert "does not use exchange API keys" in report
    assert "does not create real `OrderIntent`" in report
    assert "does not add paper trading" in report
    assert "does not add live trading" in report
    assert "does not change Money Flow rules" in report
    assert "Actual sandbox order submission is not approved" in report


def test_founder_approval_template_is_sandbox_only_and_not_broad_top20() -> None:
    report = _report()

    assert "Founder / Operator Approval Template" in report
    assert "This approval is for sandbox/testnet only." in report
    assert "This approval does not approve live trading." in report
    assert "This approval does not approve paper trading with real capital." in report
    assert "This approval does not approve production auto-submit." in report
    assert "This approval does not approve broad top-20 order submission." in report
    assert "Maximum notional or quantity" in report
    assert "Maximum sandbox orders" in report
    assert "Time window" in report
    assert "Kill switch / disable control" in report


def test_initial_sandbox_subset_is_narrow_eth_1h_not_top20_order_submission() -> None:
    report = _report()

    assert "uat3_initial_eth_1h_sandbox_order_subset" in report
    assert "`ETH`" in report
    assert "`sleeve_1h`" in report
    assert "`current baseline Money Flow rules`" in report
    assert "`not top20_broad_order_submission`" in report
    assert "UAT2 observation universe: top-20-supported Hyperliquid assets for shadow behavior review only." in report


def test_sandbox_runtime_drawdown_artifact_approval_submit_lease_and_risk_designs_exist() -> None:
    report = _report()

    assert "Sandbox Runtime Policy" in report
    assert "`runtime_mode` | `sandbox` or `uat_sandbox`" in report
    assert "`live_trading_enabled` | `false`" in report
    assert "`paper_trading_enabled` | `false`" in report
    assert "`sandbox_order_submission_enabled` | explicit `true` only for UAT3.1 approved run" in report
    assert "Sandbox Account Drawdown Feed Requirements" in report
    assert "`sandbox_account_equity`" in report
    assert "`sandbox_account`" in report
    assert "`not_live_account`" in report
    assert "Sandbox Order Artifact Separation" in report
    assert "`sandbox_order = true`" in report
    assert "Submit Lease / Duplicate Prevention Design" in report
    assert "submit lease before transport" in report
    assert "no unsafe retry after unknown state" in report
    assert "Approval Gate Design" in report
    assert "scoped to `venue`" in report
    assert "scoped to maximum notional or quantity" in report
    assert "Risk Gate Design" in report
    assert "`max_sandbox_notional`" in report
    assert "`forbidden_live_endpoint`" in report


def test_uat31_readiness_is_blocked_with_exact_blockers() -> None:
    report = _report()

    assert "`UAT3.1 is blocked`" in report
    for blocker in (
        "founder_operator_explicit_approval_required_before_uat3_1_actual_sandbox_submission",
        "sandbox_runtime_submission_policy_not_implemented",
        "sandbox_account_drawdown_feed_missing",
        "uat3_approval_scope_verification_required",
        "uat3_submit_lease_lifecycle_verification_required",
        "uat3_risk_gate_implementation_required",
        "sandbox_artifact_labeling_not_verified",
    ):
        assert blocker in report


def test_uat30_boundary_table_confirms_no_artifacts_or_exchange_calls() -> None:
    report = _report()

    assert "Orders submitted | `false`" in report
    assert "Real order intents created | `false`" in report
    assert "Submitted orders created | `false`" in report
    assert "Executable approvals created | `false`" in report
    assert "Private endpoints called | `false`" in report
    assert "Signed endpoints called | `false`" in report
    assert "Exchange API keys used | `false`" in report
    assert "Paper trading added | `false`" in report
    assert "Live trading added | `false`" in report
    assert "Money Flow rules changed | `false`" in report


def test_dashboard_has_informational_uat3_design_panel_without_order_button() -> None:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    dashboard = f"{html}\n{js}".lower()

    assert "uat3-design-panel" in html
    assert "uat3.0 sandbox design" in html.lower()
    assert "uat3.0 design/readiness only" in dashboard
    assert "actual sandbox order submission is not approved" in dashboard
    assert "hyperliquid eth usdc perpetual / sleeve_1h" in dashboard
    assert "broad top-20 order submission" in dashboard
    assert "not approved" in dashboard
    assert "sandbox account drawdown feed" in dashboard
    assert "missing" in dashboard
    assert "active order submission button</span><strong>false" in dashboard
    assert "create approval" not in dashboard
    assert "submit sandbox order" not in dashboard
    assert "enable orders" not in dashboard
