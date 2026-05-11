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

  const DEFAULT_UAT34_SUMMARY_FILES = [
    "../../docs/uat3_4_sandbox_routing_pipeline_and_order_ledger_summary.json",
  ];

  const DEFAULT_UAT42_SUMMARY_FILES = [
    "../../docs/uat4_2_live_market_dashboard_and_paper_equity_monitor_summary.json",
  ];

  const DEFAULT_PT0_SUMMARY_FILES = [
    "../../docs/pt0_tradingview_charts_and_top20_paper_sandbox_runtime_summary.json",
  ];

  const HYPERLIQUID_TESTNET_PUBLIC_INFO_URL = "https://api.hyperliquid-testnet.xyz/info";
  const TRADINGVIEW_LIGHTWEIGHT_CHARTS_VERSION = "5.2.0";
  const LIVE_MARKET_REFRESH_MS = 15000;
  const LIVE_CHART_CANDLE_COUNT = 96;
  const LIVE_TIMEFRAME_MINUTES = {
    "15m": 15,
    "1h": 60,
    "4h": 240,
  };
  const LIVE_PUBLIC_INFO_TYPES = new Set([
    "allMids",
    "candleSnapshot",
    "fundingHistory",
    "l2Book",
    "meta",
    "metaAndAssetCtxs",
  ]);

  function livePollingDisabledByQuery() {
    try {
      const params = new URLSearchParams(window.location.search || "");
      return params.get("disableLivePolling") === "true" || params.get("livePolling") === "false";
    } catch (_error) {
      return false;
    }
  }

  const UAT_WATCHLIST_SYMBOLS = [
    "BTC",
    "ETH",
    "SOL",
    "XRP",
    "ZEC",
    "BNB",
    "SUI",
    "TON",
    "DOGE",
    "TRX",
    "LAYER",
    "CHIP",
    "UNI",
    "ONDO",
    "AAVE",
  ];

  const UAT_COCKPIT_TIMEFRAMES = ["15m", "1h", "4h"];

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
    uat34Summary: null,
    uat42Summary: null,
    pt0Summary: null,
    tradingViewChart: {
      chart: null,
      mount: null,
      candleSeries: null,
      volumeSeries: null,
      indicatorSeries: {},
      key: null,
      markerHandle: null,
      resizeObserver: null,
      pendingResizeFrame: null,
      ready: false,
      fitContentApplied: false,
      lastVisibleRange: null,
    },
    liveMarketData: {
      enabled: !livePollingDisabledByQuery(),
      status: livePollingDisabledByQuery() ? "live_public_polling_disabled" : "not_started",
      disabledReason: livePollingDisabledByQuery() ? "query_flag" : null,
      endpoint: HYPERLIQUID_TESTNET_PUBLIC_INFO_URL,
      refreshMs: LIVE_MARKET_REFRESH_MS,
      lastUpdatedUtc: null,
      error: null,
      market_data: [],
      indicator_snapshots: [],
      privateSignedOrderEndpointsCalled: false,
      orderEndpointsCalled: false,
      liveEndpointCalled: false,
      timer: null,
      inFlight: false,
    },
    uatFilters: {
      symbol: "all",
      component: "all",
      status: "all",
      reason: "all",
    },
    uatCockpit: {
      symbol: "ETH",
      timeframe: "1h",
      watchlistFilter: "all",
      bottomTab: "routed",
      routedSymbol: "all",
      routedLifecycle: "all",
      routedEnvironment: "all",
      routedLabel: "all",
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
    uat3DesignPanel: document.querySelector("#uat3-design-panel"),
    uatBoundaryPanel: document.querySelector("#uat-boundary-panel"),
    uatSignalMatrix: document.querySelector("#uat-signal-matrix"),
    uatWouldOpenTable: document.querySelector("#uat-would-open-table"),
    uatNoTradeOverall: document.querySelector("#uat-no-trade-overall"),
    uatNoTradeComponent: document.querySelector("#uat-no-trade-component"),
    uatNoTradeSymbol: document.querySelector("#uat-no-trade-symbol"),
    uatTimingPanel: document.querySelector("#uat-timing-panel"),
    uatDrawdownCard: document.querySelector("#uat-drawdown-card"),
    uatRoutedOrdersSummary: document.querySelector("#uat-routed-orders-summary"),
    uatRoutedOrdersTable: document.querySelector("#uat-routed-orders-table"),
    uatCockpitSummaryCards: document.querySelector("#uat-cockpit-summary-cards"),
    uatCockpitSymbolFilter: document.querySelector("#uat-cockpit-symbol-filter"),
    uatCockpitTimeframeFilter: document.querySelector("#uat-cockpit-timeframe-filter"),
    uatWatchlistFilters: document.querySelector("#uat-watchlist-filters"),
    uatWatchlistTable: document.querySelector("#uat-watchlist-table"),
    uatPriceChart: document.querySelector("#uat-price-chart"),
    uatIndicatorPanel: document.querySelector("#uat-indicator-panel"),
    uatMarkerPanel: document.querySelector("#uat-marker-panel"),
    uatMarketDataCoverage: document.querySelector("#uat-market-data-coverage"),
    uatOrderBookPanel: document.querySelector("#uat-order-book-panel"),
    uatMarketInfoPanel: document.querySelector("#uat-market-info-panel"),
    uatSignalContextPanel: document.querySelector("#uat-signal-context-panel"),
    uatRiskContextPanel: document.querySelector("#uat-risk-context-panel"),
    uatLiveChartStatus: document.querySelector("#uat-live-chart-status"),
    uatRouteStatusCard: document.querySelector("#uat-route-status-card"),
    uatEquitySourceCard: document.querySelector("#uat-equity-source-card"),
    uatPaperEquityCard: document.querySelector("#uat-paper-equity-card"),
    uatBalancePollCard: document.querySelector("#uat-balance-poll-card"),
    uatPositionsPanel: document.querySelector("#uat-positions-panel"),
    uatRoutedSymbolFilter: document.querySelector("#uat-routed-symbol-filter"),
    uatRoutedLifecycleFilter: document.querySelector("#uat-routed-lifecycle-filter"),
    uatRoutedEnvironmentFilter: document.querySelector("#uat-routed-environment-filter"),
    uatRoutedLabelFilter: document.querySelector("#uat-routed-label-filter"),
    uatCockpitRoutedOrdersTable: document.querySelector("#uat-cockpit-routed-orders-table"),
    uatShadowSignalOverlay: document.querySelector("#uat-shadow-signal-overlay"),
    uatBottomTabs: Array.from(document.querySelectorAll("[data-uat-bottom-tab]")),
    uatBottomPanels: Array.from(document.querySelectorAll("[data-uat-bottom-panel]")),
    uatLifecyclePanel: document.querySelector("#uat-lifecycle-panel"),
    uatAuditLogPanel: document.querySelector("#uat-audit-log-panel"),
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

  function compactNumber(value, digits = 4) {
    if (value === null || value === undefined || value === "") return "n/a";
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return String(value);
    return parsed.toLocaleString(undefined, {
      maximumFractionDigits: digits,
    });
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
    state.activeView = ["evidence", "experiments", "uat-cockpit", "uat-shadow", "strategy"].includes(view)
      ? view
      : "evidence";
    elements.viewTabs.forEach((tab) => {
      tab.setAttribute("aria-selected", String(tab.dataset.view === state.activeView));
    });
    elements.viewPanels.forEach((panel) => {
      panel.hidden = panel.dataset.viewPanel !== state.activeView;
    });
    if (state.activeView === "uat-cockpit") {
      scheduleTradingViewResize();
    }
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

    if (elements.uat3DesignPanel) {
      elements.uat3DesignPanel.innerHTML = `
        <div class="warning-banner"><strong>UAT3.0 design/readiness only.</strong> Actual sandbox order submission is not approved.</div>
        <div class="boundary-grid">
          <div><span>UAT3.0 design status</span><strong>defined</strong></div>
          <div><span>UAT3.1 actual sandbox order status</span><strong>blocked</strong></div>
          <div><span>Initial sandbox subset</span><strong>Hyperliquid ETH USDC perpetual / sleeve_1h</strong></div>
          <div><span>Broad top-20 order submission</span><strong>not approved</strong></div>
          <div><span>Founder approval</span><strong>required for actual sandbox submission</strong></div>
          <div><span>Sandbox runtime policy</span><strong>fixture/implemented</strong></div>
          <div><span>Sandbox artifact label validator</span><strong>implemented</strong></div>
          <div><span>Approval scope validator</span><strong>fixture-tested</strong></div>
          <div><span>Risk gate evaluator</span><strong>fixture-tested</strong></div>
          <div><span>Sandbox account drawdown feed</span><strong>fixture only / missing live sandbox feed</strong></div>
          <div><span>Submit lease duplicate-prevention</span><strong>fixture-tested</strong></div>
          <div><span>Unified dry-run preflight</span><strong>implemented</strong></div>
          <div><span>Runtime full-blocker propagation</span><strong>implemented</strong></div>
          <div><span>Numeric edge-case validation</span><strong>implemented</strong></div>
          <div><span>Artifact label boundary enforcement</span><strong>implemented for persistence / API / dashboard / report helpers</strong></div>
          <div><span>Dry-run executable gate service</span><strong>implemented</strong></div>
          <div><span>Approval scope dry-run wiring</span><strong>implemented</strong></div>
          <div><span>Risk gate dry-run wiring</span><strong>implemented</strong></div>
          <div><span>Submit lease dry-run wiring</span><strong>implemented</strong></div>
          <div><span>Runtime policy semantics</span><strong>global orders disabled; sandbox orders separately gated</strong></div>
          <div><span>Actual sandbox approval</span><strong>missing</strong></div>
          <div><span>Sandbox drawdown feed</span><strong>fixture only / missing live-fed sandbox account truth</strong></div>
          <div><span>Real sandbox submit path</span><strong>missing</strong></div>
          <div><span>Lifecycle verification</span><strong>fixture-tested design only</strong></div>
          <div><span>Active order submission button</span><strong>false</strong></div>
        </div>
        <ul class="check-list">
          <li>UAT3.0.1 adds fixture/readiness validators only; it does not enable actual sandbox submission.</li>
          <li>UAT3.0.2 adds unified dry-run gate preflight, full runtime blocker propagation, and numeric edge-case validation only; it does not enable actual sandbox submission.</li>
          <li>UAT3.0.3 adds boundary-label enforcement helpers and dry-run executable gate wiring only; it does not enable actual sandbox submission.</li>
          <li>UAT3.1 is blocked by founder/operator approval for actual sandbox submission, live-fed sandbox drawdown, sandbox submit path wiring, executable approval-scope wiring to real persistence, risk gate wiring to the real submit path, and submit-lease integration verification.</li>
          <li>No dashboard control creates an approval, order intent, submitted order, or sandbox order.</li>
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

  function renderUatRoutedOrders() {
    const summary = state.uat34Summary;
    const records = Array.isArray(summary?.ledger_records) ? summary.ledger_records : [];
    if (elements.uatRoutedOrdersSummary) {
      const equity = summary?.equity_resolution || {};
      const cards = [
        ["Route", summary?.route_definition?.route_id || "not loaded"],
        ["Attempts", String(summary?.uat34_lifecycle_attempt_count ?? 0)],
        ["Order endpoint calls", String(summary?.order_endpoint_call_count ?? 0)],
        ["Cancel endpoint calls", String(summary?.cancel_endpoint_call_count ?? 0)],
        ["Equity source", equity.selected_equity_source || "not loaded"],
        ["Unified compatibility", summary?.unified_mode_compatibility_status || "not loaded"],
        ["No live endpoint", String(summary?.side_effect_flags?.live_endpoint_used === false)],
        ["No paper/live", String(summary?.side_effect_flags?.paper_trading_added === false && summary?.side_effect_flags?.live_trading_added === false)],
      ];
      elements.uatRoutedOrdersSummary.innerHTML = cards
        .map(([label, value]) => `
          <div>
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
          </div>
        `)
        .join("");
    }
    if (!elements.uatRoutedOrdersTable) return;
    if (!records.length) {
      setEmpty(elements.uatRoutedOrdersTable, "No UAT3.4 routed sandbox ledger records loaded.");
      return;
    }
    elements.uatRoutedOrdersTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Run</th>
            <th>Route</th>
            <th>Venue</th>
            <th>Environment</th>
            <th>Symbol</th>
            <th>Side</th>
            <th>Order Type</th>
            <th>Price</th>
            <th>Size</th>
            <th>Notional</th>
            <th>Lifecycle</th>
            <th>OID</th>
            <th>Cancel</th>
            <th>Reconcile</th>
            <th>Equity Source</th>
            <th>Labels</th>
          </tr>
        </thead>
        <tbody>
          ${records.map((row) => {
            const labels = row.sandbox_labels || {};
            return `
              <tr>
                <td>${escapeHtml(row.uat_run_id)}</td>
                <td>${escapeHtml(row.route_id)}</td>
                <td>${escapeHtml(row.venue)}</td>
                <td>${escapeHtml(row.environment)}</td>
                <td>${escapeHtml(row.symbol)}</td>
                <td>${escapeHtml(row.side)}</td>
                <td>${escapeHtml(row.order_type)}</td>
                <td>${escapeHtml(row.limit_price)}</td>
                <td>${escapeHtml(row.size)}</td>
                <td>${escapeHtml(row.estimated_notional)}</td>
                <td><span class="pill good">${escapeHtml(row.lifecycle_status)}</span></td>
                <td>${escapeHtml(row.order_id || "n/a")}</td>
                <td>${escapeHtml(row.cancel_status)}</td>
                <td>${escapeHtml(row.reconciliation_status)}</td>
                <td>${escapeHtml(row.selected_equity_source)}</td>
                <td>${escapeHtml(`sandbox=${labels.sandbox}; not_live=${labels.not_live}; not_paper=${labels.not_paper}`)}</td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    `;
  }

  function uatRecordFor(symbol, timeframe) {
    return uatRecords().find((row) => row.symbol === symbol && row.timeframe === timeframe) || null;
  }

  function precisionBySymbol(symbol) {
    const pt0Rows = Array.isArray(state.pt0Summary?.paper_universe)
      ? state.pt0Summary.paper_universe
      : [];
    const uatRows = Array.isArray(state.uat34Summary?.precision_validation)
      ? state.uat34Summary.precision_validation
      : [];
    return (
      pt0Rows.find((row) => row.symbol === symbol) ||
      uatRows.find((row) => row.symbol === symbol) ||
      null
    );
  }

  function routedLedgerRecords() {
    return Array.isArray(state.uat34Summary?.ledger_records) ? state.uat34Summary.ledger_records : [];
  }

  function pt0PaperTradeRows() {
    const rows = state.pt0Summary?.routed_orders_paper_trades?.records;
    return Array.isArray(rows) ? rows : [];
  }

  function uat42MarketRows() {
    const staticRows = Array.isArray(state.uat42Summary?.market_data) ? state.uat42Summary.market_data : [];
    const liveRows = Array.isArray(state.liveMarketData?.market_data) ? state.liveMarketData.market_data : [];
    if (!liveRows.length) return staticRows;
    const merged = new Map(staticRows.map((row) => [`${row.symbol}|${row.timeframe}`, row]));
    liveRows.forEach((row) => {
      const key = `${row.symbol}|${row.timeframe}`;
      const fallback = merged.get(key) || staticRows.find((item) => item.symbol === row.symbol) || {};
      merged.set(key, { ...fallback, ...row });
    });
    return Array.from(merged.values());
  }

  function uat42MarketFor(symbol, timeframe) {
    const rows = uat42MarketRows();
    return (
      rows.find((row) => row.symbol === symbol && row.timeframe === timeframe) ||
      rows.find((row) => row.symbol === symbol) ||
      null
    );
  }

  function uat42IndicatorFor(symbol, timeframe) {
    const liveRows = Array.isArray(state.liveMarketData?.indicator_snapshots)
      ? state.liveMarketData.indicator_snapshots
      : [];
    const liveMatch =
      liveRows.find((row) => row.symbol === symbol && row.timeframe === timeframe) ||
      liveRows.find((row) => row.symbol === symbol);
    if (liveMatch) return liveMatch;
    const rows = Array.isArray(state.uat42Summary?.indicator_snapshots)
      ? state.uat42Summary.indicator_snapshots
      : [];
    return (
      rows.find((row) => row.symbol === symbol && row.timeframe === timeframe) ||
      rows.find((row) => row.symbol === symbol) ||
      null
    );
  }

  function uat42SignalRecords() {
    const pt0Records = state.pt0Summary?.paper_scanner?.records;
    const uat42Records = state.uat42Summary?.strategy_scanner?.records;
    if (Array.isArray(pt0Records) && pt0Records.length) return pt0Records;
    return Array.isArray(uat42Records) ? uat42Records : [];
  }

  function uat42SignalFor(symbol, timeframe) {
    return (
      uat42SignalRecords().find((row) => row.symbol === symbol && row.timeframe === timeframe) ||
      uat42SignalRecords().find((row) => row.symbol === symbol) ||
      null
    );
  }

  function uat42IndicatorValue(snapshot, label) {
    const node = snapshot?.[label];
    if (!node) return "indicator_unavailable";
    if (!node.enough_history) return node.reason || "indicator_unavailable_insufficient_history";
    return node.value ?? "indicator_unavailable";
  }

  function uat42PaperEquity() {
    return state.pt0Summary?.paper_equity || state.uat42Summary?.paper_equity || {};
  }

  function uat42Polling() {
    return state.pt0Summary?.balance_position_polling || state.uat42Summary?.balance_position_polling || {};
  }

  function pt0UniverseAsset(symbol) {
    const rows = Array.isArray(state.pt0Summary?.paper_universe) ? state.pt0Summary.paper_universe : [];
    return rows.find((row) => row.symbol === symbol) || null;
  }

  function pt0Eligibility(symbol) {
    const asset = pt0UniverseAsset(symbol);
    return asset?.paper_eligibility || "blocked_metadata_not_loaded";
  }

  function pt0ApprovalSummary() {
    return state.pt0Summary?.approval_statements || {};
  }

  function pt0SizingPolicy() {
    return state.pt0Summary?.sizing_policy || state.uat42Summary?.sizing_policy || {};
  }

  function lightweightCharts() {
    return window.LightweightCharts || null;
  }

  function destroyTradingViewChart() {
    const chartState = state.tradingViewChart;
    if (chartState.pendingResizeFrame) {
      if (typeof window.cancelAnimationFrame === "function") {
        window.cancelAnimationFrame(chartState.pendingResizeFrame);
      } else {
        window.clearTimeout(chartState.pendingResizeFrame);
      }
      chartState.pendingResizeFrame = null;
    }
    if (chartState.resizeObserver) {
      chartState.resizeObserver.disconnect();
      chartState.resizeObserver = null;
    }
    if (chartState.chart) {
      chartState.chart.remove();
      chartState.chart = null;
    }
    chartState.mount = null;
    chartState.candleSeries = null;
    chartState.volumeSeries = null;
    chartState.indicatorSeries = {};
    chartState.markerHandle = null;
    chartState.key = null;
    chartState.ready = false;
    chartState.fitContentApplied = false;
    chartState.lastVisibleRange = null;
  }

  function chartTime(timestamp) {
    const parsed = Date.parse(timestamp || "");
    if (!Number.isFinite(parsed)) return Math.floor(Date.now() / 1000);
    return Math.floor(parsed / 1000);
  }

  function chartCandles(market) {
    if (state.liveMarketData?.enabled && !marketHasSelectedLiveCandles(market)) {
      return [];
    }
    const candles = Array.isArray(market?.candles) ? market.candles : [];
    return candles
      .map((candle) => ({
        time: chartTime(candle.timestamp_utc),
        open: decimal(candle.open, NaN),
        high: decimal(candle.high, NaN),
        low: decimal(candle.low, NaN),
        close: decimal(candle.close, NaN),
        volume: decimal(candle.volume, 0),
      }))
      .filter((candle) =>
        Number.isFinite(candle.time) &&
        Number.isFinite(candle.open) &&
        Number.isFinite(candle.high) &&
        Number.isFinite(candle.low) &&
        Number.isFinite(candle.close),
      )
      .sort((a, b) => a.time - b.time);
  }

  function marketHasSelectedLiveCandles(market) {
    return (
      market?.source === "hyperliquid_testnet_public_read_only_browser_poll" &&
      market?.candles_source === "hyperliquid_testnet_candleSnapshot" &&
      market?.selected_live_candles === true &&
      market?.public_read_only_confirmation === true &&
      Array.isArray(market?.candles) &&
      market.candles.length > 0
    );
  }

  function indicatorSeries(candles, label, period) {
    const closes = candles.map((candle) => candle.close);
    if (closes.length < period) return [];
    if (label === "SMA20") {
      return candles.slice(period - 1).map((candle, index) => ({
        time: candle.time,
        value: roundDisplay(
          closes.slice(index, index + period).reduce((sum, value) => sum + value, 0) / period,
        ),
      }));
    }
    const multiplier = 2 / (period + 1);
    let current = closes.slice(0, period).reduce((sum, value) => sum + value, 0) / period;
    const rows = [{ time: candles[period - 1].time, value: roundDisplay(current) }];
    for (let index = period; index < closes.length; index += 1) {
      current = (closes[index] - current) * multiplier + current;
      rows.push({ time: candles[index].time, value: roundDisplay(current) });
    }
    return rows;
  }

  function chartMarkers(candles) {
    if (!candles.length) return [];
    const firstTime = candles[0].time;
    const lastTime = candles.at(-1).time;
    const selectedMarkers = uatCockpitMarkers()
      .filter((row) => row.symbol === state.uatCockpit.symbol)
      .slice(-8);
    return selectedMarkers.map((row, index) => {
      const parsed = chartTime(row.timestamp);
      const time = parsed >= firstTime && parsed <= lastTime
        ? parsed
        : candles[Math.min(candles.length - 1, Math.max(0, candles.length - selectedMarkers.length + index))].time;
      const isGreen = row.markerType.startsWith("green");
      return {
        time,
        position: isGreen ? "belowBar" : "aboveBar",
        color: isGreen ? "#25d084" : "#ff5a66",
        shape: isGreen ? "arrowUp" : "arrowDown",
        text: `${row.markerType.replace("green marker: ", "").replace("red marker: ", "")}; ${row.source}; ${row.orderId || "n/a"}`,
      };
    });
  }

  function selectedChartKey() {
    return `${state.uatCockpit.symbol}|${state.uatCockpit.timeframe}`;
  }

  function chartDimensions(mount) {
    const rect = mount.getBoundingClientRect();
    const width = Math.max(320, Math.floor(rect.width || mount.clientWidth || 720));
    const height = Math.max(320, Math.floor(rect.height || mount.clientHeight || 520));
    return { width, height };
  }

  function resizeTradingViewChart() {
    const chartState = state.tradingViewChart;
    if (!chartState.chart || !chartState.mount) return;
    const { width, height } = chartDimensions(chartState.mount);
    chartState.chart.resize(width, height);
  }

  function scheduleTradingViewResize() {
    const chartState = state.tradingViewChart;
    if (!chartState.chart || !chartState.mount) return;
    if (chartState.pendingResizeFrame) return;
    const raf = typeof window.requestAnimationFrame === "function"
      ? window.requestAnimationFrame
      : (callback) => window.setTimeout(callback, 16);
    chartState.pendingResizeFrame = raf(() => {
      chartState.pendingResizeFrame = null;
      resizeTradingViewChart();
    });
  }

  function chartPriceRows(candles) {
    return candles.map(({ time, open, high, low, close }) => ({ time, open, high, low, close }));
  }

  function chartVolumeRows(candles) {
    return candles.map((candle) => ({
      time: candle.time,
      value: candle.volume,
      color: candle.close >= candle.open ? "rgba(37, 208, 132, 0.26)" : "rgba(255, 90, 102, 0.26)",
    }));
  }

  function chartPricePrecision(candles) {
    const latest = Math.abs(decimal(candles.at(-1)?.close, 0));
    if (latest >= 1000) return 1;
    if (latest >= 100) return 2;
    if (latest >= 1) return 4;
    return 6;
  }

  function chartPriceFormat(candles) {
    const precision = chartPricePrecision(candles);
    return {
      type: "price",
      precision,
      minMove: Number(`1e-${precision}`),
    };
  }

  function formatChartPrice(value, candles) {
    const numeric = decimal(value, NaN);
    if (!Number.isFinite(numeric)) return "n/a";
    const precision = chartPricePrecision(candles);
    return numeric.toLocaleString("en-US", {
      minimumFractionDigits: Math.min(precision, 2),
      maximumFractionDigits: precision,
    });
  }

  function chartPriceStats(candles) {
    const latest = candles.at(-1);
    if (!latest) {
      return { latest: "n/a", high: "n/a", low: "n/a", open: "n/a", close: "n/a" };
    }
    const high = Math.max(...candles.map((candle) => candle.high));
    const low = Math.min(...candles.map((candle) => candle.low));
    return {
      latest: formatChartPrice(latest.close, candles),
      high: formatChartPrice(high, candles),
      low: formatChartPrice(low, candles),
      open: formatChartPrice(latest.open, candles),
      close: formatChartPrice(latest.close, candles),
    };
  }

  function updateTradingViewChartData(candles) {
    const chartState = state.tradingViewChart;
    if (!chartState.candleSeries || !chartState.volumeSeries) return;
    const timeScale = chartState.chart?.timeScale?.();
    chartState.lastVisibleRange = timeScale?.getVisibleLogicalRange?.() || null;
    chartState.candleSeries.setData(chartPriceRows(candles));
    chartState.volumeSeries.setData(chartVolumeRows(candles));
    [
      ["EMA5", 5],
      ["EMA10", 10],
      ["SMA20", 20],
    ].forEach(([label, period]) => {
      chartState.indicatorSeries[label]?.setData(indicatorSeries(candles, label, period));
    });
    const markers = chartMarkers(candles);
    if (chartState.markerHandle && typeof chartState.markerHandle.setMarkers === "function") {
      chartState.markerHandle.setMarkers(markers);
    } else if (typeof chartState.candleSeries.setMarkers === "function") {
      chartState.candleSeries.setMarkers(markers);
    }
    const updatedTimeScale = chartState.chart?.timeScale?.();
    if (chartState.lastVisibleRange && typeof updatedTimeScale?.setVisibleLogicalRange === "function") {
      updatedTimeScale.setVisibleLogicalRange(chartState.lastVisibleRange);
    }
    scheduleTradingViewResize();
  }

  function updateTradingViewTopline(market, record, candles) {
    const symbolTarget = elements.uatPriceChart?.querySelector("[data-chart-symbol]");
    const candleTarget = elements.uatPriceChart?.querySelector("[data-chart-candle]");
    const latestTarget = elements.uatPriceChart?.querySelector("[data-chart-latest]");
    const axisLatestTarget = elements.uatPriceChart?.querySelector("[data-chart-axis-latest]");
    const axisHighTarget = elements.uatPriceChart?.querySelector("[data-chart-axis-high]");
    const axisLowTarget = elements.uatPriceChart?.querySelector("[data-chart-axis-low]");
    const axisOpenTarget = elements.uatPriceChart?.querySelector("[data-chart-axis-open]");
    const axisCloseTarget = elements.uatPriceChart?.querySelector("[data-chart-axis-close]");
    const stats = chartPriceStats(candles);
    if (symbolTarget) symbolTarget.textContent = `${state.uatCockpit.symbol}-PERP`;
    if (candleTarget) {
      candleTarget.textContent = `${state.uatCockpit.timeframe} latest candle ${market?.last_candle_close_time || record?.candle_close_time_utc || "n/a"}`;
    }
    if (latestTarget) latestTarget.textContent = stats.latest;
    if (axisLatestTarget) axisLatestTarget.textContent = stats.latest;
    if (axisHighTarget) axisHighTarget.textContent = `H ${stats.high}`;
    if (axisLowTarget) axisLowTarget.textContent = `L ${stats.low}`;
    if (axisOpenTarget) axisOpenTarget.textContent = `O ${stats.open}`;
    if (axisCloseTarget) axisCloseTarget.textContent = `C ${stats.close}`;
  }

  function renderTradingViewLightweightChart(record, market) {
    const tv = lightweightCharts();
    if (!elements.uatPriceChart || !tv) return false;
    const candles = chartCandles(market);
    if (!candles.length) return false;
    const chartState = state.tradingViewChart;
    const chartKey = selectedChartKey();
    if (chartState.ready && chartState.key === chartKey && chartState.chart && chartState.candleSeries && chartState.volumeSeries) {
      updateTradingViewTopline(market, record, candles);
      updateTradingViewChartData(candles);
      return true;
    }

    destroyTradingViewChart();
    const priceStats = chartPriceStats(candles);
    elements.uatPriceChart.innerHTML = `
      <div class="tradingview-chart-topline">
        <div>
          <strong data-chart-symbol>${escapeHtml(state.uatCockpit.symbol)}-PERP</strong>
          <span data-chart-candle>${escapeHtml(state.uatCockpit.timeframe)} latest candle ${escapeHtml(market?.last_candle_close_time || record?.candle_close_time_utc || "n/a")}</span>
        </div>
        <div class="chart-price-tape">
          <span>Latest</span>
          <strong data-chart-latest>${escapeHtml(priceStats.latest)}</strong>
        </div>
      </div>
      <div class="tradingview-chart-stage">
        <div class="tradingview-lightweight-chart" role="img" aria-label="TradingView Lightweight Charts candlestick chart with visible right price scale"></div>
        <aside class="chart-price-axis-readout" aria-label="Selected asset price scale">
          <span>Price USDC</span>
          <strong data-chart-axis-latest>${escapeHtml(priceStats.latest)}</strong>
          <small data-chart-axis-high>H ${escapeHtml(priceStats.high)}</small>
          <small data-chart-axis-low>L ${escapeHtml(priceStats.low)}</small>
          <small data-chart-axis-open>O ${escapeHtml(priceStats.open)}</small>
          <small data-chart-axis-close>C ${escapeHtml(priceStats.close)}</small>
        </aside>
      </div>
      <div class="tradingview-attribution">Charts: TradingView Lightweight Charts v${TRADINGVIEW_LIGHTWEIGHT_CHARTS_VERSION} (Apache-2.0). Public read-only Hyperliquid testnet data; no API keys, private endpoints, signed endpoints, order endpoints, or live endpoints.</div>
    `;

    const mount = elements.uatPriceChart.querySelector(".tradingview-lightweight-chart");
    const { width, height } = chartDimensions(mount);
    const chart = tv.createChart(mount, {
      width,
      height,
      layout: {
        background: { type: tv.ColorType.Solid, color: "#071014" },
        textColor: "#c9d5dc",
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: "rgba(133, 156, 171, 0.08)" },
        horzLines: { color: "rgba(133, 156, 171, 0.08)" },
      },
      crosshair: {
        mode: tv.CrosshairMode.Normal,
      },
      rightPriceScale: {
        visible: true,
        borderVisible: true,
        borderColor: "rgba(133, 156, 171, 0.18)",
        entireTextOnly: false,
        scaleMargins: { top: 0.06, bottom: 0.22 },
      },
      timeScale: {
        borderColor: "rgba(133, 156, 171, 0.18)",
        timeVisible: true,
        secondsVisible: false,
      },
    });
    const candleSeries = chart.addSeries(tv.CandlestickSeries, {
      upColor: "#25d084",
      downColor: "#ff5a66",
      borderVisible: false,
      wickUpColor: "#25d084",
      wickDownColor: "#ff5a66",
      priceFormat: chartPriceFormat(candles),
      priceLineVisible: true,
      lastValueVisible: true,
    });
    candleSeries.setData(chartPriceRows(candles));

    const volumeSeries = chart.addSeries(tv.HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
      color: "rgba(107, 132, 145, 0.35)",
    });
    chart.priceScale("volume").applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
    volumeSeries.setData(chartVolumeRows(candles));

    const lineSeries = {};
    [
      ["EMA5", 5, "#26c6da"],
      ["EMA10", 10, "#f8c15c"],
      ["SMA20", 20, "#b68cff"],
    ].forEach(([label, period, color]) => {
      const line = chart.addSeries(tv.LineSeries, {
        color,
        lineWidth: 2,
        priceFormat: chartPriceFormat(candles),
        priceLineVisible: false,
        lastValueVisible: true,
        title: label,
      });
      line.setData(indicatorSeries(candles, label, period));
      lineSeries[label] = line;
    });

    const markers = chartMarkers(candles);
    if (typeof tv.createSeriesMarkers === "function") {
      state.tradingViewChart.markerHandle = tv.createSeriesMarkers(candleSeries, markers);
    } else if (typeof candleSeries.setMarkers === "function") {
      candleSeries.setMarkers(markers);
    }
    chart.timeScale().fitContent();
    chartState.chart = chart;
    chartState.mount = mount;
    chartState.candleSeries = candleSeries;
    chartState.volumeSeries = volumeSeries;
    chartState.indicatorSeries = lineSeries;
    chartState.key = chartKey;
    chartState.ready = true;
    chartState.fitContentApplied = true;
    if (typeof ResizeObserver !== "undefined") {
      const observer = new ResizeObserver(scheduleTradingViewResize);
      observer.observe(mount);
      chartState.resizeObserver = observer;
    }
    return true;
  }

  function renderUatCockpitFilters() {
    renderSelect(elements.uatCockpitSymbolFilter, UAT_WATCHLIST_SYMBOLS, state.uatCockpit.symbol, "All watched pairs");
    renderSelect(
      elements.uatCockpitTimeframeFilter,
      UAT_COCKPIT_TIMEFRAMES,
      state.uatCockpit.timeframe,
      "All timeframes",
    );
    if (elements.uatCockpitSymbolFilter) {
      elements.uatCockpitSymbolFilter.onchange = () => {
        state.uatCockpit.symbol = elements.uatCockpitSymbolFilter.value === "all"
          ? "ETH"
          : elements.uatCockpitSymbolFilter.value;
        renderUatCockpit();
        refreshLiveMarketData();
      };
    }
    if (elements.uatCockpitTimeframeFilter) {
      elements.uatCockpitTimeframeFilter.onchange = () => {
        state.uatCockpit.timeframe = elements.uatCockpitTimeframeFilter.value === "all"
          ? "1h"
          : elements.uatCockpitTimeframeFilter.value;
        renderUatCockpit();
        refreshLiveMarketData();
      };
    }
  }

  function selectedCockpitRecord() {
    return uatRecordFor(state.uatCockpit.symbol, state.uatCockpit.timeframe);
  }

  function renderUatLiveChartStatus() {
    if (!elements.uatLiveChartStatus) return;
    const live = state.liveMarketData || {};
    const status = live.status || "not_started";
    if (!live.enabled) {
      elements.uatLiveChartStatus.textContent = `Live chart: live_public_polling_disabled; local PT0/UAT4.2 fallback only; no Hyperliquid public polling; refresh ${Math.round(LIVE_MARKET_REFRESH_MS / 1000)}s disabled`;
      return;
    }
    const updated = live.lastUpdatedUtc ? `last update ${live.lastUpdatedUtc}` : "waiting for first update";
    const error = live.error ? `; ${live.error}` : "";
    elements.uatLiveChartStatus.textContent = `Live chart: ${status}; public-read-only testnet; ${updated}; refresh ${Math.round(LIVE_MARKET_REFRESH_MS / 1000)}s${error}`;
  }

  function renderUatCockpitSummaryCards() {
    if (!elements.uatCockpitSummaryCards) return;
    const cards = [
      ["Environment", "sandbox/testnet", "no live endpoint"],
    ];
    elements.uatCockpitSummaryCards.innerHTML = cards
      .map(([label, value, detail]) => `
        <div class="status-chip">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
          <small>${escapeHtml(detail)}</small>
        </div>
      `)
      .join("");
  }

  function renderUatWatchlist() {
    if (!elements.uatWatchlistTable) return;
    const filterOptions = [
      ["all", "All"],
      ["would_open", "Would-open"],
      ["no_trade", "No-trade"],
      ["active_sandbox_route", "Active sandbox route"],
      ["missing_data", "Missing data"],
      ["favorites", "Favorites"],
    ];
    if (elements.uatWatchlistFilters) {
      elements.uatWatchlistFilters.innerHTML = filterOptions
        .map(([id, label]) => `
          <button class="micro-tab" type="button" role="tab" aria-selected="${state.uatCockpit.watchlistFilter === id}" data-watchlist-filter="${escapeHtml(id)}">${escapeHtml(label)}</button>
        `)
        .join("");
      elements.uatWatchlistFilters.querySelectorAll("button").forEach((button) => {
        button.addEventListener("click", () => {
          state.uatCockpit.watchlistFilter = button.dataset.watchlistFilter || "all";
          renderUatCockpit();
        });
      });
    }

    const rows = UAT_WATCHLIST_SYMBOLS.map((symbol) => {
      const records = uatRecords().filter((row) => row.symbol === symbol);
      const selectedRecord = uatRecordFor(symbol, state.uatCockpit.timeframe) || records[0];
      const market = uat42MarketFor(symbol, state.uatCockpit.timeframe);
      const paperSignal = uat42SignalFor(symbol, state.uatCockpit.timeframe);
      const precision = precisionBySymbol(symbol);
      const eligibility = pt0Eligibility(symbol);
      const eligibilityReasons = (pt0UniverseAsset(symbol)?.reason_codes || []).join(", ");
      const chartAvailable = Boolean(market?.candle_data_available) || records.length > 0;
      const latest = market?.latest_price || selectedRecord?.indicator_summary?.latest_close || precision?.sample_mid || "n/a";
      const signalStatus = paperSignal?.status || selectedRecord?.signal_status || "no_data";
      const precisionStatus = precision
        ? precision.precision_validation_passed || precision.paper_eligibility === "eligible"
          ? "precision_ok"
          : `precision_blocked: ${(precision.reason_codes || []).join(", ")}`
        : "precision_not_loaded";
      const isActiveRoute = symbol === "ETH" && routedLedgerRecords().some((row) => row.symbol === "ETH");
      return {
        symbol,
        latest,
        change24h: market?.change_24h_pct,
        volume24h: market?.volume_24h,
        signalStatus,
        precisionStatus,
        chartAvailable,
        marketDataStatus: market?.market_data_status || (chartAvailable ? "refreshed_public_read_only_local_json" : "market_data_unavailable"),
        orderStatus: isActiveRoute
          ? "active ETH sandbox route; approval and risk gates required"
          : eligibility === "eligible"
          ? "paper/sandbox eligible under PT0 gates"
          : eligibility,
        eligibility,
        eligibilityReasons,
        activeRoute: isActiveRoute,
      };
    }).filter((row) => {
      switch (state.uatCockpit.watchlistFilter) {
        case "would_open":
          return row.signalStatus === "would_open";
        case "no_trade":
          return row.signalStatus === "no_trade";
        case "active_sandbox_route":
          return row.activeRoute;
        case "missing_data":
          return !row.chartAvailable;
        case "favorites":
          return row.symbol === "ETH";
        default:
          return true;
      }
    });

    if (!rows.length) {
      setEmpty(elements.uatWatchlistTable, "No watched markets match the selected filter.");
      return;
    }
    elements.uatWatchlistTable.innerHTML = rows
      .map((row) => `
        <button class="market-row ${row.symbol === state.uatCockpit.symbol ? "active" : ""}" type="button" data-symbol="${escapeHtml(row.symbol)}">
          <span class="market-symbol">${escapeHtml(row.symbol)}</span>
          <span class="market-product">Hyperliquid perp / USDC</span>
          <span class="market-price">${escapeHtml(compactNumber(row.latest))}</span>
          <span class="market-change ${decimal(row.change24h) >= 0 ? "positive" : "negative"}">${escapeHtml(row.change24h === null || row.change24h === undefined ? "24h change unavailable" : pct(decimal(row.change24h)))}</span>
          <span class="market-signal ${row.signalStatus === "would_open" ? "positive" : row.signalStatus === "no_trade" ? "neutral" : "warn"}">${escapeHtml(row.signalStatus)}</span>
          <span class="market-data-state">${escapeHtml(row.marketDataStatus)}</span>
          <span class="market-badge">paper/sandbox only</span>
          <span class="market-badge ${row.eligibility === "eligible" ? "safe" : "warn"}" title="${escapeHtml(row.eligibilityReasons || row.orderStatus)}">${escapeHtml(row.orderStatus)}</span>
        </button>
      `)
      .join("");
    elements.uatWatchlistTable.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        state.uatCockpit.symbol = button.dataset.symbol || "ETH";
        renderUatCockpit();
      });
    });
  }

  function renderUatMarketDataCoverage() {
    if (!elements.uatMarketDataCoverage) return;
    elements.uatMarketDataCoverage.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Latest Price / Mid</th>
            <th>Candles</th>
            <th>Selected Timeframe</th>
            <th>Last Candle Close</th>
            <th>Source</th>
            <th>Endpoint Category</th>
            <th>Failure Reason</th>
          </tr>
        </thead>
        <tbody>
          ${UAT_WATCHLIST_SYMBOLS.map((symbol) => {
            const record = uatRecordFor(symbol, state.uatCockpit.timeframe) || uatRecords().find((row) => row.symbol === symbol);
            const market = uat42MarketFor(symbol, state.uatCockpit.timeframe);
            const latest = market?.latest_price || record?.indicator_summary?.latest_close || precisionBySymbol(symbol)?.sample_mid || "n/a";
            return `
              <tr>
                <td>${escapeHtml(symbol)}</td>
                <td>${escapeHtml(latest)}</td>
                <td>${escapeHtml(market?.candle_data_available ? "yes" : record ? "yes_local_shadow" : "no")}</td>
                <td>${escapeHtml(state.uatCockpit.timeframe)}</td>
                <td>${escapeHtml(market?.last_candle_close_time || record?.candle_close_time_utc || "n/a")}</td>
                <td>${escapeHtml(market ? "Hyperliquid testnet public polling / PT0-UAT4.2 JSON fallback" : "docs/uat2_shadow_strategy_top20_observation_summary.json")}</td>
                <td>${escapeHtml(market?.endpoint_category || "public_read_only / local_summary_json")}</td>
                <td>${escapeHtml(market?.failure_reason || (record ? "none" : "market_data_unavailable"))}</td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    `;
  }

  function renderUatChartAndIndicators() {
    const record = selectedCockpitRecord();
    const market = uat42MarketFor(state.uatCockpit.symbol, state.uatCockpit.timeframe);
    const liveIndicators = uat42IndicatorFor(state.uatCockpit.symbol, state.uatCockpit.timeframe);
    if (elements.uatPriceChart) {
      if (!record && !market) {
        destroyTradingViewChart();
        setEmpty(elements.uatPriceChart, "No chart snapshot is available for the selected pair/timeframe.");
      } else {
        const rendered = renderTradingViewLightweightChart(record, market);
        if (!rendered) {
          destroyTradingViewChart();
          setEmpty(
            elements.uatPriceChart,
            "TradingView Lightweight Charts is waiting for public-read-only candles. Dashboard falls back to PT0/UAT4.2 summary state without inventing chart data.",
          );
        }
      }
    }
    if (!elements.uatIndicatorPanel) return;
    const ind = record?.indicator_summary || {};
    const indicatorRows = [
      ["EMA5", uat42IndicatorValue(liveIndicators, "EMA5") || ind.ema5],
      ["EMA10", uat42IndicatorValue(liveIndicators, "EMA10") || ind.ema10],
      ["SMA20", uat42IndicatorValue(liveIndicators, "SMA20") || ind.sma20],
      ["RSI", uat42IndicatorValue(liveIndicators, "RSI") || ind.rsi14],
      ["MACD", uat42IndicatorValue(liveIndicators, "MACD") || ind.macd],
      ["MACD signal", uat42IndicatorValue(liveIndicators, "MACD signal") || ind.macd_signal],
      ["MACD histogram", uat42IndicatorValue(liveIndicators, "MACD histogram") || ind.macd_histogram],
      ["Regime label", "regime_unavailable"],
      ["Trend label", "trend_context_from_indicator_stack"],
      ["Volatility label", "volatility_context_unavailable"],
      ["Entry quality", uat42SignalFor(state.uatCockpit.symbol, state.uatCockpit.timeframe)?.status || record?.signal_status || "no_data"],
    ];
    elements.uatIndicatorPanel.innerHTML = indicatorRows
      .map(([label, value]) => `
        <div class="indicator-tile">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(compactNumber(value || "indicator_unavailable_insufficient_history"))}</strong>
        </div>
      `)
      .join("");
  }

  function uatCockpitMarkers() {
    const shadowMarkers = uatRecords()
      .filter((row) => ["would_open", "would_close"].includes(row.signal_status))
      .map((row) => ({
        symbol: row.symbol,
        component: row.component,
        timestamp: row.candle_close_time_utc,
        markerType: row.signal_status === "would_open" ? "green marker: shadow would-open" : "red marker: shadow would-close",
        source: "shadow audit",
        reasonCodes: row.reason_codes || [],
        orderId: "n/a",
        labels: "shadow signal; no order intent; no paper/live",
      }));
    const routedMarkers = routedLedgerRecords().flatMap((row) => [
      {
        symbol: row.symbol,
        component: row.route_id,
        timestamp: state.uat34Summary?.recorded_at_utc || "uat3.4",
        markerType: "green marker: sandbox order accepted/open",
        source: "routed sandbox order ledger",
        reasonCodes: row.reason_codes || [],
        orderId: row.order_id || "n/a",
        labels: "sandbox/testnet lifecycle probe; not live; not paper; not performance validation",
      },
      {
        symbol: row.symbol,
        component: row.route_id,
        timestamp: state.uat34Summary?.recorded_at_utc || "uat3.4",
        markerType: "red marker: sandbox cancel",
        source: "routed sandbox order ledger",
        reasonCodes: [row.cancel_status || "cancel_status_unknown"],
        orderId: row.order_id || "n/a",
        labels: "sandbox cancel; not live; not paper; not performance validation",
      },
    ]);
    const paperObservationMarkers = uat42SignalRecords()
      .filter((row) => ["would_open", "would_close", "would_reduce"].includes(row.status))
      .map((row) => ({
        symbol: row.symbol,
        component: row.component,
        timestamp: row.timestamp_utc || row.candle_close_time,
        markerType: row.status === "would_open"
          ? "green marker: paper would-open"
          : "red marker: paper would-close",
        source: row.source || "paper scanner",
        reasonCodes: row.reason_codes || [],
        orderId: "n/a",
        labels: "internal paper-equity scanner; sandbox/testnet only; not live; not real capital; no order artifact",
      }));
    return [...shadowMarkers, ...paperObservationMarkers, ...routedMarkers];
  }

  function renderUatMarkers() {
    if (!elements.uatMarkerPanel) return;
    const markers = uatCockpitMarkers().filter(
      (row) => state.uatCockpit.symbol === "all" || row.symbol === state.uatCockpit.symbol,
    );
    if (!markers.length) {
      setEmpty(elements.uatMarkerPanel, "No UAT markers match the selected pair.");
      return;
    }
    elements.uatMarkerPanel.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Component / Route</th>
            <th>Timestamp</th>
            <th>Marker Type</th>
            <th>Source</th>
            <th>Reasons</th>
            <th>OID</th>
            <th>Labels</th>
          </tr>
        </thead>
        <tbody>
          ${markers.map((row) => `
            <tr>
              <td>${escapeHtml(row.symbol)}</td>
              <td>${escapeHtml(row.component)}</td>
              <td>${escapeHtml(row.timestamp)}</td>
              <td><span class="marker-pill ${row.markerType.startsWith("green") ? "green" : "red"}">${escapeHtml(row.markerType)}</span></td>
              <td>${escapeHtml(row.source)}</td>
              <td>${escapeHtml(row.reasonCodes.join(", ") || "none")}</td>
              <td>${escapeHtml(row.orderId)}</td>
              <td>${escapeHtml(`${row.labels}; tooltip includes sandbox/not-live and no paper/live confirmation`)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderUatRightRail() {
    const record = selectedCockpitRecord();
    const market = uat42MarketFor(state.uatCockpit.symbol, state.uatCockpit.timeframe);
    const liveIndicators = uat42IndicatorFor(state.uatCockpit.symbol, state.uatCockpit.timeframe);
    const paperSignal = uat42SignalFor(state.uatCockpit.symbol, state.uatCockpit.timeframe);
    const poll = uat42Polling();
    const paperEquity = uat42PaperEquity();
    const ind = record?.indicator_summary || {};
    const precision = precisionBySymbol(state.uatCockpit.symbol) || {};
    const route = state.uat34Summary?.route_definition || {};
    const equity = state.uat34Summary?.equity_resolution || {};
    const drawdown = state.uat34Summary?.drawdown_feed || {};
    const reasons = record?.reason_codes?.join(", ") || "none";
    const riskReasons = record?.risk_summary?.risk_reason_codes?.join(", ") || "none";
    const microRows = (rows) => rows
      .map(([label, value, tone]) => `
        <div class="micro-row ${tone || ""}">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(compactNumber(value))}</strong>
        </div>
      `)
      .join("");

    if (elements.uatOrderBookPanel) {
      const book = market?.order_book || {};
      elements.uatOrderBookPanel.innerHTML = `
        ${microRows([
          ["Bid", book.bid || "order_book_unavailable", book.bid ? "positive" : "muted"],
          ["Ask", book.ask || "order_book_unavailable", book.ask ? "negative" : "muted"],
          ["Spread", book.spread || "market_data_unavailable", book.spread ? "" : "muted"],
          ["Reference close", market?.latest_price || ind.latest_close || "n/a", "positive"],
          ["Source", market?.source || "local_summary_json", ""],
          ["Endpoint category", "public_read_only", ""],
          ["Private endpoint", "not used", "safe"],
        ])}
      `;
    }

    if (elements.uatMarketInfoPanel) {
      elements.uatMarketInfoPanel.innerHTML = `
        ${microRows([
          ["Latest price", market?.latest_price || ind.latest_close || precision.sample_mid || "n/a", "positive"],
          ["Mark price", market?.mark_price || "market_data_unavailable", market?.mark_price ? "" : "muted"],
          ["24h volume", market?.volume_24h || "market_data_unavailable", market?.volume_24h ? "" : "muted"],
          ["Open interest", market?.open_interest || "market_data_unavailable", market?.open_interest ? "" : "muted"],
          ["Funding", market?.funding || "market_data_unavailable", market?.funding ? "" : "muted"],
          ["Asset id", precision.asset_id ?? "n/a", ""],
          ["Tick/lot precision", precision.precision_validation_passed === true ? "passed" : precision.reason_codes?.join(", ") || "not loaded", precision.precision_validation_passed === true ? "safe" : "warn"],
        ])}
      `;
    }

    if (elements.uatSignalContextPanel) {
      elements.uatSignalContextPanel.innerHTML = `
        ${microRows([
          ["Money Flow status", paperSignal?.status || record?.signal_status || "no_data", paperSignal?.status === "would_open" || record?.signal_status === "would_open" ? "positive" : "neutral"],
          ["Component", paperSignal?.component || record?.component || "n/a", ""],
          ["RSI state", uat42IndicatorValue(liveIndicators, "RSI") || ind.rsi14 || "indicator_unavailable", ""],
          ["MACD state", uat42IndicatorValue(liveIndicators, "MACD histogram") || ind.macd_histogram || "indicator_unavailable", ""],
          ["Trend stack", liveIndicators ? "EMA/SMA values loaded" : ind.ema5 && ind.ema10 && ind.sma20 ? "EMA/SMA values loaded" : "indicator_unavailable", ""],
          ["Entry quality", paperSignal?.status === "would_open" ? "paper observation would-open" : record?.signal_status === "would_open" ? "shadow would-open only" : "no entry", paperSignal?.status === "would_open" || record?.signal_status === "would_open" ? "positive" : "neutral"],
          ["No-trade reason", paperSignal?.status === "no_trade" ? (paperSignal.reason_codes || []).join(", ") : record?.signal_status === "no_trade" ? reasons : "not_applicable", ""],
        ])}
      `;
    }

    if (elements.uatRiskContextPanel) {
      elements.uatRiskContextPanel.innerHTML = `
        ${microRows([
          ["Sandbox route", route.route_id || "not loaded", ""],
          ["Drawdown status", drawdown.status || "not loaded", drawdown.status === "sandbox_drawdown_feed_live_fed_verified" ? "safe" : "warn"],
          ["Equity source", equity.selected_equity_source || "not loaded", ""],
          ["Internal paper equity", paperEquity.current_paper_equity || "not loaded", "safe"],
          ["Sizing basis", pt0SizingPolicy().sizing_basis || "not loaded", ""],
          ["Balance poll", `${poll.poll_interval_seconds || 60}s sandbox read-only`, "safe"],
          ["Sandbox equity", equity.selected_sandbox_equity || drawdown.sandbox_account_equity || "n/a", ""],
          ["Not-live-account", String(Boolean(drawdown.not_live_account)), "safe"],
          ["Risk status", record?.risk_summary?.risk_status || "not loaded", ""],
          ["Risk reasons", riskReasons, ""],
          ["Order submission", "disabled in dashboard", "safe"],
        ])}
      `;
    }
  }

  function renderUatRouteAndEquityCards() {
    const route = state.uat34Summary?.route_definition || {};
    const account = state.uat34Summary?.account_targeting_summary || {};
    const equity = state.uat34Summary?.equity_resolution || {};
    const paperEquity = uat42PaperEquity();
    const sizingPolicy = pt0SizingPolicy();
    const polling = uat42Polling();
    const sandboxConfirmation = polling.sandbox_account_confirmation || {};
    if (elements.uatRouteStatusCard) {
      const rows = [
        ["Route id", route.route_id || "fixed_target_hyperliquid_testnet_eth"],
        ["Venue", "Hyperliquid"],
        ["Environment", route.environment || "testnet/sandbox"],
        ["Symbol", route.symbol || "ETH"],
        ["Account role", account.account_role || "user"],
        ["vaultAddress", account.vaultAddress_present ? "present" : "omitted"],
        ["Selected equity source", equity.selected_equity_source || "standard_perp_clearinghouse"],
        ["Unified compatibility", state.uat34Summary?.unified_mode_compatibility_status || "supported"],
        ["Order scope", "sandbox only"],
        ["Paper", "approved for testnet/sandbox only"],
        ["Live", "not approved"],
        ["Broad top-20 paper/sandbox", "approved under PT0 gates"],
      ];
      elements.uatRouteStatusCard.innerHTML = rows
        .map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`)
        .join("");
    }
    if (!elements.uatEquitySourceCard) return;
    const equityRows = [
      ["selected_equity_source", equity.selected_equity_source || "not loaded"],
      ["standard_perp_clearinghouse status", equity.perp_account_value ? "available" : "not loaded"],
      ["perp_account_value", equity.perp_account_value ?? "n/a"],
      ["perp_withdrawable", equity.perp_withdrawable ?? "n/a"],
      ["unified_margin_spot_clearinghouse fallback status", "supported"],
      ["spot_usdc_total", equity.spot_usdc_total ?? "n/a"],
      ["spot_usdc_hold", equity.spot_usdc_hold ?? "n/a"],
      ["selected_sandbox_equity", equity.selected_sandbox_equity ?? "n/a"],
    ];
    elements.uatEquitySourceCard.innerHTML = equityRows
      .map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`)
      .join("");

    if (elements.uatPaperEquityCard) {
      const paperRows = [
        ["Internal Paper Equity", paperEquity.current_paper_equity || "10000"],
        ["Starting paper equity", paperEquity.initial_paper_equity || "10000"],
        ["Realized PnL", paperEquity.realized_pnl || "0"],
        ["Unrealized PnL", paperEquity.unrealized_pnl || "0"],
        ["Drawdown", paperEquity.drawdown_percent || "0"],
        ["Source", paperEquity.source || "internal_paper_equity_ledger"],
        ["Sizing basis", sizingPolicy.sizing_basis || "realized_equity"],
        ["Risk display", sizingPolicy.risk_display_basis || "realized_plus_unrealized"],
      ];
      elements.uatPaperEquityCard.innerHTML = paperRows
        .map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`)
        .join("");
    }

    if (elements.uatBalancePollCard) {
      const pollRows = [
        ["Poll interval", polling.poll_interval_seconds ? `${polling.poll_interval_seconds} seconds` : "60 seconds"],
        ["Poll source", polling.policy?.source || "sandbox_private_read_only"],
        ["Sandbox equity", sandboxConfirmation.sandbox_account_equity || "not loaded"],
        ["Withdrawable", sandboxConfirmation.withdrawable || "n/a"],
        ["Available", sandboxConfirmation.available_balance || "n/a"],
        ["Not live account", String(Boolean(sandboxConfirmation.not_live_account))],
        ["Last poll", sandboxConfirmation.timestamp_utc || "not loaded"],
        ["Order endpoint", String(Boolean(sandboxConfirmation.private_order_endpoints_called))],
      ];
      elements.uatBalancePollCard.innerHTML = pollRows
        .map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`)
        .join("");
    }

    if (elements.uatPositionsPanel) {
      const positions = Array.isArray(sandboxConfirmation.open_positions)
        ? sandboxConfirmation.open_positions
        : [];
      if (!positions.length) {
        setEmpty(
          elements.uatPositionsPanel,
          "No sandbox positions loaded. If unavailable, the dashboard shows explicit unavailable state instead of inventing values.",
        );
      } else {
        elements.uatPositionsPanel.innerHTML = `
          <table>
            <thead><tr><th>Symbol</th><th>Size</th><th>Entry</th><th>Unrealized PnL</th><th>Source</th></tr></thead>
            <tbody>
              ${positions.map((row) => `
                <tr>
                  <td>${escapeHtml(row.symbol || row.coin || "unknown")}</td>
                  <td>${escapeHtml(row.size || row.szi || "n/a")}</td>
                  <td>${escapeHtml(row.entry_price || row.entryPx || "n/a")}</td>
                  <td>${escapeHtml(row.unrealized_pnl || row.unrealizedPnl || "n/a")}</td>
                  <td>sandbox_private_read_only</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        `;
      }
    }
  }

  function renderUatCockpitRoutedFilters(records) {
    renderSelect(elements.uatRoutedSymbolFilter, uniqueSorted(records.map((row) => row.symbol)), state.uatCockpit.routedSymbol, "All symbols");
    renderSelect(
      elements.uatRoutedLifecycleFilter,
      uniqueSorted(records.map((row) => row.lifecycle_status)),
      state.uatCockpit.routedLifecycle,
      "All lifecycle states",
    );
    renderSelect(
      elements.uatRoutedEnvironmentFilter,
      uniqueSorted(records.map((row) => row.environment)),
      state.uatCockpit.routedEnvironment,
      "All environments",
    );
    renderSelect(elements.uatRoutedLabelFilter, ["sandbox_not_live"], state.uatCockpit.routedLabel, "All labels");
    [
      [elements.uatRoutedSymbolFilter, "routedSymbol"],
      [elements.uatRoutedLifecycleFilter, "routedLifecycle"],
      [elements.uatRoutedEnvironmentFilter, "routedEnvironment"],
      [elements.uatRoutedLabelFilter, "routedLabel"],
    ].forEach(([select, key]) => {
      if (!select) return;
      select.onchange = () => {
        state.uatCockpit[key] = select.value || "all";
        renderUatCockpit();
      };
    });
  }

  function renderUatCockpitRoutedOrders() {
    const records = routedLedgerRecords();
    const paperRows = pt0PaperTradeRows();
    renderUatCockpitRoutedFilters(records);
    if (!elements.uatCockpitRoutedOrdersTable) return;
    const filtered = records.filter((row) => {
      const labels = row.sandbox_labels || {};
      const labelOk =
        state.uatCockpit.routedLabel === "all" ||
        (labels.sandbox === true && labels.not_live === true && labels.not_paper === true);
      return (
        (state.uatCockpit.routedSymbol === "all" || row.symbol === state.uatCockpit.routedSymbol) &&
        (state.uatCockpit.routedLifecycle === "all" || row.lifecycle_status === state.uatCockpit.routedLifecycle) &&
        (state.uatCockpit.routedEnvironment === "all" || row.environment === state.uatCockpit.routedEnvironment) &&
        labelOk
      );
    });
    if (!filtered.length) {
      setEmpty(elements.uatCockpitRoutedOrdersTable, "No routed sandbox orders match the selected filters.");
      return;
    }
    elements.uatCockpitRoutedOrdersTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Run id</th>
            <th>Source</th>
            <th>Route id</th>
            <th>Route type</th>
            <th>Venue</th>
            <th>Environment</th>
            <th>Symbol</th>
            <th>Side</th>
            <th>Order type</th>
            <th>Limit price</th>
            <th>Size</th>
            <th>Notional</th>
            <th>TIF</th>
            <th>Asset id</th>
            <th>OID</th>
            <th>Lifecycle</th>
            <th>Cancel</th>
            <th>Reconcile</th>
            <th>Open remains</th>
            <th>Position changed</th>
            <th>Equity source</th>
            <th>Paper equity before</th>
            <th>Paper equity after</th>
            <th>Paper PnL</th>
            <th>Sandbox labels</th>
            <th>No paper/live</th>
            <th>Sanitized response</th>
          </tr>
        </thead>
        <tbody>
          ${filtered.map((row) => {
            const labels = row.sandbox_labels || {};
            const paper = paperRows.find((item) => item.sandbox_order_id === row.order_id || item.route === row.route_id) || {};
            return `
              <tr>
                <td>${escapeHtml(row.uat_run_id)}</td>
                <td>${escapeHtml(paper.source || "routed sandbox order ledger")}</td>
                <td>${escapeHtml(row.route_id)}</td>
                <td>${escapeHtml(row.route_type)}</td>
                <td>${escapeHtml(row.venue)}</td>
                <td>${escapeHtml(row.environment)}</td>
                <td>${escapeHtml(row.symbol)}</td>
                <td>${escapeHtml(row.side)}</td>
                <td>${escapeHtml(row.order_type)}</td>
                <td>${escapeHtml(row.limit_price)}</td>
                <td>${escapeHtml(row.size)}</td>
                <td>${escapeHtml(row.estimated_notional)}</td>
                <td>${escapeHtml(row.tif)}</td>
                <td>${escapeHtml(row.asset_id)}</td>
                <td>${escapeHtml(row.order_id || "n/a")}</td>
                <td>${escapeHtml(row.lifecycle_status)}</td>
                <td>${escapeHtml(row.cancel_status)}</td>
                <td>${escapeHtml(row.reconciliation_status)}</td>
                <td>${escapeHtml(String(Boolean(row.open_order_remains)))}</td>
                <td>${escapeHtml(row.position_changed)}</td>
                <td>${escapeHtml(row.selected_equity_source)}</td>
                <td>${escapeHtml(paper.paper_equity_before || uat42PaperEquity().initial_paper_equity || "10000")}</td>
                <td>${escapeHtml(paper.paper_equity_after || uat42PaperEquity().current_paper_equity || "10000")}</td>
                <td>${escapeHtml(`realized=${paper.realized_pnl || uat42PaperEquity().realized_pnl || "0"}; unrealized=${paper.unrealized_pnl || uat42PaperEquity().unrealized_pnl || "0"}`)}</td>
                <td>${escapeHtml(`sandbox=${labels.sandbox}; testnet=${labels.testnet}; not_live=${labels.not_live}; not_paper=${labels.not_paper}`)}</td>
                <td>${escapeHtml(String(Boolean(row.no_live_no_paper_confirmation)))}</td>
                <td>${escapeHtml(JSON.stringify(row.sanitized_exchange_response || {}))}</td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    `;
  }

  function renderUatBottomTabs() {
    elements.uatBottomTabs.forEach((tab) => {
      const selected = tab.dataset.uatBottomTab === state.uatCockpit.bottomTab;
      tab.setAttribute("aria-selected", String(selected));
      tab.onclick = () => {
        state.uatCockpit.bottomTab = tab.dataset.uatBottomTab || "routed";
        renderUatCockpit();
      };
    });
    elements.uatBottomPanels.forEach((panel) => {
      panel.hidden = panel.dataset.uatBottomPanel !== state.uatCockpit.bottomTab;
    });
  }

  function renderUatLifecyclePanel() {
    if (!elements.uatLifecyclePanel) return;
    const records = routedLedgerRecords();
    if (!records.length) {
      setEmpty(elements.uatLifecyclePanel, "No routed sandbox lifecycle records loaded.");
      return;
    }
    const record = records[0];
    const steps = [
      ["planned", "complete", "fixed-target sandbox route selected"],
      ["submitted", record.endpoint_called ? "complete" : "not_reached", "exactly one sandbox/testnet endpoint call in UAT3.4"],
      ["accepted/open", record.reason_codes?.includes("order_accepted_open") ? "complete" : "not_reached", `oid ${record.order_id || "n/a"}`],
      ["canceled", record.cancel_status === "success" ? "complete" : "not_reached", `cancel status ${record.cancel_status || "n/a"}`],
      ["reconciled", record.reconciliation_status === "completed" ? "complete" : "not_reached", `open order remains ${String(Boolean(record.open_order_remains))}`],
    ];
    elements.uatLifecyclePanel.innerHTML = steps
      .map(([step, status, detail]) => `
        <div class="lifecycle-step ${status === "complete" ? "complete" : ""}">
          <span>${escapeHtml(step)}</span>
          <strong>${escapeHtml(status)}</strong>
          <small>${escapeHtml(detail)}</small>
        </div>
      `)
      .join("");
  }

  function renderUatAuditPanel() {
    if (!elements.uatAuditLogPanel) return;
    const records = routedLedgerRecords();
    const poll = uat42Polling();
    const events = [
      [
        "live_public_charting",
        state.liveMarketData?.status || "not_started",
        `${state.liveMarketData?.lastUpdatedUtc || "waiting"}; TradingView Lightweight Charts; Hyperliquid testnet public info only; no keys/private/signed/order endpoints`,
      ],
      ["pt0_approval", "paper_trading_approved", "Hyperliquid testnet/sandbox only; live and real-capital trading remain not approved"],
      ["pt0_top20", "broader_supported_top20_paper_sandbox_approved", "unsupported assets remain blocked by metadata/precision/risk gates"],
      ["pt0_charting", `TradingView Lightweight Charts ${TRADINGVIEW_LIGHTWEIGHT_CHARTS_VERSION}`, "official local bundle; hosted widget not used"],
      ["pt0_paper_equity", "internal_10000_usdc_ledger_visible", "paper-equity simulation; not real capital"],
      ["pt0_balance_poll", `${poll.poll_interval_seconds || 60}s sandbox private read-only policy`, "order-capable categories forbidden"],
      ["uat4.2_monitor", "live_public_market_data_summary_loaded", "public-read-only refresh JSON; no keys"],
      ["uat4.1_dashboard", "exchange_style_redesign", "dashboard visualization only; no exchange call"],
      ["uat4.0_cockpit", "local_json_loaded", "UAT2 shadow summary and UAT3.4 routed ledger"],
      ["uat3.4_route", records.length ? "accepted/open -> canceled -> reconciled lifecycle" : "ledger_missing", "sandbox/testnet lifecycle probe; not live; not performance validation"],
      ["safety", "order controls disabled", "paper/sandbox routing remains risk-gated; no live endpoint"],
      ["security", "secrets redacted", "dashboard displays sanitized summaries only"],
    ];
    elements.uatAuditLogPanel.innerHTML = `
      <table>
        <thead><tr><th>Source</th><th>Event</th><th>Sanitized detail</th></tr></thead>
        <tbody>
          ${events.map(([source, event, detail]) => `
            <tr>
              <td>${escapeHtml(source)}</td>
              <td>${escapeHtml(event)}</td>
              <td>${escapeHtml(detail)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderUatShadowSignalOverlay() {
    if (!elements.uatShadowSignalOverlay) return;
    const rows = uatRecords().filter((row) => row.symbol === state.uatCockpit.symbol);
    const paperRows = uat42SignalRecords().filter((row) => row.symbol === state.uatCockpit.symbol);
    if (!rows.length && !paperRows.length) {
      setEmpty(elements.uatShadowSignalOverlay, "No shadow signals available for the selected pair.");
      return;
    }
    elements.uatShadowSignalOverlay.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Component</th>
            <th>Timeframe</th>
            <th>Status</th>
            <th>Reason codes</th>
            <th>next_candle_open</th>
            <th>next_candle_close</th>
            <th>Marker mapping</th>
            <th>Same-candle close</th>
            <th>Operator explanation</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((row) => `
            <tr>
              <td>${escapeHtml(row.symbol)}</td>
              <td>${escapeHtml(row.component)}</td>
              <td>${escapeHtml(row.timeframe)}</td>
              <td>${escapeHtml(row.signal_status)}</td>
              <td>${escapeHtml((row.reason_codes || []).join(", ") || "none")}</td>
              <td>${escapeHtml(row.timing_status_by_assumption?.next_candle_open || "n/a")}</td>
              <td>${escapeHtml(row.timing_status_by_assumption?.next_candle_close || "n/a")}</td>
              <td>${escapeHtml(row.signal_status === "would_open" ? "green marker: shadow would-open, not actual trade" : "side-panel only")}</td>
              <td>same_candle_close_research_only remains research-only</td>
              <td>${escapeHtml(row.operator_visible_explanation || "")}</td>
            </tr>
          `).join("")}
          ${paperRows.map((row) => `
            <tr>
              <td>${escapeHtml(row.symbol)}</td>
              <td>${escapeHtml(row.component)}</td>
              <td>${escapeHtml(row.timeframe)}</td>
              <td>${escapeHtml(row.status)}</td>
              <td>${escapeHtml((row.reason_codes || []).join(", ") || "none")}</td>
              <td>${escapeHtml(row.next_candle_open_assumption || "observation_only")}</td>
              <td>${escapeHtml(row.next_candle_close_assumption || "observation_only")}</td>
              <td>${escapeHtml(row.status === "would_open" ? "green marker: paper observation would-open, not actual trade" : "side-panel only")}</td>
              <td>${escapeHtml(row.same_candle_close_research_only || "research_only")}</td>
              <td>${escapeHtml(row.operator_explanation || "paper observation only")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function liveChartDisclaimer() {
    const live = state.liveMarketData || {};
    if (!live.enabled) {
      return "Live public chart polling is disabled by query flag. Dashboard is using committed PT0/UAT4.2 local summary JSON only. No API keys, private order endpoints, signed order endpoints, order endpoints, or live endpoints are used.";
    }
    if (live.status === "live_public_read_only_connected") {
      return `TradingView Lightweight Charts is rendering Hyperliquid testnet public info every ${Math.round(LIVE_MARKET_REFRESH_MS / 1000)} seconds. No API keys, private order endpoints, signed order endpoints, order endpoints, or live endpoints are used.`;
    }
    if (live.error) {
      return `Live public chart polling is unavailable (${live.error}). Dashboard is falling back to committed PT0/UAT4.2 local summary JSON. No API keys, private order endpoints, signed order endpoints, order endpoints, or live endpoints are used.`;
    }
    return "TradingView Lightweight Charts public polling is starting. Dashboard falls back to committed PT0/UAT4.2 local summary JSON until the first public-read-only update arrives. No API keys, private order endpoints, signed order endpoints, order endpoints, or live endpoints are used.";
  }

  async function postHyperliquidPublicInfo(payload) {
    if (!payload || !LIVE_PUBLIC_INFO_TYPES.has(payload.type)) {
      throw new Error("dashboard_live_chart_public_info_type_not_allowlisted");
    }
    const body = JSON.stringify(payload);
    if (/\"user\"|\"action\"|\"signature\"|\"vaultAddress\"/i.test(body)) {
      throw new Error("dashboard_live_chart_private_or_order_payload_forbidden");
    }
    const response = await fetch(HYPERLIQUID_TESTNET_PUBLIC_INFO_URL, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body,
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error(`public_read_only_http_${response.status}`);
    }
    return response.json();
  }

  function liveCandlePayload(symbol, timeframe) {
    const intervalMinutes = LIVE_TIMEFRAME_MINUTES[timeframe] || 60;
    const endTime = Date.now();
    const startTime = endTime - intervalMinutes * LIVE_CHART_CANDLE_COUNT * 60 * 1000;
    return {
      type: "candleSnapshot",
      req: {
        coin: symbol,
        interval: timeframe,
        startTime,
        endTime,
      },
    };
  }

  function normalizeLiveCandles(payload) {
    if (!Array.isArray(payload)) return [];
    return payload
      .map((row) => {
        const startedAt = Number(row.t ?? row.T ?? row.time ?? row.timestamp ?? 0);
        return {
          timestamp_utc: Number.isFinite(startedAt) && startedAt > 0 ? new Date(startedAt).toISOString() : "n/a",
          open: String(row.o ?? row.open ?? ""),
          high: String(row.h ?? row.high ?? ""),
          low: String(row.l ?? row.low ?? ""),
          close: String(row.c ?? row.close ?? ""),
          volume: String(row.v ?? row.volume ?? "0"),
        };
      })
      .filter((row) => row.close !== "");
  }

  function computeDashboardIndicators(candles, symbol, timeframe) {
    const closes = candles.map((row) => decimal(row.close)).filter((value) => Number.isFinite(value));
    const timestamp = candles.at(-1)?.timestamp_utc || new Date().toISOString();
    const value = (label, raw, enough) => ({
      label,
      value: enough && Number.isFinite(raw) ? String(roundDisplay(raw)) : null,
      enough_history: Boolean(enough && Number.isFinite(raw)),
      reason: enough && Number.isFinite(raw) ? "computed_live_public_read_only" : "indicator_unavailable_insufficient_history",
    });
    const macdValues = macd(closes);
    return {
      symbol,
      timeframe,
      timestamp_utc: timestamp,
      EMA5: value("EMA5", ema(closes, 5), closes.length >= 5),
      EMA10: value("EMA10", ema(closes, 10), closes.length >= 10),
      SMA20: value("SMA20", sma(closes, 20), closes.length >= 20),
      RSI: value("RSI", rsi(closes, 14), closes.length >= 15),
      MACD: value("MACD", macdValues.macd, closes.length >= 35),
      "MACD signal": value("MACD signal", macdValues.signal, closes.length >= 35),
      "MACD histogram": value("MACD histogram", macdValues.histogram, closes.length >= 35),
    };
  }

  function sma(values, period) {
    if (values.length < period) return NaN;
    return values.slice(-period).reduce((sum, value) => sum + value, 0) / period;
  }

  function ema(values, period) {
    if (values.length < period) return NaN;
    const multiplier = 2 / (period + 1);
    let current = values.slice(0, period).reduce((sum, value) => sum + value, 0) / period;
    values.slice(period).forEach((value) => {
      current = (value - current) * multiplier + current;
    });
    return current;
  }

  function rsi(values, period) {
    if (values.length <= period) return NaN;
    const gains = [];
    const losses = [];
    for (let index = 1; index < values.length; index += 1) {
      const delta = values[index] - values[index - 1];
      gains.push(Math.max(delta, 0));
      losses.push(Math.abs(Math.min(delta, 0)));
    }
    let avgGain = gains.slice(0, period).reduce((sum, value) => sum + value, 0) / period;
    let avgLoss = losses.slice(0, period).reduce((sum, value) => sum + value, 0) / period;
    for (let index = period; index < gains.length; index += 1) {
      avgGain = (avgGain * (period - 1) + gains[index]) / period;
      avgLoss = (avgLoss * (period - 1) + losses[index]) / period;
    }
    if (avgLoss === 0) return 100;
    return 100 - 100 / (1 + avgGain / avgLoss);
  }

  function macd(values) {
    if (values.length < 35) return { macd: NaN, signal: NaN, histogram: NaN };
    const macdSeries = [];
    for (let index = 26; index <= values.length; index += 1) {
      const slice = values.slice(0, index);
      macdSeries.push(ema(slice, 12) - ema(slice, 26));
    }
    const signal = ema(macdSeries, 9);
    const latest = macdSeries.at(-1);
    return { macd: latest, signal, histogram: latest - signal };
  }

  function roundDisplay(value) {
    return Math.round(value * 1_000_000) / 1_000_000;
  }

  function buildLiveMarketRows(mids, symbol, timeframe, candles) {
    const localRows = Array.isArray(state.uat42Summary?.market_data) ? state.uat42Summary.market_data : [];
    return UAT_WATCHLIST_SYMBOLS.map((watchSymbol) => {
      const fallback = localRows.find((row) => row.symbol === watchSymbol) || {};
      const mid = mids && Object.prototype.hasOwnProperty.call(mids, watchSymbol) ? mids[watchSymbol] : fallback.latest_price;
      const isSelected = watchSymbol === symbol;
      const hasSelectedCandles = isSelected && candles.length > 0;
      return {
        ...fallback,
        symbol: watchSymbol,
        venue: "hyperliquid",
        product_type: "USDC perpetual",
        quote_or_settlement: "USDC",
        timeframe,
        latest_price: mid ? String(mid) : fallback.latest_price || null,
        mid_price: mid ? String(mid) : fallback.mid_price || null,
        mark_price: mid ? String(mid) : fallback.mark_price || null,
        candles: hasSelectedCandles ? candles : [],
        candles_source: hasSelectedCandles ? "hyperliquid_testnet_candleSnapshot" : "awaiting_selected_symbol_candleSnapshot",
        selected_live_candles: hasSelectedCandles,
        candle_data_available: hasSelectedCandles,
        selected_timeframe_available: hasSelectedCandles,
        last_candle_close_time: hasSelectedCandles ? candles.at(-1).timestamp_utc : null,
        source: hasSelectedCandles
          ? "hyperliquid_testnet_public_read_only_browser_poll"
          : "hyperliquid_testnet_public_allMids_browser_poll",
        endpoint_category: "public_read_only",
        market_data_status: hasSelectedCandles
          ? "live_public_read_only_streaming"
          : "live_public_mid_only_waiting_for_selected_candles",
        failure_reason: hasSelectedCandles ? null : "selected_symbol_candleSnapshot_not_loaded_yet",
        public_read_only_confirmation: true,
        private_signed_order_endpoints_called: false,
      };
    });
  }

  function sanitizeLiveChartError(error) {
    const message = String(error?.message || error || "unknown_error");
    return message.replace(/[A-Fa-f0-9]{32,}/g, "[REDACTED]").slice(0, 120);
  }

  async function refreshLiveMarketData() {
    if (!state.liveMarketData.enabled || state.liveMarketData.inFlight || typeof fetch !== "function") return;
    state.liveMarketData.inFlight = true;
    state.liveMarketData.status = "live_public_read_only_refreshing";
    renderUatLiveChartStatus();
    try {
      const symbol = state.uatCockpit.symbol || "ETH";
      const timeframe = state.uatCockpit.timeframe || "1h";
      const [mids, candlePayload] = await Promise.all([
        postHyperliquidPublicInfo({ type: "allMids" }),
        postHyperliquidPublicInfo(liveCandlePayload(symbol, timeframe)),
      ]);
      const candles = normalizeLiveCandles(candlePayload);
      state.liveMarketData.market_data = buildLiveMarketRows(mids, symbol, timeframe, candles);
      state.liveMarketData.indicator_snapshots = candles.length ? [computeDashboardIndicators(candles, symbol, timeframe)] : [];
      state.liveMarketData.status = "live_public_read_only_connected";
      state.liveMarketData.lastUpdatedUtc = new Date().toISOString();
      state.liveMarketData.error = null;
    } catch (error) {
      state.liveMarketData.status = "live_public_read_only_unavailable";
      state.liveMarketData.error = sanitizeLiveChartError(error);
    } finally {
      state.liveMarketData.inFlight = false;
      render();
    }
  }

  function startLiveMarketPolling() {
    if (!state.liveMarketData.enabled || state.liveMarketData.timer || typeof fetch !== "function") return;
    refreshLiveMarketData();
    state.liveMarketData.timer = window.setInterval(refreshLiveMarketData, LIVE_MARKET_REFRESH_MS);
  }

  function renderUatCockpit() {
    renderUatBottomTabs();
    renderUatCockpitFilters();
    renderUatLiveChartStatus();
    renderUatCockpitSummaryCards();
    renderUatWatchlist();
    renderUatMarketDataCoverage();
    renderUatChartAndIndicators();
    renderUatMarkers();
    renderUatRightRail();
    renderUatRouteAndEquityCards();
    renderUatCockpitRoutedOrders();
    renderUatShadowSignalOverlay();
    renderUatLifecyclePanel();
    renderUatAuditPanel();
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
        elements.uat3DesignPanel,
        elements.uatBoundaryPanel,
        elements.uatNoTradeOverall,
        elements.uatNoTradeComponent,
        elements.uatNoTradeSymbol,
        elements.uatTimingPanel,
        elements.uatDrawdownCard,
        elements.uatRoutedOrdersTable,
      ].forEach((target) => {
        if (target) setEmpty(target, "Load docs/uat2_shadow_strategy_top20_observation_summary.json.");
      });
      renderUatRoutedOrders();
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
    renderUatRoutedOrders();
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
    renderUatCockpit();
    renderUatDashboard();
  }

  function classifyJson(payload) {
    if (Array.isArray(payload?.campaign_results)) return "review";
    if (Array.isArray(payload?.run_reports)) return "batch";
    if (Array.isArray(payload?.summary_rows) && payload?.report === "sv1_17_true_replay_experiment_summary") {
      return "experiment_summary";
    }
    if (Array.isArray(payload?.audit_records) && payload?.uat3_readiness_decision) return "uat2_shadow_summary";
    if (payload?.report === "uat3_4_sandbox_routing_pipeline_and_order_ledger") return "uat34_routed_orders_summary";
    if (payload?.report === "uat4_2_live_market_dashboard_and_paper_equity_monitor") return "uat42_live_monitor_summary";
    if (payload?.report === "pt0_tradingview_charts_and_top20_paper_sandbox_runtime") return "pt0_runtime_summary";
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
    await loadDefaultUat34Summaries();
    await loadDefaultUat42Summaries();
    await loadDefaultPt0Summaries();

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
        if (type === "uat34_routed_orders_summary") state.uat34Summary = payload;
        if (type === "uat42_live_monitor_summary") state.uat42Summary = payload;
        if (type === "pt0_runtime_summary") state.pt0Summary = payload;
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

  async function loadDefaultUat34Summaries() {
    for (const path of DEFAULT_UAT34_SUMMARY_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (classifyJson(payload) === "uat34_routed_orders_summary") {
          state.uat34Summary = payload;
        }
      } catch (error) {
        console.warn(`Could not load ${path}`, error);
      }
    }
  }

  async function loadDefaultUat42Summaries() {
    for (const path of DEFAULT_UAT42_SUMMARY_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (classifyJson(payload) === "uat42_live_monitor_summary") {
          state.uat42Summary = payload;
        }
      } catch (error) {
        console.warn(`Could not load ${path}`, error);
      }
    }
  }

  async function loadDefaultPt0Summaries() {
    for (const path of DEFAULT_PT0_SUMMARY_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (classifyJson(payload) === "pt0_runtime_summary") {
          state.pt0Summary = payload;
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
  startLiveMarketPolling();
})();
