from pathlib import Path


def test_evidence_dashboard_static_assets_exist() -> None:
    dashboard_dir = Path("apps/dashboard")

    assert (dashboard_dir / "index.html").exists()
    assert (dashboard_dir / "evidence-dashboard.css").exists()
    assert (dashboard_dir / "evidence-dashboard.js").exists()
    assert (dashboard_dir / "README.md").exists()
    assert (dashboard_dir / "DESIGN.md").exists()


def test_evidence_dashboard_uses_exchange_workstation_design_and_boundaries() -> None:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    css = Path("apps/dashboard/evidence-dashboard.css").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")

    assert "../../variables.css" in css
    assert "--color-shell" in css
    assert "--color-panel" in css
    assert "--color-green" in css
    assert "--color-red" in css
    assert "--color-amber" in css
    assert ".uat-workstation-grid" in css
    assert ".exchange-chart-shell" in css
    assert ".tradingview-lightweight-chart" in css
    assert ".uat-right-rail" in css
    assert ".uat-bottom-blotter" in css

    # DASH-IA1: the product is Money Flow OS with exactly two surfaces.
    assert "Money Flow OS" in html
    assert "Money Flow Evidence Dashboard" not in html
    nav = html[html.index('<nav class="view-tabs"') : html.index("</nav>", html.index('<nav class="view-tabs"'))]
    assert 'data-view="paper-observation"' in nav
    assert 'data-view="research-log"' in nav
    assert "Paper Trading" in nav
    assert "Research Log" in nav
    assert nav.index('data-view="paper-observation"') < nav.index('data-view="research-log"')
    assert 'data-view="paper-observation" aria-selected="true"' in nav
    assert 'data-view="research-log" aria-selected="false"' in nav
    # Retired navigation surfaces (DASH-PT1.1 + DASH-IA1).
    for retired in ("historical-replay", "evidence-lab", "strategy", "evidence\"", "audit", "experiments"):
        assert f'data-view="{retired}"' not in nav
    assert 'data-view-panel="historical-replay"' not in html
    assert 'data-view-panel="evidence-lab"' not in html
    assert 'data-view-panel="strategy"' not in html
    assert 'data-view-panel="evidence"' not in html
    for retired_label in ("Historical Replay", "The Lab", "Strategy</button>", "Audit Review"):
        assert retired_label not in nav

    # Research Log placeholder is data-driven from committed summaries.
    assert 'data-view-panel="research-log"' in html
    assert "research-log-verdict-list" in html
    assert "RLOG1" in html
    # RLOG1: the Research Log renders honest post-mortems from the committed
    # docs/research_log.json (built read-only by scripts/build_research_log.py).
    assert "docs/research_log.json" in js
    assert "renderResearchLog" in js
    assert "loadResearchLogSummaries" in js
    assert "RESEARCH_LOG_OUTCOME_CLASSES" in js
    # The naive status-string coloring is gone: outcome comes only from the
    # authored taxonomy, and the old fallback chain must not return.
    assert "researchLogVerdict(" not in js
    assert "payload?.verdict || payload?.conclusion" not in js
    assert "rlog-badge" in js
    assert "research-log-standing" in html
    assert "research-log-rail" in html
    assert "no strategy is production-approved and live trading is not approved" in html.lower()

    # Hidden legacy UAT regression surfaces are preserved (non-nav).
    assert "UAT Chart Cockpit" in html
    assert "UAT2 Shadow Run" in html
    assert "uat2_shadow_strategy_top20_observation_summary.json" in js
    assert "renderUatDashboard" in js
    assert "TradingView Lightweight Charts" in js
    assert "CandlestickSeries" in js
    assert "renderUatRightRail" in js
    assert "renderUatBottomTabs" in js

    # Theme system + chart palette stay intact.
    assert "dashboard-theme-selector" in html
    assert "DASHBOARD_THEME_STORAGE_KEY" in js
    assert 'safeTheme = DASHBOARD_THEMES.has(theme) ? theme : "red-zone"' in js
    assert "applyDashboardTheme" in js
    assert "dashboardChartColors" in js
    assert "--color-chart-surface" in css
    assert "--color-chart-candle-up: #f5f7f2" in css
    assert "--color-chart-candle-down: #050607" in css
    assert 'html[data-theme="light"]' in css
    assert 'html[data-theme="red-zone"]' in css
    assert "chartColors.background" in js
    assert "chartColors.candleUp" in js

    # Safety boundaries: no order controls anywhere.
    assert "setActiveView" in js
    assert "live trading approved: yes" not in html.lower()
    assert "submit order" not in html.lower()
    assert "cancel order" not in html.lower()


def test_pt_rt1_paper_observation_dashboard_tab() -> None:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    css = Path("apps/dashboard/evidence-dashboard.css").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    summary = Path("docs/pt_rt1_real_time_paper_observation_and_testnet_plumbing_summary.json").read_text(encoding="utf-8")

    nav = html[html.index('<nav class="view-tabs"') : html.index("</nav>", html.index('<nav class="view-tabs"'))]
    assert 'data-view="paper-observation"' in nav
    assert "Paper Trading" in nav
    assert "Paper Observation" not in nav
    assert 'data-view-panel="paper-observation"' in html
    assert "Cockpit / Global Filters" in html
    assert "Week 2 configured truth plus display filters" in html
    # DASH-IA1: Paper Trading is the default view.
    assert 'activeView: "paper-observation"' in js
    assert "Public mainnet candles remain strategy truth" in html
    assert "paper-observation-summary-cards" in html
    assert "paper-runtime-control-title" in html
    assert "paper-runtime-duration" in html
    assert "paper-runtime-output" in html
    assert "paper-runtime-start" in html
    assert "paper-runtime-stop" in html
    assert "paper-runtime-control-status" in html
    assert "paper-runtime-log-files" in html
    assert 'id="paper-observation-terminal-grid"' in html
    assert "paper-observation-left-rail" in html
    assert "paper-observation-center-stage" in html
    assert "paper-observation-right-rail" in html
    assert 'id="paper-observation-bottom-blotter"' in html
    assert "paper-observation-blotter-tabs" in html
    assert 'data-paper-terminal-tab="open"' in html
    assert 'data-paper-terminal-tab="closed"' in html
    assert 'data-paper-terminal-tab="signals"' in html
    assert 'data-paper-terminal-tab="lifecycle"' in html
    assert 'data-paper-terminal-tab="logs"' in html
    assert 'data-paper-terminal-tab="scoreboard"' in html
    assert 'data-paper-terminal-tab="diagnostics"' in html
    assert "paper-observation-daily-review" in html
    assert "paper-observation-final-review-card" in html
    assert "Daily Review / Anomaly Flags" in html
    assert "OBS-OS1 review pack" in html
    assert "Mac caffeinate" in html
    assert '<p class="eyebrow" id="paper-runtime-control-title">Runtime Control</p>' in html
    assert "<span>Starts an allowlisted local run with Mac caffeinate.</span>" in html
    assert "<span>Available only through `scripts/run_dashboard_control_server.py`.</span>" in html
    assert "paper-runtime-card-heading" in html
    assert ".paper-runtime-card-heading" in css
    assert ".paper-runtime-control-copy" in css
    assert "paper-runtime-control-message" in html
    assert "paperRuntimeControlMessage" in js
    assert "Control server message" in js
    assert "Latest runtime artifact" in js
    assert "Safety profile" in js
    assert "Week 2 active scope" in js
    assert "Runtime Logs" in js
    assert "Read-only log files" in js
    assert "scripts/watch_pt_rt1_runtime.py --status" in js
    assert "runtimeLogFiles: Array.isArray(payload?.runtime_log_files)" in js
    assert "runtimeLogFilesRenderKey" in js
    assert "paperTerminalTabs" in js
    assert "paperTerminalPanels" in js
    assert "setPaperObservationTerminalTab" in js
    assert 'terminalTab: "open"' in js
    assert "tail -n 50 -F" in js
    assert ".paper-runtime-log-files" in css
    assert ".paper-runtime-tail-command" in css
    assert "Baseline-only testnet lifecycle is separate from synthetic PnL" in html
    assert "Candidate lanes cannot send testnet orders" in html
    assert "Week 1 active with PT-RT1.5.3 hotfix" in html
    assert "PT-RT1.5.3 size hotfix smoke" in html
    assert "paper-observation-connection-status" in html
    assert "paper-observation-lane-filter" in html
    assert "paper-observation-scanner-table" in html
    assert "Watchlist" in html
    assert "paper-observation-health-banner" in html
    assert "paper-observation-timeframe-breakdown" in html
    assert "paper-observation-signal-table" in html
    assert "Signal / Decision Stream" in html

    # DASH-PT3 layout: Global Filters lead the body; the dense status strip
    # ("H1") is the final reference band after the Testnet footer; runtime +
    # live critical-state pills live in the header. Testnet transport remains
    # a full-width footer card below Daily Review (not in the right rail).
    assert "paper-observation-filterbar" in html
    assert "top-runtime-pill" in html
    assert "top-live-pill" in html
    assert "LIVE DISABLED" in html
    assert "NOT APPROVED" in html
    assert html.index("top-runtime-pill") < html.index("paper-observation-filterbar")
    assert html.index("paper-observation-filterbar") < html.index("paper-observation-terminal-grid")
    assert html.index("paper-observation-testnet-footer") < html.index("paper-observation-health-banner")
    assert html.index("paper-observation-daily-review") < html.index("paper-observation-health-banner")
    terminal_grid = html[
        html.index("paper-observation-terminal-grid") : html.index("paper-observation-bottom-blotter")
    ]
    assert "paper-observation-filterbar" not in terminal_grid
    assert "paper-observation-testnet-panel" not in terminal_grid
    assert terminal_grid.index("paper-observation-left-rail") < terminal_grid.index("paper-observation-center-stage")
    assert terminal_grid.index("paper-observation-center-stage") < terminal_grid.index("paper-observation-right-rail")
    assert terminal_grid.index("paper-observation-scanner-table") < terminal_grid.index("paper-observation-live-chart")
    assert terminal_grid.index("paper-observation-live-chart") < terminal_grid.index("paper-runtime-control-title")
    assert "paper-observation-testnet-footer" in html
    assert html.index("paper-observation-daily-review") < html.index("paper-observation-testnet-footer")
    assert html.index("paper-observation-testnet-footer") < html.index("paper-observation-probe-status")
    assert html.index("paper-observation-bottom-blotter") < html.index("paper-observation-open-positions")
    assert html.index("paper-observation-bottom-blotter") < html.index("paper-observation-daily-review")
    assert html.index("paper-observation-open-positions") < html.index("paper-observation-closed-trades")
    assert html.index("paper-observation-closed-trades") < html.index("paper-observation-signal-table")
    assert html.index("paper-observation-signal-table") < html.index("paper-observation-testnet-lifecycle")
    assert html.index("paper-observation-testnet-lifecycle") < html.index("paper-runtime-log-files")
    assert html.index("paper-runtime-log-files") < html.index("paper-observation-lane-table")
    assert html.index("paper-observation-lane-table") < html.index("paper-observation-summary-cards")
    assert html.index("paper-observation-summary-cards") < html.index("paper-observation-timeframe-breakdown")
    assert "paper-observation-lane-table" in html
    assert "paper-observation-lane-detail" in html
    paper_view = html[html.index('data-view-panel="paper-observation"') : html.index('id="uat-cockpit-view"')]
    assert "strategy-wildcard-diagnostics" not in html
    assert "Wildcard Diagnostics" not in html
    assert "paper-observation-live-chart" in paper_view
    assert "paper-observation-open-positions" in paper_view
    assert "paper-observation-closed-trades" in paper_view
    assert "paper-observation-risk-table" in paper_view
    assert "paper-observation-probe-status" in paper_view
    assert "paper-observation-testnet-lifecycle" in paper_view
    assert "paper-observation-connection-panel" in paper_view
    assert ".paper-observation-view" in css
    assert "paper-runtime-control-compact" in html
    assert "paper-observation-cockpit" in html
    assert ".paper-observation-cockpit" in css
    assert ".paper-runtime-control-compact" in css
    assert ".paper-observation-terminal-grid" in css
    # Skinnier rails: prototype-like proportions; the chart dominates.
    # DASH-PT3: rails widened (watchlist readable, Runtime Control untruncated);
    # the center chart remains the dominant flexible panel.
    assert "grid-template-columns: minmax(212px, 252px) minmax(0, 1fr) minmax(300px, 344px)" in css
    assert ".top-status-pill" in css
    assert "top-pill-blink" in css
    assert ".paper-observation-filterbar" in css
    assert ".paper-observation-testnet-footer" in css
    assert ".paper-observation-left-rail .paper-observation-watchlist-panel .data-table-shell" in css
    assert "height: 100%" in css
    assert ".paper-observation-right-rail .paper-runtime-control" in css
    assert ".paper-observation-left-rail" in css
    assert ".paper-observation-center-stage" in css
    assert ".paper-observation-right-rail" in css
    assert ".paper-observation-bottom-blotter" in css
    assert ".paper-observation-blotter-tabs" in css
    assert ".paper-observation-blotter-panel[hidden]" in css
    assert ".paper-observation-daily-review-grid" in css
    assert ".paper-observation-anomaly-list" in css
    assert ".paper-runtime-control-message" in css
    assert ".paper-observation-lower-diagnostics" in css
    assert ".paper-observation-controls" in css
    assert ".paper-runtime-control" in css
    assert "DEFAULT_PT_RT1_SUMMARY_FILES" in js
    assert "DEFAULT_PT_RT1_DECISION_LOG_FILES" in js
    assert "DEFAULT_PT_RT1_TRADE_LOG_FILES" in js
    assert "pt_rt1_6_week2_active/decisions.jsonl" in js
    assert "pt_rt1_6_week2_active/trades.jsonl" in js
    assert "pt_rt1_5_2_transport_smoke/testnet_order_lifecycle.jsonl" in js
    assert "slice(-60)" in js
    assert "MF-O" in js
    assert "RR20" in js
    assert "state.ptRt1TradeRows = rows" in js
    assert "state.ptRt1TradeSource = path" in js
    assert "DEFAULT_PT_RT1_TESTNET_LIFECYCLE_FILES" in js
    assert "DEFAULT_PT_RT1_DAILY_REVIEW_FILES" in js
    assert "reports/paper_reviews/pt_rt1_6_week2_active/latest_review.json" in js
    assert "obs_os1_week2_paper_observation_daily_review" in js
    assert "renderPaperObservationDailyReview" in js
    assert "No generated OBS-OS1 daily review loaded yet" in js
    assert "Synthetic Ledger only" in js
    assert "parsePaperObservationDecisionLog" in js
    assert "parsePaperObservationTradeLog" in js
    assert "parsePaperObservationTestnetLifecycleLog" in js
    assert "loadDefaultPtRt1TradeRows" in js
    assert "loadDefaultPtRt1TestnetLifecycleRows" in js
    assert "paperObservationClosedRowComplete" in js
    assert "paperObservationRecentSignalRows" in js
    assert "paperObservationLaneRuntimeRollup" in js
    assert "realizedEquity" in js
    assert "No paper decisions match the selected signal category" in js
    assert "/api/paper-runtime/status" in js
    assert "/api/paper-runtime/start" in js
    assert "/api/paper-runtime/stop" in js
    assert "--decision-log-mode" in Path("scripts/run_dashboard_control_server.py").read_text(encoding="utf-8")
    assert "startPaperRuntime" in js
    assert "stopPaperRuntime" in js
    assert "elements.paperRuntimeStart.disabled = control.running || control.inFlight" in js
    assert "decision_log_stats" in js
    assert "paperObservationBytes" in js
    assert "Start/stop requires launching the local control server." in js
    assert "paper_runtime_started_with_caffeinate" in js
    assert "runtime_started_with_mac_caffeinate" in js
    assert "const caffeinateLabel = control.running ? \"active\" : \"waiting_for_start\"" in js
    assert "paper-runtime-caffeinate-detail" in js
    assert "control.message || \"local_control_server_ready\"" in js
    assert "paper-runtime-safety-flags" in js
    assert "enable-baseline-testnet-transport" in Path("scripts/run_dashboard_control_server.py").read_text(encoding="utf-8")
    assert "pt-rt1-5-testnet-order-notional-usdc" in Path("scripts/run_dashboard_control_server.py").read_text(encoding="utf-8")
    assert "syncPaperRuntimeControlPolling" in js
    assert "state.activeView === \"paper-observation\"" in js
    assert "renderPaperObservationConnectionStatus" in js
    assert "renderPaperObservation" in js
    assert "renderPaperObservationLaneDetail" in js
    assert "paperObservationPaginationControls" in js
    assert "PAPER_OBSERVATION_PAGE_SIZE = 25" in js
    assert "Entry price" in js
    assert "Exit price" in js
    assert "synthetic public-mainnet paper PnL, not exchange fills" in js
    assert "paperObservationChartTarget" in js
    assert "paperObservationRuntimeMarkers" in js
    assert "const PAPER_OBSERVATION_RSI_PANE = 0" in js
    assert "const PAPER_OBSERVATION_PRICE_PANE = 1" in js
    assert "const PAPER_OBSERVATION_MACD_PANE = 2" in js
    assert "historicalConstantRows" in js
    assert "paperObservationRsiRows" in js
    assert "paperObservationMacdSeries" in js
    assert "renderPaperObservationIndicatorLegend" in js
    assert "data-paper-observation-indicator-legend" in js
    assert "Pane order: RSI, candles, MACD. Public mainnet display only." in js
    assert "paper_opened" in js
    assert "paper_closed" in js
    assert "Opened and closed synthetic markers" in html
    assert "https://api.hyperliquid.xyz/info" in js
    assert "HYPERLIQUID_MAINNET_PUBLIC_INFO_URL" in js
    assert "PAPER_OBSERVATION_MARKET_REFRESH_MS = 1000" in js
    assert "PAPER_OBSERVATION_MARKET_STALE_MS = 120000" in js
    assert "startPaperObservationMarketPolling" in js
    assert "hyperliquid_mainnet_candleSnapshot_browser_poll" in js
    assert "paper_observation_public_mainnet_connected" in js
    assert "data-paper-observation-symbol" in js
    assert "paper-observation-watchlist-table" in js
    assert "paper-observation-lifecycle-panel" in html
    assert ".paper-observation-lifecycle-panel .data-table-shell" in css
    assert "<th>Mid price</th>" in js
    assert "<th>Health</th>" in js
    watchlist_renderer = js[js.index("function renderPaperObservationScanner") : js.index("function paperObservationLaneRuntimeRollup")]
    assert "<th>Status</th>" not in watchlist_renderer
    assert "paperObservationMdHealth" in js
    assert "mid_stale_or_thin_tick" in js
    assert "mid_unavailable_but_candles_available" in js
    assert "candle_unavailable_blocking" in js
    assert "mid_health_blocks_strategy" in js
    assert "stale or missing mids are warning-only when candles are available" in js
    assert "renderPaperObservationSignalGeneration" in js
    assert "intended_entry_signals" in js
    assert "state.ptRt1DecisionRows" in js
    assert "synthetic_entry" in js
    assert "renderPaperObservationScanner();" in js
    assert ".paper-observation-tick" in css
    assert ".paper-observation-watchlist-table" in css
    assert ".paper-observation-pagination" in css
    assert "dashboard_live_chart_public_info_endpoint_not_allowlisted" in js
    assert "private_or_order_payload_forbidden" in js
    assert "Hyperliquid public mainnet info endpoint" in summary
    assert "money_flow_v1_2_baseline" in summary
    assert "TESTNET FILLS MUST NOT UPDATE STRATEGY PAPER PNL" in summary
    assert "order-button" not in html
    assert "live trading approved: yes" not in html.lower()


def test_ev_audit1_audit_review_data_stays_loadable_but_tab_is_hidden() -> None:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    css = Path("apps/dashboard/evidence-dashboard.css").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    summary = Path("docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review_summary.json").read_text(encoding="utf-8")

    nav = html[html.index('<nav class="view-tabs"') : html.index("</nav>", html.index('<nav class="view-tabs"'))]
    assert 'data-view="audit-review"' not in nav
    assert 'data-view-panel="audit-review"' not in html
    assert "Audit</button>" not in nav
    assert "Audit Review" not in html
    assert "EV-AUDIT1 review" not in html

    assert "DEFAULT_EV_AUDIT_SUMMARY_FILES" in js
    assert "ev_audit1_full_hypothesis_data_and_paper_readiness_review_summary.json" in js
    assert "ev_audit_summary" in js
    assert "state.evAuditSummary" in js
    assert "renderAuditReview" in js
    assert "renderAuditReviewVerdictCards" in js
    assert "renderAuditReviewScorecard" in js
    assert "renderAuditReviewPaperReadiness" in js
    assert "renderAuditReviewHypothesisTable" in js
    assert "renderAuditReviewTradeTable" in js
    assert "renderAuditReviewLosingStreaks" in js
    assert "renderAuditReviewIssues" in js
    assert "renderAuditReviewDataIntegrity" in js
    assert "renderAuditReviewInventory" in js
    assert '"audit-review"' not in js
    assert "data_not_available_in_audit_bundle" in js

    assert ".audit-review-view" in css
    assert ".audit-review-header" in css
    assert ".audit-review-verdict" in css
    assert ".audit-review-two-column" in css
    assert ".audit-score-bar" in css
    assert ".audit-score-fill" in css

    assert '"phase": "EV-AUDIT1"' in summary
    assert "no_strategy_has_clean_production_or_paper_candidate_status" in summary
    assert "paper_observation_ready_with_conditions" in summary


def test_evidence_lab_retired_but_research_artifacts_preserved() -> None:
    """DASH-IA1 retired The Lab (evidence-lab) navigation surface and its
    render code. The underlying SOR-EV / MF-ORIG evidence packs, summaries,
    builder scripts, and docs must all remain on disk as reference."""
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    report = Path("docs/sor_ev2_2_variant_chart_overlay.md").read_text(encoding="utf-8")

    nav = html[html.index('<nav class="view-tabs"') : html.index("</nav>", html.index('<nav class="view-tabs"'))]
    assert "The Lab" not in nav
    assert 'data-view="evidence-lab"' not in nav
    assert 'data-view-panel="evidence-lab"' not in html
    assert "renderEvidenceLab" not in js
    assert "evidenceLabOverlay" not in js

    # Nothing deleted from disk: artifacts stay as institutional memory.
    for doc in (
        "docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants_summary.json",
        "docs/sor_ev2_true_forward_stop_and_rejected_signal_replay_summary.json",
        "docs/sor_ev3_avoid_sideways_low_volatility_summary.json",
        "docs/mf_orig_ev1_original_money_flow_reconstruction_summary.json",
        "docs/mf_orig_ev2_multitimeframe_evidence_summary.json",
        "docs/sor_ev2_2_variant_chart_overlay.md",
    ):
        assert Path(doc).exists(), f"retired-surface artifact must stay on disk: {doc}"
    sv202_builder = Path("scripts/build_sv202_dashboard_chart_data.py").read_text(encoding="utf-8")
    mf_orig_builder = Path("scripts/build_mf_orig_ev2_multitimeframe_evidence.py").read_text(encoding="utf-8")
    assert 'selected_output_root = output_root / "selected"' in sv202_builder
    assert 'selected_output_root = output_root / "selected"' in mf_orig_builder
    assert "No variant is approved for production" in report

    # The Research Log lists these phases via docs/research_log.json, whose
    # Decision-Log blocks reference the committed summaries.
    research_log = Path("docs/research_log.json").read_text(encoding="utf-8")
    assert "sor_ev1_money_flow_trade_loss_anatomy_and_variants_summary.json" in research_log
    assert "sor_ev2_true_forward_stop_and_rejected_signal_replay_summary.json" in research_log
    assert "sor_ev3_avoid_sideways_low_volatility_summary.json" in research_log
    assert "mf_orig_ev1_original_money_flow_reconstruction_summary.json" in research_log
    assert "mf_orig_ev2_multitimeframe_evidence_summary.json" in research_log


def test_uat_cockpit_summary_header_only_shows_environment_card() -> None:
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    start = js.index("function renderUatCockpitSummaryCards()")
    end = js.index("function renderUatWatchlist()", start)
    summary_renderer = js[start:end]

    assert '["Environment", "sandbox/testnet", "no live endpoint"]' in summary_renderer
    for removed_label in (
        '["Market"',
        '["Timeframe"',
        '["Charting"',
        '["Live chart"',
        '["Paper"',
        '["Top-20"',
        '["Signal"',
        '["Route"',
        '["Records"',
        '["Paper equity"',
        '["Balance poll"',
        '["Orders"',
        '["Live / capital"',
    ):
        assert removed_label not in summary_renderer


def test_pt_rt1_4_paper_trading_command_center_active_timeframe_ui() -> None:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")

    assert "paper-observation-health-banner" in html
    assert "Weekly Scoreboard" in html
    assert "Timeframe Breakdown" in html
    assert "Watchlist" in html
    assert "Signal / Decision Stream" in html
    assert "paper-observation-review-window-filter" in html
    assert "paper-observation-signal-category-filter" in html
    assert html.index("paper-observation-terminal-grid") < html.index("paper-observation-bottom-blotter")
    assert html.index("paper-observation-controls") < html.index("paper-observation-live-chart")
    assert html.index("paper-observation-scanner-table") < html.index("paper-observation-live-chart")
    assert html.index("paper-observation-live-chart") < html.index("paper-runtime-control-title")
    assert html.index("paper-runtime-control-title") < html.index("paper-observation-probe-status")
    assert html.index("paper-observation-bottom-blotter") < html.index("paper-observation-open-positions")
    assert html.index("paper-observation-open-positions") < html.index("paper-observation-closed-trades")
    assert html.index("paper-observation-closed-trades") < html.index("paper-observation-signal-table")
    assert html.index("paper-observation-signal-table") < html.index("paper-observation-testnet-lifecycle")
    assert html.index("paper-observation-signal-table") < html.index("paper-observation-lane-table")
    assert 'timeframe: "1h"' in js
    assert 'PAPER_OBSERVATION_ACTIVE_TIMEFRAMES = ["1h", "4h", "1d"]' in js
    assert 'PAPER_OBSERVATION_DISABLED_TIMEFRAMES = ["15m"]' in js
    assert "disabled_for_week1_noise_reduction" in js
    assert "sum across active paper timeframes only: 1h + 4h + 1d" in js
    assert "15m paused / legacy" in js
    assert "<th>Mid price</th>" in js
    assert "<th>Health</th>" in js
    assert "no_activity_for_selected_timeframe" in js
    assert "Actual opens + intended entries" in js
    assert "No-trade / blocked" in js
    assert "Data unavailable" in js
    assert "Testnet order transport" in js
    assert "Audit-only shapes" in js
    assert "Money Flow v1.2 fresh baseline opens only" in js
    assert "Candidate transport" in js
    assert "Strategy PnL update" in js
    assert "order buttons" not in html.lower()
    assert "manual trade" not in html.lower()


def test_dash_pt1_1_week2_paper_trading_ui_truth() -> None:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")

    paper_view = html[html.index('data-view-panel="paper-observation"') : html.index('id="uat-cockpit-view"')]
    nav = html[html.index('<nav class="view-tabs"') : html.index("</nav>", html.index('<nav class="view-tabs"'))]

    assert "Audit</button>" not in nav
    assert "PT-RT1 forward observation" not in paper_view
    assert "Cockpit / Global Filters" in paper_view
    assert "Live Public Candles + Paper Markers" in paper_view
    assert "Runtime Control" in paper_view
    assert "Watchlist" in paper_view
    assert "Testnet Order Lifecycle" in paper_view
    assert "Open Synthetic Positions" in paper_view
    assert "Closed Synthetic Trades" in paper_view
    assert "Signal / Decision Stream" in paper_view
    # DASH-IA1 order: filters bar above the grid; testnet transport is the
    # full-width footer below Daily Review.
    assert paper_view.index("Cockpit / Global Filters") < paper_view.index("Watchlist")
    assert paper_view.index("Cockpit / Global Filters") < paper_view.index("Live Public Candles + Paper Markers")
    assert paper_view.index("Watchlist") < paper_view.index("Live Public Candles + Paper Markers")
    assert paper_view.index("Live Public Candles + Paper Markers") < paper_view.index("Runtime Control")
    assert paper_view.index("Runtime Control") < paper_view.index("Daily Review / Anomaly Flags")
    assert paper_view.index("Daily Review / Anomaly Flags") < paper_view.index("Testnet Order Transport")
    assert paper_view.index("Open Synthetic Positions") < paper_view.index("Daily Review / Anomaly Flags")
    assert paper_view.index("Open Synthetic Positions") < paper_view.index("Testnet Order Lifecycle")
    assert paper_view.index("Closed Synthetic Trades") < paper_view.index("Signal / Decision Stream")

    assert 'PAPER_OBSERVATION_WEEK2_ACTIVE_LANE_IDS = [\n    "money_flow_v1_2_baseline",\n    "avoid_low_rolling_range_20",\n    "mf_orig_1d_stage2_breakout_resistance_full_equity"' in js
    assert 'PAPER_OBSERVATION_WEEK2_ARCHIVED_LANE_IDS = [' in js
    assert 'PAPER_OBSERVATION_CONFIGURED_SYMBOLS = ["AVAX", "BNB", "BTC", "DOGE", "ETH", "HYPE", "SOL", "SUI", "XRP"]' in js
    assert "All active lanes" in js
    assert "All configured symbols" in js
    assert "paperObservationConfiguredLaneRow" in js
    assert "Scanner symbols\", String(paperObservationBaseScannerRows().length)" in js
    assert "paused_legacy_timeframe_excluded_from_active_week_scoring" in js
    assert "15m_paused_legacy" not in js

    # The Strategy tab is retired (DASH-IA1); lane truth lives in the Paper
    # Trading status strip (rendered from PAPER_OBSERVATION_WEEK2_LANE_POLICIES)
    # and the committed lane policies keep the Week 2 boundaries.
    assert 'id="strategy-view"' not in html
    assert "Week 2 Active Strategy Slate" not in html
    assert "Baseline-only gated testnet eligible" in js
    assert "Synthetic-only / no testnet" in js
    assert "PAPER_OBSERVATION_WEEK2_LANE_POLICIES" in js
    assert "paperObservationLaneChip" in js
    assert "renderPaperObservationHealthBanner" in js


def test_paper_trading_prefers_active_week_runtime_before_smoke_artifacts() -> None:
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")

    active_summary = "../../reports/paper_runtime/pt_rt1_6_week2_active/summary.json"
    legacy_active_summary = "../../reports/paper_runtime/pt_rt1_5_2_week1_active/summary.json"
    smoke_summary = "../../reports/paper_runtime/pt_rt1_5_3_transport_smoke/summary.json"
    active_lifecycle = "../../reports/paper_runtime/pt_rt1_6_week2_active/testnet_order_lifecycle.jsonl"
    legacy_active_lifecycle = "../../reports/paper_runtime/pt_rt1_5_2_week1_active/testnet_order_lifecycle.jsonl"
    smoke_lifecycle = "../../reports/paper_runtime/pt_rt1_5_3_transport_smoke/testnet_order_lifecycle.jsonl"

    assert js.index(active_summary) < js.index(legacy_active_summary)
    assert js.index(active_summary) < js.index(smoke_summary)
    assert js.index(active_lifecycle) < js.index(legacy_active_lifecycle)
    assert js.index(active_lifecycle) < js.index(smoke_lifecycle)
    assert 'output: "pt_rt1_6_week2_active"' in js
    assert "duration: payload?.duration || state.paperRuntimeControl.duration" in js
    assert "output: payload?.output || state.paperRuntimeControl.output" in js
    assert "const lifecycleRows = paperObservationTestnetLifecycleRows(summary);" in js
    assert "signedLifecycleRows.length" in js
    assert "<span>Order kill switch</span>" in js
    assert "<span>Lifecycle rows</span>" in js
