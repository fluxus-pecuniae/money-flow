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
    assert "Evidence Dashboard" in html
    assert "Trying to load regenerated SV2.0.2 canonical evidence packs." in html
    assert "evidence-date-start" in html
    assert "evidence-date-end" in html
    assert "evidence-date-clear" in html
    assert "fresh 10k slice" in js
    assert "rebased_from_date_filter" in js
    nav = html[html.index('<nav class="view-tabs"') : html.index("</nav>", html.index('<nav class="view-tabs"'))]
    assert 'data-view="experiments"' not in nav
    assert 'data-view-panel="experiments"' not in html
    assert 'data-view="historical-replay"' in nav
    assert 'data-view="evidence"' in nav
    assert 'data-view="evidence-lab"' in nav
    assert 'data-view="audit-review"' in nav
    assert 'data-view="paper-observation"' in nav
    assert 'data-view="strategy"' in nav
    assert 'data-view="uat-shadow"' not in nav
    assert 'data-view="uat-cockpit"' not in nav
    assert nav.index('data-view="strategy"') < nav.index('data-view="historical-replay"')
    assert nav.index('data-view="historical-replay"') < nav.index('data-view="evidence"')
    assert nav.index('data-view="evidence"') < nav.index('data-view="evidence-lab"')
    assert nav.index('data-view="evidence-lab"') < nav.index('data-view="audit-review"')
    assert nav.index('data-view="audit-review"') < nav.index('data-view="paper-observation"')
    assert 'data-view="historical-replay" aria-selected="true"' in nav
    assert "Money Flow UAT Workstation" in html
    assert "UAT Chart Cockpit" in html
    assert "Markets" in html
    assert "Order Book" in html
    assert "Market Info" in html
    assert "Signal Context" in html
    assert "Risk Context" in html
    assert "data-uat-bottom-tab=\"routed\"" in html
    assert "data-uat-bottom-tab=\"shadow\"" in html
    assert "data-uat-bottom-tab=\"balances\"" in html
    assert "data-uat-bottom-tab=\"lifecycle\"" in html
    assert "data-uat-bottom-tab=\"audit\"" in html
    assert "UAT2 Shadow Run" in html
    assert "uat2_shadow_strategy_top20_observation_summary.json" in js
    assert "renderUatDashboard" in js
    assert "TradingView Lightweight Charts" in js
    assert "CandlestickSeries" in js
    assert "renderUatRightRail" in js
    assert "renderUatBottomTabs" in js
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
    assert "Unified dry-run preflight" in js
    assert "Runtime full-blocker propagation" in js
    assert "Numeric edge-case validation" in js
    assert "Artifact label boundary enforcement" in js
    assert "Dry-run executable gate service" in js
    assert "global orders disabled; sandbox orders separately gated" in js
    assert "No interactive approval action exists" in js
    assert "SV1.15 Hypothesis Experiments" not in html
    assert "experiment-replay-filter" not in html
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
    assert "completed-trade overlay, still negative" not in html
    assert "Methodology Boundary" not in html
    assert "not true forward replays" not in html
    assert "data-view=\"strategy\"" in html
    assert "Strategy Logic" in html
    assert "Variant Strategy Ideas" in html
    assert "avoid_low_rolling_range_20" in html
    assert "avoid_low_rolling_range_50" in html
    assert "mf_orig_stage_filter_only_full_equity" in html
    assert "mf_orig_stage2_pullback_reclaim_full_equity" in html
    assert "mf_orig_1d_stage2_5_20_crossover_full_equity" in html
    assert "mf_orig_1d_stage2_breakout_resistance_full_equity" in html
    assert "MF_ORIG_FULL_EQUITY_STRATEGY_IDS" in js
    assert "isVisibleDashboardStrategyRow" in js
    assert "HIDDEN_DASHBOARD_SYMBOLS" in js
    assert "isVisibleDashboardSymbol" in js
    assert '"SHIB"' in js
    assert '"OKB"' in js
    assert "<span>mf_orig_stage2_pullback_reclaim</span>" not in html
    assert "<span>mf_orig_1d_stage2_5_20_crossover</span>" not in html
    assert "<span>mf_orig_1d_stage2_breakout_resistance</span>" not in html
    assert "Stop / Exit Replay Ideas" not in html
    assert "Entry Timing Ideas" not in html
    assert "fixed_stop_loss_pct_*" not in html
    assert "macd_histogram_*" not in html
    assert "They do not change production Money Flow v1.2" in html
    assert ".variant-strategy-grid" in css
    assert "1D / sleeve_1d" not in html
    assert "<td>1D</td>" in html
    assert "EMA5 > EMA10 > SMA20" in html
    assert "MACD > signal and histogram >= 0" in html
    assert "RSI reaches the sleeve trim threshold" in html
    assert "Load JSON" in html
    assert "hero-load-copy" in html
    assert "review-status" not in html
    assert "local review" not in js
    assert html.index("SV2.0.2 canonical evidence packs") < html.index('<nav class="view-tabs"')
    assert html.index("Load JSON") < html.index('<nav class="view-tabs"')
    assert "setActiveView" in js
    assert "SV115_VARIANTS" in js
    assert "sideways_regime_avoidance_15m" in js
    assert "higher_low_confirmation_20c" in js
    assert "completed_trade_overlay_estimate" in js
    assert "lookahead_diagnostic_proxy" in js
    assert "upper-bound only; not candidate" in js
    assert "No variant is authorized for production, paper trading, or live trading." in js
    assert "No paper trading, live trading, routing, execution behavior, or strategy authorization follows from this replay." in js
    assert "SV2.0.2 canonical packs loaded" in js
    assert "regenerated canonical pack JSON files loaded" in js
    assert "Legacy dynamic equity reports loaded" not in js
    assert "SV202_DASHBOARD_CHART_FILES" in js
    assert "sv2_0_2_dashboard_chart_data" in js
    assert "money_flow_v1_2_canonical" in js
    assert "Money Flow v1.2" in js
    assert "Money Flow v1.1" not in js
    assert "HIDDEN_DASHBOARD_STRATEGY_IDS" in js
    assert 'selectedComponent: "sleeve_1d"' in js
    assert "defaultEvidenceComponent" in js
    assert "dashboard-theme-selector" in html
    assert "Dark" in html
    assert "Light" in html
    assert "Red Zone" in html
    assert "DASHBOARD_THEME_STORAGE_KEY" in js
    assert 'stored : "red-zone"' in js
    assert 'safeTheme = DASHBOARD_THEMES.has(theme) ? theme : "red-zone"' in js
    assert "applyDashboardTheme" in js
    assert "dashboardChartColors" in js
    assert "--color-chart-surface" in css
    assert "--color-chart-surface: #d7dce2" in css
    assert "--color-chart-grid" in css
    assert "--color-chart-candle-up" in css
    assert "--color-chart-candle-up: #f5f7f2" in css
    assert "--color-chart-candle-down: #050607" in css
    assert "--color-surface-glass" in css
    assert 'html[data-theme="light"]' in css
    assert 'html[data-theme="red-zone"]' in css
    assert "#17202a" in css
    assert "var(--color-chart-panel)" in css
    assert "var(--color-chart-grid-muted)" in css
    assert "chartColors.background" in js
    assert "chartColors.candleUp" in js
    assert ".theme-control" in css
    assert "evidence-replay-strategy-filter" in html
    assert "evidence-replay-fill-filter" in html
    assert "evidence-period-filter" in html
    assert "run-ledger-totals" in html
    assert "Strategy Comparison" in html
    assert "strategy-comparison-left-strategy" in html
    assert "strategy-comparison-right-strategy" in html
    assert "strategy-comparison-symbol" in html
    assert "strategy-comparison-timeframe" in html
    assert "strategy-comparison-fill" in html
    assert "strategy-comparison-chart" in html
    assert "strategyComparison" in js
    assert "renderStrategyComparison" in js
    assert "strategyComparisonVerdict" in js
    assert "STRATEGY_COMPARISON_ALL_STRATEGIES_ID" in js
    assert "All strategies" in js
    assert "strategyComparisonSideReplays" in js
    assert "selectableIds = [STRATEGY_COMPARISON_ALL_STRATEGIES_ID, ...ids]" in js
    assert "leftStrategyId === STRATEGY_COMPARISON_ALL_STRATEGIES_ID" in js
    assert "strategyComparisonLineClass" in js
    assert "line-alt-1" in css
    assert "${winner} looks better" in js
    assert "Strategy A has higher net PnL" in js
    assert "Strategy B has higher net PnL" in js
    assert ".strategy-comparison-panel" in css
    assert ".comparison-line" in css
    assert "comparison-axis-label" in js
    assert "comparison-endpoint-label" in css
    assert "strategyComparisonEquitySeries" in js
    assert "strategyComparisonEndpointMarkup" in js
    assert "exact selected replay JSON" in js
    assert "Equity value (USDC)" in js
    assert ">Time<" in js
    assert "evidenceReplayStrategyId" in js
    assert "EVIDENCE_ALL_REPLAY_STRATEGIES_ID" in js
    assert "pt_rt1_1c_24h_dry_run/summary.json" in js
    assert "All replay strategies" in js
    assert 'timeframe: "1d"' in js
    assert 'canonicalTimeframe(defaultReplay.timeframe || "1d")' in js
    assert "renderEvidenceStrategyFilter" in js
    assert "renderEvidenceReplayFillFilter" in js
    assert "renderEvidencePeriodFilter" in js
    assert "evidencePeriodOptions" in js
    assert "evidencePeriodMatches" in js
    assert 'evidencePeriod: "all_periods"' in js
    assert "All periods" in js
    assert "evidenceReplayFillAssumption" in js
    assert "evidenceReplayRunLedgerRows" in js
    assert "sorEv3SummaryReplays" in js
    assert "avoid_low_rolling_range_20" in js
    assert "avoid_low_rolling_range_50" in js
    assert "timeframeSortRank" in js
    assert "SV202_CANONICAL_TIMEFRAMES.indexOf(canonicalTimeframe(timeframe))" in js
    assert "runLedgerSortButton" in js
    assert "data-run-ledger-sort-key" in js
    assert "sortRunLedgerRows" in js
    assert "runLedgerTotals" in js
    assert "Total Ending Equity" in js
    assert "Total PnL" in js
    assert "Avg Win Rate" in js
    assert "runLedgerFilterControls" not in js
    assert "Ending equity min" not in js
    assert "Net PnL min" not in js
    assert "Drawdown min" not in js
    assert "renderComponentCards(selected)" in js
    assert ".component-card-title" in css
    assert "font-size: 12px;" in css
    assert ".run-ledger-sort-button" in css
    assert ".run-ledger-totals" in css
    assert ".run-ledger-filters" not in css
    assert "Canonical evidence packs / batch reports" in js
    assert "classifyEvidenceReplayResult" in js
    assert "improved_pnl_drawdown" in js
    assert "improved_pnl_not_drawdown" in js
    assert "improved_drawdown_not_pnl" in js
    assert "same_result" in js
    assert "no bueno" in js
    assert "result-pill" in css
    assert "result-same" in css
    assert 'id="historical-replay-arrow-descriptions-toggle" type="checkbox">' in html
    assert html.index('id="historical-replay-equity-panel"') < html.index('id="historical-replay-chart"')
    assert "historical-data-summary-card" in js
    assert "historical-data-summary-grid" in css
    assert "historical-data-summary-warning-row" in js
    assert "dynamic_equity_pct" not in js
    assert "Ending Equity" in js
    assert "calls_private_exchange_endpoints" in js
    assert "calls_exchange_order_endpoints" in js
    assert "Manual review" in js
    assert "paper_trading_auto_approved" not in js


def test_pt_rt1_paper_observation_dashboard_tab() -> None:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    css = Path("apps/dashboard/evidence-dashboard.css").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    summary = Path("docs/pt_rt1_real_time_paper_observation_and_testnet_plumbing_summary.json").read_text(encoding="utf-8")

    nav = html[html.index('<nav class="view-tabs"') : html.index("</nav>", html.index('<nav class="view-tabs"'))]
    assert 'data-view="paper-observation"' in nav
    assert 'data-view-panel="paper-observation"' in html
    assert "Paper Observation" in html
    assert "PT-RT1 forward observation" in html
    assert "10 isolated 10,000 USDC synthetic paper ledgers" in html
    assert "Paper observation only" in html
    assert "No real capital" in html
    assert "No live trading" in html
    assert "No exchange orders from strategy lane" in html
    assert "Public mainnet data is strategy truth" in html
    assert "Testnet probes are plumbing only" in html
    assert "display-only filters" in html
    assert "not canonical evidence" in html
    assert "not backend replay" in html
    assert "paper-observation-summary-cards" in html
    assert "paper-runtime-control-title" in html
    assert "paper-runtime-duration" in html
    assert "paper-runtime-output" in html
    assert "paper-runtime-start" in html
    assert "paper-runtime-stop" in html
    assert "paper-runtime-control-status" in html
    assert "Mac caffeinate" in html
    assert "--disable-testnet-probes" in html
    assert "--public-mainnet-only" in html
    assert "This creates synthetic paper decisions only" in html
    assert "No exchange orders are created" in html
    assert "paper-observation-connection-status" in html
    assert "paper-observation-lane-filter" in html
    assert "paper-observation-scanner-table" in html
    assert "paper-observation-signal-table" in html
    assert "Signal Generation" in html
    assert "Market Data Health" not in html
    assert "paper-observation-lane-table" in html
    assert "paper-observation-lane-detail" in html
    assert "paper-observation-wildcard-diagnostics" in html
    assert "paper-observation-live-chart" in html
    assert "paper-observation-open-positions" in html
    assert "paper-observation-closed-trades" in html
    assert "paper-observation-risk-table" in html
    assert "paper-observation-probe-status" in html
    assert ".paper-observation-view" in css
    assert ".paper-observation-controls" in css
    assert ".paper-runtime-control" in css
    assert "DEFAULT_PT_RT1_SUMMARY_FILES" in js
    assert "/api/paper-runtime/status" in js
    assert "/api/paper-runtime/start" in js
    assert "/api/paper-runtime/stop" in js
    assert "startPaperRuntime" in js
    assert "stopPaperRuntime" in js
    assert "Start/stop requires launching the local control server." in js
    assert "Static dashboard servers can still display data" in js
    assert "enable-testnet-probes" not in js
    assert "DEFAULT_SV21_BROAD_SUMMARY_FILES" in js
    assert "SV21_BROAD_HISTORICAL_REPLAY_TIMESTAMP" in js
    assert "20260516T091500Z" in js
    assert "SV21_BROAD_PERIODS" in js
    assert "SV21_BROAD_CANDIDATE_STRATEGY_IDS" in js
    assert "mf_orig_stage_filter_only_full_equity" in js
    assert "mf_orig_stage2_pullback_reclaim_full_equity" in js
    assert "wildcard_volatility_expansion_breakout" in js
    assert "sv2_1_broad_hyperliquid_1d_period_evidence_summary.json" in js
    assert "loadDefaultSv21BroadEvidenceBatches" in js
    assert "sv21BroadSummaryReplays" in js
    assert "sv21BroadSelectedChartDataPath" in js
    assert "summary.candidate_evidence_status?.evidence_pack_paths" in js
    assert "SV21_BROAD_BATCH_LOAD_LIMIT = 3000" in js
    assert "compactRunSummaryFromRun" in js
    assert "sv21RunSummaryByKey" in js
    assert "replaySummaryFromCompactRun" in js
    assert "sv21BroadPackSlug" in js
    assert "row.evidence_pack_path" in js
    assert "summary: runSummaryByKey.get" in js
    assert "historical-replay-period-filter" in html
    assert "_sv21_replay.json" in js
    assert "sv2_1_broad_1d_dashboard_chart_data" in js
    assert "historicalReplayPeriodMatches" in js
    assert "period: \"ALL\"" in js
    assert "<th>Period</th>" in js
    assert "evidence_pack_paths" in js
    assert "SV2.0.2 + SV2.1 evidence packs loaded" in js
    assert "SV2.1 founder-approved 1D period pack JSON files loaded" in js
    assert "pt_rt1_1b_hyperliquid_live_market_data_and_runtime_readiness_summary.json" in js
    assert "renderPaperObservationConnectionStatus" in js
    assert "pt_rt1_real_time_paper_observation_and_testnet_plumbing_summary.json" in js
    assert "renderPaperObservation" in js
    assert "renderPaperObservationLaneDetail" in js
    assert "renderPaperObservationWildcardDiagnostics" in js
    assert "https://api.hyperliquid.xyz/info" in js
    assert "HYPERLIQUID_MAINNET_PUBLIC_INFO_URL" in js
    assert "PAPER_OBSERVATION_MARKET_REFRESH_MS = 1000" in js
    assert "PAPER_OBSERVATION_MARKET_STALE_MS = 120000" in js
    assert "startPaperObservationMarketPolling" in js
    assert "hyperliquid_mainnet_candleSnapshot_browser_poll" in js
    assert "liveBookPayload" not in js
    assert "fetchPaperObservationBooks" not in js
    assert "paper_observation_public_mainnet_connected" in js
    assert "data-paper-observation-symbol" in js
    assert "paper-observation-watchlist-table" in js
    assert "<th>Symbol</th>" in js
    assert "<th>Bid</th>" not in js
    assert "<th>Ask</th>" not in js
    assert "<th>Mid price</th>" in js
    assert "<th>Health</th>" in js
    assert "paperObservationMdHealth" in js
    assert "renderPaperObservationSignalGeneration" in js
    assert "intended_entry_signals" in js
    assert "entry_recorded" in js
    watchlist_renderer = js[js.index("function renderPaperObservationScanner") : js.index("function renderPaperObservationSignalGeneration")]
    assert "<th>Venue symbol</th>" not in watchlist_renderer
    assert "<th>Reason codes</th>" not in watchlist_renderer
    assert ".paper-observation-tick" in css
    assert ".paper-observation-watchlist-table" in css
    assert "dashboard_live_chart_public_info_endpoint_not_allowlisted" in js
    assert "private_or_order_payload_forbidden" in js
    assert "Hyperliquid public mainnet info endpoint" in summary
    assert "money_flow_v1_2_baseline" in summary
    assert "avoid_low_rolling_range_50" in summary
    assert "avoid_low_rolling_range_20" in summary
    assert "mf_orig_stage_filter_only_full_equity" in summary
    assert "mf_orig_stage2_pullback_reclaim_full_equity" in summary
    assert "mf_orig_1d_stage2_5_20_crossover_full_equity" in summary
    assert "mf_orig_1d_stage2_breakout_resistance_full_equity" in summary
    assert "wildcard_btc_regime_guard" in summary
    assert "wildcard_multi_timeframe_alignment" in summary
    assert "wildcard_volatility_expansion_breakout" in summary
    assert "TRON" in summary
    assert "TRX" in summary
    assert "PEPE" in summary
    assert "kPEPE" in summary
    assert "pepe_kpepe_unit_semantics_deferred" in summary
    assert "okb_support_not_confirmed" in summary
    assert "PT_RT1_TESTNET_PROBES_ENABLED" in summary
    assert "TESTNET FILLS MUST NOT UPDATE STRATEGY PAPER PNL" in summary
    assert "order-button" not in html
    assert "live trading approved: yes" not in html.lower()


def test_ev_audit1_audit_review_dashboard_tab() -> None:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    css = Path("apps/dashboard/evidence-dashboard.css").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    summary = Path("docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review_summary.json").read_text(encoding="utf-8")

    nav = html[html.index('<nav class="view-tabs"') : html.index("</nav>", html.index('<nav class="view-tabs"'))]
    assert 'data-view="audit-review"' in nav
    assert nav.index('data-view="evidence-lab"') < nav.index('data-view="audit-review"')
    assert 'data-view-panel="audit-review"' in html
    assert "Audit Review" in html
    assert "EV-AUDIT1 review" in html
    assert "Scope: audit-only" in html
    assert "Canonical baseline: SV2.0.2" in html
    assert "Production approval: no" in html
    assert "Paper/live approval: no" in html
    assert "No strategy is approved for production, paper runtime, or live trading." in html
    assert "audit-review-verdict-cards" in html
    assert "audit-review-scorecard" in html
    assert "audit-review-paper-readiness" in html
    assert "audit-review-top-hypotheses" in html
    assert "audit-review-worst-hypotheses" in html
    assert "audit-review-winning-trades" in html
    assert "audit-review-losing-trades" in html
    assert "audit-review-losing-streaks" in html
    assert "audit-review-issues" in html
    assert "audit-review-data-integrity" in html
    assert "audit-review-inventory" in html

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
    assert '"audit-review"' in js
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


def test_sor_ev21_evidence_lab_static_ui() -> None:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    css = Path("apps/dashboard/evidence-dashboard.css").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    report = Path("docs/sor_ev2_2_variant_chart_overlay.md").read_text(encoding="utf-8")

    nav = html[html.index('<nav class="view-tabs"') : html.index("</nav>", html.index('<nav class="view-tabs"'))]
    assert "Evidence Lab" in nav
    assert 'data-view="evidence-lab"' in nav
    assert 'data-view="experiments"' not in nav
    assert "SV1.15 Hypothesis Experiments" not in html
    assert "Evidence Lab / Variant Review" in html
    assert "SOR-EV1/SOR-EV2/SOR-EV3 research variants" in html
    assert "Canonical baseline: SV2.0.2" in html
    assert "Variant status: evidence-only" in html
    assert ".evidence-lab-badges" in css
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in css
    assert "Production rules changed: no" not in html
    assert "Production rules" not in js
    assert "Live approval: no" in html
    assert "Orders submitted: no" in html
    assert "Only true_forward_replay variants can become candidates for deeper evidence" in html
    assert "Dashboard date filters are display-only recalculations from loaded trades" in html
    assert "Variant Summary Matrix" in html
    assert "Control Pockets" in html
    assert "Worst Trades" in html
    assert "Late Entry Analysis" in html
    assert "Large Adverse Candle Analysis" in html
    assert "RSI / MACD Rejections" in html
    assert "Variant Chart Overlay" in html
    assert "Founder Candidate: avoid_sideways_low_volatility" in html
    assert "Original Money Flow Reconstruction" in html
    assert "Latest MF-ORIG-EV2 multi-timeframe evidence-pack run" in html
    assert "founder-review labels separate promising, mixed, deferred, and hard-rejected outcomes" in html
    assert "evidence-lab-overlay-symbol" in html
    assert "evidence-lab-overlay-timeframe" in html
    assert "evidence-lab-overlay-fill" in html
    assert "evidence-lab-overlay-variant" in html
    assert "evidence-lab-overlay-mode" in html
    assert "evidence-lab-toggle-large-loss" in html
    assert "evidence-lab-toggle-stop-exits" in html
    assert "evidence-lab-toggle-late-extension" in html
    assert "evidence-lab-toggle-adverse-candles" in html
    assert "evidence-lab-toggle-ma-breaks" in html
    assert "evidence-lab-toggle-hide-baseline-entries" in html
    assert "evidence-lab-clear-focus" in html
    assert "Worst Trades Focus" in html
    assert "Control Pocket View" in html
    assert html.index("Variant Chart Overlay") < html.index("Variant Summary Matrix")
    assert html.index("Variant Summary Matrix") < html.index("Control Pockets")

    assert "sor_ev1_money_flow_trade_loss_anatomy_and_variants_summary.json" in js
    assert "sor_ev2_true_forward_stop_and_rejected_signal_replay_summary.json" in js
    assert "sor_ev3_avoid_sideways_low_volatility_summary.json" in js
    assert "mf_orig_ev1_original_money_flow_reconstruction_summary.json" in js
    assert "mf_orig_ev2_multitimeframe_evidence_summary.json" in js
    assert "MF_ORIG_EV2_DASHBOARD_CHART_FILES" in js
    assert "mf_orig_ev2_dashboard_chart_data" in js
    assert "mfOrigEv2SummaryReplays" in js
    assert "sv202SummaryReplaysFromBatches" in js
    assert "loadHistoricalReplayChartData" in js
    assert "sv202SelectedChartDataPath" in js
    assert "mfOrigEv2SelectedChartDataPath" in js
    assert "safeReplayPathSegment" in js
    assert "_sv202_replay.json" in js
    assert "_mf_orig_ev2_replay.json" in js
    assert js.index('payload?.report === "mf_orig_ev2_dashboard_chart_data"') < js.index('startsWith("MF-ORIG-EV2")')
    assert "selected chart data loads lazily" in js
    assert "for (const path of SV202_DASHBOARD_CHART_FILES)" not in js
    assert "[...SV202_DASHBOARD_CHART_FILES, ...MF_ORIG_EV2_DASHBOARD_CHART_FILES]" not in js
    sv202_builder = Path("scripts/build_sv202_dashboard_chart_data.py").read_text(encoding="utf-8")
    mf_orig_builder = Path("scripts/build_mf_orig_ev2_multitimeframe_evidence.py").read_text(encoding="utf-8")
    assert 'selected_output_root = output_root / "selected"' in sv202_builder
    assert 'selected_output_root = output_root / "selected"' in mf_orig_builder
    assert "selected_files_written" in sv202_builder
    assert "_sv202_replay.json" in sv202_builder
    assert "_mf_orig_ev2_replay.json" in mf_orig_builder
    assert "renderEvidenceLabFounderCandidate" in js
    assert "renderEvidenceLabMfOrig" in js
    assert "data_not_available_in_mf_orig_bundle" in js
    assert "MF-ORIG-EV1.1 is a corrected replay/report run" in js
    assert "not a new canonical evidence-pack run" in js
    assert "MF-ORIG-EV2 generated multi-timeframe evidence packs" in js
    assert "positive 1d pockets" in js
    assert "accounting_invariant_summary" in js
    assert "blocked_open_signals" in js
    assert "signals, not canonical trade-count reduction" in js
    assert "Promising labels" in js
    assert "metric-cell-full-row" in js
    assert ".metric-cell-full-row" in css
    assert ".compact-grid" in css
    assert "FOUNDER_LABEL_RANK" in js
    assert "evidenceLabFounderLabelRank" in js
    assert "sortedRows.map((row)" in js
    assert "sortedVariants.map" in js
    assert "Founder Label" in js
    assert "Review Status" in js
    assert "Hard Rejected" in js
    assert "promising_high_pnl_control_preserved_trade_count_risk" in js
    assert "promising_chop_filter_control_risk" in js
    assert "promising_extension_filter_overfit_risk" in js
    assert "promising_diagnostic_only" in js
    assert "mixed_positive_pnl_drawdown_risk" in js
    assert "not_promoted_no_op" in js
    assert "deferred_needs_true_forward_replay" in js
    assert "founder_review_label" in js
    assert "promotion_status" in js
    assert "promotion_blockers" in js
    assert "promising_high_pnl_control_risk" in js
    assert "promising_control_pocket_risk" in js
    assert "rejected_not_promoted" not in js
    assert "SV202_CANONICAL_TIMESTAMP" in js
    assert "fixed_stop_loss" in js
    assert "atr_stop" in js
    assert "recent_low_stop" in js
    assert "large_bear_candle_exit" in js
    assert "earlier_macd_entry" in js
    assert "lower_rsi_trend_intact_entry" in js
    assert "extension_filter" in js
    assert "chop_filter" in js
    assert "completed_trade_overlay_estimate" in js
    assert "lookahead_diagnostic_proxy" in js
    assert "data_not_available_in_sor_ev_bundle" in js
    assert "exact_overlay_unavailable_from_sor_ev_bundle" in js
    assert "diagnostic_only_not_candidate" in js
    assert "renderEvidenceLabOverlayControls" in js
    assert "renderEvidenceLabOverlayChart" in js
    assert "evidence-lab-chart-stage" in js
    assert ".evidence-lab-chart-stage" in css
    assert "Historical price USDC" in js
    assert "evidenceLabBaselineMarkers" in js
    assert "evidenceLabVariantMarkers" in js
    assert "renderEvidenceLabWorstFocusTable" in js
    assert "renderEvidenceLabControlPocketView" in js
    assert "FOUNDER_REVIEW_MARKER_COLOR" in js
    assert "Hide baseline entries/exits" in html
    assert "hideBaselineMarkers" in js
    assert "evidenceLabClearFocus" in js
    assert "state.sorEv1Summary?.worst_trades || []" in js
    assert "Focused" in js
    assert "founder-review feature" in js
    assert "variant_chart_overlay_deferred_to_sor_ev2_2" not in js
    assert "production_approved" in js
    assert "No variant is approved for production" in js
    assert "No variant is production-approved" not in js
    assert "calls_private_exchange_endpoints" in js
    assert "calls_exchange_order_endpoints" in js
    assert "live trading approved: yes" not in html.lower()
    assert "production-approved" not in html.lower()
    assert "submit order" not in html.lower()
    assert "cancel order" not in html.lower()
    assert "retry button" not in html.lower()
    assert "SOR-EV2.2" in report
    assert "baseline markers" in report.lower()
    assert "variant markers" in report.lower()
    assert "worst-trade focus" in report.lower()
    assert "control-pocket view" in report.lower()
    assert "No variant is approved for production" in report


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
