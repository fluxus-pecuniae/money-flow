(function () {
  "use strict";

  const DEFAULT_FILES = [
    "../../reports/strategy_validation_reviews/sv1_13_2_dynamic_equity_20260507T104500Z/money_flow_evidence_review.json",
    "../../reports/strategy_validation/money_flow_hyperliquid_public_ytd_recent_dynamic_equity_sleeve_15m/20260507T104500Z/batch_report.json",
    "../../reports/strategy_validation/money_flow_hyperliquid_public_ytd_recent_dynamic_equity_sleeve_1h/20260507T104500Z/batch_report.json",
    "../../reports/strategy_validation/money_flow_hyperliquid_public_ytd_recent_dynamic_equity_sleeve_4h/20260507T104500Z/batch_report.json",
  ];

  const DEFAULT_EXPERIMENT_SUMMARY_FILES = [
    "../../docs/strategy_validation_sv1_17_true_replay_experiments_summary.json",
  ];

  const DEFAULT_UAT2_SUMMARY_FILES = [
    "../../docs/uat2_shadow_strategy_top20_observation_summary.json",
  ];

  const SV115_BASELINE = [
    {
      component: "sleeve_15m",
      scenarios: 36,
      endingEquitySum: 274061.42,
      netPnlSum: -85938.58,
      minEndingEquity: 6459.22,
      maxDrawdown: 3645.61,
      trades: 7660,
    },
    {
      component: "sleeve_1h",
      scenarios: 36,
      endingEquitySum: 381997.91,
      netPnlSum: 21997.91,
      minEndingEquity: 8313.22,
      maxDrawdown: 2150.85,
      trades: 4484,
    },
    {
      component: "sleeve_4h",
      scenarios: 36,
      endingEquitySum: 287620.62,
      netPnlSum: -72379.38,
      minEndingEquity: 6772.35,
      maxDrawdown: 3492.34,
      trades: 1280,
    },
  ];

  const SV115_VARIANTS = [
    {
      id: "extension_limit_4h_1_5pct",
      label: "4h extension limit 1.5%",
      component: "sleeve_4h",
      baselineNet: -72379.38,
      variantNet: -41687.13,
      delta: 30692.25,
      methodology: "completed_trade_overlay_estimate",
      drawdown: 2179.32,
      filtered: 240,
      avoidedLosers: 196,
      missedWinners: 44,
      status: "overlay improved; needs true replay",
    },
    {
      id: "extension_limit_4h_2_0pct",
      label: "4h extension limit 2.0%",
      component: "sleeve_4h",
      baselineNet: -72379.38,
      variantNet: -66323.01,
      delta: 6056.37,
      methodology: "completed_trade_overlay_estimate",
      drawdown: 3093.98,
      filtered: 72,
      avoidedLosers: 52,
      missedWinners: 20,
      status: "overlay improved; needs true replay",
    },
    {
      id: "higher_low_confirmation_20c",
      label: "Higher-low confirmation",
      component: "sleeve_15m + sleeve_1h",
      baselineNet: -63940.66,
      variantNet: -81652.17,
      delta: -17711.51,
      methodology: "completed_trade_overlay_estimate",
      drawdown: 3645.61,
      filtered: 408,
      avoidedLosers: 251,
      missedWinners: 157,
      status: "deteriorated; damaged ETH 1h",
    },
    {
      id: "recent_low_invalidation_proxy_20c",
      label: "Recent-low invalidation proxy",
      component: "sleeve_1h + sleeve_4h",
      baselineNet: -50381.47,
      variantNet: 247743.31,
      delta: 298124.78,
      methodology: "lookahead_diagnostic_proxy",
      drawdown: 1937.18,
      filtered: 2088,
      avoidedLosers: 2088,
      missedWinners: 0,
      status: "upper-bound only; not candidate",
    },
    {
      id: "resistance_proximity_0_25pct",
      label: "Resistance proximity 0.25%",
      component: "all sleeves",
      baselineNet: -136320.05,
      variantNet: -107096.22,
      delta: 29223.83,
      methodology: "completed_trade_overlay_estimate",
      drawdown: 3492.34,
      filtered: 2974,
      avoidedLosers: 2251,
      missedWinners: 723,
      status: "overlay improved; slight ETH 1h damage",
    },
    {
      id: "resistance_proximity_0_50pct",
      label: "Resistance proximity 0.50%",
      component: "all sleeves",
      baselineNet: -136320.05,
      variantNet: -100502.45,
      delta: 35817.6,
      methodology: "completed_trade_overlay_estimate",
      drawdown: 3492.34,
      filtered: 5612,
      avoidedLosers: 4234,
      missedWinners: 1378,
      status: "overlay improved; damaged ETH 1h",
    },
    {
      id: "sideways_regime_avoidance_15m",
      label: "15m sideways avoidance",
      component: "sleeve_15m",
      baselineNet: -85938.58,
      variantNet: -6258.54,
      delta: 79680.04,
      methodology: "completed_trade_overlay_estimate",
      drawdown: 600.73,
      filtered: 6988,
      avoidedLosers: 5459,
      missedWinners: 1529,
      status: "reduced 15m losses; still negative",
    },
  ];

  const SV115_ETH_1H = [
    ["higher_low_confirmation_20c", 27143.25, 20406.69, -6736.57, "deteriorated"],
    ["recent_low_invalidation_proxy_20c", 27143.25, 118927.38, 91784.13, "preserved or improved, proxy caveat"],
    ["resistance_proximity_0_25pct", 27143.25, 26599.19, -544.06, "slightly deteriorated"],
    ["resistance_proximity_0_50pct", 27143.25, 3727.39, -23415.86, "damaged"],
  ];

  const SV115_FINDINGS = [
    "Most SV1.15 numbers are completed-trade overlay estimates, not full candle-by-candle forward replays.",
    "Recent-low invalidation is a lookahead diagnostic upper bound, not a candidate rule result until exact exit replay exists.",
    "Lower-RSI entry admission is not implemented; current evidence only supports RSI-zone attribution from completed trades.",
    "ETH 1h completed trades were stronger in the upper half of the current RSI band than the lower half.",
    "15m lower-band completed trades were negative across BTC, ETH, and SOL.",
    "4h RSI zones were negative across symbols in this campaign.",
    "ETH 1h continuation-style completed trades were stronger than pullback-style completed trades.",
    "No variant is authorized for production, paper trading, or live trading.",
  ];

  const SV115_METHODOLOGY = [
    "completed_trade_overlay_estimate: filters already-completed baseline trades; useful for ranking hypotheses, not authorizing rules.",
    "lookahead_diagnostic_proxy: uses completed-trade hindsight; current recent-low result is an upper-bound diagnostic only.",
    "reporting_only_attribution: labels completed trades without changing entries or exits.",
    "deferred_requires_rejected_signal_replay: lower-RSI admission needs rejected-signal instrumentation before true testing.",
  ];

  const EXPERIMENT_MODES = [
    {
      id: "sv115_overlays",
      label: "SV1.15 overlays",
    },
    {
      id: "sv116_true_replay",
      label: "SV1.16 true replay",
    },
    {
      id: "sv117_true_replay_round1",
      label: "SV1.17 replay round 1",
    },
    {
      id: "sv117_true_replay_full_suite",
      label: "SV1.17 full suite",
    },
  ];

  const SV116_REPLAY_ROWS = [
    {
      id: "baseline_current_money_flow_rules",
      label: "Baseline current Money Flow",
      component: "sleeve_1h",
      methodology: "true_forward_replay",
      contexts: 2976,
      trades: 117,
      endingEquity: 11388.92997084,
      netPnl: 1388.92997084,
      rejectedEntries: 2055,
      variantCandidates: 0,
      variantEntries: 0,
      winRate: 0.35042735,
      profitFactor: 1.21629414,
      closedDrawdown: 1677.7053037,
      markToMarketDrawdown: 1753.27047986,
      worstTrade: -409.14514081,
      status: "baseline replay parity checked",
    },
    {
      id: "lower_rsi_floor_trend_intact_v1",
      label: "Lower RSI trend-intact v1",
      component: "sleeve_1h",
      methodology: "true_forward_replay_research_only",
      contexts: 2976,
      trades: 137,
      endingEquity: 10902.09279976,
      netPnl: 902.09279976,
      rejectedEntries: 2011,
      variantCandidates: 1428,
      variantEntries: 29,
      winRate: 0.30656934,
      profitFactor: 1.12715544,
      closedDrawdown: 1694.79623292,
      markToMarketDrawdown: 1777.46211574,
      worstTrade: -399.05289817,
      status: "deteriorated vs baseline; not authorized",
    },
  ];

  const SV116_REPLAY_FINDINGS = [
    "SV1.16 is true candle-by-candle replay instrumentation, not a completed-trade overlay.",
    "Baseline replay parity is checked on deterministic fixtures for trade count, entry times, exit times, net account PnL, and ending equity.",
    "The ETH 1h lower-RSI replay admitted 29 replay-only entries but ended below the baseline sampled scenario.",
    "Below-floor RSI contexts are now visible for future testing instead of being inferred from completed trades.",
    "The lower-RSI variant remains research-only and does not change production RSI floors or entry rules.",
    "No paper trading, live trading, routing, execution behavior, or strategy authorization follows from this replay.",
  ];

  const SV116_REPLAY_METHODOLOGY = [
    "true_forward_replay: candles are processed chronologically with position occupancy and dynamic-equity sizing.",
    "per_candle_true_replay_context_research_only: each evaluated candle records baseline decision/rejection context.",
    "lower_rsi_floor_trend_intact_v1: admits below-floor RSI only inside Strategy Validation replay when trend, MACD, non-extension, and pullback/support gates pass.",
    "SV1.15 completed-trade overlays remain diagnostic and are not replaced or retroactively validated by SV1.16.",
  ];

  const SV117_REPLAY_ROWS = [
    {
      id: "baseline_current_money_flow_rules",
      label: "Baseline current Money Flow",
      component: "sleeve_1h",
      methodology: "true_forward_replay",
      contexts: 2976,
      trades: 117,
      endingEquity: 11388.92997084,
      netPnl: 1388.92997084,
      rejectedEntries: 2055,
      variantCandidates: 0,
      variantEntries: 0,
      nearSupportEntries: 0,
      nearResistanceEntries: 0,
      fallingKnifeCandidates: 0,
      winRate: 0.35042735,
      profitFactor: 1.21629414,
      closedDrawdown: 1677.7053037,
      markToMarketDrawdown: 1753.27047986,
      worstTrade: -409.14514081,
      status: "baseline replay anchor",
    },
    {
      id: "lower_rsi_floor_trend_intact_v1",
      label: "Lower RSI trend-intact v1",
      component: "sleeve_1h",
      methodology: "true_forward_replay_research_only",
      contexts: 2976,
      trades: 137,
      endingEquity: 10902.09279976,
      netPnl: 902.09279976,
      rejectedEntries: 2011,
      variantCandidates: 1428,
      variantEntries: 29,
      nearSupportEntries: 4,
      nearResistanceEntries: 11,
      fallingKnifeCandidates: 1392,
      winRate: 0.30656934,
      profitFactor: 1.12715544,
      closedDrawdown: 1694.79623292,
      markToMarketDrawdown: 1777.46211574,
      worstTrade: -399.05289817,
      status: "deteriorated vs baseline",
    },
    {
      id: "lower_rsi_floor_trend_intact_v2_narrow",
      label: "Lower RSI narrow trend-intact",
      component: "sleeve_1h",
      methodology: "true_forward_replay_research_only",
      contexts: 2976,
      trades: 129,
      endingEquity: 10792.71889062,
      netPnl: 792.71889062,
      rejectedEntries: 2028,
      variantCandidates: 1445,
      variantEntries: 18,
      nearSupportEntries: 4,
      nearResistanceEntries: 9,
      fallingKnifeCandidates: 1399,
      winRate: 0.31782946,
      profitFactor: 1.11578949,
      closedDrawdown: 1731.53053481,
      markToMarketDrawdown: 1829.08721434,
      worstTrade: -393.02492005,
      status: "deteriorated vs baseline",
    },
    {
      id: "lower_rsi_support_confirmed_v1",
      label: "Lower RSI support-confirmed",
      component: "sleeve_1h",
      methodology: "true_forward_replay_research_only",
      contexts: 2976,
      trades: 117,
      endingEquity: 11388.92997084,
      netPnl: 1388.92997084,
      rejectedEntries: 2055,
      variantCandidates: 1472,
      variantEntries: 0,
      nearSupportEntries: 0,
      nearResistanceEntries: 0,
      fallingKnifeCandidates: 1408,
      winRate: 0.35042735,
      profitFactor: 1.21629414,
      closedDrawdown: 1677.7053037,
      markToMarketDrawdown: 1753.27047986,
      worstTrade: -409.14514081,
      status: "unchanged; admitted no trades",
    },
    {
      id: "lower_rsi_ema10_hold_no_resistance_v1",
      label: "Lower RSI EMA10 hold / no resistance",
      component: "sleeve_1h",
      methodology: "true_forward_replay_research_only",
      contexts: 2976,
      trades: 126,
      endingEquity: 11293.7316455,
      netPnl: 1293.7316455,
      rejectedEntries: 2027,
      variantCandidates: 1444,
      variantEntries: 14,
      nearSupportEntries: 0,
      nearResistanceEntries: 0,
      fallingKnifeCandidates: 1401,
      winRate: 0.32539683,
      profitFactor: 1.18808633,
      closedDrawdown: 1460.47919814,
      markToMarketDrawdown: 1537.82040938,
      worstTrade: -410.16124843,
      status: "deteriorated; lower drawdown",
    },
  ];

  const SV117_REPLAY_FINDINGS = [
    "SV1.17 tests round-one true replay variants, not completed-trade overlays.",
    "No lower-RSI or market-structure variant beat the ETH 1h baseline in the sampled next-candle-open 5 bps fee / 3 bps slippage scenario.",
    "The support-confirmed variant admitted no below-floor RSI trades and therefore matched baseline.",
    "The EMA10-hold/no-resistance variant reduced mark-to-market drawdown versus baseline but still ended below baseline equity.",
    "Most below-floor candidates still carried falling-knife/chop risk proxies, so lower RSI is not automatically better for long-only entries.",
    "No variant is authorized for production, paper trading, or live trading.",
  ];

  const SV117_REPLAY_METHODOLOGY = [
    "true_forward_replay: candles are processed chronologically with position occupancy and dynamic-equity sizing.",
    "round_one_scope: Hyperliquid ETH sleeve_1h only, next-candle-open fill, 5 bps fee, 3 bps slippage.",
    "market_structure_context: prior-20-candle swing support/resistance is research context only.",
    "SV1.16.1 counter truth: variant-admitted candles are separated from variant no-trade counts.",
  ];

  const SV117_FULL_SUITE_FINDINGS = [
    "SV1.17 full suite now covers BTC/ETH/SOL across sleeve_15m, sleeve_1h, and sleeve_4h.",
    "Each row is an independent dynamic-equity true replay scenario, not one combined portfolio account.",
    "15m baselines remain negative across BTC, ETH, and SOL in this public campaign.",
    "ETH 1h baseline remains the only baseline scenario above starting equity.",
    "Some variants improve losing BTC or ETH scenarios versus their own baseline, but several still finish below starting equity and need broader validation.",
    "No variant is authorized for production, paper trading, or live trading.",
  ];

  const SV117_FULL_SUITE_METHODOLOGY = [
    "full_suite_scope: BTC/ETH/SOL x sleeve_15m/sleeve_1h/sleeve_4h.",
    "scenario_boundary: symbol + component + fill/cost assumptions define one independent account-style replay.",
    "delta_vs_baseline: variant ending equity minus the matching same-symbol/same-component baseline.",
    "dashboard_source: docs/strategy_validation_sv1_17_true_replay_experiments_summary.json.",
  ];

  const state = {
    review: null,
    batches: [],
    selectedComponent: "all",
    activeView: "evidence",
    experimentMode: "sv115_overlays",
    sv117FullSuiteRows: null,
    uat2Summary: null,
    uatFilters: {
      symbol: "all",
      component: "all",
      status: "all",
      reason: "all",
    },
  };

  const elements = {
    viewTabs: Array.from(document.querySelectorAll("[data-view]")),
    viewPanels: Array.from(document.querySelectorAll("[data-view-panel]")),
    status: document.querySelector("#review-status"),
    sourceLabel: document.querySelector("#data-source-label"),
    sourceDetail: document.querySelector("#data-source-detail"),
    fileInput: document.querySelector("#json-file-input"),
    metricPacks: document.querySelector("#metric-packs"),
    metricPacksDetail: document.querySelector("#metric-packs-detail"),
    metricRuns: document.querySelector("#metric-runs"),
    metricRunsDetail: document.querySelector("#metric-runs-detail"),
    metricCoverage: document.querySelector("#metric-coverage"),
    metricBoundary: document.querySelector("#metric-boundary"),
    componentFilter: document.querySelector("#component-filter"),
    boundaryFlags: document.querySelector("#boundary-flags"),
    componentCards: document.querySelector("#component-cards"),
    detailSubtitle: document.querySelector("#detail-subtitle"),
    timingChart: document.querySelector("#timing-chart"),
    symbolChart: document.querySelector("#symbol-chart"),
    regimeTable: document.querySelector("#regime-table"),
    checklist: document.querySelector("#review-checklist"),
    runTable: document.querySelector("#run-table"),
    experimentVariantCards: document.querySelector("#experiment-variant-cards"),
    experimentReplayFilter: document.querySelector("#experiment-replay-filter"),
    experimentsTitle: document.querySelector("#experiments-title"),
    experimentsSubtitle: document.querySelector("#experiments-subtitle"),
    experimentMetricALabel: document.querySelector("#experiment-metric-a-label"),
    experimentMetricAValue: document.querySelector("#experiment-metric-a-value"),
    experimentMetricADetail: document.querySelector("#experiment-metric-a-detail"),
    experimentMetricBLabel: document.querySelector("#experiment-metric-b-label"),
    experimentMetricBValue: document.querySelector("#experiment-metric-b-value"),
    experimentMetricBDetail: document.querySelector("#experiment-metric-b-detail"),
    experimentMetricCLabel: document.querySelector("#experiment-metric-c-label"),
    experimentMetricCValue: document.querySelector("#experiment-metric-c-value"),
    experimentMetricCDetail: document.querySelector("#experiment-metric-c-detail"),
    experimentMetricDLabel: document.querySelector("#experiment-metric-d-label"),
    experimentMetricDValue: document.querySelector("#experiment-metric-d-value"),
    experimentMetricDDetail: document.querySelector("#experiment-metric-d-detail"),
    experimentBaselineTable: document.querySelector("#experiment-baseline-table"),
    experimentEthTable: document.querySelector("#experiment-eth-table"),
    experimentFindings: document.querySelector("#experiment-findings"),
    experimentMethodology: document.querySelector("#experiment-methodology"),
    experimentTable: document.querySelector("#experiment-table"),
    uatSummaryCards: document.querySelector("#uat-summary-cards"),
    uatSymbolFilter: document.querySelector("#uat-symbol-filter"),
    uatComponentFilter: document.querySelector("#uat-component-filter"),
    uatStatusFilter: document.querySelector("#uat-status-filter"),
    uatReasonFilter: document.querySelector("#uat-reason-filter"),
    uatEthCandidateCard: document.querySelector("#uat-eth-candidate-card"),
    uat3ReadinessPanel: document.querySelector("#uat3-readiness-panel"),
    uatBoundaryPanel: document.querySelector("#uat-boundary-panel"),
    uatSignalMatrix: document.querySelector("#uat-signal-matrix"),
    uatWouldOpenTable: document.querySelector("#uat-would-open-table"),
    uatNoTradeOverall: document.querySelector("#uat-no-trade-overall"),
    uatNoTradeComponent: document.querySelector("#uat-no-trade-component"),
    uatNoTradeSymbol: document.querySelector("#uat-no-trade-symbol"),
    uatTimingPanel: document.querySelector("#uat-timing-panel"),
    uatDrawdownCard: document.querySelector("#uat-drawdown-card"),
  };

  function decimal(value, fallback = 0) {
    if (value === null || value === undefined || value === "") return fallback;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function money(value) {
    const parsed = decimal(value);
    const sign = parsed < 0 ? "-" : "";
    return `${sign}$${Math.abs(parsed).toLocaleString(undefined, {
      maximumFractionDigits: 0,
    })}`;
  }

  function pct(value) {
    return `${(decimal(value) * 100).toLocaleString(undefined, {
      maximumFractionDigits: 1,
    })}%`;
  }

  function cleanComponentName(component) {
    return String(component || "unknown").replace("sleeve_", "").toUpperCase();
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function batchComponent(batch) {
    const matrixComponent = batch.assumptions_matrix?.components?.[0];
    const comparisonComponent = batch.comparison_summary?.component_comparison?.[0]?.component_keys;
    return matrixComponent || comparisonComponent || batch.batch_name || "unknown";
  }

  function batchSummary(batch) {
    const comparison = batch.comparison_summary || {};
    const componentComparison = comparison.component_comparison?.[0] || {};
    const coverage = comparison.data_coverage_comparison || [];
    const runs = batch.run_reports || [];
    const completedRuns = runs.filter((run) => run.status === "completed");
    const component = batchComponent(batch);
    const firstRun = completedRuns[0]?.report;
    const firstCoverage = coverage[0];
    const totalExpected = coverage.reduce(
      (sum, row) => sum + decimal(row.total_expected_candle_count),
      0,
    );
    const totalActual = coverage.reduce((sum, row) => sum + decimal(row.total_actual_candle_count), 0);

    return {
      batch,
      component,
      label: cleanComponentName(component),
      timeframe:
        firstRun?.component_reports?.[0]?.timeframe ||
        firstRun?.data_coverage_summary?.components?.[0]?.timeframe ||
        component.replace("sleeve_", ""),
      window:
        firstCoverage?.date_window ||
        `${firstRun?.start_at || "unknown"} -> ${firstRun?.end_at || "unknown"}`,
      completedRunCount: decimal(componentComparison.completed_run_count, completedRuns.length),
      blockedRunCount: decimal(componentComparison.blocked_run_count),
      totalNetPnl: decimal(componentComparison.total_net_pnl),
      averageNetPnl: decimal(componentComparison.average_net_pnl),
      totalTrades: decimal(componentComparison.total_trades),
      totalFees: decimal(componentComparison.total_fees),
      totalSlippage: decimal(componentComparison.total_slippage_cost),
      largestDrawdown: decimal(componentComparison.largest_mark_to_market_drawdown),
      coveragePercent: totalExpected > 0 ? totalActual / totalExpected : 0,
      expectedCandles: totalExpected,
      actualCandles: totalActual,
      fillTiming: comparison.fill_timing_comparison || [],
      symbols: comparison.symbol_comparison || [],
      regimes: comparison.regime_comparison || [],
      runSummaries: comparison.run_summaries || [],
      bestNetPnl: comparison.highest_observed_net_pnl_run || null,
      worstNetPnl: comparison.lowest_observed_net_pnl_run || null,
      bestWinRate: comparison.highest_observed_win_rate_run || null,
    };
  }

  function allSummaries() {
    return state.batches.map(batchSummary).sort((a, b) => a.component.localeCompare(b.component));
  }

  function activeSummaries() {
    const summaries = allSummaries();
    if (state.selectedComponent === "all") return summaries;
    return summaries.filter((summary) => summary.component === state.selectedComponent);
  }

  function setEmpty(target, message) {
    target.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
  }

  function setActiveView(view) {
    state.activeView = ["evidence", "experiments", "uat-shadow", "strategy"].includes(view)
      ? view
      : "evidence";
    elements.viewTabs.forEach((tab) => {
      tab.setAttribute("aria-selected", String(tab.dataset.view === state.activeView));
    });
    elements.viewPanels.forEach((panel) => {
      panel.hidden = panel.dataset.viewPanel !== state.activeView;
    });
  }

  function renderMetrics(summaries) {
    const generatedPaths = state.review?.generated_evidence_pack_paths || [];
    const packCount =
      generatedPaths.length ||
      state.review?.generated_campaign_count ||
      summaries.filter((summary) => summary.completedRunCount > 0).length;
    const totalRuns = summaries.reduce((sum, summary) => sum + summary.completedRunCount, 0);
    const totalExpected = summaries.reduce((sum, summary) => sum + summary.expectedCandles, 0);
    const totalActual = summaries.reduce((sum, summary) => sum + summary.actualCandles, 0);
    const coverage = totalExpected > 0 ? totalActual / totalExpected : 0;

    elements.status.textContent = state.review?.paper_readiness_review_status || "local review";
    elements.metricPacks.textContent = String(packCount);
    elements.metricPacksDetail.textContent =
      state.review?.blocked_campaign_count === 0 ? "generated" : "mixed";
    elements.metricRuns.textContent = String(totalRuns);
    elements.metricRunsDetail.textContent = `${summaries.length} component packs`;
    elements.metricCoverage.textContent = pct(coverage);
    elements.metricBoundary.textContent = state.review?.paper_readiness_review_status
      ? "review"
      : "blocked";
  }

  function renderFlags() {
    const flags = [
      ["No live artifacts", state.review?.creates_live_artifacts === false],
      ["No exchange adapters", state.review?.calls_exchange_adapters === false],
      ["No private endpoints", state.review?.calls_private_exchange_endpoints === false],
      ["No order endpoints", state.review?.calls_exchange_order_endpoints === false],
      ["Manual review", true],
    ];
    elements.boundaryFlags.innerHTML = flags
      .map(([label, ok]) => `<span class="pill ${ok ? "good" : "warn"}">${escapeHtml(label)}</span>`)
      .join("");
  }

  function renderFilters(summaries) {
    const components = ["all", ...summaries.map((summary) => summary.component)];
    elements.componentFilter.innerHTML = components
      .map((component) => {
        const label = component === "all" ? "All" : cleanComponentName(component);
        return `<button class="segment-button" type="button" role="tab" aria-selected="${
          state.selectedComponent === component
        }" data-component="${escapeHtml(component)}">${escapeHtml(label)}</button>`;
      })
      .join("");
    elements.componentFilter.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        state.selectedComponent = button.dataset.component || "all";
        render();
      });
    });
  }

  function renderComponentCards(summaries) {
    const maxMagnitude = Math.max(...summaries.map((summary) => Math.abs(summary.totalNetPnl)), 1);
    elements.componentCards.innerHTML = summaries
      .map((summary) => {
        const width = Math.max(3, Math.round((Math.abs(summary.totalNetPnl) / maxMagnitude) * 100));
        const isSelected =
          state.selectedComponent === "all" || state.selectedComponent === summary.component;
        return `
          <button class="component-card" type="button" aria-current="${isSelected}" data-component="${
            escapeHtml(summary.component)
          }">
            <div class="component-card-header">
              <span class="component-card-title">${escapeHtml(summary.label)}</span>
              <span>${escapeHtml(summary.timeframe)}</span>
            </div>
            <div class="pnl-track" aria-label="Sum net PnL across research runs magnitude">
              <div class="pnl-fill ${summary.totalNetPnl >= 0 ? "positive" : ""}" style="width:${width}%"></div>
            </div>
            <div class="component-card-metrics">
              <div class="mini-metric"><span>Sum Net</span><strong>${escapeHtml(money(summary.totalNetPnl))}</strong></div>
              <div class="mini-metric"><span>Sum Trades</span><strong>${escapeHtml(summary.totalTrades)}</strong></div>
              <div class="mini-metric"><span>Drawdown</span><strong>${escapeHtml(money(summary.largestDrawdown))}</strong></div>
            </div>
          </button>
        `;
      })
      .join("");
    elements.componentCards.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        state.selectedComponent = button.dataset.component || "all";
        render();
      });
    });
  }

  function renderBarList(target, rows, labelKey, valueKey, formatter) {
    if (!rows.length) {
      setEmpty(target, "No rows loaded.");
      return;
    }
    const values = rows.map((row) => decimal(row[valueKey]));
    const maxMagnitude = Math.max(...values.map(Math.abs), 1);
    target.innerHTML = rows
      .map((row) => {
        const value = decimal(row[valueKey]);
        const width = Math.max(3, Math.round((Math.abs(value) / maxMagnitude) * 100));
        return `
          <div class="bar-row">
            <span class="bar-label">${escapeHtml(row[labelKey] || "unknown")}</span>
            <div class="bar-track"><div class="bar-fill ${
              value >= 0 ? "positive" : ""
            }" style="width:${width}%"></div></div>
            <span class="bar-value">${escapeHtml(formatter(value))}</span>
          </div>
        `;
      })
      .join("");
  }

  function renderDetail(summaries) {
    const selected = summaries[0];
    if (!selected) {
      elements.detailSubtitle.textContent = "No component selected.";
      setEmpty(elements.timingChart, "Load evidence review and batch report JSON.");
      setEmpty(elements.symbolChart, "Load evidence review and batch report JSON.");
      setEmpty(elements.regimeTable, "Load evidence review and batch report JSON.");
      elements.checklist.innerHTML = "";
      return;
    }

    elements.detailSubtitle.textContent = `${selected.label} / ${selected.window} / grouped research sums, not one account`;
    renderBarList(
      elements.timingChart,
      selected.fillTiming,
      "fill_timing",
      "average_net_pnl",
      money,
    );
    renderBarList(elements.symbolChart, selected.symbols, "symbol", "total_net_pnl", money);
    renderRegimeTable(selected.regimes);
    renderChecklist();
  }

  function renderRegimeTable(rows) {
    if (!rows.length) {
      setEmpty(elements.regimeTable, "No regime rows loaded.");
      return;
    }
    elements.regimeTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Type</th>
            <th>Regime</th>
            <th>Trades</th>
            <th>Sum Net PnL</th>
            <th>Win Rate</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(row.regime_type || "")}</td>
                  <td>${escapeHtml(row.regime_label || "")}</td>
                  <td>${escapeHtml(row.total_trades ?? row.trade_count ?? 0)}</td>
                  <td>${escapeHtml(money(row.total_net_pnl ?? row.net_pnl))}</td>
                  <td>${escapeHtml(row.win_rate === null || row.win_rate === undefined ? "n/a" : pct(row.win_rate))}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderChecklist() {
    const criteria = state.review?.manual_paper_trading_readiness_criteria || [
      "Founder/operator review is complete; this is not an automated go/no-go decision.",
      "Observed performance survives next-candle timing assumptions.",
      "Drawdown remains within founder/operator research tolerance.",
    ];
    elements.checklist.innerHTML = criteria.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  }

  function renderRunTable(summaries) {
    const rows = summaries
      .flatMap((summary) => summary.runSummaries.map((row) => ({ ...row, component: summary.label })))
      .slice()
      .sort((a, b) => decimal(b.metrics?.net_pnl) - decimal(a.metrics?.net_pnl))
      .slice(0, 36);

    if (!rows.length) {
      setEmpty(elements.runTable, "No run summaries loaded.");
      return;
    }

    elements.runTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Component</th>
            <th>Symbol</th>
            <th>Fill</th>
            <th>Fee</th>
            <th>Slip</th>
            <th>Sizing</th>
            <th>Ending Equity</th>
            <th>Scenario Net PnL</th>
            <th>Win</th>
            <th>Trades</th>
            <th>Drawdown</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(row.component)}</td>
                  <td>${escapeHtml(row.symbol)}</td>
                  <td>${escapeHtml(row.fill_timing)}</td>
                  <td>${escapeHtml(row.fee_bps)}</td>
                  <td>${escapeHtml(row.slippage_bps)}</td>
                  <td>${escapeHtml(row.metrics?.capital_sizing_mode || row.capital_sizing_mode || "constant_initial_capital_notional_per_trade")}</td>
                  <td>${escapeHtml(money(row.metrics?.ending_equity ?? row.metrics?.net_pnl))}</td>
                  <td>${escapeHtml(money(row.metrics?.net_pnl))}</td>
                  <td>${escapeHtml(pct(row.metrics?.win_rate))}</td>
                  <td>${escapeHtml(row.metrics?.number_of_trades ?? 0)}</td>
                  <td>${escapeHtml(money(row.metrics?.mark_to_market_max_drawdown))}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderExperimentCards() {
    if (!elements.experimentVariantCards) return;
    if (isReplayExperimentMode()) {
      renderReplayCards();
      return;
    }
    const maxMagnitude = Math.max(...SV115_VARIANTS.map((row) => Math.abs(row.delta)), 1);
    elements.experimentVariantCards.innerHTML = SV115_VARIANTS.map((row) => {
      const width = Math.max(3, Math.round((Math.abs(row.delta) / maxMagnitude) * 100));
      return `
        <article class="component-card experiment-card" aria-current="${row.delta >= 0}">
          <div class="component-card-header">
            <span class="component-card-title">${escapeHtml(row.label)}</span>
            <span>${escapeHtml(row.symbol ? `${row.symbol} ${row.component}` : row.component)}</span>
          </div>
          <p class="card-note">${escapeHtml(row.methodology)}</p>
          <div class="pnl-track" aria-label="Delta versus baseline magnitude">
            <div class="pnl-fill ${row.delta >= 0 ? "positive" : ""}" style="width:${width}%"></div>
          </div>
          <div class="component-card-metrics">
            <div class="mini-metric"><span>Delta</span><strong>${escapeHtml(money(row.delta))}</strong></div>
            <div class="mini-metric"><span>Filtered</span><strong>${escapeHtml(row.filtered)}</strong></div>
            <div class="mini-metric"><span>Status</span><strong>${escapeHtml(row.status)}</strong></div>
          </div>
        </article>
      `;
    }).join("");
  }

  function renderExperimentBaseline() {
    if (!elements.experimentBaselineTable) return;
    if (isReplayExperimentMode()) {
      renderReplayComparisonTable();
      return;
    }
    elements.experimentBaselineTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Component</th>
            <th>Scenarios</th>
            <th>Ending Equity Sum</th>
            <th>Net Account PnL Sum</th>
            <th>Min Ending Equity</th>
            <th>Max Drawdown</th>
            <th>Trades</th>
          </tr>
        </thead>
        <tbody>
          ${SV115_BASELINE.map((row) => `
            <tr>
              <td>${escapeHtml(row.component)}</td>
              <td>${escapeHtml(row.scenarios)}</td>
              <td>${escapeHtml(money(row.endingEquitySum))}</td>
              <td>${escapeHtml(money(row.netPnlSum))}</td>
              <td>${escapeHtml(money(row.minEndingEquity))}</td>
              <td>${escapeHtml(money(row.maxDrawdown))}</td>
              <td>${escapeHtml(row.trades)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderExperimentEth() {
    if (!elements.experimentEthTable) return;
    if (isReplayExperimentMode()) {
      renderReplayRejectedContextTable();
      return;
    }
    elements.experimentEthTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Variant</th>
            <th>Baseline Net Sum</th>
            <th>Variant Net Sum</th>
            <th>Delta</th>
            <th>ETH 1h Status</th>
          </tr>
        </thead>
        <tbody>
          ${SV115_ETH_1H.map(([variant, baseline, result, delta, status]) => `
            <tr>
              <td>${escapeHtml(variant)}</td>
              <td>${escapeHtml(money(baseline))}</td>
              <td>${escapeHtml(money(result))}</td>
              <td>${escapeHtml(money(delta))}</td>
              <td>${escapeHtml(status)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderExperimentFindings() {
    if (!elements.experimentFindings) return;
    const findings =
      state.experimentMode === "sv117_true_replay_full_suite"
        ? SV117_FULL_SUITE_FINDINGS
        : state.experimentMode === "sv117_true_replay_round1"
        ? SV117_REPLAY_FINDINGS
        : state.experimentMode === "sv116_true_replay"
          ? SV116_REPLAY_FINDINGS
          : SV115_FINDINGS;
    const methodology =
      state.experimentMode === "sv117_true_replay_full_suite"
        ? SV117_FULL_SUITE_METHODOLOGY
        : state.experimentMode === "sv117_true_replay_round1"
        ? SV117_REPLAY_METHODOLOGY
        : state.experimentMode === "sv116_true_replay"
          ? SV116_REPLAY_METHODOLOGY
          : SV115_METHODOLOGY;
    elements.experimentFindings.innerHTML = findings.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    if (!elements.experimentMethodology) return;
    elements.experimentMethodology.innerHTML = methodology.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  }

  function renderExperimentTable() {
    if (!elements.experimentTable) return;
    if (isReplayExperimentMode()) {
      renderReplayLedger();
      return;
    }
    elements.experimentTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Variant</th>
            <th>Methodology</th>
            <th>Baseline Net</th>
            <th>Variant Net</th>
            <th>Delta</th>
            <th>Drawdown</th>
            <th>Filtered</th>
            <th>Losing Avoided</th>
            <th>Winning Missed</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${SV115_VARIANTS.map((row) => `
            <tr>
              <td>${escapeHtml(row.id)}</td>
              <td>${escapeHtml(row.methodology)}</td>
              <td>${escapeHtml(money(row.baselineNet))}</td>
              <td>${escapeHtml(money(row.variantNet))}</td>
              <td>${escapeHtml(money(row.delta))}</td>
              <td>${escapeHtml(money(row.drawdown))}</td>
              <td>${escapeHtml(row.filtered)}</td>
              <td>${escapeHtml(row.avoidedLosers)}</td>
              <td>${escapeHtml(row.missedWinners)}</td>
              <td>${escapeHtml(row.status)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderExperimentModeFilter() {
    if (!elements.experimentReplayFilter) return;
    elements.experimentReplayFilter.innerHTML = EXPERIMENT_MODES.map(
      (mode) => `
        <button class="segment-button" type="button" role="tab" aria-selected="${
          state.experimentMode === mode.id
        }" data-experiment-mode="${escapeHtml(mode.id)}">${escapeHtml(mode.label)}</button>
      `,
    ).join("");
    elements.experimentReplayFilter.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        state.experimentMode = button.dataset.experimentMode || "sv115_overlays";
        renderExperiments();
      });
    });
  }

  function renderExperimentHeader() {
    const replayMode = isReplayExperimentMode();
    const sv117Mode = state.experimentMode === "sv117_true_replay_round1";
    const sv117FullSuiteMode = state.experimentMode === "sv117_true_replay_full_suite";
    elements.experimentsTitle.textContent = replayMode
      ? sv117FullSuiteMode
        ? "SV1.17 Full-Suite True Replay"
        : sv117Mode
        ? "SV1.17 True Replay Round 1"
        : "SV1.16 True Replay Results"
      : "SV1.15 Hypothesis Experiments";
    elements.experimentsSubtitle.textContent = replayMode
      ? sv117FullSuiteMode
        ? "BTC/ETH/SOL across 15m/1h/4h; every row is an independent research replay scenario."
        : sv117Mode
        ? "Lower-RSI plus market-structure replay variants; research-only and not production rule changes."
        : "Rejected-signal replay; true replay remains research-only and not a production rule change."
      : "Dynamic-equity diagnostics; overlays are not true forward replays or production rule changes.";
    elements.experimentMetricALabel.textContent = replayMode ? "Replay Scope" : "Baseline Winner";
    elements.experimentMetricAValue.textContent = replayMode
      ? sv117FullSuiteMode
        ? "3 x 3"
        : "ETH 1H"
      : "1H";
    elements.experimentMetricADetail.textContent = replayMode
      ? sv117FullSuiteMode
        ? "BTC/ETH/SOL x 15m/1h/4h"
        : "Hyperliquid true replay"
      : "positive grouped dynamic-equity sum";
    elements.experimentMetricBLabel.textContent = replayMode ? "Replay Entries" : "Largest 15m Lift";
    elements.experimentMetricBValue.textContent = replayMode
      ? sv117FullSuiteMode
        ? "80 max"
        : sv117Mode
        ? "29 max"
        : "29"
      : "$79.7k";
    elements.experimentMetricBDetail.textContent = replayMode
      ? sv117FullSuiteMode
        ? "per scenario variant entries"
        : sv117Mode
        ? "round-one variant entries"
        : "lower-RSI entries admitted"
      : "completed-trade overlay, still negative";
    elements.experimentMetricCLabel.textContent = replayMode ? "Ending Equity Delta" : "Largest 4h Lift";
    elements.experimentMetricCValue.textContent = replayMode
      ? sv117FullSuiteMode
        ? "Mixed"
        : sv117Mode
        ? "None beat"
        : money(10902.09279976 - 11388.92997084)
      : "$30.7k";
    elements.experimentMetricCDetail.textContent = replayMode
      ? sv117FullSuiteMode
        ? "some improve losing baselines"
        : sv117Mode
        ? "baseline remained strongest"
        : "variant minus baseline"
      : "completed-trade overlay";
    elements.experimentMetricDLabel.textContent = replayMode ? "Authorization" : "Methodology";
    elements.experimentMetricDValue.textContent = replayMode ? "None" : "None";
    elements.experimentMetricDDetail.textContent = replayMode
      ? "research-only replay"
      : "no hypothesis authorized";
  }

  function renderReplayCards() {
    const rows = activeReplayRows();
    const maxMagnitude = Math.max(...rows.map((row) => Math.abs(row.netPnl)), 1);
    elements.experimentVariantCards.innerHTML = rows.map((row) => {
      const width = Math.max(3, Math.round((Math.abs(row.netPnl) / maxMagnitude) * 100));
      return `
        <article class="component-card experiment-card" aria-current="${row.netPnl >= 0}">
          <div class="component-card-header">
            <span class="component-card-title">${escapeHtml(row.label)}</span>
            <span>${escapeHtml(row.component)}</span>
          </div>
          <p class="card-note">${escapeHtml(row.methodology)}</p>
          <div class="pnl-track" aria-label="Net account PnL magnitude">
            <div class="pnl-fill ${row.netPnl >= 0 ? "positive" : ""}" style="width:${width}%"></div>
          </div>
          <div class="component-card-metrics">
            <div class="mini-metric"><span>Net PnL</span><strong>${escapeHtml(money(row.netPnl))}</strong></div>
            <div class="mini-metric"><span>Trades</span><strong>${escapeHtml(row.trades)}</strong></div>
            <div class="mini-metric"><span>Status</span><strong>${escapeHtml(row.status)}</strong></div>
          </div>
        </article>
      `;
    }).join("");
  }

  function renderReplayComparisonTable() {
    const rows = activeReplayRows();
    elements.experimentBaselineTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Replay</th>
            <th>Symbol</th>
            <th>Component</th>
            <th>Contexts</th>
            <th>Trades</th>
            <th>Ending Equity</th>
            <th>Net Account PnL</th>
            <th>Win Rate</th>
            <th>Profit Factor</th>
            <th>MTM Drawdown</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((row) => `
            <tr>
              <td>${escapeHtml(row.label)}</td>
              <td>${escapeHtml(row.symbol || "ETH")}</td>
              <td>${escapeHtml(row.component)}</td>
              <td>${escapeHtml(row.contexts)}</td>
              <td>${escapeHtml(row.trades)}</td>
              <td>${escapeHtml(money(row.endingEquity))}</td>
              <td>${escapeHtml(money(row.netPnl))}</td>
              <td>${escapeHtml(pct(row.winRate))}</td>
              <td>${escapeHtml(row.profitFactor.toFixed(2))}</td>
              <td>${escapeHtml(money(row.markToMarketDrawdown))}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderReplayRejectedContextTable() {
    const rows = activeReplayRows();
    elements.experimentEthTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Replay</th>
            <th>Symbol</th>
            <th>Component</th>
            <th>Rejected Entries</th>
            <th>Variant Candidates</th>
            <th>Variant Entries</th>
            <th>Worst Trade</th>
            <th>Closed DD</th>
            <th>Near Support</th>
            <th>Near Resistance</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((row) => `
            <tr>
              <td>${escapeHtml(row.id)}</td>
              <td>${escapeHtml(row.symbol || "ETH")}</td>
              <td>${escapeHtml(row.component)}</td>
              <td>${escapeHtml(row.rejectedEntries)}</td>
              <td>${escapeHtml(row.variantCandidates)}</td>
              <td>${escapeHtml(row.variantEntries)}</td>
              <td>${escapeHtml(money(row.worstTrade))}</td>
              <td>${escapeHtml(money(row.closedDrawdown))}</td>
              <td>${escapeHtml(row.nearSupportEntries ?? 0)}</td>
              <td>${escapeHtml(row.nearResistanceEntries ?? 0)}</td>
              <td>${escapeHtml(row.status)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderReplayLedger() {
    const rows = activeReplayRows();
    const baseline = rows[0];
    elements.experimentTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Replay ID</th>
            <th>Symbol</th>
            <th>Component</th>
            <th>Methodology</th>
            <th>Net PnL</th>
            <th>Delta vs Baseline</th>
            <th>Ending Equity</th>
            <th>Trades</th>
            <th>Replay Entries</th>
            <th>Rejected Entries</th>
            <th>Falling-Knife Candidates</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((row) => `
            <tr>
              <td>${escapeHtml(row.id)}</td>
              <td>${escapeHtml(row.symbol || "ETH")}</td>
              <td>${escapeHtml(row.component)}</td>
              <td>${escapeHtml(row.methodology)}</td>
              <td>${escapeHtml(money(row.netPnl))}</td>
              <td>${escapeHtml(money(row.deltaVsBaseline ?? row.netPnl - baseline.netPnl))}</td>
              <td>${escapeHtml(money(row.endingEquity))}</td>
              <td>${escapeHtml(row.trades)}</td>
              <td>${escapeHtml(row.variantEntries)}</td>
              <td>${escapeHtml(row.rejectedEntries)}</td>
              <td>${escapeHtml(row.fallingKnifeCandidates ?? 0)}</td>
              <td>${escapeHtml(row.status)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function isReplayExperimentMode() {
    return ["sv116_true_replay", "sv117_true_replay_round1", "sv117_true_replay_full_suite"].includes(
      state.experimentMode,
    );
  }

  function activeReplayRows() {
    if (state.experimentMode === "sv117_true_replay_full_suite") {
      return state.sv117FullSuiteRows || SV117_REPLAY_ROWS;
    }
    return state.experimentMode === "sv117_true_replay_round1" ? SV117_REPLAY_ROWS : SV116_REPLAY_ROWS;
  }

  function renderExperiments() {
    renderExperimentModeFilter();
    renderExperimentHeader();
    renderExperimentCards();
    renderExperimentBaseline();
    renderExperimentEth();
    renderExperimentFindings();
    renderExperimentTable();
  }

  function uatRecords() {
    return Array.isArray(state.uat2Summary?.audit_records) ? state.uat2Summary.audit_records : [];
  }

  function countRecordsBy(records, key) {
    return records.reduce((counts, row) => {
      const value = row[key] || "unknown";
      counts[value] = (counts[value] || 0) + 1;
      return counts;
    }, {});
  }

  function countNoTradeReasons(records) {
    const counts = {};
    records
      .filter((row) => row.signal_status === "no_trade")
      .forEach((row) => {
        (row.reason_codes || ["unknown"]).forEach((reason) => {
          counts[reason] = (counts[reason] || 0) + 1;
        });
      });
    return Object.entries(counts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }

  function uniqueSorted(values) {
    return Array.from(new Set(values.filter(Boolean))).sort((a, b) => String(a).localeCompare(String(b)));
  }

  function renderSelect(select, values, activeValue, labelAll) {
    if (!select) return;
    select.innerHTML = [
      `<option value="all">${escapeHtml(labelAll)}</option>`,
      ...values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`),
    ].join("");
    select.value = values.includes(activeValue) ? activeValue : "all";
  }

  function uatFilteredRecords(records) {
    const filters = state.uatFilters;
    return records.filter((row) => {
      const reasons = row.reason_codes || [];
      return (
        (filters.symbol === "all" || row.symbol === filters.symbol) &&
        (filters.component === "all" || row.component === filters.component) &&
        (filters.status === "all" || row.signal_status === filters.status) &&
        (filters.reason === "all" || reasons.includes(filters.reason))
      );
    });
  }

  function renderUatFilters(records) {
    const symbols = uniqueSorted(records.map((row) => row.symbol));
    const components = uniqueSorted(records.map((row) => row.component));
    const statuses = uniqueSorted(records.map((row) => row.signal_status));
    const reasons = uniqueSorted(records.flatMap((row) => row.reason_codes || []));

    renderSelect(elements.uatSymbolFilter, symbols, state.uatFilters.symbol, "All symbols");
    renderSelect(elements.uatComponentFilter, components, state.uatFilters.component, "All components");
    renderSelect(elements.uatStatusFilter, statuses, state.uatFilters.status, "All statuses");
    renderSelect(elements.uatReasonFilter, reasons, state.uatFilters.reason, "All reasons");

    [
      [elements.uatSymbolFilter, "symbol"],
      [elements.uatComponentFilter, "component"],
      [elements.uatStatusFilter, "status"],
      [elements.uatReasonFilter, "reason"],
    ].forEach(([select, key]) => {
      if (!select) return;
      select.onchange = () => {
        state.uatFilters[key] = select.value || "all";
        renderUatDashboard();
      };
    });
  }

  function renderUatSummaryCards(records) {
    if (!elements.uatSummaryCards) return;
    const summary = state.uat2Summary;
    const signalCounts = countRecordsBy(records, "signal_status");
    const fetchResults = Array.isArray(summary?.candle_fetch_results) ? summary.candle_fetch_results : [];
    const successes = fetchResults.filter((row) => row.success).length;
    const failures = fetchResults.filter((row) => !row.success).length;
    const boundary = summary?.boundary_flags || {};
    const mode = summary?.mode || {};
    const cards = [
      ["Run id", summary?.run_id || "not loaded", "bounded shadow run"],
      ["Runtime mode", mode.runtime_mode || "unknown", "explicit UAT mode"],
      ["Shadow only", String(Boolean(mode.shadow_only)), "no order action"],
      ["Symbols", String((summary?.symbols_evaluated || []).length), (summary?.symbols_evaluated || []).join(", ")],
      ["Components", String((summary?.components_evaluated || []).length), (summary?.components_evaluated || []).join(", ")],
      ["Shadow records", String(records.length), "audit records"],
      ["Would open", String(signalCounts.would_open || 0), "shadow would-open"],
      ["No trade", String(signalCounts.no_trade || 0), "shadow no-trade"],
      ["Invalid", String(signalCounts.invalid || 0), "shadow invalid"],
      ["Risk blocked", String(signalCounts.risk_blocked || 0), "shadow risk-blocked"],
      ["Candle fetch OK", String(successes), "public read-only"],
      ["Candle fetch fail", String(failures), "public read-only"],
      ["No API keys used", String(boundary.api_keys_used === false), "boundary flag"],
      ["No private endpoints", String(boundary.private_endpoints_called === false), "boundary flag"],
      ["No signed endpoints", String(boundary.signed_endpoints_called === false), "boundary flag"],
      ["No order endpoints", String(boundary.order_endpoints_called === false), "boundary flag"],
      ["No orders submitted", String(boundary.orders_submitted === false), "boundary flag"],
      ["No strategy decisions", String(boundary.strategy_decisions_created === false), "boundary flag"],
      ["No order intents", String(boundary.order_intents_created === false), "boundary flag"],
      ["No submitted orders", String(boundary.submitted_orders_created === false), "boundary flag"],
    ];

    elements.uatSummaryCards.innerHTML = cards
      .map(
        ([label, value, detail]) => `
          <article class="metric-cell">
            <span class="metric-label">${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
            <small>${escapeHtml(detail)}</small>
          </article>
        `,
      )
      .join("");
  }

  function renderUatSignalMatrix(rows) {
    if (!elements.uatSignalMatrix) return;
    if (!rows.length) {
      setEmpty(elements.uatSignalMatrix, "No UAT2 shadow records match the selected filters.");
      return;
    }
    elements.uatSignalMatrix.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Component</th>
            <th>Timeframe</th>
            <th>Status</th>
            <th>Reason Codes</th>
            <th>Next Open</th>
            <th>Next Close</th>
            <th>Risk Status</th>
            <th>Operator Explanation</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((row) => `
            <tr>
              <td>${escapeHtml(row.symbol)}</td>
              <td>${escapeHtml(row.component)}</td>
              <td>${escapeHtml(row.timeframe)}</td>
              <td><span class="pill ${row.signal_status === "would_open" ? "warn" : "good"}">${escapeHtml(row.signal_status)}</span></td>
              <td>${escapeHtml((row.reason_codes || []).join(", ") || "none")}</td>
              <td>${escapeHtml(row.timing_status_by_assumption?.next_candle_open || "not_applicable")}</td>
              <td>${escapeHtml(row.timing_status_by_assumption?.next_candle_close || "not_applicable")}</td>
              <td>${escapeHtml(row.risk_summary?.risk_status || "unknown")}</td>
              <td>${escapeHtml(row.operator_visible_explanation || "")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderUatWouldOpen(records) {
    if (!elements.uatWouldOpenTable) return;
    const rows = records.filter((row) => row.signal_status === "would_open");
    if (!rows.length) {
      setEmpty(elements.uatWouldOpenTable, "No shadow would-open records loaded.");
      return;
    }
    elements.uatWouldOpenTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Component</th>
            <th>Candle Close</th>
            <th>Reason Codes</th>
            <th>Latest Close</th>
            <th>RSI</th>
            <th>MACD / Hist</th>
            <th>EMA5 / EMA10 / SMA20</th>
            <th>Next Open</th>
            <th>Next Close</th>
            <th>Risk Summary</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((row) => {
            const ind = row.indicator_summary || {};
            return `
              <tr>
                <td>${escapeHtml(row.symbol)}</td>
                <td>${escapeHtml(`${row.component} / ${row.timeframe}`)}</td>
                <td>${escapeHtml(row.candle_close_time_utc)}</td>
                <td>${escapeHtml((row.reason_codes || []).join(", "))}</td>
                <td>${escapeHtml(ind.latest_close)}</td>
                <td>${escapeHtml(ind.rsi14)}</td>
                <td>${escapeHtml(`${ind.macd || "n/a"} / ${ind.macd_histogram || "n/a"}`)}</td>
                <td>${escapeHtml(`${ind.ema5 || "n/a"} / ${ind.ema10 || "n/a"} / ${ind.sma20 || "n/a"}`)}</td>
                <td>${escapeHtml(`${row.timing_status_by_assumption?.next_candle_open || "n/a"}: ${ind.next_candle_open || "n/a"}`)}</td>
                <td>${escapeHtml(`${row.timing_status_by_assumption?.next_candle_close || "n/a"}: ${ind.next_candle_close || "n/a"}`)}</td>
                <td>${escapeHtml(row.risk_summary?.risk_status || "unknown")}</td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    `;
  }

  function renderUatNoTradeBreakdown(records) {
    const overall = countNoTradeReasons(records);
    if (!overall.length) {
      setEmpty(elements.uatNoTradeOverall, "No no-trade records loaded.");
    } else {
      const max = Math.max(...overall.map(([, count]) => count), 1);
      elements.uatNoTradeOverall.innerHTML = overall
        .map(([reason, count]) => `
          <div class="bar-row">
            <span class="bar-label">${escapeHtml(reason)}</span>
            <div class="bar-track"><div class="bar-fill positive" style="width:${Math.max(3, Math.round((count / max) * 100))}%"></div></div>
            <span class="bar-value">${escapeHtml(count)}</span>
          </div>
        `)
        .join("");
    }

    const renderGroupedReasons = (target, groupKey) => {
      if (!target) return;
      const grouped = {};
      records
        .filter((row) => row.signal_status === "no_trade")
        .forEach((row) => {
          const group = row[groupKey] || "unknown";
          grouped[group] ||= {};
          (row.reason_codes || ["unknown"]).forEach((reason) => {
            grouped[group][reason] = (grouped[group][reason] || 0) + 1;
          });
        });
      const rows = Object.entries(grouped).sort((a, b) => a[0].localeCompare(b[0]));
      if (!rows.length) {
        setEmpty(target, "No grouped no-trade reasons loaded.");
        return;
      }
      target.innerHTML = `
        <table>
          <thead><tr><th>${escapeHtml(groupKey)}</th><th>Reason Counts</th></tr></thead>
          <tbody>
            ${rows.map(([group, counts]) => `
              <tr>
                <td>${escapeHtml(group)}</td>
                <td>${escapeHtml(Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([reason, count]) => `${reason}: ${count}`).join(", "))}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    };

    renderGroupedReasons(elements.uatNoTradeComponent, "component");
    renderGroupedReasons(elements.uatNoTradeSymbol, "symbol");
  }

  function renderUatEthCandidate(records) {
    if (!elements.uatEthCandidateCard) return;
    const record = records.find((row) => row.symbol === "ETH" && row.component === "sleeve_1h");
    const reasons = record?.reason_codes?.join(", ") || "not loaded";
    elements.uatEthCandidateCard.innerHTML = `
      <article class="component-card" aria-current="true">
        <div class="component-card-header">
          <span class="component-card-title">money_flow_hyperliquid_eth_1h_baseline_uat_candidate</span>
          <span>observation-only</span>
        </div>
        <p class="card-note">Hyperliquid ETH USDC perpetual / sleeve_1h / current baseline Money Flow rules.</p>
        <div class="component-card-metrics">
          <div class="mini-metric"><span>UAT2 status</span><strong>${escapeHtml(record?.signal_status || "not loaded")}</strong></div>
          <div class="mini-metric"><span>Reason</span><strong>${escapeHtml(reasons)}</strong></div>
          <div class="mini-metric"><span>Orders</span><strong>not approved</strong></div>
        </div>
        <p class="strategy-note">Evidence candidate status: observation candidate only. Paper trading: not approved. Live trading: not approved. Order submission: not approved.</p>
      </article>
    `;
  }

  function renderUatTimingAndDrawdown(records) {
    if (elements.uatTimingPanel) {
      const timingCounts = records.reduce((counts, row) => {
        ["next_candle_open", "next_candle_close"].forEach((key) => {
          const status = row.timing_status_by_assumption?.[key] || "not_applicable";
          counts[`${key}:${status}`] = (counts[`${key}:${status}`] || 0) + 1;
        });
        return counts;
      }, {});
      elements.uatTimingPanel.innerHTML = `
        <ul class="check-list">
          <li><strong>next_candle_open</strong>: represented in UAT2 shadow records.</li>
          <li><strong>next_candle_close</strong>: represented in UAT2 shadow records.</li>
          <li><strong>same_candle_close_research_only</strong>: excluded from UAT2 primary action assumptions and remains research-only.</li>
          <li>Timing status counts: ${escapeHtml(Object.entries(timingCounts).map(([key, value]) => `${key}=${value}`).join(", "))}</li>
          <li>UAT2 does not execute any action from these assumptions.</li>
        </ul>
      `;
    }
    if (!elements.uatDrawdownCard) return;
    const drawdown = state.uat2Summary?.shadow_drawdown_state || {};
    elements.uatDrawdownCard.innerHTML = `
      <div class="boundary-grid">
        <div><span>Source</span><strong>${escapeHtml(drawdown.source || "not loaded")}</strong></div>
        <div><span>Not live account drawdown</span><strong>${escapeHtml(String(Boolean(drawdown.not_live_account_drawdown)))}</strong></div>
        <div><span>Initial shadow equity</span><strong>${escapeHtml(drawdown.initial_shadow_equity ?? "n/a")}</strong></div>
        <div><span>Current shadow equity</span><strong>${escapeHtml(drawdown.current_shadow_equity ?? "n/a")}</strong></div>
        <div><span>Max drawdown amount</span><strong>${escapeHtml(drawdown.max_drawdown_amount ?? "n/a")}</strong></div>
        <div><span>Max drawdown percent</span><strong>${escapeHtml(drawdown.max_drawdown_percent ?? "n/a")}</strong></div>
        <div><span>Threshold breached</span><strong>${escapeHtml(String(Boolean(drawdown.threshold_breached)))}</strong></div>
        <div><span>Reason codes</span><strong>${escapeHtml((drawdown.reason_codes || []).join(", ") || "none")}</strong></div>
      </div>
      <div class="warning-banner">UAT2 did not simulate PnL. This is not live account drawdown. This is not performance validation.</div>
    `;
  }

  function renderUatReadinessAndBoundaries() {
    if (elements.uat3ReadinessPanel) {
      const blockers = state.uat2Summary?.remaining_blockers || [];
      elements.uat3ReadinessPanel.innerHTML = `
        <div class="warning-banner"><strong>UAT3 is blocked.</strong></div>
        <ul class="check-list">
          ${blockers.map((blocker) => `<li>${escapeHtml(blocker)}</li>`).join("")}
          <li>Founder approval at this stage would approve UAT3 sandbox-order design/scoping only.</li>
          <li>It would not approve actual sandbox order submission.</li>
          <li>It would not approve paper trading.</li>
          <li>It would not approve live trading.</li>
          <li>No interactive approval action exists in this dashboard.</li>
        </ul>
      `;
    }

    if (!elements.uatBoundaryPanel) return;
    const boundary = state.uat2Summary?.boundary_flags || {};
    const fields = [
      "api_keys_used",
      "private_endpoints_called",
      "signed_endpoints_called",
      "order_endpoints_called",
      "orders_submitted",
      "strategy_decisions_created",
      "signal_events_created",
      "order_intents_created",
      "prepared_orders_created",
      "execution_readiness_assessments_created",
      "submitted_orders_created",
      "approvals_created",
      "routing_artifacts_created",
      "paper_trading_added",
      "live_trading_added",
      "evidence_packs_generated",
      "money_flow_rules_changed",
    ];
    elements.uatBoundaryPanel.innerHTML = fields
      .map((field) => {
        const value = Boolean(boundary[field]);
        return `
          <div class="${value ? "critical" : ""}">
            <span>${escapeHtml(field)}</span>
            <strong>${escapeHtml(String(value))}</strong>
          </div>
        `;
      })
      .join("");
  }

  function renderUatDashboard() {
    const records = uatRecords();
    if (!state.uat2Summary) {
      if (elements.uatSummaryCards) setEmpty(elements.uatSummaryCards, "UAT2 summary JSON not loaded.");
      [
        elements.uatSignalMatrix,
        elements.uatWouldOpenTable,
        elements.uatEthCandidateCard,
        elements.uat3ReadinessPanel,
        elements.uatBoundaryPanel,
        elements.uatNoTradeOverall,
        elements.uatNoTradeComponent,
        elements.uatNoTradeSymbol,
        elements.uatTimingPanel,
        elements.uatDrawdownCard,
      ].forEach((target) => {
        if (target) setEmpty(target, "Load docs/uat2_shadow_strategy_top20_observation_summary.json.");
      });
      return;
    }
    renderUatFilters(records);
    renderUatSummaryCards(records);
    renderUatEthCandidate(records);
    renderUatReadinessAndBoundaries();
    renderUatSignalMatrix(uatFilteredRecords(records));
    renderUatWouldOpen(records);
    renderUatNoTradeBreakdown(records);
    renderUatTimingAndDrawdown(records);
  }

  function render() {
    const summaries = allSummaries();
    const selected = activeSummaries();
    renderMetrics(summaries);
    renderFlags();
    renderFilters(summaries);
    renderComponentCards(summaries);
    renderDetail(selected);
    renderRunTable(selected);
    renderExperiments();
    renderUatDashboard();
  }

  function classifyJson(payload) {
    if (Array.isArray(payload?.campaign_results)) return "review";
    if (Array.isArray(payload?.run_reports)) return "batch";
    if (Array.isArray(payload?.summary_rows) && payload?.report === "sv1_17_true_replay_experiment_summary") {
      return "experiment_summary";
    }
    if (Array.isArray(payload?.audit_records) && payload?.uat3_readiness_decision) return "uat2_shadow_summary";
    return "unknown";
  }

  async function loadDefaultFiles() {
    const loaded = [];
    for (const path of DEFAULT_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        loaded.push({ path, payload });
      } catch (error) {
        console.warn(`Could not load ${path}`, error);
      }
    }

    await loadDefaultExperimentSummaries();
    await loadDefaultUat2Summaries();

    if (!loaded.length) {
      elements.sourceLabel.textContent = "Manual load";
      elements.sourceDetail.textContent = "Use the JSON loader to select local evidence files.";
      render();
      return;
    }

    state.review = null;
    state.batches = [];
    loaded.forEach(({ payload }) => {
      const type = classifyJson(payload);
      if (type === "review") state.review = payload;
      if (type === "batch") state.batches.push(payload);
    });
    elements.sourceLabel.textContent = "Dynamic equity reports loaded";
    elements.sourceDetail.textContent = `${loaded.length} JSON files from ignored SV1.13.2 dynamic_equity_pct reports paths.`;
    render();
  }

  function handleFiles(files) {
    const readers = Array.from(files).map(
      (file) =>
        new Promise((resolve) => {
          const reader = new FileReader();
          reader.onload = () => {
            try {
              resolve({ name: file.name, payload: JSON.parse(String(reader.result)) });
            } catch (error) {
              resolve({ name: file.name, error });
            }
          };
          reader.readAsText(file);
        }),
    );

    Promise.all(readers).then((items) => {
      const valid = items.filter((item) => item.payload);
      if (!valid.length) return;
      state.review = null;
      state.batches = [];
      valid.forEach(({ payload }) => {
        const type = classifyJson(payload);
        if (type === "review") state.review = payload;
        if (type === "batch") state.batches.push(payload);
        if (type === "experiment_summary") state.sv117FullSuiteRows = normalizeReplayRows(payload.summary_rows);
        if (type === "uat2_shadow_summary") state.uat2Summary = payload;
      });
      state.selectedComponent = "all";
      elements.sourceLabel.textContent = "Manual JSON loaded";
      elements.sourceDetail.textContent = `${valid.length} local files selected.`;
      render();
    });
  }

  async function loadDefaultExperimentSummaries() {
    for (const path of DEFAULT_EXPERIMENT_SUMMARY_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (classifyJson(payload) === "experiment_summary") {
          state.sv117FullSuiteRows = normalizeReplayRows(payload.summary_rows);
        }
      } catch (error) {
        console.warn(`Could not load ${path}`, error);
      }
    }
  }

  async function loadDefaultUat2Summaries() {
    for (const path of DEFAULT_UAT2_SUMMARY_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (classifyJson(payload) === "uat2_shadow_summary") {
          state.uat2Summary = payload;
        }
      } catch (error) {
        console.warn(`Could not load ${path}`, error);
      }
    }
  }

  function normalizeReplayRows(rows) {
    return (rows || []).map((row) => ({
      ...row,
      contexts: decimal(row.contexts),
      trades: decimal(row.trades),
      endingEquity: decimal(row.endingEquity),
      netPnl: decimal(row.netPnl),
      deltaVsBaseline: decimal(row.deltaVsBaseline),
      rejectedEntries: decimal(row.rejectedEntries),
      variantCandidates: decimal(row.variantCandidates),
      variantEntries: decimal(row.variantEntries),
      nearSupportEntries: decimal(row.nearSupportEntries),
      nearResistanceEntries: decimal(row.nearResistanceEntries),
      fallingKnifeCandidates: decimal(row.fallingKnifeCandidates),
      winRate: decimal(row.winRate),
      profitFactor: decimal(row.profitFactor),
      closedDrawdown: decimal(row.closedDrawdown),
      markToMarketDrawdown: decimal(row.markToMarketDrawdown),
      worstTrade: decimal(row.worstTrade),
    }));
  }

  elements.fileInput.addEventListener("change", (event) => {
    handleFiles(event.target.files || []);
  });

  elements.viewTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      setActiveView(tab.dataset.view || "evidence");
    });
  });

  setActiveView(state.activeView);
  render();
  loadDefaultFiles();
})();
