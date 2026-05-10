from pathlib import Path


def test_evidence_dashboard_static_assets_exist() -> None:
    dashboard_dir = Path("apps/dashboard")

    assert (dashboard_dir / "index.html").exists()
    assert (dashboard_dir / "evidence-dashboard.css").exists()
    assert (dashboard_dir / "evidence-dashboard.js").exists()
    assert (dashboard_dir / "README.md").exists()


def test_evidence_dashboard_uses_gus_design_tokens_and_boundaries() -> None:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    css = Path("apps/dashboard/evidence-dashboard.css").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")

    assert "../../variables.css" in css
    assert "--color-grid-canvas" in css
    assert "--color-scroll-highlight" in css
    assert "box-shadow" not in css
    assert "Evidence Dashboard" in html
    assert "data-view=\"experiments\"" in html
    assert "data-view=\"uat-shadow\"" in html
    assert "UAT2 Shadow Run" in html
    assert "uat2_shadow_strategy_top20_observation_summary.json" in js
    assert "renderUatDashboard" in js
    assert "uat-signal-matrix" in html
    assert "uat-would-open-table" in html
    assert "uat-boundary-panel" in html
    assert "uat3-design-panel" in html
    assert "Would-open means the shadow strategy conditions were met" in html
    assert "UAT3.0 design/readiness only" in js
    assert "Actual sandbox order submission is not approved" in js
    assert "Sandbox runtime policy" in js
    assert "Sandbox artifact label validator" in js
    assert "Risk gate evaluator" in js
    assert "No interactive approval action exists" in js
    assert "SV1.15 Hypothesis Experiments" in html
    assert "experiment-replay-filter" in html
    assert "SV1.16 True Replay Results" in js
    assert "SV1.17 True Replay Round 1" in js
    assert "SV1.17 Full-Suite True Replay" in js
    assert "sv117_true_replay_round1" in js
    assert "sv117_true_replay_full_suite" in js
    assert "strategy_validation_sv1_17_true_replay_experiments_summary.json" in js
    assert "SV117_REPLAY_ROWS" in js
    assert "SV117_FULL_SUITE_FINDINGS" in js
    assert "sv116_true_replay" in js
    assert "SV116_REPLAY_ROWS" in js
    assert "lower_rsi_floor_trend_intact_v1" in js
    assert "lower_rsi_floor_trend_intact_v2_narrow" in js
    assert "lower_rsi_support_confirmed_v1" in js
    assert "lower_rsi_ema10_hold_no_resistance_v1" in js
    assert "true_forward_replay_research_only" in js
    assert "variant minus baseline" in js
    assert "baseline remained strongest" in js
    assert "completed-trade overlay, still negative" in html
    assert "Methodology Boundary" in html
    assert "not true forward replays" in html
    assert "data-view=\"strategy\"" in html
    assert "Strategy Logic" in html
    assert "EMA5 > EMA10 > SMA20" in html
    assert "MACD > signal and histogram >= 0" in html
    assert "RSI reaches the sleeve trim threshold" in html
    assert "Load JSON" in html
    assert "setActiveView" in js
    assert "SV115_VARIANTS" in js
    assert "sideways_regime_avoidance_15m" in js
    assert "higher_low_confirmation_20c" in js
    assert "completed_trade_overlay_estimate" in js
    assert "lookahead_diagnostic_proxy" in js
    assert "upper-bound only; not candidate" in js
    assert "No variant is authorized for production, paper trading, or live trading." in js
    assert "No paper trading, live trading, routing, execution behavior, or strategy authorization follows from this replay." in js
    assert "reports/strategy_validation_reviews/sv1_13_2_dynamic_equity_20260507T104500Z" in js
    assert "dynamic_equity_pct" in js
    assert "Ending Equity" in js
    assert "calls_private_exchange_endpoints" in js
    assert "calls_exchange_order_endpoints" in js
    assert "Manual review" in js
    assert "paper_trading_auto_approved" not in js
