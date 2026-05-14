(function () {
  "use strict";

  const SV202_CANONICAL_TIMESTAMP = "20260512T064916Z";
  const SV202_CANONICAL_SYMBOLS = ["AVAX", "BNB", "BTC", "DOGE", "ETH", "HYPE", "SOL", "SUI", "XRP"];
  const SV202_CANONICAL_TIMEFRAMES = ["15m", "1h", "4h", "1d"];
  const SV202_CANONICAL_BATCH_FILES = SV202_CANONICAL_TIMEFRAMES.flatMap((timeframe) =>
    SV202_CANONICAL_SYMBOLS.map(
      (symbol) =>
        `../../reports/strategy_validation/money_flow_sv2_0_2_hyperliquid_public_${symbol.toLowerCase()}_${timeframe}_canonical_db_imported/${SV202_CANONICAL_TIMESTAMP}/batch_report.json`,
    ),
  );
  const SV202_DASHBOARD_CHART_FILES = SV202_CANONICAL_TIMEFRAMES.flatMap((timeframe) =>
    SV202_CANONICAL_SYMBOLS.map(
      (symbol) =>
        `../../reports/strategy_validation/sv2_0_2_dashboard_chart_data/${SV202_CANONICAL_TIMESTAMP}/hyperliquid_public_${symbol.toLowerCase()}_${timeframe}_chart.json`,
    ),
  );
  const MF_ORIG_EV2_TIMESTAMP = "20260513T002746Z";
  const MF_ORIG_FULL_EQUITY_STRATEGY_IDS = new Set([
    "mf_orig_stage_filter_only_full_equity",
    "mf_orig_stage2_pullback_reclaim_full_equity",
    "mf_orig_1d_stage2_5_20_crossover_full_equity",
    "mf_orig_1d_stage2_breakout_resistance_full_equity",
  ]);
  const HIDDEN_DASHBOARD_STRATEGY_IDS = new Set([
    "baseline_current_money_flow_rules",
  ]);
  const MF_ORIG_EV2_DASHBOARD_CHART_FILES = SV202_CANONICAL_TIMEFRAMES.flatMap((timeframe) =>
    SV202_CANONICAL_SYMBOLS.map(
      (symbol) =>
        `../../reports/strategy_validation/mf_orig_ev2_dashboard_chart_data/${MF_ORIG_EV2_TIMESTAMP}/hyperliquid_public_${symbol.toLowerCase()}_${timeframe}_mf_orig_ev2_chart.json`,
    ),
  );

  const DEFAULT_FILES = [
    ...SV202_CANONICAL_BATCH_FILES,
  ];
  const EVIDENCE_BATCH_REPORTS_STRATEGY_ID = "canonical_batch_reports";
  const STRATEGY_COMPARISON_ALL_STRATEGIES_ID = "all_strategy_comparison_strategies";
  const DASHBOARD_THEME_STORAGE_KEY = "money-flow-dashboard-theme";
  const DASHBOARD_THEMES = new Set(["dark", "light", "red-zone"]);
  const EVIDENCE_ALL_REPLAY_STRATEGIES_ID = "all_replay_strategies";
  const EVIDENCE_PRIORITY_REPLAY_STRATEGY_IDS = new Set([
    "avoid_low_rolling_range_20",
    "avoid_low_rolling_range_50",
  ]);

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

  const DEFAULT_PT002_REPLAY_SUMMARY_FILES = [
    "../../docs/pt0_0_3_historical_strategy_replay_summary.json",
    "../../docs/pt0_0_2_historical_strategy_replay_summary.json",
  ];

  const DEFAULT_SV20_SUMMARY_FILES = [
    "../../docs/sv2_0_historical_data_refresh_summary.json",
  ];

  const DEFAULT_SOR_EV_SUMMARY_FILES = [
    "../../docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants_summary.json",
    "../../docs/sor_ev2_true_forward_stop_and_rejected_signal_replay_summary.json",
    "../../docs/sor_ev3_avoid_sideways_low_volatility_summary.json",
  ];

  const DEFAULT_MF_ORIG_SUMMARY_FILES = [
    "../../docs/mf_orig_ev1_original_money_flow_reconstruction_summary.json",
    "../../docs/mf_orig_ev2_multitimeframe_evidence_summary.json",
  ];

  const DEFAULT_EV_AUDIT_SUMMARY_FILES = [
    "../../docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review_summary.json",
  ];

  const DEFAULT_PT_RT1_SUMMARY_FILES = [
    "../../reports/paper_runtime/pt_rt1_1b_smoke/summary.json",
    "../../reports/paper_runtime/pt_rt1_1b_24h_dry_run/summary.json",
    "../../docs/pt_rt1_1b_hyperliquid_live_market_data_and_runtime_readiness_summary.json",
    "../../docs/pt_rt1_real_time_paper_observation_and_testnet_plumbing_summary.json",
  ];

  const HYPERLIQUID_TESTNET_PUBLIC_INFO_URL = "https://api.hyperliquid-testnet.xyz/info";
  const TRADINGVIEW_LIGHTWEIGHT_CHARTS_VERSION = "5.2.0";
  const CHART_BACKGROUND_COLOR = "#10171b";
  const CHART_TEXT_COLOR = "#d8e1e5";
  const CANDLE_UP_COLOR = "#f5f7f2";
  const CANDLE_DOWN_COLOR = "#050607";
  const CANDLE_BORDER_COLOR = "#e7ece8";
  const CANDLE_WICK_COLOR = "#e7ece8";
  const FOUNDER_REVIEW_MARKER_COLOR = "#f5f7f2";
  const SOR_EV3_FOUNDER_LABEL_HELP = {
    candidate_for_more_evidence: "Passes strict evidence gates; still evidence-only.",
    promising_high_pnl_control_preserved_trade_count_risk: "Large aggregate PnL improvement and control pockets preserved, but trade-count reduction is large enough to require narrower review.",
    promising_high_pnl_control_preserved: "Large aggregate PnL improvement with control pockets preserved; still evidence-only.",
    promising_chop_filter_control_risk: "Directionally useful chop/sideways filter, but control-pocket or drawdown gates failed.",
    promising_extension_filter_overfit_risk: "Extension filter improved aggregate PnL, but overfit/control-pocket risk remains.",
    promising_diagnostic_only: "Interesting diagnostic overlay, but not true-forward candidate evidence.",
    promising_high_pnl_control_risk: "Large aggregate PnL improvement, but drawdown/control-pocket preservation failed.",
    promising_control_pocket_risk: "Directionally interesting aggregate improvement, but not clean enough for promotion.",
    mixed_positive_pnl_control_damage: "Positive aggregate PnL with too much damage to strong baseline pockets.",
    mixed_positive_pnl_drawdown_risk: "Positive aggregate PnL, but worst drawdown worsened.",
    mixed_small_pnl_drawdown_risk: "Small positive PnL with worse drawdown; not enough for promotion.",
    not_promoted_no_op: "No material behavior change versus baseline.",
    not_promoted_insufficient_data: "Evidence bundle does not contain enough data for a useful conclusion.",
    not_promoted_low_impact: "Too little aggregate impact for more evidence.",
    deferred_needs_true_forward_replay: "Deferred until true-forward replay data exists.",
    rejected_negative_aggregate: "Aggregate PnL was worse than baseline.",
  };
  const FOUNDER_LABEL_RANK = {
    candidate_for_more_evidence: 0,
    promising_high_pnl_control_preserved: 10,
    promising_high_pnl_control_preserved_trade_count_risk: 11,
    promising_extension_filter_overfit_risk: 20,
    promising_chop_filter_control_risk: 21,
    promising_high_pnl_control_risk: 22,
    promising_control_pocket_risk: 23,
    promising_diagnostic_only: 24,
    mixed_positive_pnl_control_damage: 40,
    mixed_positive_pnl_drawdown_risk: 41,
    mixed_small_pnl_drawdown_risk: 42,
    not_promoted_low_impact: 60,
    not_promoted_no_op: 61,
    not_promoted_insufficient_data: 62,
    deferred_needs_true_forward_replay: 80,
    rejected_negative_aggregate: 100,
  };
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
    selectedComponent: "sleeve_1d",
    evidenceReplayStrategyId: EVIDENCE_BATCH_REPORTS_STRATEGY_ID,
    evidenceReplayFillAssumption: "next_candle_open",
    evidenceDateStart: "",
    evidenceDateEnd: "",
    theme: initialDashboardTheme(),
    strategyComparison: {
      leftStrategyId: "money_flow_v1_2_canonical",
      rightStrategyId: "",
      symbol: "ETH",
      timeframe: "1h",
      fillAssumption: "next_candle_open",
    },
    runLedgerSort: {
      key: "",
      direction: "desc",
    },
    activeView: "historical-replay",
    experimentMode: "sv115_overlays",
    sv117FullSuiteRows: null,
    uat2Summary: null,
    uat34Summary: null,
    uat42Summary: null,
    pt0Summary: null,
    pt002HistoricalReplay: null,
    sv202HistoricalReplay: null,
    loadedHistoricalChartDataPaths: new Set(),
    loadingHistoricalChartDataPaths: new Set(),
    sv20Summary: null,
    sorEv1Summary: null,
    sorEv2Summary: null,
    sorEv3Summary: null,
    mfOrigSummary: null,
    evAuditSummary: null,
    ptRt1Summary: null,
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
    historicalReplayChart: {
      chart: null,
      mount: null,
      candleSeries: null,
      volumeSeries: null,
      indicatorSeries: {},
      markerHandle: null,
      markerTradeIds: new Map(),
      key: null,
      ready: false,
      pendingResizeFrame: null,
      resizeObserver: null,
      lastVisibleRange: null,
    },
    evidenceLabOverlay: {
      symbol: "ETH",
      timeframe: "1h",
      fillAssumption: "next_candle_open",
      variantId: "fixed_stop_loss_pct_2",
      overlayMode: "both",
      showLargeLossTrades: true,
      showStopExits: true,
      showLateExtensionEntries: false,
      showAdverseCandles: false,
      showMaBreaks: false,
      hideBaselineMarkers: false,
      selectedWorstTradeId: null,
    },
    evidenceLabOverlayChart: {
      chart: null,
      mount: null,
      candleSeries: null,
      volumeSeries: null,
      indicatorSeries: {},
      markerHandle: null,
      markerIds: new Map(),
      key: null,
      ready: false,
      pendingResizeFrame: null,
      resizeObserver: null,
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
    paperObservation: {
      symbol: "ETH",
      timeframe: "1h",
      laneId: "money_flow_v1_2_baseline",
      dateStart: "",
      dateEnd: "",
    },
    historicalReplay: {
      strategyId: "money_flow_v1_2_canonical",
      symbol: "ETH",
      timeframe: "4h",
      fillAssumption: "next_candle_open",
      selectedTradeId: null,
      showArrowDescriptions: false,
      dateStart: "",
      dateEnd: "",
    },
  };

  const elements = {
    viewTabs: Array.from(document.querySelectorAll("[data-view]")),
    viewPanels: Array.from(document.querySelectorAll("[data-view-panel]")),
    status: document.querySelector("#review-status"),
    sourceLabel: document.querySelector("#data-source-label"),
    sourceDetail: document.querySelector("#data-source-detail"),
    fileInput: document.querySelector("#json-file-input"),
    themeSelector: document.querySelector("#dashboard-theme-selector"),
    metricPacks: document.querySelector("#metric-packs"),
    metricPacksDetail: document.querySelector("#metric-packs-detail"),
    metricRuns: document.querySelector("#metric-runs"),
    metricRunsDetail: document.querySelector("#metric-runs-detail"),
    metricCoverage: document.querySelector("#metric-coverage"),
    metricBoundary: document.querySelector("#metric-boundary"),
    componentFilter: document.querySelector("#component-filter"),
    evidenceReplayStrategyFilter: document.querySelector("#evidence-replay-strategy-filter"),
    evidenceReplayFillFilter: document.querySelector("#evidence-replay-fill-filter"),
    evidenceDateStart: document.querySelector("#evidence-date-start"),
    evidenceDateEnd: document.querySelector("#evidence-date-end"),
    evidenceDateClear: document.querySelector("#evidence-date-clear"),
    strategyComparisonLeftStrategy: document.querySelector("#strategy-comparison-left-strategy"),
    strategyComparisonRightStrategy: document.querySelector("#strategy-comparison-right-strategy"),
    strategyComparisonSymbol: document.querySelector("#strategy-comparison-symbol"),
    strategyComparisonTimeframe: document.querySelector("#strategy-comparison-timeframe"),
    strategyComparisonFill: document.querySelector("#strategy-comparison-fill"),
    strategyComparisonVerdict: document.querySelector("#strategy-comparison-verdict"),
    strategyComparisonChart: document.querySelector("#strategy-comparison-chart"),
    strategyComparisonMetrics: document.querySelector("#strategy-comparison-metrics"),
    boundaryFlags: document.querySelector("#boundary-flags"),
    componentCards: document.querySelector("#component-cards"),
    detailSubtitle: document.querySelector("#detail-subtitle"),
    timingChart: document.querySelector("#timing-chart"),
    symbolChart: document.querySelector("#symbol-chart"),
    regimeTable: document.querySelector("#regime-table"),
    checklist: document.querySelector("#review-checklist"),
    runTable: document.querySelector("#run-table"),
    runTableSubtitle: document.querySelector("#run-table-subtitle"),
    runLedgerTotals: document.querySelector("#run-ledger-totals"),
    evidenceLabSummaryCards: document.querySelector("#evidence-lab-summary-cards"),
    evidenceLabFounderCandidate: document.querySelector("#evidence-lab-founder-candidate"),
    evidenceLabMfOrig: document.querySelector("#evidence-lab-mf-orig"),
    evidenceLabVariantMatrix: document.querySelector("#evidence-lab-variant-matrix"),
    evidenceLabControlPockets: document.querySelector("#evidence-lab-control-pockets"),
    evidenceLabWorstTrades: document.querySelector("#evidence-lab-worst-trades"),
    evidenceLabLateEntry: document.querySelector("#evidence-lab-late-entry"),
    evidenceLabAdverseCandles: document.querySelector("#evidence-lab-adverse-candles"),
    evidenceLabRsiMacd: document.querySelector("#evidence-lab-rsi-macd"),
    evidenceLabChartOverlay: document.querySelector("#evidence-lab-chart-overlay"),
    evidenceLabOverlaySymbol: document.querySelector("#evidence-lab-overlay-symbol"),
    evidenceLabOverlayTimeframe: document.querySelector("#evidence-lab-overlay-timeframe"),
    evidenceLabOverlayFill: document.querySelector("#evidence-lab-overlay-fill"),
    evidenceLabOverlayVariant: document.querySelector("#evidence-lab-overlay-variant"),
    evidenceLabOverlayMode: document.querySelector("#evidence-lab-overlay-mode"),
    evidenceLabToggleLargeLoss: document.querySelector("#evidence-lab-toggle-large-loss"),
    evidenceLabToggleStopExits: document.querySelector("#evidence-lab-toggle-stop-exits"),
    evidenceLabToggleLateExtension: document.querySelector("#evidence-lab-toggle-late-extension"),
    evidenceLabToggleAdverseCandles: document.querySelector("#evidence-lab-toggle-adverse-candles"),
    evidenceLabToggleMaBreaks: document.querySelector("#evidence-lab-toggle-ma-breaks"),
    evidenceLabToggleHideBaselineEntries: document.querySelector("#evidence-lab-toggle-hide-baseline-entries"),
    evidenceLabOverlayMethodology: document.querySelector("#evidence-lab-overlay-methodology"),
    evidenceLabOverlayInspector: document.querySelector("#evidence-lab-overlay-inspector"),
    evidenceLabClearFocus: document.querySelector("#evidence-lab-clear-focus"),
    evidenceLabWorstFocusTable: document.querySelector("#evidence-lab-worst-focus-table"),
    evidenceLabControlPocketView: document.querySelector("#evidence-lab-control-pocket-view"),
    evidenceLabOverlayUnavailable: document.querySelector("#evidence-lab-overlay-unavailable"),
    auditReviewVerdictCards: document.querySelector("#audit-review-verdict-cards"),
    auditReviewScorecard: document.querySelector("#audit-review-scorecard"),
    auditReviewPaperReadiness: document.querySelector("#audit-review-paper-readiness"),
    auditReviewTopHypotheses: document.querySelector("#audit-review-top-hypotheses"),
    auditReviewWorstHypotheses: document.querySelector("#audit-review-worst-hypotheses"),
    auditReviewWinningTrades: document.querySelector("#audit-review-winning-trades"),
    auditReviewLosingTrades: document.querySelector("#audit-review-losing-trades"),
    auditReviewLosingStreaks: document.querySelector("#audit-review-losing-streaks"),
    auditReviewIssues: document.querySelector("#audit-review-issues"),
    auditReviewDataIntegrity: document.querySelector("#audit-review-data-integrity"),
    auditReviewInventory: document.querySelector("#audit-review-inventory"),
    paperObservationSummaryCards: document.querySelector("#paper-observation-summary-cards"),
    paperObservationSymbolFilter: document.querySelector("#paper-observation-symbol-filter"),
    paperObservationTimeframeFilter: document.querySelector("#paper-observation-timeframe-filter"),
    paperObservationLaneFilter: document.querySelector("#paper-observation-lane-filter"),
    paperObservationDateStart: document.querySelector("#paper-observation-date-start"),
    paperObservationDateEnd: document.querySelector("#paper-observation-date-end"),
    paperObservationDateClear: document.querySelector("#paper-observation-date-clear"),
    paperObservationConnectionStatus: document.querySelector("#paper-observation-connection-status"),
    paperObservationScannerTable: document.querySelector("#paper-observation-scanner-table"),
    paperObservationHealthTable: document.querySelector("#paper-observation-health-table"),
    paperObservationLaneTable: document.querySelector("#paper-observation-lane-table"),
    paperObservationLaneDetail: document.querySelector("#paper-observation-lane-detail"),
    paperObservationWildcardDiagnostics: document.querySelector("#paper-observation-wildcard-diagnostics"),
    paperObservationLiveChart: document.querySelector("#paper-observation-live-chart"),
    paperObservationProbeStatus: document.querySelector("#paper-observation-probe-status"),
    paperObservationOpenPositions: document.querySelector("#paper-observation-open-positions"),
    paperObservationClosedTrades: document.querySelector("#paper-observation-closed-trades"),
    paperObservationRiskTable: document.querySelector("#paper-observation-risk-table"),
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
    historicalReplaySymbolFilter: document.querySelector("#historical-replay-symbol-filter"),
    historicalReplayTimeframeFilter: document.querySelector("#historical-replay-timeframe-filter"),
    historicalReplayFillFilter: document.querySelector("#historical-replay-fill-filter"),
    historicalReplayStrategyFilter: document.querySelector("#historical-replay-strategy-filter"),
    historicalReplayDateStart: document.querySelector("#historical-replay-date-start"),
    historicalReplayDateEnd: document.querySelector("#historical-replay-date-end"),
    historicalReplayDateClear: document.querySelector("#historical-replay-date-clear"),
    historicalReplayArrowDescriptionsToggle: document.querySelector("#historical-replay-arrow-descriptions-toggle"),
    historicalReplaySourceStatus: document.querySelector("#historical-replay-source-status"),
    historicalReplayDataHorizonPanel: document.querySelector("#historical-data-horizon-panel"),
    historicalReplayChart: document.querySelector("#historical-replay-chart"),
    historicalReplayEquityPanel: document.querySelector("#historical-replay-equity-panel"),
    historicalTradeInspector: document.querySelector("#historical-trade-inspector"),
    historicalReplayTradesTable: document.querySelector("#historical-replay-trades-table"),
    historicalComparisonTable: document.querySelector("#historical-comparison-table"),
    historicalSandboxLedger: document.querySelector("#historical-sandbox-ledger"),
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

  function timestampMs(value) {
    if (value === null || value === undefined || value === "") return NaN;
    if (Number.isFinite(value)) return Number(value) * 1000;
    const parsed = Date.parse(String(value));
    return Number.isFinite(parsed) ? parsed : NaN;
  }

  function dateRange(startDate, endDate) {
    const start = startDate ? Date.parse(`${startDate}T00:00:00Z`) : NaN;
    const end = endDate ? Date.parse(`${endDate}T23:59:59.999Z`) : NaN;
    return {
      active: Boolean(startDate || endDate),
      start: Number.isFinite(start) ? start : null,
      end: Number.isFinite(end) ? end : null,
      label: startDate && endDate
        ? `${startDate} to ${endDate}`
        : startDate
          ? `from ${startDate}`
          : endDate
            ? `through ${endDate}`
            : "all dates",
    };
  }

  function inDateRange(value, range) {
    if (!range?.active) return true;
    const parsed = timestampMs(value);
    if (!Number.isFinite(parsed)) return false;
    if (range.start !== null && parsed < range.start) return false;
    if (range.end !== null && parsed > range.end) return false;
    return true;
  }

  function evidenceDateRange() {
    return dateRange(state.evidenceDateStart, state.evidenceDateEnd);
  }

  function historicalDateRange() {
    return dateRange(state.historicalReplay.dateStart, state.historicalReplay.dateEnd);
  }

  function tradeExitTimestamp(trade) {
    return trade?.exit_fill_time || trade?.exit_time || trade?.exit_signal_time || trade?.entry_fill_time || trade?.entry_time;
  }

  function tradeEntryTimestamp(trade) {
    return trade?.entry_fill_time || trade?.entry_time || trade?.entry_signal_time;
  }

  function tradeInDateRange(trade, range) {
    if (!range?.active) return true;
    if (range.start !== null && !inDateRange(tradeEntryTimestamp(trade), { active: true, start: range.start, end: null })) {
      return false;
    }
    if (range.end !== null && !inDateRange(tradeExitTimestamp(trade), { active: true, start: null, end: range.end })) {
      return false;
    }
    if (range.start === null && range.end !== null) {
      return inDateRange(tradeExitTimestamp(trade), range);
    }
    return true;
  }

  function flattenReportTrades(report) {
    return (report?.component_reports || []).flatMap((component) => component.trades || []);
  }

  function rebaseTrades(trades, startingEquity = 10000) {
    let currentEquity = startingEquity;
    return trades.map((trade) => {
      const originalEquity = decimal(trade.equity_before_trade ?? trade.equity_before_entry, NaN);
      const equityRatio = Number.isFinite(originalEquity) && originalEquity !== 0
        ? currentEquity / originalEquity
        : 1;
      const tradeReturn = decimal(trade.return_pct, NaN);
      const netPnl = Number.isFinite(tradeReturn)
        ? currentEquity * tradeReturn
        : decimal(trade.net_pnl) * equityRatio;
      const rebased = {
        ...trade,
        original_equity_before_trade: trade.equity_before_trade ?? trade.equity_before_entry,
        original_equity_after_trade: trade.equity_after_trade ?? trade.equity_after_exit,
        original_net_pnl: trade.net_pnl,
        equity_before_entry: currentEquity,
        equity_before_trade: currentEquity,
        net_pnl: netPnl,
        gross_pnl: decimal(trade.gross_pnl) * equityRatio,
        fees: decimal(trade.fees) * equityRatio,
        slippage_cost: decimal(trade.slippage_cost ?? trade.total_slippage_cost) * equityRatio,
        entry_notional: decimal(trade.entry_notional) * equityRatio,
        exit_notional: decimal(trade.exit_notional) * equityRatio,
        drawdown_after_trade: decimal(trade.drawdown_after_trade ?? trade.max_adverse_excursion) * equityRatio,
        rebased_starting_equity: startingEquity,
        rebased_from_date_filter: true,
      };
      currentEquity += netPnl;
      rebased.equity_after_exit = currentEquity;
      rebased.equity_after_trade = currentEquity;
      return rebased;
    });
  }

  function maxDrawdownFromEquityValues(values) {
    let peak = null;
    let drawdown = 0;
    values.forEach((value) => {
      const parsed = decimal(value, NaN);
      if (!Number.isFinite(parsed)) return;
      peak = peak === null ? parsed : Math.max(peak, parsed);
      drawdown = Math.max(drawdown, peak - parsed);
    });
    return drawdown;
  }

  function filteredTradeMetrics(trades, fallbackStartingEquity = 10000) {
    const startingEquity = trades.length
      ? decimal(trades[0].equity_before_trade ?? trades[0].equity_before_entry, fallbackStartingEquity)
      : fallbackStartingEquity;
    const endingEquity = trades.length
      ? decimal(trades.at(-1).equity_after_trade ?? trades.at(-1).equity_after_exit, startingEquity)
      : startingEquity;
    const netPnl = trades.reduce((sum, trade) => sum + decimal(trade.net_pnl), 0);
    const grossPnl = trades.reduce((sum, trade) => sum + decimal(trade.gross_pnl), 0);
    const fees = trades.reduce((sum, trade) => sum + decimal(trade.fees), 0);
    const slippage = trades.reduce((sum, trade) => sum + decimal(trade.slippage_cost ?? trade.total_slippage_cost), 0);
    const wins = trades.filter((trade) => decimal(trade.net_pnl) > 0).length;
    const equityValues = [startingEquity, ...trades.map((trade) => trade.equity_after_trade ?? trade.equity_after_exit)];
    const maxDrawdown = maxDrawdownFromEquityValues(equityValues);
    return {
      startingEquity,
      endingEquity,
      netPnl,
      grossPnl,
      fees,
      slippage,
      tradeCount: trades.length,
      wins,
      winRate: trades.length ? wins / trades.length : null,
      maxDrawdown,
      maxDrawdownPct: startingEquity > 0 ? maxDrawdown / startingEquity : null,
    };
  }

  function batchComponent(batch) {
    const matrixComponent = batch.assumptions_matrix?.components?.[0];
    const comparisonComponent = batch.comparison_summary?.component_comparison?.[0]?.component_keys;
    return matrixComponent || comparisonComponent || batch.batch_name || "unknown";
  }

  function addAggregate(group, key, label, trade) {
    if (!key) return;
    if (!group.has(key)) {
      group.set(key, {
        label,
        total_net_pnl: 0,
        total_fees: 0,
        total_slippage_cost: 0,
        total_trades: 0,
        winning_trades: 0,
      });
    }
    const row = group.get(key);
    row.total_net_pnl += decimal(trade.net_pnl);
    row.total_fees += decimal(trade.fees);
    row.total_slippage_cost += decimal(trade.slippage_cost);
    row.total_trades += 1;
    if (decimal(trade.net_pnl) > 0) row.winning_trades += 1;
  }

  function aggregateRows(group, labelKey) {
    return Array.from(group.values()).map((row) => ({
      ...row,
      [labelKey]: row.label,
      average_net_pnl: row.total_trades ? row.total_net_pnl / row.total_trades : 0,
      win_rate: row.total_trades ? row.winning_trades / row.total_trades : null,
    }));
  }

  function dateFilteredBatchSummary(batch, baseSummary) {
    const range = evidenceDateRange();
    const runs = batch.run_reports || [];
    const component = baseSummary.component;
    const fillGroups = new Map();
    const symbolGroups = new Map();
    const regimeGroups = new Map();
    const filteredRunSummaries = [];
    let allTrades = [];

    runs.filter((run) => run.status === "completed").forEach((run, index) => {
      const report = run.report || {};
      const rawTrades = flattenReportTrades(report).filter((trade) => tradeInDateRange(trade, range));
      if (!rawTrades.length) return;
      const trades = rebaseTrades(rawTrades, 10000);
      allTrades = allTrades.concat(trades);
      const metrics = filteredTradeMetrics(trades, 10000);
      const fillTiming = report.assumptions?.fill_timing || trades[0]?.fill_timing || "unknown";
      const symbol = report.symbol || trades[0]?.symbol || baseSummary.symbol;
      trades.forEach((trade) => {
        addAggregate(fillGroups, fillTiming, fillTiming, trade);
        addAggregate(symbolGroups, trade.symbol || symbol, trade.symbol || symbol, trade);
        addAggregate(regimeGroups, `market:${trade.entry_market_regime || "unknown"}`, trade.entry_market_regime || "unknown", trade);
        addAggregate(regimeGroups, `volatility:${trade.entry_volatility_regime || "unknown"}`, trade.entry_volatility_regime || "unknown", trade);
      });
      filteredRunSummaries.push({
        run_id: run.run_id || report.report_id || `filtered-run-${index}`,
        status: "completed",
        symbol,
        fill_timing: fillTiming,
        fee_bps: report.assumptions?.fee_bps ?? trades[0]?.fee_bps ?? "n/a",
        slippage_bps: report.assumptions?.slippage_bps ?? trades[0]?.slippage_bps ?? "n/a",
        capital_sizing_mode: report.aggregate_metrics?.capital_sizing_mode || trades[0]?.capital_sizing_mode,
        start_at: state.evidenceDateStart || report.start_at,
        end_at: state.evidenceDateEnd || report.end_at,
        metrics: {
          capital_sizing_mode: report.aggregate_metrics?.capital_sizing_mode || trades[0]?.capital_sizing_mode,
          ending_equity: metrics.endingEquity,
          net_pnl: metrics.netPnl,
          win_rate: metrics.winRate,
          number_of_trades: metrics.tradeCount,
          mark_to_market_max_drawdown: metrics.maxDrawdown,
        },
      });
    });

    const totalNetPnl = filteredRunSummaries.reduce((sum, row) => sum + decimal(row.metrics?.net_pnl), 0);
    const totalFees = allTrades.reduce((sum, trade) => sum + decimal(trade.fees), 0);
    const totalSlippage = allTrades.reduce((sum, trade) => sum + decimal(trade.slippage_cost), 0);
    const largestDrawdown = Math.max(...filteredRunSummaries.map((row) => decimal(row.metrics?.mark_to_market_max_drawdown)), 0);
    const regimes = aggregateRows(regimeGroups, "regime_label").map((row) => ({
      ...row,
      regime_type: String(row.label || "").includes("volatility") ? "volatility" : "market",
      trade_count: row.total_trades,
    }));
    return {
      ...baseSummary,
      window: `fresh 10k slice ${range.label}`,
      completedRunCount: filteredRunSummaries.length,
      blockedRunCount: 0,
      totalNetPnl,
      averageNetPnl: filteredRunSummaries.length ? totalNetPnl / filteredRunSummaries.length : 0,
      totalTrades: allTrades.length,
      totalFees,
      totalSlippage,
      largestDrawdown,
      fillTiming: aggregateRows(fillGroups, "fill_timing"),
      symbols: aggregateRows(symbolGroups, "symbol"),
      regimes,
      runSummaries: filteredRunSummaries,
      bestNetPnl: filteredRunSummaries.slice().sort((a, b) => decimal(b.metrics?.net_pnl) - decimal(a.metrics?.net_pnl))[0] || null,
      worstNetPnl: filteredRunSummaries.slice().sort((a, b) => decimal(a.metrics?.net_pnl) - decimal(b.metrics?.net_pnl))[0] || null,
    };
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
    const symbol = batch.assumptions_matrix?.symbols?.[0] || firstRun?.symbol || "unknown";
    const totalExpected = coverage.reduce(
      (sum, row) => sum + decimal(row.total_expected_candle_count),
      0,
    );
    const totalActual = coverage.reduce((sum, row) => sum + decimal(row.total_actual_candle_count), 0);

    const summary = {
      batch,
      component,
      symbol,
      label: `${symbol} ${cleanComponentName(component)}`,
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
    return evidenceDateRange().active ? dateFilteredBatchSummary(batch, summary) : summary;
  }

  function allSummaries() {
    return state.batches.map(batchSummary).sort((a, b) =>
      timeframeSortRank(a.timeframe) - timeframeSortRank(b.timeframe) ||
      a.component.localeCompare(b.component),
    );
  }

  function timeframeSortRank(timeframe) {
    const index = SV202_CANONICAL_TIMEFRAMES.indexOf(canonicalTimeframe(timeframe));
    return index >= 0 ? index : SV202_CANONICAL_TIMEFRAMES.length;
  }

  function initialDashboardTheme() {
    try {
      const stored = window.localStorage?.getItem(DASHBOARD_THEME_STORAGE_KEY);
      return DASHBOARD_THEMES.has(stored) ? stored : "red-zone";
    } catch (_error) {
      return "red-zone";
    }
  }

  function applyDashboardTheme(theme) {
    const safeTheme = DASHBOARD_THEMES.has(theme) ? theme : "red-zone";
    state.theme = safeTheme;
    document.documentElement.dataset.theme = safeTheme;
    if (elements.themeSelector) elements.themeSelector.value = safeTheme;
    try {
      window.localStorage?.setItem(DASHBOARD_THEME_STORAGE_KEY, safeTheme);
    } catch (_error) {
      // Theme persistence is optional; the visual switch should still work.
    }
  }

  function dashboardCssVar(name, fallback) {
    const value = window.getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return value || fallback;
  }

  function dashboardChartColors() {
    return {
      background: dashboardCssVar("--color-chart-surface", CHART_BACKGROUND_COLOR),
      text: dashboardCssVar("--color-chart-text", CHART_TEXT_COLOR),
      grid: dashboardCssVar("--color-chart-grid", "rgba(133, 156, 171, 0.08)"),
      border: dashboardCssVar("--color-chart-border", "rgba(133, 156, 171, 0.18)"),
      candleUp: dashboardCssVar("--color-chart-candle-up", CANDLE_UP_COLOR),
      candleDown: dashboardCssVar("--color-chart-candle-down", CANDLE_DOWN_COLOR),
      candleBorder: dashboardCssVar("--color-chart-candle-border", CANDLE_BORDER_COLOR),
      candleWick: dashboardCssVar("--color-chart-candle-wick", CANDLE_WICK_COLOR),
    };
  }

  function isMfOrigStrategyId(strategyId) {
    return String(strategyId || "").startsWith("mf_orig_");
  }

  function isVisibleMfOrigStrategyId(strategyId) {
    return !isMfOrigStrategyId(strategyId) || MF_ORIG_FULL_EQUITY_STRATEGY_IDS.has(String(strategyId));
  }

  function isVisibleDashboardStrategyRow(row) {
    const strategyId = row?.strategy_id || row?.hypothesis_id || row?.id;
    return !HIDDEN_DASHBOARD_STRATEGY_IDS.has(String(strategyId || "")) && isVisibleMfOrigStrategyId(strategyId);
  }

  function dashboardStrategyLabel(label, strategyId = "") {
    const rawLabel = String(label || "").trim();
    const rawId = String(strategyId || "").trim();
    if (rawLabel === "OG replay / strategy" || rawId === "baseline_current_money_flow_rules") return "Legacy replay";
    if (rawLabel === "Money Flow v1.2 canonical" || rawLabel === "SV2.0.2 canonical Money Flow v1.2") return "Money Flow v1.2";
    return rawLabel || rawId || "Money Flow strategy";
  }

  function sv202ReplayStrategies() {
    const replays = Array.isArray(state.sv202HistoricalReplay?.replays)
      ? state.sv202HistoricalReplay.replays
      : [];
    return Array.from(
      new Map(
        replays
          .map((replay) => [
            replay.strategy_id || "money_flow_v1_2_canonical",
            {
              value: replay.strategy_id || "money_flow_v1_2_canonical",
              label: dashboardStrategyLabel(replay.strategy_label, replay.strategy_id || "money_flow_v1_2_canonical"),
            },
          ])
          .filter(([value]) => value && !HIDDEN_DASHBOARD_STRATEGY_IDS.has(String(value))),
      ).values(),
    ).sort((left, right) => {
      if (left.value === "money_flow_v1_2_canonical") return -1;
      if (right.value === "money_flow_v1_2_canonical") return 1;
      const leftPriority = EVIDENCE_PRIORITY_REPLAY_STRATEGY_IDS.has(left.value) ? 0 : 1;
      const rightPriority = EVIDENCE_PRIORITY_REPLAY_STRATEGY_IDS.has(right.value) ? 0 : 1;
      return leftPriority - rightPriority || left.label.localeCompare(right.label);
    });
  }

  function evidenceReplayStrategyOptions() {
    return [
      {
        value: EVIDENCE_BATCH_REPORTS_STRATEGY_ID,
        label: "Canonical evidence packs / batch reports",
      },
      {
        value: EVIDENCE_ALL_REPLAY_STRATEGIES_ID,
        label: "All replay strategies",
      },
      ...sv202ReplayStrategies(),
    ];
  }

  function selectedEvidenceReplayStrategyLabel() {
    return (
      evidenceReplayStrategyOptions().find((option) => option.value === state.evidenceReplayStrategyId)?.label ||
      "Canonical evidence packs / batch reports"
    );
  }

  function activeSummaries() {
    const summaries = allSummaries();
    if (state.selectedComponent === "all") return summaries;
    return summaries.filter((summary) => summary.component === state.selectedComponent);
  }

  function defaultEvidenceComponent(summaries) {
    const components = Array.from(new Set((summaries || []).map((summary) => summary.component).filter(Boolean)));
    if (components.includes("sleeve_1d")) return "sleeve_1d";
    return components[0] || "all";
  }

  function setEmpty(target, message) {
    target.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
  }

  function setActiveView(view) {
    state.activeView = ["evidence", "evidence-lab", "audit-review", "paper-observation", "historical-replay", "uat-cockpit", "uat-shadow", "strategy"].includes(view)
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
    if (state.activeView === "historical-replay") {
      scheduleHistoricalReplayChartResize();
    }
    if (state.activeView === "evidence-lab") {
      scheduleEvidenceLabOverlayChartResize();
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

    if (elements.status) {
      elements.status.textContent = state.review?.paper_readiness_review_status || "";
    }
    elements.metricPacks.textContent = String(packCount);
    elements.metricPacksDetail.textContent =
      state.review?.blocked_campaign_count === 0 ? "generated" : "mixed";
    elements.metricRuns.textContent = String(totalRuns);
    elements.metricRunsDetail.textContent = evidenceDateRange().active
      ? `${summaries.length} packs / fresh 10k slice ${evidenceDateRange().label}`
      : `${summaries.length} component packs`;
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
    const components = [
      "all",
      ...Array.from(new Set(
        summaries
          .slice()
          .sort((a, b) => timeframeSortRank(a.timeframe) - timeframeSortRank(b.timeframe) || a.component.localeCompare(b.component))
          .map((summary) => summary.component),
      )),
    ];
    if (!components.includes(state.selectedComponent)) {
      state.selectedComponent = defaultEvidenceComponent(summaries);
    }
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

  function evidenceReplayFillOptions() {
    const fills = uniqueSorted(
      (state.sv202HistoricalReplay?.replays || [])
        .map(replayFillAssumption)
        .filter(Boolean),
    );
    return fills.length ? fills : ["next_candle_open", "next_candle_close"];
  }

  function renderEvidenceStrategyFilter() {
    if (!elements.evidenceReplayStrategyFilter) return;
    const options = evidenceReplayStrategyOptions();
    if (!options.some((option) => option.value === state.evidenceReplayStrategyId)) {
      state.evidenceReplayStrategyId = EVIDENCE_BATCH_REPORTS_STRATEGY_ID;
    }
    renderSelectWithoutAll(elements.evidenceReplayStrategyFilter, options, state.evidenceReplayStrategyId);
    elements.evidenceReplayStrategyFilter.onchange = () => {
      state.evidenceReplayStrategyId =
        elements.evidenceReplayStrategyFilter.value || EVIDENCE_BATCH_REPORTS_STRATEGY_ID;
      render();
    };
  }

  function renderEvidenceReplayFillFilter() {
    if (!elements.evidenceReplayFillFilter) return;
    const fills = evidenceReplayFillOptions();
    const options = [
      { value: "all", label: "All fill assumptions" },
      ...fills.map((fill) => ({ value: fill, label: fill })),
    ];
    if (state.evidenceReplayFillAssumption !== "all" && !fills.includes(state.evidenceReplayFillAssumption)) {
      state.evidenceReplayFillAssumption = fills.includes("next_candle_open") ? "next_candle_open" : fills[0] || "all";
    }
    renderSelectWithoutAll(elements.evidenceReplayFillFilter, options, state.evidenceReplayFillAssumption);
    elements.evidenceReplayFillFilter.onchange = () => {
      state.evidenceReplayFillAssumption = elements.evidenceReplayFillFilter.value || "all";
      render();
    };
  }

  function renderEvidenceDateControls() {
    if (elements.evidenceDateStart) {
      elements.evidenceDateStart.value = state.evidenceDateStart || "";
      elements.evidenceDateStart.onchange = () => {
        state.evidenceDateStart = elements.evidenceDateStart.value;
        render();
      };
    }
    if (elements.evidenceDateEnd) {
      elements.evidenceDateEnd.value = state.evidenceDateEnd || "";
      elements.evidenceDateEnd.onchange = () => {
        state.evidenceDateEnd = elements.evidenceDateEnd.value;
        render();
      };
    }
    if (elements.evidenceDateClear) {
      elements.evidenceDateClear.onclick = () => {
        state.evidenceDateStart = "";
        state.evidenceDateEnd = "";
        render();
      };
    }
  }

  function strategyComparisonReplays() {
    return (Array.isArray(state.sv202HistoricalReplay?.replays)
      ? state.sv202HistoricalReplay.replays
      : []).filter(isVisibleDashboardStrategyRow);
  }

  function strategyComparisonStrategyOptions(includeAll = false) {
    const options = Array.from(
      new Map(
        strategyComparisonReplays()
          .map((replay) => [
            replay.strategy_id || "money_flow_v1_2_canonical",
            {
              value: replay.strategy_id || "money_flow_v1_2_canonical",
              label: dashboardStrategyLabel(replay.strategy_label, replay.strategy_id || "money_flow_v1_2_canonical"),
            },
          ])
          .filter(([value]) => value && !HIDDEN_DASHBOARD_STRATEGY_IDS.has(String(value))),
      ).values(),
    ).sort((left, right) => {
      if (left.value === "money_flow_v1_2_canonical") return -1;
      if (right.value === "money_flow_v1_2_canonical") return 1;
      const leftPriority = EVIDENCE_PRIORITY_REPLAY_STRATEGY_IDS.has(left.value) ? 0 : 1;
      const rightPriority = EVIDENCE_PRIORITY_REPLAY_STRATEGY_IDS.has(right.value) ? 0 : 1;
      return leftPriority - rightPriority || left.label.localeCompare(right.label);
    });
    return includeAll
      ? [{ value: STRATEGY_COMPARISON_ALL_STRATEGIES_ID, label: "All strategies" }, ...options]
      : options;
  }

  function syncStrategyComparisonSelection() {
    const options = strategyComparisonStrategyOptions();
    const ids = options.map((option) => option.value);
    const selectableIds = [STRATEGY_COMPARISON_ALL_STRATEGIES_ID, ...ids];
    if (!ids.length) return;
    if (!selectableIds.includes(state.strategyComparison.leftStrategyId)) {
      state.strategyComparison.leftStrategyId = ids.includes("money_flow_v1_2_canonical") ? "money_flow_v1_2_canonical" : ids[0];
    }
    if (
      !selectableIds.includes(state.strategyComparison.rightStrategyId) ||
      (state.strategyComparison.rightStrategyId === state.strategyComparison.leftStrategyId &&
        state.strategyComparison.leftStrategyId !== STRATEGY_COMPARISON_ALL_STRATEGIES_ID)
    ) {
      state.strategyComparison.rightStrategyId = ids.find((id) => id !== state.strategyComparison.leftStrategyId) || ids[0];
    }
    const replays = strategyComparisonReplays();
    const symbols = uniqueSorted(replays.map((replay) => replay.symbol));
    const timeframes = uniqueSorted(replays.map((replay) => canonicalTimeframe(replay.timeframe)))
      .sort((left, right) => timeframeSortRank(left) - timeframeSortRank(right));
    const fills = uniqueSorted(replays.map(replayFillAssumption));
    if (!symbols.includes(state.strategyComparison.symbol)) state.strategyComparison.symbol = symbols.includes("ETH") ? "ETH" : symbols[0] || "ETH";
    if (!timeframes.includes(canonicalTimeframe(state.strategyComparison.timeframe))) state.strategyComparison.timeframe = timeframes.includes("1h") ? "1h" : timeframes[0] || "1h";
    if (!fills.includes(state.strategyComparison.fillAssumption)) state.strategyComparison.fillAssumption = fills.includes("next_candle_open") ? "next_candle_open" : fills[0] || "next_candle_open";
  }

  function strategyComparisonReplay(strategyId) {
    return strategyComparisonReplays().find(
      (replay) =>
        (replay.strategy_id || "money_flow_v1_2_canonical") === strategyId &&
        replay.symbol === state.strategyComparison.symbol &&
        sameTimeframe(replay.timeframe, state.strategyComparison.timeframe) &&
        replayFillAssumption(replay) === state.strategyComparison.fillAssumption,
    ) || null;
  }

  function strategyComparisonSideReplays(strategyId) {
    const scoped = strategyComparisonReplays().filter((replay) =>
      replay.symbol === state.strategyComparison.symbol &&
      sameTimeframe(replay.timeframe, state.strategyComparison.timeframe) &&
      replayFillAssumption(replay) === state.strategyComparison.fillAssumption,
    );
    if (strategyId === STRATEGY_COMPARISON_ALL_STRATEGIES_ID) {
      const optionOrder = new Map(strategyComparisonStrategyOptions().map((option, index) => [option.value, index]));
      return scoped.slice().sort((left, right) =>
        (optionOrder.get(left.strategy_id || "money_flow_v1_2_canonical") ?? 999) -
        (optionOrder.get(right.strategy_id || "money_flow_v1_2_canonical") ?? 999),
      );
    }
    const replay = scoped.find((row) => (row.strategy_id || "money_flow_v1_2_canonical") === strategyId);
    return replay ? [replay] : [];
  }

  function strategyComparisonScopedReplay(replay) {
    return replay ? filteredReplayByRange(replay, evidenceDateRange()) : null;
  }

  function strategyComparisonMetric(replay, key, fallback = 0) {
    return decimal(strategyComparisonScopedReplay(replay)?.summary?.[key] ?? replay?.summary?.[key], fallback);
  }

  function strategyComparisonEquitySeries(replay) {
    const scoped = strategyComparisonScopedReplay(replay) || replay || {};
    const rawCurve = Array.isArray(scoped.equity_curve) && scoped.equity_curve.length
      ? scoped.equity_curve
      : replay?.equity_curve || [];
    const trades = Array.isArray(scoped.trades) && scoped.trades.length ? scoped.trades : replay?.trades || [];
    const series = rawCurve
      .map((point, index) => {
        if (typeof point === "object" && point !== null) {
          const value = decimal(point.equity ?? point.equity_after_trade ?? point.equity_after_exit, NaN);
          const time = Date.parse(point.timestamp_utc || point.timestamp || point.time || point.date || point.exit_time || point.entry_time);
          return {
            value,
            time: Number.isFinite(time) ? time : null,
          };
        }
        const value = decimal(point, NaN);
        const trade = index === 0 ? trades[0] : trades[index - 1];
        const time = Date.parse(index === 0 ? tradeEntryTimestamp(trade) : tradeExitTimestamp(trade));
        return {
          value,
          time: Number.isFinite(time) ? time : null,
        };
      })
      .filter((point) => Number.isFinite(point.value));
    if (series.length >= 2) return series;
    const summary = scoped.summary || replay?.summary || {};
    const bounds = strategyComparisonReplayTimeBoundsFromTrades(trades);
    return [
      {
        value: decimal(summary.starting_equity, 10000),
        time: bounds.start,
      },
      {
        value: decimal(summary.ending_equity, summary.starting_equity ?? 10000),
        time: bounds.end,
      },
    ];
  }

  function comparisonWinner(left, right, mode = "higher") {
    if (!Number.isFinite(left) || !Number.isFinite(right)) return "none";
    if (left === right) return "tie";
    if (mode === "lower") return left < right ? "left" : "right";
    return left > right ? "left" : "right";
  }

  function strategyComparisonVerdict(leftReplay, rightReplay) {
    if (!leftReplay || !rightReplay) {
      return { label: "comparison unavailable", className: "unknown", details: "Select two strategies with matching currency, timeframe, and fill assumption." };
    }
    const leftNet = strategyComparisonMetric(leftReplay, "net_pnl");
    const rightNet = strategyComparisonMetric(rightReplay, "net_pnl");
    const leftDrawdown = strategyComparisonMetric(leftReplay, "max_drawdown");
    const rightDrawdown = strategyComparisonMetric(rightReplay, "max_drawdown");
    const pnlWinner = comparisonWinner(leftNet, rightNet, "higher");
    const drawdownWinner = comparisonWinner(leftDrawdown, rightDrawdown, "lower");
    if (pnlWinner === "tie" && drawdownWinner === "tie") {
      return { label: "same headline result", className: "same", details: "Net PnL and drawdown match for this selection." };
    }
    if (pnlWinner === drawdownWinner && ["left", "right"].includes(pnlWinner)) {
      const winner = pnlWinner === "left" ? "Strategy A" : "Strategy B";
      return { label: `${winner} looks better`, className: "good", details: "Higher net PnL and lower drawdown on this loaded replay row." };
    }
    const pnlText = pnlWinner === "left" ? "Strategy A has higher net PnL" : pnlWinner === "right" ? "Strategy B has higher net PnL" : "Net PnL is tied";
    const drawdownText = drawdownWinner === "left" ? "Strategy A has lower drawdown" : drawdownWinner === "right" ? "Strategy B has lower drawdown" : "Drawdown is tied";
    return { label: "mixed comparison", className: "warn", details: `${pnlText}; ${drawdownText}.` };
  }

  function strategyComparisonBadge(side, winner, text) {
    if (winner === side) return `<span class="comparison-badge good">${escapeHtml(text)}</span>`;
    if (winner === "tie") return `<span class="comparison-badge same">tie</span>`;
    return "";
  }

  function renderStrategyComparisonControls(options, symbols, timeframes, fills) {
    renderSelectWithoutAll(elements.strategyComparisonLeftStrategy, options, state.strategyComparison.leftStrategyId);
    renderSelectWithoutAll(elements.strategyComparisonRightStrategy, options, state.strategyComparison.rightStrategyId);
    renderSelectWithoutAll(elements.strategyComparisonSymbol, symbols.map((symbol) => ({ value: symbol, label: symbol })), state.strategyComparison.symbol);
    renderSelectWithoutAll(elements.strategyComparisonTimeframe, timeframes.map((timeframe) => ({ value: timeframe, label: displayTimeframe(timeframe) })), canonicalTimeframe(state.strategyComparison.timeframe));
    renderSelectWithoutAll(elements.strategyComparisonFill, fills.map((fill) => ({ value: fill, label: fill })), state.strategyComparison.fillAssumption);
    if (elements.strategyComparisonLeftStrategy) {
      elements.strategyComparisonLeftStrategy.onchange = () => {
        state.strategyComparison.leftStrategyId = elements.strategyComparisonLeftStrategy.value;
        if (
          state.strategyComparison.rightStrategyId === state.strategyComparison.leftStrategyId &&
          state.strategyComparison.leftStrategyId !== STRATEGY_COMPARISON_ALL_STRATEGIES_ID
        ) {
          state.strategyComparison.rightStrategyId = options.map((option) => option.value).find((id) => id !== state.strategyComparison.leftStrategyId) || state.strategyComparison.leftStrategyId;
        }
        render();
      };
    }
    if (elements.strategyComparisonRightStrategy) {
      elements.strategyComparisonRightStrategy.onchange = () => {
        state.strategyComparison.rightStrategyId = elements.strategyComparisonRightStrategy.value;
        if (
          state.strategyComparison.rightStrategyId === state.strategyComparison.leftStrategyId &&
          state.strategyComparison.rightStrategyId !== STRATEGY_COMPARISON_ALL_STRATEGIES_ID
        ) {
          state.strategyComparison.leftStrategyId = options.map((option) => option.value).find((id) => id !== state.strategyComparison.rightStrategyId) || state.strategyComparison.rightStrategyId;
        }
        render();
      };
    }
    if (elements.strategyComparisonSymbol) {
      elements.strategyComparisonSymbol.onchange = () => {
        state.strategyComparison.symbol = elements.strategyComparisonSymbol.value;
        render();
      };
    }
    if (elements.strategyComparisonTimeframe) {
      elements.strategyComparisonTimeframe.onchange = () => {
        state.strategyComparison.timeframe = elements.strategyComparisonTimeframe.value;
        render();
      };
    }
    if (elements.strategyComparisonFill) {
      elements.strategyComparisonFill.onchange = () => {
        state.strategyComparison.fillAssumption = elements.strategyComparisonFill.value;
        render();
      };
    }
  }

  function strategyComparisonPointX(point, index, length, timeBounds, plotWidth, margin) {
    if (Number.isFinite(point.time) && Number.isFinite(timeBounds.start) && Number.isFinite(timeBounds.end) && timeBounds.end > timeBounds.start) {
      return margin.left + ((point.time - timeBounds.start) / (timeBounds.end - timeBounds.start)) * plotWidth;
    }
    return margin.left + (length === 1 ? plotWidth : (index / (length - 1)) * plotWidth);
  }

  function strategyComparisonPolyline(series, minValue, maxValue, timeBounds, plotWidth, plotHeight, margin) {
    const span = Math.max(maxValue - minValue, 1);
    return series.map((point, index) => {
      const x = strategyComparisonPointX(point, index, series.length, timeBounds, plotWidth, margin);
      const y = margin.top + plotHeight - ((point.value - minValue) / span) * plotHeight;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    }).join(" ");
  }

  function strategyComparisonReplayTimeBoundsFromTrades(trades) {
    const times = (trades || [])
      .flatMap((trade) => [tradeEntryTimestamp(trade), tradeExitTimestamp(trade)])
      .map((value) => Date.parse(value))
      .filter((value) => Number.isFinite(value));
    if (!times.length) return { start: null, end: null };
    return { start: Math.min(...times), end: Math.max(...times) };
  }

  function strategyComparisonSeriesTimeBounds(series) {
    const times = (series || []).map((point) => point.time).filter((value) => Number.isFinite(value));
    if (!times.length) return { start: null, end: null };
    return { start: Math.min(...times), end: Math.max(...times) };
  }

  function strategyComparisonCombinedTimeBounds(...seriesList) {
    const bounds = seriesList.map(strategyComparisonSeriesTimeBounds);
    const starts = bounds.map((bound) => bound.start).filter((value) => Number.isFinite(value));
    const ends = bounds.map((bound) => bound.end).filter((value) => Number.isFinite(value));
    if (!starts.length || !ends.length) return { start: null, end: null };
    return { start: Math.min(...starts), end: Math.max(...ends) };
  }

  function strategyComparisonTimeTicks(...seriesList) {
    const timeBounds = strategyComparisonCombinedTimeBounds(...seriesList);
    const bounds = [timeBounds];
    const starts = bounds.map((bound) => bound.start).filter((value) => Number.isFinite(value));
    const ends = bounds.map((bound) => bound.end).filter((value) => Number.isFinite(value));
    if (!starts.length || !ends.length) {
      return [
        { ratio: 0, label: "Start" },
        { ratio: 0.5, label: "Mid" },
        { ratio: 1, label: "End" },
      ];
    }
    const start = Math.min(...starts);
    const end = Math.max(...ends);
    return [
      { ratio: 0, label: strategyComparisonAxisDate(start) },
      { ratio: 0.5, label: strategyComparisonAxisDate(start + ((end - start) / 2)) },
      { ratio: 1, label: strategyComparisonAxisDate(end) },
    ];
  }

  function strategyComparisonAxisDate(value) {
    if (!Number.isFinite(value)) return "n/a";
    return new Date(value).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "2-digit",
      timeZone: "UTC",
    });
  }

  function strategyComparisonYAxisTicks(minValue, maxValue) {
    const midpoint = minValue + ((maxValue - minValue) / 2);
    return [maxValue, midpoint, minValue];
  }

  function strategyComparisonEndpointMarkup(point, series, minValue, maxValue, timeBounds, plotWidth, plotHeight, margin, className, label) {
    if (!point || !Number.isFinite(point.value)) return "";
    const x = strategyComparisonPointX(point, Math.max(series.length - 1, 0), series.length, timeBounds, plotWidth, margin);
    const y = margin.top + plotHeight - ((point.value - minValue) / Math.max(maxValue - minValue, 1)) * plotHeight;
    const labelX = Math.min(x + 10, margin.left + plotWidth - 78);
    const labelY = Math.max(y - 8, margin.top + 12);
    return `
      <circle cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="4" class="comparison-endpoint ${escapeHtml(className)}"></circle>
      <text x="${labelX.toFixed(2)}" y="${labelY.toFixed(2)}" class="comparison-endpoint-label ${escapeHtml(className)}">${escapeHtml(label)} ${escapeHtml(money(point.value))}</text>
    `;
  }

  function strategyComparisonLineClass(side, index) {
    return `line-${side}${index === 0 ? "" : ` line-alt-${((index - 1) % 6) + 1}`}`;
  }

  function strategyComparisonLinesForSide(replays, side) {
    return (replays || []).map((replay, index) => {
      if (replay?.chart_data_lazy && replay.chart_data_path) {
        loadHistoricalReplayChartData(replay.chart_data_path);
      }
      const series = strategyComparisonEquitySeries(replay);
      return {
        side,
        replay,
        series,
        className: strategyComparisonLineClass(side, index),
        label: dashboardStrategyLabel(replay.strategy_label, replay.strategy_id || `Strategy ${side.toUpperCase()}`),
      };
    }).filter((line) => line.series.length);
  }

  function renderStrategyComparisonChart(leftReplays, rightReplays) {
    if (!elements.strategyComparisonChart) return;
    const lines = [
      ...strategyComparisonLinesForSide(leftReplays, "a"),
      ...strategyComparisonLinesForSide(rightReplays, "b"),
    ];
    if (!lines.length) {
      setEmpty(elements.strategyComparisonChart, "No matching strategy rows found for this currency/timeframe/fill selection.");
      return;
    }
    const allSeries = lines.flatMap((line) => line.series);
    const all = allSeries.map((point) => point.value).filter((value) => Number.isFinite(value));
    const minValue = Math.min(...all);
    const maxValue = Math.max(...all);
    const width = 980;
    const height = 340;
    const margin = { top: 18, right: 28, bottom: 64, left: 92 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const timeBounds = strategyComparisonCombinedTimeBounds(...lines.map((line) => line.series));
    const yTicks = strategyComparisonYAxisTicks(minValue, maxValue);
    const xTicks = strategyComparisonTimeTicks(...lines.map((line) => line.series));
    const loading = [...(leftReplays || []), ...(rightReplays || [])].some((replay) =>
      replay?.chart_data_lazy && replay.chart_data_path && !state.loadedHistoricalChartDataPaths.has(replay.chart_data_path),
    );
    elements.strategyComparisonChart.innerHTML = `
      <div class="strategy-comparison-layout">
        <div class="strategy-comparison-legend" aria-label="Strategy comparison legend">
          ${lines.map((line) => `
            <span><i class="line-key ${escapeHtml(line.className)}"></i> ${escapeHtml(line.side === "a" ? "Strategy A" : "Strategy B")}: ${escapeHtml(line.label)} <small>${escapeHtml(line.series.length)} equity points</small></span>
          `).join("")}
          ${loading ? "<span>Loading exact selected replay JSON; summary endpoints shown until loaded.</span>" : ""}
        </div>
        <div class="strategy-comparison-plot">
          <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Strategy equity comparison over time">
            ${yTicks.map((value) => {
              const y = margin.top + plotHeight - ((value - minValue) / Math.max(maxValue - minValue, 1)) * plotHeight;
              return `
                <line x1="${margin.left}" y1="${y.toFixed(2)}" x2="${margin.left + plotWidth}" y2="${y.toFixed(2)}" class="comparison-grid-line"></line>
                <text x="${margin.left - 12}" y="${(y + 4).toFixed(2)}" text-anchor="end" class="comparison-axis-tick">${escapeHtml(money(value))}</text>
              `;
            }).join("")}
            ${xTicks.map((tick) => {
              const x = margin.left + tick.ratio * plotWidth;
              return `
                <line x1="${x.toFixed(2)}" y1="${margin.top}" x2="${x.toFixed(2)}" y2="${margin.top + plotHeight}" class="comparison-grid-line muted"></line>
                <text x="${x.toFixed(2)}" y="${margin.top + plotHeight + 24}" text-anchor="middle" class="comparison-axis-tick">${escapeHtml(tick.label)}</text>
              `;
            }).join("")}
            <line x1="${margin.left}" y1="${margin.top + plotHeight}" x2="${margin.left + plotWidth}" y2="${margin.top + plotHeight}" class="comparison-axis"></line>
            <line x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${margin.top + plotHeight}" class="comparison-axis"></line>
            <text x="${margin.left + (plotWidth / 2)}" y="${height - 14}" text-anchor="middle" class="comparison-axis-label">Time</text>
            <text x="18" y="${margin.top + (plotHeight / 2)}" text-anchor="middle" transform="rotate(-90 18 ${margin.top + (plotHeight / 2)})" class="comparison-axis-label">Equity value (USDC)</text>
            ${lines.map((line, index) => {
              const points = strategyComparisonPolyline(line.series, minValue, maxValue, timeBounds, plotWidth, plotHeight, margin);
              const endpoint = strategyComparisonEndpointMarkup(line.series.at(-1), line.series, minValue, maxValue, timeBounds, plotWidth, plotHeight, margin, line.className, line.side.toUpperCase());
              return `
                <polyline class="comparison-line ${escapeHtml(line.className)}" points="${escapeHtml(points)}" style="--line-index: ${index}"></polyline>
                ${endpoint}
              `;
            }).join("")}
          </svg>
        </div>
      </div>
    `;
  }

  function renderStrategyComparisonMetrics(leftReplay, rightReplay) {
    if (!elements.strategyComparisonMetrics || !elements.strategyComparisonVerdict) return;
    const verdict = strategyComparisonVerdict(leftReplay, rightReplay);
    elements.strategyComparisonVerdict.innerHTML = `<span class="result-pill result-${escapeHtml(verdict.className)}" title="${escapeHtml(verdict.details)}">${escapeHtml(verdict.label)}</span>`;
    if (!leftReplay || !rightReplay) {
      setEmpty(elements.strategyComparisonMetrics, "Choose two strategies with available replay rows.");
      return;
    }
    const left = strategyComparisonScopedReplay(leftReplay) || leftReplay;
    const right = strategyComparisonScopedReplay(rightReplay) || rightReplay;
    const metricRows = [
      ["Ending equity", "ending_equity", "higher", money],
      ["Net PnL", "net_pnl", "higher", money],
      ["Max drawdown", "max_drawdown", "lower", money],
      ["Win rate", "win_rate", "higher", pct],
      ["Trades", "trade_count", "higher", (value) => compactNumber(value, 0)],
      ["Profit factor", "profit_factor", "higher", (value) => compactNumber(value, 2)],
    ];
    elements.strategyComparisonMetrics.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Metric</th>
            <th>Strategy A</th>
            <th>Strategy B</th>
          </tr>
        </thead>
        <tbody>
          ${metricRows.map(([label, key, mode, formatter]) => {
            const leftValue = decimal(left.summary?.[key], NaN);
            const rightValue = decimal(right.summary?.[key], NaN);
            const winner = comparisonWinner(leftValue, rightValue, mode);
            return `
              <tr>
                <td>${escapeHtml(label)}</td>
                <td>${escapeHtml(Number.isFinite(leftValue) ? formatter(leftValue) : "n/a")} ${strategyComparisonBadge("left", winner, mode === "lower" ? "lower" : "better")}</td>
                <td>${escapeHtml(Number.isFinite(rightValue) ? formatter(rightValue) : "n/a")} ${strategyComparisonBadge("right", winner, mode === "lower" ? "lower" : "better")}</td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    `;
  }

  function renderStrategyComparison() {
    if (!elements.strategyComparisonChart) return;
    syncStrategyComparisonSelection();
    const options = strategyComparisonStrategyOptions(true);
    const replays = strategyComparisonReplays();
    const symbols = uniqueSorted(replays.map((replay) => replay.symbol));
    const timeframes = uniqueSorted(replays.map((replay) => canonicalTimeframe(replay.timeframe)))
      .sort((left, right) => timeframeSortRank(left) - timeframeSortRank(right));
    const fills = uniqueSorted(replays.map(replayFillAssumption));
    renderStrategyComparisonControls(options, symbols, timeframes, fills);
    if (!options.length) {
      setEmpty(elements.strategyComparisonChart, "No replay strategy data loaded yet.");
      setEmpty(elements.strategyComparisonMetrics, "Load SV2.0.2 / MF-ORIG replay JSON to compare strategies.");
      elements.strategyComparisonVerdict.innerHTML = "";
      return;
    }
    const leftReplays = strategyComparisonSideReplays(state.strategyComparison.leftStrategyId);
    const rightReplays = state.strategyComparison.leftStrategyId === STRATEGY_COMPARISON_ALL_STRATEGIES_ID
      ? []
      : strategyComparisonSideReplays(state.strategyComparison.rightStrategyId);
    renderStrategyComparisonChart(leftReplays, rightReplays);
    renderStrategyComparisonMetrics(leftReplays.length === 1 ? leftReplays[0] : null, rightReplays.length === 1 ? rightReplays[0] : null);
  }

  function renderComponentCards(summaries) {
    const maxMagnitude = Math.max(...summaries.map((summary) => Math.abs(summary.totalNetPnl)), 1);
    elements.componentCards.innerHTML = summaries
      .slice()
      .sort((a, b) => timeframeSortRank(a.timeframe) - timeframeSortRank(b.timeframe) || a.component.localeCompare(b.component))
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

  function evidenceReplayRunLedgerRows() {
    if (state.evidenceReplayStrategyId === EVIDENCE_BATCH_REPORTS_STRATEGY_ID) return null;
    const replays = Array.isArray(state.sv202HistoricalReplay?.replays)
      ? state.sv202HistoricalReplay.replays
      : [];
    const range = evidenceDateRange();
    const replayKey = (replay) =>
      `${replay.symbol || "unknown"}|${canonicalTimeframe(replay.timeframe)}|${replay.fill_assumption || "unknown"}`;
    const baselineByKey = new Map();
    replays
      .filter((replay) => (replay.strategy_id || "money_flow_v1_2_canonical") === "money_flow_v1_2_canonical")
      .forEach((replay) => {
        const scopedReplay = filteredReplayByRange(replay, range);
        const summary = scopedReplay?.summary || {};
        baselineByKey.set(replayKey(replay), {
          net_pnl: summary.net_pnl,
          max_drawdown: summary.max_drawdown,
        });
      });
    return replays
      .filter((replay) => {
        const strategyId = replay.strategy_id || "money_flow_v1_2_canonical";
        if (HIDDEN_DASHBOARD_STRATEGY_IDS.has(String(strategyId))) return false;
        if (state.evidenceReplayStrategyId === EVIDENCE_ALL_REPLAY_STRATEGIES_ID) return true;
        return strategyId === state.evidenceReplayStrategyId;
      })
      .filter((replay) => {
        const component = replay.component || `sleeve_${canonicalTimeframe(replay.timeframe)}`;
        return state.selectedComponent === "all" || component === state.selectedComponent;
      })
      .filter((replay) =>
        state.evidenceReplayFillAssumption === "all" || replayFillAssumption(replay) === state.evidenceReplayFillAssumption,
      )
      .map((replay) => {
        const scopedReplay = filteredReplayByRange(replay, range);
        const summary = scopedReplay?.summary || {};
        const strategyId = replay.strategy_id || "money_flow_v1_2_canonical";
        const baseline = baselineByKey.get(replayKey(replay));
        const result = classifyEvidenceReplayResult({
          strategy_id: strategyId,
          net_pnl: summary.net_pnl,
          max_drawdown: summary.max_drawdown,
        }, baseline);
        return {
          strategy_id: strategyId,
          strategy_label: dashboardStrategyLabel(replay.strategy_label, replay.strategy_id || "money_flow_v1_2_canonical"),
          component: replay.component || `sleeve_${canonicalTimeframe(replay.timeframe)}`,
          symbol: replay.symbol || "unknown",
          timeframe: canonicalTimeframe(replay.timeframe),
          fill_timing: replay.fill_assumption || "unknown",
          ending_equity: summary.ending_equity,
          net_pnl: summary.net_pnl,
          win_rate: summary.win_rate,
          trade_count: summary.trade_count,
          max_drawdown: summary.max_drawdown,
          source: replay.data_source || replay.strategy_truth_lane || "sv2_0_2_dashboard_chart_data",
          evidence_pack_path: replay.evidence_pack_path,
          research_only: replay.research_only !== false,
          production_approved: replay.production_approved === true,
          result_label: result.label,
          result_class: result.className,
          pnl_delta_vs_v12: result.pnlDelta,
          drawdown_delta_vs_v12: result.drawdownDelta,
        };
      })
      .sort((left, right) =>
        left.strategy_label.localeCompare(right.strategy_label) ||
        left.symbol.localeCompare(right.symbol) ||
        SV202_CANONICAL_TIMEFRAMES.indexOf(left.timeframe) - SV202_CANONICAL_TIMEFRAMES.indexOf(right.timeframe) ||
        left.fill_timing.localeCompare(right.fill_timing),
      );
  }

  function classifyEvidenceReplayResult(row, baseline) {
    if ((row.strategy_id || "money_flow_v1_2_canonical") === "money_flow_v1_2_canonical") {
      return { label: "baseline_v1_2", className: "baseline", pnlDelta: 0, drawdownDelta: 0 };
    }
    if (!baseline) {
      return { label: "baseline_unavailable", className: "unknown", pnlDelta: null, drawdownDelta: null };
    }
    const pnlDelta = decimal(row.net_pnl) - decimal(baseline.net_pnl);
    const drawdownDelta = decimal(row.max_drawdown) - decimal(baseline.max_drawdown);
    const pnlBetter = pnlDelta > 0;
    const drawdownBetter = drawdownDelta < 0;
    if (pnlDelta === 0 && drawdownDelta === 0) {
      return { label: "same_result", className: "same", pnlDelta, drawdownDelta };
    }
    if (pnlBetter && drawdownBetter) {
      return { label: "improved_pnl_drawdown", className: "good", pnlDelta, drawdownDelta };
    }
    if (pnlBetter && !drawdownBetter) {
      return { label: "improved_pnl_not_drawdown", className: "warn", pnlDelta, drawdownDelta };
    }
    if (!pnlBetter && drawdownBetter) {
      return { label: "improved_drawdown_not_pnl", className: "warn", pnlDelta, drawdownDelta };
    }
    return { label: "no bueno", className: "bad", pnlDelta, drawdownDelta };
  }

  function resultPill(row) {
    const title = row.pnl_delta_vs_v12 === null || row.drawdown_delta_vs_v12 === null
      ? "No matching Money Flow v1.2 baseline row found for this symbol/timeframe/fill."
      : `PnL delta vs v1.2: ${money(row.pnl_delta_vs_v12)}; drawdown delta vs v1.2: ${money(row.drawdown_delta_vs_v12)}. Lower drawdown is better.`;
    return `<span class="result-pill result-${escapeHtml(row.result_class || "unknown")}" title="${escapeHtml(title)}">${escapeHtml(row.result_label || "baseline_unavailable")}</span>`;
  }

  function runLedgerSortNumber(value) {
    if (value === null || value === undefined || value === "") return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function runLedgerSortButton(key, label) {
    const active = state.runLedgerSort.key === key;
    const direction = active ? state.runLedgerSort.direction : "none";
    return `
      <button class="run-ledger-sort-button" type="button" data-run-ledger-sort-key="${escapeHtml(key)}" aria-pressed="${active}">
        <span>${escapeHtml(label)}</span>
        <small>${escapeHtml(direction === "none" ? "sort" : direction)}</small>
      </button>
    `;
  }

  function sortRunLedgerRows(rows, fallbackSort = null) {
    const sorted = rows.slice();
    const key = state.runLedgerSort.key;
    if (!key) {
      return fallbackSort ? sorted.sort(fallbackSort) : sorted;
    }
    const direction = state.runLedgerSort.direction === "asc" ? 1 : -1;
    return sorted.sort((left, right) => {
      const leftValue = runLedgerSortNumber(left[key]);
      const rightValue = runLedgerSortNumber(right[key]);
      if (leftValue === null && rightValue === null) return 0;
      if (leftValue === null) return 1;
      if (rightValue === null) return -1;
      return (leftValue - rightValue) * direction;
    });
  }

  function bindRunLedgerSortControls() {
    if (!elements.runTable) return;
    elements.runTable.querySelectorAll("[data-run-ledger-sort-key]").forEach((button) => {
      button.addEventListener("click", () => {
        const key = button.dataset.runLedgerSortKey || "";
        if (state.runLedgerSort.key === key) {
          state.runLedgerSort.direction = state.runLedgerSort.direction === "desc" ? "asc" : "desc";
        } else {
          state.runLedgerSort.key = key;
          state.runLedgerSort.direction = "desc";
        }
        render();
      });
    });
  }

  function runLedgerTotals(rows) {
    if (!rows.length) return null;
    const endingEquity = rows.reduce((total, row) => total + decimal(row.ending_equity), 0);
    const netPnl = rows.reduce((total, row) => total + decimal(row.net_pnl), 0);
    const winRates = rows
      .map((row) => runLedgerSortNumber(row.win_rate))
      .filter((value) => value !== null);
    const avgWinRate = winRates.length
      ? winRates.reduce((total, value) => total + value, 0) / winRates.length
      : null;
    return { endingEquity, netPnl, avgWinRate, scenarioCount: rows.length };
  }

  function renderRunLedgerTotals(rows) {
    if (!elements.runLedgerTotals) return;
    const totals = runLedgerTotals(rows);
    if (!totals) {
      elements.runLedgerTotals.innerHTML = "";
      return;
    }
    elements.runLedgerTotals.innerHTML = `
      <span><small>Scenarios</small><strong>${escapeHtml(totals.scenarioCount)}</strong></span>
      <span><small>Total Ending Equity</small><strong>${escapeHtml(money(totals.endingEquity))}</strong></span>
      <span><small>Total PnL</small><strong class="${totals.netPnl >= 0 ? "positive" : "negative"}">${escapeHtml(money(totals.netPnl))}</strong></span>
      <span><small>Avg Win Rate</small><strong>${escapeHtml(totals.avgWinRate === null ? "n/a" : pct(totals.avgWinRate))}</strong></span>
    `;
  }

  function renderEvidenceReplayRunLedger(rows) {
    const label = selectedEvidenceReplayStrategyLabel();
    if (elements.runTableSubtitle) {
      const fillLabel = state.evidenceReplayFillAssumption === "all" ? "all fill assumptions" : state.evidenceReplayFillAssumption;
      elements.runTableSubtitle.textContent =
        `Replay strategy: ${label}. Fill assumption: ${fillLabel}. Rows are generated Historical Replay scenarios from loaded dashboard chart-data JSON; date filters are display-only, not canonical pack regeneration.`;
    }
    renderRunLedgerTotals(rows);
    if (!rows.length) {
      setEmpty(elements.runTable, "No generated replay rows loaded for this Evidence replay strategy/component/fill selection.");
      return;
    }
    const ledgerRows = rows
      .map((row) => ({
        ...row,
        endingEquity: row.ending_equity,
        netPnl: row.net_pnl,
        drawdown: row.max_drawdown,
      }));
    const sortedRows = sortRunLedgerRows(ledgerRows);
    elements.runTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Strategy</th>
            <th>Component</th>
            <th>Symbol</th>
            <th>Timeframe</th>
            <th>Fill</th>
            <th>${runLedgerSortButton("endingEquity", "Ending Equity")}</th>
            <th>${runLedgerSortButton("netPnl", "Scenario Net PnL")}</th>
            <th>Win</th>
            <th>Trades</th>
            <th>${runLedgerSortButton("drawdown", "Drawdown")}</th>
            <th>Result</th>
            <th>Boundary</th>
          </tr>
        </thead>
        <tbody>
          ${sortedRows.map((row) => `
            <tr>
              <td>${escapeHtml(row.strategy_label)}</td>
              <td>${escapeHtml(cleanComponentName(row.component))}</td>
              <td>${escapeHtml(row.symbol)}</td>
              <td>${escapeHtml(displayTimeframe(row.timeframe))}</td>
              <td>${escapeHtml(row.fill_timing)}</td>
              <td>${escapeHtml(money(row.ending_equity))}</td>
              <td class="${decimal(row.net_pnl) >= 0 ? "positive" : "negative"}">${escapeHtml(money(row.net_pnl))}</td>
              <td>${escapeHtml(row.win_rate === null || row.win_rate === undefined ? "n/a" : pct(row.win_rate))}</td>
              <td>${escapeHtml(row.trade_count ?? 0)}</td>
              <td>${escapeHtml(money(row.max_drawdown))}</td>
              <td>${resultPill(row)}</td>
              <td>${escapeHtml(row.production_approved ? "unexpected_approved" : "research-only / no production approval")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
    bindRunLedgerSortControls();
  }

  function renderRunTable(summaries) {
    const replayRows = evidenceReplayRunLedgerRows();
    if (replayRows) {
      renderEvidenceReplayRunLedger(replayRows);
      return;
    }
    if (elements.runTableSubtitle) {
      elements.runTableSubtitle.textContent =
        "Scenario results from loaded batch reports; dynamic equity is per scenario and not one combined account.";
    }
    renderRunLedgerTotals([]);
    const rawRows = summaries
      .flatMap((summary) => summary.runSummaries.map((row) => ({
        ...row,
        component: summary.label,
        endingEquity: row.metrics?.ending_equity ?? row.metrics?.net_pnl,
        netPnl: row.metrics?.net_pnl,
        drawdown: row.metrics?.mark_to_market_max_drawdown,
        result_label: "baseline_v1_2",
        result_class: "baseline",
        pnl_delta_vs_v12: 0,
        drawdown_delta_vs_v12: 0,
      })));
    if (!rawRows.length) {
      setEmpty(elements.runTable, "No run summaries loaded.");
      return;
    }
    const rows = sortRunLedgerRows(rawRows, (a, b) => decimal(b.metrics?.net_pnl) - decimal(a.metrics?.net_pnl))
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
            <th>${runLedgerSortButton("endingEquity", "Ending Equity")}</th>
            <th>${runLedgerSortButton("netPnl", "Scenario Net PnL")}</th>
            <th>Win</th>
            <th>Trades</th>
            <th>${runLedgerSortButton("drawdown", "Drawdown")}</th>
            <th>Result</th>
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
                  <td>${resultPill(row)}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
    bindRunLedgerSortControls();
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
    if (!elements.experimentsTitle) return;
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

  function canonicalTimeframe(value) {
    const raw = String(value || "").trim();
    return raw === "1D" ? "1d" : raw;
  }

  function displayTimeframe(value) {
    const canonical = canonicalTimeframe(value);
    return canonical === "1d" ? "1D" : canonical;
  }

  function sameTimeframe(left, right) {
    return canonicalTimeframe(left) === canonicalTimeframe(right);
  }

  function renderSelect(select, values, activeValue, labelAll) {
    if (!select) return;
    const normalized = values.map((value) =>
      typeof value === "object" && value !== null
        ? { value: value.value, label: value.label || value.value }
        : { value, label: displayTimeframe(value) },
    );
    select.innerHTML = [
      `<option value="all">${escapeHtml(labelAll)}</option>`,
      ...normalized.map((row) => `<option value="${escapeHtml(row.value)}">${escapeHtml(row.label)}</option>`),
    ].join("");
    select.value = normalized.some((row) => row.value === activeValue) ? activeValue : "all";
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
    const chartColors = dashboardChartColors();
    const chart = tv.createChart(mount, {
      width,
      height,
      layout: {
        background: { type: tv.ColorType.Solid, color: chartColors.background },
        textColor: chartColors.text,
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: chartColors.grid },
        horzLines: { color: chartColors.grid },
      },
      crosshair: {
        mode: tv.CrosshairMode.Normal,
      },
      rightPriceScale: {
        visible: true,
        borderVisible: true,
        borderColor: chartColors.border,
        entireTextOnly: false,
        scaleMargins: { top: 0.06, bottom: 0.22 },
      },
      timeScale: {
        borderColor: chartColors.border,
        timeVisible: true,
        secondsVisible: false,
      },
    });
    const candleSeries = chart.addSeries(tv.CandlestickSeries, {
      upColor: chartColors.candleUp,
      downColor: chartColors.candleDown,
      borderVisible: true,
      borderUpColor: chartColors.candleBorder,
      borderDownColor: chartColors.candleBorder,
      wickUpColor: chartColors.candleWick,
      wickDownColor: chartColors.candleWick,
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

  function destroyHistoricalReplayChart() {
    const chartState = state.historicalReplayChart;
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
    chartState.markerTradeIds = new Map();
    chartState.key = null;
    chartState.ready = false;
    chartState.lastVisibleRange = null;
  }

  function historicalReplays() {
    const sv202 = Array.isArray(state.sv202HistoricalReplay?.replays)
      ? state.sv202HistoricalReplay.replays
      : [];
    const pt = Array.isArray(state.pt002HistoricalReplay?.replays)
      ? state.pt002HistoricalReplay.replays
      : [];
    return [...sv202, ...pt]
      .filter(isVisibleDashboardStrategyRow)
      .filter((row) => isHistoricalReplayStrategyVisible(row.strategy_id || "money_flow_v1_2_canonical"));
  }

  function replayIdentity(row) {
    return [
      row?.strategy_id || "money_flow_v1_2_canonical",
      row?.symbol || "unknown",
      canonicalTimeframe(row?.timeframe || "unknown"),
      row?.fill_assumption || "unknown",
    ].join("|");
  }

  function mergeReplayRows(existing, incoming) {
    const merged = new Map();
    (existing || []).filter(isVisibleDashboardStrategyRow).forEach((row) => {
      merged.set(replayIdentity(row), row);
    });
    (incoming || []).filter(isVisibleDashboardStrategyRow).forEach((row) => {
      const key = replayIdentity(row);
      const previous = merged.get(key) || {};
      merged.set(key, {
        ...previous,
        ...row,
        chart_data_lazy: row.chart_data_lazy ?? previous.chart_data_lazy,
      });
    });
    return Array.from(merged.values());
  }

  function chartDataUrl(repoRelativePath) {
    if (!repoRelativePath) return "";
    if (repoRelativePath.startsWith("../") || repoRelativePath.startsWith("/")) return repoRelativePath;
    return `../../${repoRelativePath}`;
  }

  function safeReplayPathSegment(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function sv202SelectedChartDataPath(symbol, timeframe, strategyId, fillAssumption) {
    return chartDataUrl(
      `reports/strategy_validation/sv2_0_2_dashboard_chart_data/${SV202_CANONICAL_TIMESTAMP}/selected/` +
      `hyperliquid_public_${safeReplayPathSegment(symbol)}_${canonicalTimeframe(timeframe)}_` +
      `${safeReplayPathSegment(strategyId)}_${safeReplayPathSegment(fillAssumption)}_sv202_replay.json`,
    );
  }

  function mfOrigEv2SelectedChartDataPath(symbol, timeframe, strategyId, fillAssumption) {
    return chartDataUrl(
      `reports/strategy_validation/mf_orig_ev2_dashboard_chart_data/${MF_ORIG_EV2_TIMESTAMP}/selected/` +
      `hyperliquid_public_${safeReplayPathSegment(symbol)}_${canonicalTimeframe(timeframe)}_` +
      `${safeReplayPathSegment(strategyId)}_${safeReplayPathSegment(fillAssumption)}_mf_orig_ev2_replay.json`,
    );
  }

  function sv202SummaryReplaysFromBatches() {
    return (state.batches || []).flatMap((batch) =>
      (batch.run_reports || []).flatMap((run) => {
        if (run.status !== "completed") return [];
        const request = run.request || {};
        const metrics = run.report?.aggregate_metrics || {};
        const symbol = request.symbol || run.report?.symbol || "unknown";
        const component = request.component_keys?.[0] || Object.keys(metrics.trades_by_component_timeframe || {})[0] || "";
        const timeframe = canonicalTimeframe(component.replace(/^sleeve_/, "") || run.report?.timeframe || "unknown");
        const fillAssumption = request.assumptions?.fill_timing || "unknown";
        const chartDataPath = sv202SelectedChartDataPath(
          symbol,
          timeframe,
          "money_flow_v1_2_canonical",
          fillAssumption,
        );
        return [{
          strategy_id: "money_flow_v1_2_canonical",
          strategy_label: "Money Flow v1.2",
          component: component || `sleeve_${timeframe}`,
          symbol,
          timeframe,
          fill_assumption: fillAssumption,
          research_only: false,
          production_approved: false,
          data_source: "SV2.0.2 canonical batch report; selected chart data loads lazily",
          strategy_truth_lane: "historical_public_mainnet_candles",
          chart_data_path: chartDataPath,
          chart_data_lazy: Boolean(chartDataPath),
          evidence_pack_path: run.evidence_pack_path,
          summary: {
            starting_equity: metrics.starting_equity || request.assumptions?.initial_capital || "10000",
            ending_equity: metrics.ending_equity,
            net_pnl: metrics.net_pnl || metrics.net_account_pnl,
            max_drawdown: metrics.max_drawdown || metrics.mark_to_market_max_drawdown,
            max_drawdown_pct: metrics.max_drawdown_pct || metrics.mark_to_market_max_drawdown_pct,
            trade_count: metrics.number_of_trades,
            win_rate: metrics.win_rate,
            largest_loss: metrics.worst_trade_net_pnl,
            largest_win: metrics.best_trade_net_pnl,
            profit_factor: metrics.profit_factor,
          },
          candles: [],
          indicators: [],
          markers: [],
          trades: [],
          equity_curve: [],
        }];
      }),
    );
  }

  function mfOrigEv2SummaryReplays() {
    const summary = state.mfOrigSummary || {};
    if (summary.phase !== "MF-ORIG-EV2") return [];
    return (summary.replay_results || [])
      .filter((row) => isVisibleMfOrigStrategyId(row.hypothesis_id))
      .map((row) => {
      const timeframe = canonicalTimeframe(row.timeframe);
      const chartDataPath = mfOrigEv2SelectedChartDataPath(
        row.symbol,
        timeframe,
        row.hypothesis_id,
        row.fill_timing,
      );
      return {
        strategy_id: row.hypothesis_id,
        strategy_label: row.display_hypothesis_id || row.hypothesis_id,
        component: `sleeve_${timeframe}`,
        symbol: row.symbol,
        timeframe,
        fill_assumption: row.fill_timing,
        research_only: true,
        production_approved: row.production_approved === true,
        data_source: "MF-ORIG-EV2 compact summary; selected chart data loads lazily",
        strategy_truth_lane: "historical_public_mainnet_candles",
        chart_data_path: chartDataPath,
        chart_data_lazy: Boolean(chartDataPath),
        summary: {
          starting_equity: row.initial_equity,
          ending_equity: row.ending_equity,
          net_pnl: row.net_pnl,
          max_drawdown: row.max_drawdown,
          max_drawdown_pct: row.mark_to_market_max_drawdown_pct,
          trade_count: row.trade_count,
          win_rate: row.win_rate,
          largest_loss: row.largest_loss,
          largest_win: row.largest_win,
          profit_factor: row.profit_factor,
        },
        candles: [],
        indicators: [],
        markers: [],
        trades: [],
        equity_curve: [],
      };
    });
  }

  function sorEv3SummaryReplays() {
    const summary = state.sorEv3Summary || {};
    if (summary.phase !== "SOR-EV3") return [];
    return (summary.variant_results || [])
      .filter((row) => EVIDENCE_PRIORITY_REPLAY_STRATEGY_IDS.has(row.variant_id))
      .map((row) => {
      const timeframe = canonicalTimeframe(row.timeframe);
      const strategyId = row.variant_id || "unknown_sor_ev3_variant";
      const fillAssumption = row.fill_timing || row.fill_assumption || "unknown";
      const chartDataPath = sv202SelectedChartDataPath(
        row.symbol,
        timeframe,
        strategyId,
        fillAssumption,
      );
      return {
        strategy_id: strategyId,
        strategy_label: `SOR-EV3 ${strategyId}`,
        component: row.component_key || `sleeve_${timeframe}`,
        symbol: row.symbol,
        timeframe,
        fill_assumption: fillAssumption,
        research_only: true,
        production_approved: row.production_approved === true,
        data_source: "SOR-EV3 compact summary; selected chart data loads lazily",
        strategy_truth_lane: "historical_public_mainnet_candles",
        chart_data_path: chartDataPath,
        chart_data_lazy: Boolean(chartDataPath),
        summary: {
          starting_equity: row.baseline_ending_equity !== undefined && row.baseline_net_pnl !== undefined
            ? decimal(row.baseline_ending_equity) - decimal(row.baseline_net_pnl)
            : "10000",
          ending_equity: row.variant_ending_equity,
          net_pnl: row.variant_net_pnl,
          max_drawdown: row.variant_max_drawdown || row.max_drawdown,
          trade_count: row.trade_count,
          win_rate: row.win_rate,
          largest_loss: row.variant_largest_loss || row.largest_loss,
          largest_win: row.largest_win,
          profit_factor: row.profit_factor,
        },
        candles: [],
        indicators: [],
        markers: [],
        trades: [],
        equity_curve: [],
      };
    });
  }

  function selectedHistoricalReplay() {
    const exact = historicalReplays().find(
      (row) =>
        (row.strategy_id || "baseline_current_money_flow_rules") === state.historicalReplay.strategyId &&
        row.symbol === state.historicalReplay.symbol &&
        sameTimeframe(row.timeframe, state.historicalReplay.timeframe) &&
        (!row.fill_assumption || row.fill_assumption === state.historicalReplay.fillAssumption),
    );
    if (exact) return exact;
    const sameSelection = historicalReplays().find(
      (row) =>
        row.symbol === state.historicalReplay.symbol &&
        sameTimeframe(row.timeframe, state.historicalReplay.timeframe) &&
        (!row.fill_assumption || row.fill_assumption === state.historicalReplay.fillAssumption),
    );
    if (sameSelection) return sameSelection;
    if (!state.historicalReplay.symbol && !state.historicalReplay.timeframe) {
      return historicalReplays()[0] || null;
    }
    return null;
  }

  function historicalReplayKey() {
    return `${state.historicalReplay.strategyId}|${state.historicalReplay.symbol}|${canonicalTimeframe(state.historicalReplay.timeframe)}|${state.historicalReplay.fillAssumption}|${state.historicalReplay.dateStart}|${state.historicalReplay.dateEnd}`;
  }

  const HISTORICAL_RSI_PANE = 0;
  const HISTORICAL_PRICE_PANE = 1;
  const HISTORICAL_MACD_PANE = 2;
  const HIDDEN_HISTORICAL_REPLAY_STRATEGY_IDS = new Set([
    "baseline_current_money_flow_rules",
    "macd_removed_research_only",
    "only_close_on_5_20_cross_research_only",
  ]);

  function isHistoricalReplayStrategyVisible(strategyId) {
    return !HIDDEN_HISTORICAL_REPLAY_STRATEGY_IDS.has(String(strategyId || ""));
  }

  function filteredReplayByRange(replay, range) {
    if (!replay || !range.active) return replay;
    const candles = (replay.candles || []).filter((row) => inDateRange(row.timestamp_utc || row.time, range));
    const indicators = (replay.indicators || []).filter((row) => inDateRange(row.timestamp_utc || row.time, range));
    const rawTrades = (replay.trades || []).filter((trade) => tradeInDateRange(trade, range));
    const trades = rebaseTrades(rawTrades, 10000);
    const tradeIds = new Set(trades.map((trade) => trade.trade_id).filter(Boolean));
    const markers = (replay.markers || []).filter((marker) =>
      inDateRange(marker.time, range) &&
      (!marker.trade_id || tradeIds.has(marker.trade_id)),
    );
    const baseStarting = decimal(replay.summary?.starting_equity, 10000);
    const metrics = filteredTradeMetrics(trades, baseStarting);
    return {
      ...replay,
      candles,
      indicators,
      trades,
      markers,
      equity_curve: [metrics.startingEquity, ...trades.map((trade) => trade.equity_after_trade ?? trade.equity_after_exit)],
      summary: {
        ...(replay.summary || {}),
        starting_equity: metrics.startingEquity,
        ending_equity: metrics.endingEquity,
        net_pnl: metrics.netPnl,
        trade_count: metrics.tradeCount,
        win_rate: metrics.winRate,
        max_drawdown: metrics.maxDrawdown,
        max_drawdown_pct: metrics.maxDrawdownPct,
      },
      date_filter_label: range.label,
    };
  }

  function filteredHistoricalReplay(replay) {
    return filteredReplayByRange(replay, historicalDateRange());
  }

  function historicalChartCandles(replay) {
    return (replay?.candles || [])
      .map((candle) => ({
        time: chartTime(candle.timestamp_utc || candle.time),
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

  function historicalIndicatorRows(replay, label) {
    const key = {
      EMA5: "EMA5",
      EMA10: "EMA10",
      SMA20: "SMA20",
    }[label];
    if (!key) return [];
    return (replay?.indicators || [])
      .map((row) => ({
        time: chartTime(row.timestamp_utc || row.time),
        value: decimal(row[key], NaN),
      }))
      .filter((row) => Number.isFinite(row.time) && Number.isFinite(row.value))
      .sort((a, b) => a.time - b.time);
  }

  function historicalOscillatorRows(replay, key) {
    return (replay?.indicators || [])
      .map((row) => ({
        time: chartTime(row.timestamp_utc || row.time),
        value: decimal(row[key], NaN),
      }))
      .filter((row) => Number.isFinite(row.time) && Number.isFinite(row.value))
      .sort((a, b) => a.time - b.time);
  }

  function historicalMacdHistogramRows(replay) {
    return historicalOscillatorRows(replay, "MACD_histogram").map((row) => ({
      ...row,
      color: row.value >= 0 ? "rgba(37, 208, 132, 0.52)" : "rgba(255, 90, 102, 0.52)",
    }));
  }

  function historicalConstantRows(candles, value) {
    if (!candles.length) return [];
    return [
      { time: candles[0].time, value },
      { time: candles.at(-1).time, value },
    ];
  }

  function historicalLatestIndicatorValue(replay, key) {
    const row = historicalOscillatorRows(replay, key).at(-1);
    return row ? compactNumber(row.value) : "indicator_unavailable";
  }

  function renderHistoricalIndicatorLegend(replay) {
    return `
      <span><b class="legend-dot rsi"></b>RSI 14 ${escapeHtml(historicalLatestIndicatorValue(replay, "RSI"))}</span>
      <span><b class="legend-dot macd"></b>MACD ${escapeHtml(historicalLatestIndicatorValue(replay, "MACD"))}</span>
      <span><b class="legend-dot macd-signal"></b>Signal ${escapeHtml(historicalLatestIndicatorValue(replay, "MACD_signal"))}</span>
      <span><b class="legend-dot macd-histogram"></b>Hist ${escapeHtml(historicalLatestIndicatorValue(replay, "MACD_histogram"))}</span>
      <span>Pane order: RSI, candles, MACD. All panes share the same candle time scale.</span>
    `;
  }

  function historicalTradeForMarker(replay, marker) {
    if (!marker?.trade_id) return null;
    return (replay?.trades || []).find((trade) => trade.trade_id === marker.trade_id) || null;
  }

  function historicalMarkerReasons(reasons, fallback) {
    const values = (Array.isArray(reasons) ? reasons : [])
      .map((reason) => String(reason || "").trim())
      .filter(Boolean);
    return values.length ? values.join(", ") : fallback;
  }

  function historicalMarkerPnl(value) {
    if (value === null || value === undefined || value === "") return "n/a";
    return money(value);
  }

  function historicalMarkerPnlLine(value) {
    return `PnL: ${historicalMarkerPnl(value)}`;
  }

  function historicalMarkerLines(replay, marker) {
    const trade = historicalTradeForMarker(replay, marker);
    const pnlValue = trade?.net_pnl ?? marker?.net_pnl;
    if (!state.historicalReplay.showArrowDescriptions) {
      return [historicalMarkerPnlLine(pnlValue)];
    }
    const markerReasons = Array.isArray(marker?.reason_codes) ? marker.reason_codes : [];
    const markerType = String(marker?.marker_type || "");
    const entryReasons = trade?.entry_reason_codes?.length
      ? trade.entry_reason_codes
      : markerType.includes("entry")
        ? markerReasons
        : [];
    const exitReasons = trade?.exit_reason_codes?.length
      ? trade.exit_reason_codes
      : markerType.includes("exit")
        ? markerReasons
        : [];
    const parts = [];
    if (entryReasons.length) {
      parts.push(`Entry: ${historicalMarkerReasons(entryReasons, "n/a")}`);
    }
    parts.push(`Exit: ${historicalMarkerReasons(exitReasons, "n/a")}`);
    parts.push(`Net PnL: ${historicalMarkerPnl(pnlValue)}`);
    return parts;
  }

  function historicalMarkerObjectId(marker, parsed, index) {
    const raw = [
      marker?.trade_id || "no-trade",
      marker?.marker_type || "marker",
      parsed,
      index,
    ].join("-");
    return `historical-marker-${raw.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
  }

  function historicalChartMarkers(replay, candles, markerTradeIds = new Map()) {
    markerTradeIds.clear();
    if (!candles.length) return [];
    const firstTime = candles[0].time;
    const lastTime = candles.at(-1).time;
    return (replay?.markers || [])
      .flatMap((marker) => {
        const parsed = chartTime(marker.time);
        if (parsed < firstTime || parsed > lastTime) return [];
        const role = marker.color_role || "gray";
        const isEntry = role === "green";
        const isTrim = role === "yellow";
        const markerBase = {
          time: parsed,
          position: isEntry ? "belowBar" : "aboveBar",
          color: isEntry ? "#25d084" : isTrim ? "#f8c15c" : "#ff5a66",
          shape: isEntry ? "arrowUp" : isTrim ? "circle" : "arrowDown",
        };
        return historicalMarkerLines(replay, marker).map((line, index) => ({
          ...markerBase,
          id: historicalMarkerObjectId(marker, parsed, index),
          size: index === 0 ? 1 : 0,
          text: line,
        })).map((chartMarker) => {
          if (marker.trade_id) {
            markerTradeIds.set(chartMarker.id, marker.trade_id);
          }
          return chartMarker;
        });
      })
      .filter(Boolean);
  }

  function lightweightChartTimeToUnix(value) {
    if (value === null || value === undefined || value === "") return NaN;
    if (Number.isFinite(value)) return Number(value);
    if (value && typeof value === "object" && value.year && value.month && value.day) {
      return Math.floor(Date.UTC(value.year, value.month - 1, value.day) / 1000);
    }
    return chartTime(value);
  }

  function historicalTradeIdFromChartClick(param, replay) {
    const objectId = param?.hoveredObjectId || param?.hoveredObject?.id || null;
    const mappedTradeId = objectId ? state.historicalReplayChart.markerTradeIds?.get(objectId) : null;
    if (mappedTradeId) return mappedTradeId;
    const clickedTime = lightweightChartTimeToUnix(param?.time);
    if (!Number.isFinite(clickedTime)) return null;
    const marker = (replay?.markers || []).find(
      (row) => row.trade_id && chartTime(row.time) === clickedTime,
    );
    return marker?.trade_id || null;
  }

  function selectHistoricalReplayTrade(tradeId) {
    if (!tradeId) return;
    state.historicalReplay.selectedTradeId = tradeId;
    const replay = filteredHistoricalReplay(selectedHistoricalReplay());
    renderHistoricalTradeInspector(replay);
    renderHistoricalEquityPanel(replay);
    renderHistoricalTradesTable(replay);
  }

  function resizeHistoricalReplayChart() {
    const chartState = state.historicalReplayChart;
    if (!chartState.chart || !chartState.mount) return;
    const { width, height } = chartDimensions(chartState.mount);
    chartState.chart.resize(width, height);
    setHistoricalReplayPaneHeights(chartState.chart, height);
  }

  function setHistoricalReplayPaneHeights(chart, height) {
    if (!chart || typeof chart.panes !== "function") return;
    const panes = chart.panes();
    if (!Array.isArray(panes) || panes.length < 3) return;
    [
      [HISTORICAL_RSI_PANE, 15, Math.round(height * 0.15)],
      [HISTORICAL_PRICE_PANE, 70, Math.round(height * 0.7)],
      [HISTORICAL_MACD_PANE, 15, Math.max(1, Math.round(height * 0.15))],
    ].forEach(([paneIndex, stretchFactor, fallbackHeight]) => {
      if (typeof panes[paneIndex]?.setStretchFactor === "function") {
        panes[paneIndex].setStretchFactor(stretchFactor);
      } else if (typeof panes[paneIndex]?.setHeight === "function") {
        panes[paneIndex].setHeight(fallbackHeight);
      }
    });
  }

  function applyHistoricalReplayPaneScale(chart, paneIndex) {
    if (!chart || typeof chart.priceScale !== "function") return;
    const chartColors = dashboardChartColors();
    try {
      chart.priceScale("right", paneIndex).applyOptions({
        visible: true,
        borderVisible: true,
        borderColor: chartColors.border,
      });
    } catch (_error) {
      // Lightweight Charts creates pane scales lazily; missing pane scales are non-fatal.
    }
  }

  function scheduleHistoricalReplayChartResize() {
    const chartState = state.historicalReplayChart;
    if (!chartState.chart || !chartState.mount) return;
    if (chartState.pendingResizeFrame) return;
    const raf = typeof window.requestAnimationFrame === "function"
      ? window.requestAnimationFrame
      : (callback) => window.setTimeout(callback, 16);
    chartState.pendingResizeFrame = raf(() => {
      chartState.pendingResizeFrame = null;
      resizeHistoricalReplayChart();
    });
  }

  function updateHistoricalReplayChartData(replay, candles) {
    const chartState = state.historicalReplayChart;
    if (!chartState.candleSeries || !chartState.volumeSeries) return;
    const timeScale = chartState.chart?.timeScale?.();
    chartState.lastVisibleRange = timeScale?.getVisibleLogicalRange?.() || null;
    chartState.candleSeries.setData(chartPriceRows(candles));
    chartState.volumeSeries.setData(chartVolumeRows(candles));
    ["EMA5", "EMA10", "SMA20"].forEach((label) => {
      chartState.indicatorSeries[label]?.setData(historicalIndicatorRows(replay, label));
    });
    chartState.indicatorSeries.RSI?.setData(historicalOscillatorRows(replay, "RSI"));
    chartState.indicatorSeries.RSI_floor?.setData(historicalConstantRows(candles, 0));
    chartState.indicatorSeries.RSI_ceiling?.setData(historicalConstantRows(candles, 100));
    chartState.indicatorSeries.MACD?.setData(historicalOscillatorRows(replay, "MACD"));
    chartState.indicatorSeries.MACD_signal?.setData(historicalOscillatorRows(replay, "MACD_signal"));
    chartState.indicatorSeries.MACD_histogram?.setData(historicalMacdHistogramRows(replay));
    const markerTradeIds = chartState.markerTradeIds || new Map();
    const markers = historicalChartMarkers(replay, candles, markerTradeIds);
    chartState.markerTradeIds = markerTradeIds;
    if (chartState.markerHandle && typeof chartState.markerHandle.setMarkers === "function") {
      chartState.markerHandle.setMarkers(markers);
    } else if (typeof chartState.candleSeries.setMarkers === "function") {
      chartState.candleSeries.setMarkers(markers);
    }
    if (chartState.lastVisibleRange && typeof timeScale?.setVisibleLogicalRange === "function") {
      timeScale.setVisibleLogicalRange(chartState.lastVisibleRange);
    }
    const legend = elements.historicalReplayChart?.querySelector("[data-historical-indicator-legend]");
    if (legend) {
      legend.innerHTML = renderHistoricalIndicatorLegend(replay);
    }
    scheduleHistoricalReplayChartResize();
  }

  function renderHistoricalReplayChart(replay) {
    const tv = lightweightCharts();
    if (!elements.historicalReplayChart || !tv) return false;
    const candles = historicalChartCandles(replay);
    if (!candles.length) {
      destroyHistoricalReplayChart();
      setEmpty(elements.historicalReplayChart, "Historical replay candles are unavailable for this symbol/timeframe.");
      return false;
    }
    const chartState = state.historicalReplayChart;
    const chartKey = historicalReplayKey();
    if (chartState.ready && chartState.key === chartKey && chartState.chart && chartState.candleSeries && chartState.volumeSeries) {
      updateHistoricalReplayChartData(replay, candles);
      return true;
    }

    destroyHistoricalReplayChart();
    const priceStats = chartPriceStats(candles);
    elements.historicalReplayChart.innerHTML = `
      <div class="tradingview-chart-topline">
        <div>
          <strong>${escapeHtml(state.historicalReplay.symbol)}-PERP historical replay</strong>
          <span>${escapeHtml(replay.strategy_label || state.historicalReplay.strategyId)} / ${escapeHtml(displayTimeframe(state.historicalReplay.timeframe))} / ${escapeHtml(state.historicalReplay.fillAssumption)} / not testnet strategy truth</span>
        </div>
        <aside class="chart-price-axis-readout chart-price-axis-readout-inline" aria-label="Historical replay price scale">
          <span>Historical price USDC</span>
          <strong>${escapeHtml(priceStats.latest)}</strong>
          <small>H ${escapeHtml(priceStats.high)}</small>
          <small>L ${escapeHtml(priceStats.low)}</small>
          <small>O ${escapeHtml(priceStats.open)}</small>
          <small>C ${escapeHtml(priceStats.close)}</small>
        </aside>
      </div>
      <div class="tradingview-chart-stage historical-chart-stage">
        <div class="tradingview-lightweight-chart" role="img" aria-label="Historical replay candlestick chart with visible right price scale"></div>
      </div>
      <div class="historical-overlay-legend" data-historical-indicator-legend>${renderHistoricalIndicatorLegend(replay)}</div>
      <div class="tradingview-attribution">Charts: TradingView Lightweight Charts v${TRADINGVIEW_LIGHTWEIGHT_CHARTS_VERSION} (Apache-2.0). Historical replay data only; Hyperliquid testnet prices are not strategy truth.</div>
    `;
    const mount = elements.historicalReplayChart.querySelector(".tradingview-lightweight-chart");
    const { width, height } = chartDimensions(mount);
    const chartColors = dashboardChartColors();
    const chart = tv.createChart(mount, {
      width,
      height,
      layout: {
        background: { type: tv.ColorType.Solid, color: chartColors.background },
        textColor: chartColors.text,
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: chartColors.grid },
        horzLines: { color: chartColors.grid },
      },
      crosshair: { mode: tv.CrosshairMode.Normal },
      rightPriceScale: {
        visible: true,
        borderVisible: true,
        borderColor: chartColors.border,
        scaleMargins: { top: 0.05, bottom: 0.08 },
      },
      timeScale: {
        borderColor: chartColors.border,
        timeVisible: true,
        secondsVisible: false,
      },
    });
    const lineSeries = {};
    const rsiSeries = chart.addSeries(tv.LineSeries, {
      color: "#22d3ee",
      lineWidth: 2,
      priceScaleId: "right",
      priceFormat: { type: "price", precision: 2, minMove: 0.01 },
      priceLineVisible: true,
      lastValueVisible: true,
      title: "RSI 14",
    }, HISTORICAL_RSI_PANE);
    rsiSeries.setData(historicalOscillatorRows(replay, "RSI"));
    if (typeof rsiSeries.createPriceLine === "function") {
      rsiSeries.createPriceLine({ price: 70, color: "rgba(255, 90, 102, 0.55)", lineWidth: 1, lineStyle: tv.LineStyle.Dashed, axisLabelVisible: false, title: "RSI 70" });
      rsiSeries.createPriceLine({ price: 30, color: "rgba(37, 208, 132, 0.45)", lineWidth: 1, lineStyle: tv.LineStyle.Dashed, axisLabelVisible: false, title: "RSI 30" });
    }
    lineSeries.RSI = rsiSeries;
    const rsiFloor = chart.addSeries(tv.LineSeries, {
      color: "rgba(0, 0, 0, 0)",
      lineWidth: 1,
      priceScaleId: "right",
      priceFormat: { type: "price", precision: 2, minMove: 0.01 },
      priceLineVisible: false,
      lastValueVisible: false,
      title: "RSI floor",
    }, HISTORICAL_RSI_PANE);
    rsiFloor.setData(historicalConstantRows(candles, 0));
    const rsiCeiling = chart.addSeries(tv.LineSeries, {
      color: "rgba(0, 0, 0, 0)",
      lineWidth: 1,
      priceScaleId: "right",
      priceFormat: { type: "price", precision: 2, minMove: 0.01 },
      priceLineVisible: false,
      lastValueVisible: false,
      title: "RSI ceiling",
    }, HISTORICAL_RSI_PANE);
    rsiCeiling.setData(historicalConstantRows(candles, 100));
    lineSeries.RSI_floor = rsiFloor;
    lineSeries.RSI_ceiling = rsiCeiling;
    const candleSeries = chart.addSeries(tv.CandlestickSeries, {
      upColor: chartColors.candleUp,
      downColor: chartColors.candleDown,
      borderVisible: true,
      borderUpColor: chartColors.candleBorder,
      borderDownColor: chartColors.candleBorder,
      wickUpColor: chartColors.candleWick,
      wickDownColor: chartColors.candleWick,
      priceFormat: chartPriceFormat(candles),
      priceLineVisible: true,
      lastValueVisible: true,
    }, HISTORICAL_PRICE_PANE);
    candleSeries.setData(chartPriceRows(candles));
    const volumeSeries = chart.addSeries(tv.HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
      color: "rgba(107, 132, 145, 0.35)",
    }, HISTORICAL_PRICE_PANE);
    chart.priceScale("volume", HISTORICAL_PRICE_PANE).applyOptions({ scaleMargins: { top: 0.94, bottom: 0 } });
    volumeSeries.setData(chartVolumeRows(candles));
    [
      ["EMA5", "#26c6da"],
      ["EMA10", "#f8c15c"],
      ["SMA20", "#b68cff"],
    ].forEach(([label, color]) => {
      const line = chart.addSeries(tv.LineSeries, {
        color,
        lineWidth: 2,
        priceFormat: chartPriceFormat(candles),
        priceLineVisible: false,
        lastValueVisible: true,
        title: label,
      }, HISTORICAL_PRICE_PANE);
      line.setData(historicalIndicatorRows(replay, label));
      lineSeries[label] = line;
    });
    const macdHistogram = chart.addSeries(tv.HistogramSeries, {
      priceScaleId: "right",
      priceFormat: { type: "price", precision: 4, minMove: 0.0001 },
      base: 0,
      color: "rgba(37, 208, 132, 0.42)",
      title: "MACD histogram",
    }, HISTORICAL_MACD_PANE);
    macdHistogram.setData(historicalMacdHistogramRows(replay));
    const macdLine = chart.addSeries(tv.LineSeries, {
      color: "#22d3ee",
      lineWidth: 2,
      priceScaleId: "right",
      priceFormat: { type: "price", precision: 4, minMove: 0.0001 },
      priceLineVisible: true,
      lastValueVisible: true,
      title: "MACD",
    }, HISTORICAL_MACD_PANE);
    macdLine.setData(historicalOscillatorRows(replay, "MACD"));
    if (typeof macdLine.createPriceLine === "function") {
      macdLine.createPriceLine({ price: 0, color: "rgba(201, 213, 220, 0.35)", lineWidth: 1, lineStyle: tv.LineStyle.Dashed, axisLabelVisible: false, title: "MACD zero" });
    }
    const macdSignalLine = chart.addSeries(tv.LineSeries, {
      color: "#f8c15c",
      lineWidth: 2,
      priceScaleId: "macd",
      priceFormat: { type: "price", precision: 4, minMove: 0.0001 },
      priceLineVisible: true,
      lastValueVisible: true,
      title: "MACD signal",
    }, HISTORICAL_MACD_PANE);
    macdSignalLine.setData(historicalOscillatorRows(replay, "MACD_signal"));
    lineSeries.MACD = macdLine;
    lineSeries.MACD_signal = macdSignalLine;
    lineSeries.MACD_histogram = macdHistogram;
    applyHistoricalReplayPaneScale(chart, HISTORICAL_RSI_PANE);
    applyHistoricalReplayPaneScale(chart, HISTORICAL_PRICE_PANE);
    applyHistoricalReplayPaneScale(chart, HISTORICAL_MACD_PANE);
    chartState.markerTradeIds = new Map();
    const markers = historicalChartMarkers(replay, candles, chartState.markerTradeIds);
    if (typeof tv.createSeriesMarkers === "function") {
      chartState.markerHandle = tv.createSeriesMarkers(candleSeries, markers);
    } else if (typeof candleSeries.setMarkers === "function") {
      candleSeries.setMarkers(markers);
    }
    if (typeof chart.subscribeClick === "function") {
      chart.subscribeClick((param) => {
        const tradeId = historicalTradeIdFromChartClick(param, replay);
        if (tradeId) {
          selectHistoricalReplayTrade(tradeId);
        }
      });
    }
    chart.timeScale().fitContent();
    chartState.chart = chart;
    chartState.mount = mount;
    chartState.candleSeries = candleSeries;
    chartState.volumeSeries = volumeSeries;
    chartState.indicatorSeries = lineSeries;
    chartState.key = chartKey;
    chartState.ready = true;
    setHistoricalReplayPaneHeights(chart, height);
    if (typeof ResizeObserver !== "undefined") {
      const observer = new ResizeObserver(scheduleHistoricalReplayChartResize);
      observer.observe(mount);
      chartState.resizeObserver = observer;
    }
    return true;
  }

  function renderHistoricalReplayFilters() {
    const summary = state.pt002HistoricalReplay || {};
    const sv20 = state.sv20Summary || {};
    const replays = historicalReplays();
    const symbols = Array.from(new Set([
      ...replays.map((row) => row.symbol).filter(Boolean),
      ...(Array.isArray(summary.symbols) ? summary.symbols : []),
      ...(Array.isArray(sv20.symbols) ? sv20.symbols : []),
    ]));
    const timeframes = Array.from(new Set([
      ...replays.map((row) => row.timeframe).filter(Boolean),
      ...(Array.isArray(summary.timeframes) ? summary.timeframes : []),
      ...(Array.isArray(sv20.timeframes) ? sv20.timeframes : []),
    ].map(canonicalTimeframe)));
    const fills = Array.from(new Set([
      ...replays.map((row) => row.fill_assumption).filter(Boolean),
      ...(Array.isArray(summary.fill_assumptions) ? summary.fill_assumptions.map((row) => row.id || row) : []),
    ]));
    if (!isHistoricalReplayStrategyVisible(state.historicalReplay.strategyId)) {
      state.historicalReplay.strategyId = "money_flow_v1_2_canonical";
      state.historicalReplay.selectedTradeId = null;
    }
    const strategies = Array.from(
      new Map(
        [
          ...replays.map((row) => [
            row.strategy_id || "baseline_current_money_flow_rules",
            {
              value: row.strategy_id || "baseline_current_money_flow_rules",
              label: dashboardStrategyLabel(row.strategy_label, row.strategy_id || "baseline_current_money_flow_rules"),
            },
          ]),
          ...(Array.isArray(summary.strategies)
            ? summary.strategies.map((row) => [row.id, { value: row.id, label: dashboardStrategyLabel(row.label || row.id, row.id) }])
            : []),
        ].filter(([value]) => value),
      ).values(),
    ).filter((strategy) => isHistoricalReplayStrategyVisible(strategy.value));
    renderSelect(
      elements.historicalReplayStrategyFilter,
      strategies,
      state.historicalReplay.strategyId,
      "Select replay strategy",
    );
    renderSelect(elements.historicalReplaySymbolFilter, symbols, state.historicalReplay.symbol, "Select symbol");
    renderSelect(elements.historicalReplayTimeframeFilter, timeframes, state.historicalReplay.timeframe, "Select timeframe");
    renderSelect(elements.historicalReplayFillFilter, fills, state.historicalReplay.fillAssumption, "Select fill");
    if (elements.historicalReplayDateStart) {
      elements.historicalReplayDateStart.value = state.historicalReplay.dateStart || "";
      elements.historicalReplayDateStart.onchange = () => {
        state.historicalReplay.dateStart = elements.historicalReplayDateStart.value;
        state.historicalReplay.selectedTradeId = null;
        renderHistoricalReplay();
      };
    }
    if (elements.historicalReplayDateEnd) {
      elements.historicalReplayDateEnd.value = state.historicalReplay.dateEnd || "";
      elements.historicalReplayDateEnd.onchange = () => {
        state.historicalReplay.dateEnd = elements.historicalReplayDateEnd.value;
        state.historicalReplay.selectedTradeId = null;
        renderHistoricalReplay();
      };
    }
    if (elements.historicalReplayDateClear) {
      elements.historicalReplayDateClear.onclick = () => {
        state.historicalReplay.dateStart = "";
        state.historicalReplay.dateEnd = "";
        state.historicalReplay.selectedTradeId = null;
        renderHistoricalReplay();
      };
    }
    if (elements.historicalReplayArrowDescriptionsToggle) {
      elements.historicalReplayArrowDescriptionsToggle.checked = Boolean(state.historicalReplay.showArrowDescriptions);
      elements.historicalReplayArrowDescriptionsToggle.onchange = () => {
        state.historicalReplay.showArrowDescriptions = elements.historicalReplayArrowDescriptionsToggle.checked;
        renderHistoricalReplay();
      };
    }
    if (elements.historicalReplayStrategyFilter) {
      elements.historicalReplayStrategyFilter.onchange = () => {
        state.historicalReplay.strategyId = elements.historicalReplayStrategyFilter.value === "all"
          ? "money_flow_v1_2_canonical"
          : elements.historicalReplayStrategyFilter.value;
        state.historicalReplay.selectedTradeId = null;
        renderHistoricalReplay();
      };
    }
    if (elements.historicalReplaySymbolFilter) {
      elements.historicalReplaySymbolFilter.onchange = () => {
        state.historicalReplay.symbol = elements.historicalReplaySymbolFilter.value === "all"
          ? "ETH"
          : elements.historicalReplaySymbolFilter.value;
        state.historicalReplay.selectedTradeId = null;
        renderHistoricalReplay();
      };
    }
    if (elements.historicalReplayTimeframeFilter) {
      elements.historicalReplayTimeframeFilter.onchange = () => {
        state.historicalReplay.timeframe = elements.historicalReplayTimeframeFilter.value === "all"
          ? "1h"
          : canonicalTimeframe(elements.historicalReplayTimeframeFilter.value);
        state.historicalReplay.selectedTradeId = null;
        renderHistoricalReplay();
      };
    }
    if (elements.historicalReplayFillFilter) {
      elements.historicalReplayFillFilter.onchange = () => {
        state.historicalReplay.fillAssumption = elements.historicalReplayFillFilter.value === "all"
          ? "next_candle_open"
          : elements.historicalReplayFillFilter.value;
        state.historicalReplay.selectedTradeId = null;
        renderHistoricalReplay();
      };
    }
  }

  function renderHistoricalReplaySourceStatus(replay) {
    if (!elements.historicalReplaySourceStatus) return;
    const summary = state.pt002HistoricalReplay || {};
    const sv20Source = state.sv20Summary?.source || {};
    const canonicalEvidence = state.sv20Summary?.canonical_evidence_status || {};
    const dataset = historicalReadinessForSelection();
    const warnings = dataset?.reason_codes || [];
    elements.historicalReplaySourceStatus.innerHTML = `
      <span>Replay strategy: ${escapeHtml(dashboardStrategyLabel(replay?.strategy_label, state.historicalReplay.strategyId))}</span>
      <span>Money Flow version: ${escapeHtml(state.sv20Summary?.money_flow_version || "money_flow_v1_1 replay source")}</span>
      <span>Canonical evidence: ${escapeHtml(canonicalEvidence.status || "not_loaded")}</span>
      <span>Evidence packs: ${escapeHtml((canonicalEvidence.evidence_pack_paths || []).length)}</span>
      <span>Compact replay canonical: ${escapeHtml(canonicalEvidence.compact_replay_rows_are_canonical_evidence === false ? "false" : "unknown")}</span>
      <span>Source: ${escapeHtml(sv20Source.historical_strategy_truth || dataset?.source || summary.source?.source_kind || "historical source not loaded")}</span>
      <span>Range: ${escapeHtml(dataset?.start_time || dataset?.earliest_candle || "n/a")} -> ${escapeHtml(dataset?.end_time || dataset?.latest_candle || "n/a")}</span>
      <span>Coverage: ${escapeHtml(dataset?.target_coverage_percent ? pct(dataset.target_coverage_percent) : dataset?.coverage_percent || "n/a")}</span>
      <span>Candles: ${escapeHtml(dataset?.candle_count ?? replay?.candles?.length ?? 0)}</span>
      <span>DB imported: ${escapeHtml(dataset?.db_imported ? "yes" : "no")}</span>
      <span>Evidence-ready: ${escapeHtml(dataset?.canonical_evidence_ready || dataset?.evidence_ready ? "yes" : "no")}</span>
      <span>Replay-ready: ${escapeHtml(dataset?.replay_ready ? "yes" : "no")}</span>
      <span>Aggregation: ${escapeHtml(dataset?.aggregation_used ? `from ${dataset.aggregation_source_timeframe || "lower timeframe"}` : "source candles")}</span>
      <span>Warnings: ${escapeHtml(warnings.slice(0, 3).join(", ") || "none")}</span>
      <span>Testnet strategy truth: ${escapeHtml(sv20Source.testnet_prices_used_as_strategy_truth === false || summary.source?.testnet_prices_used_as_strategy_truth === false ? "false" : "unknown")}</span>
    `;
  }

  function historicalReadinessRows() {
    const ptRows = Array.isArray(state.pt002HistoricalReplay?.data_readiness)
      ? state.pt002HistoricalReplay.data_readiness
      : Array.isArray(state.pt002HistoricalReplay?.datasets)
        ? state.pt002HistoricalReplay.datasets
        : [];
    const sv202Rows = Array.isArray(state.sv202HistoricalReplay?.data_readiness)
      ? state.sv202HistoricalReplay.data_readiness
      : [];
    const sv20Rows = Array.isArray(state.sv20Summary?.data_readiness)
      ? state.sv20Summary.data_readiness
      : Array.isArray(state.sv20Summary?.datasets)
        ? state.sv20Summary.datasets
      : [];
    return [...sv202Rows, ...sv20Rows, ...ptRows];
  }

  function historicalReadinessForSelection() {
    return historicalReadinessRows().find(
      (row) =>
        (row.symbol || row.requested_symbol) === state.historicalReplay.symbol &&
        sameTimeframe(row.timeframe, state.historicalReplay.timeframe),
    );
  }

  function renderHistoricalDataHorizonPanel() {
    if (!elements.historicalReplayDataHorizonPanel) return;
    const selected = historicalReadinessForSelection();
    const canonicalEvidence = state.sv20Summary?.canonical_evidence_status || {};
    if (!selected) {
      setEmpty(elements.historicalReplayDataHorizonPanel, "Historical data horizon is unavailable for this selection.");
      return;
    }
    const aggregationCopy = selected.aggregation_used
      ? `1D candles aggregated from ${selected.aggregation_source_timeframe || "lower timeframe"} historical replay data.`
      : selected.component === "sleeve_1d"
        ? "SV2.0 treats 1D as a real Money Flow sleeve; source readiness is direct Hyperliquid public mainnet 1d candles when available."
        : "Candles loaded from historical replay source.";
    const rangeStart = selected.actual_earliest_available || selected.start_time || selected.earliest_candle || "missing";
    const rangeEnd = selected.actual_latest_available || selected.end_time || selected.latest_candle || "missing";
    const warnings = selected.reason_codes || [];
    const coverage = selected.target_coverage_percent ? pct(selected.target_coverage_percent) : selected.coverage_percent || "n/a";
    const source = selected.source_kind || selected.selected_data_source || selected.source || "historical source";
    elements.historicalReplayDataHorizonPanel.innerHTML = `
      <article class="historical-data-summary-card${warnings.length || selected.aggregation_used ? " warning" : ""}">
        <div class="historical-data-summary-heading">
          <div>
            <span>Historical data readiness</span>
            <strong>${escapeHtml(state.historicalReplay.symbol || "Symbol")} ${escapeHtml(displayTimeframe(state.historicalReplay.timeframe || "timeframe"))}</strong>
          </div>
          <small>${escapeHtml(selected.replay_ready ? "replay_ready" : "data_missing")}</small>
        </div>
        <dl class="historical-data-summary-grid">
          <div>
            <dt>Range</dt>
            <dd>${escapeHtml(`${rangeStart} -> ${rangeEnd}`)}</dd>
            <small>${escapeHtml(selected.component || "selected replay window")}</small>
          </div>
          <div>
            <dt>Coverage</dt>
            <dd>${escapeHtml(coverage)}</dd>
            <small>${escapeHtml(selected.candle_count ?? 0)} candles / target window</small>
          </div>
          <div>
            <dt>Source</dt>
            <dd>${escapeHtml(source)}</dd>
            <small>${escapeHtml(aggregationCopy)}</small>
          </div>
          <div>
            <dt>Canonical evidence</dt>
            <dd>${escapeHtml(canonicalEvidence.status || "not_loaded")}</dd>
            <small>${escapeHtml(selected.db_imported ? "DB imported through hardened candle importer" : "not DB imported")}</small>
          </div>
          <div class="historical-data-summary-warning-row">
            <dt>Warnings</dt>
            <dd>${escapeHtml(warnings.join(", ") || "none")}</dd>
            <small>Missing data is reported as data readiness, not strategy failure.</small>
          </div>
        </dl>
      </article>
    `;
  }

  function selectedHistoricalTrade(replay) {
    const trades = replay?.trades || [];
    if (!trades.length) return null;
    return (
      trades.find((trade) => trade.trade_id === state.historicalReplay.selectedTradeId) ||
      trades[0]
    );
  }

  function renderHistoricalTradeInspector(replay) {
    if (!elements.historicalTradeInspector) return;
    const trade = selectedHistoricalTrade(replay);
    if (!trade) {
      setEmpty(elements.historicalTradeInspector, "No historical replay trades for this selection.");
      return;
    }
    const entry = trade.entry_indicators || {};
    const exit = trade.exit_indicators || {};
    const entryReasons = Array.isArray(trade.entry_reason_codes) ? trade.entry_reason_codes : [];
    const exitReasons = Array.isArray(trade.exit_reason_codes) ? trade.exit_reason_codes : [];
    const reasonChips = (reasons, emptyLabel) => {
      const values = reasons.map((reason) => String(reason || "").trim()).filter(Boolean);
      if (!values.length) return `<span class="reason-chip muted">${escapeHtml(emptyLabel)}</span>`;
      return values.map((reason) => `<span class="reason-chip">${escapeHtml(reason)}</span>`).join("");
    };
    const metricTile = (label, value, detail = "") => `
      <article class="trade-inspector-metric">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(value)}</strong>
        ${detail ? `<small>${escapeHtml(detail)}</small>` : ""}
      </article>
    `;
    const pnlClass = decimal(trade.net_pnl) >= 0 ? "positive" : "negative";
    const exitReason = trade.exit_reason || exitReasons.join(", ") || "exit reason unavailable";
    const replayMode = trade.rebased_from_date_filter
      ? "fresh 10k date-window replay"
      : "historical replay only";
    elements.historicalTradeInspector.innerHTML = `
      <article class="trade-inspector-card overlay-inspector-card historical-replay-focus-card" aria-label="Selected historical replay trade">
        <span class="eyebrow">Trade Inspector Focus Mode</span>
        <h3>${escapeHtml(trade.symbol)} ${escapeHtml(displayTimeframe(trade.timeframe))} ${escapeHtml(String(trade.trade_id || "n/a").slice(0, 12))}</h3>
        <dl class="overlay-inspector-grid trade-inspector-focus-grid">
          <dt>Trade</dt><dd>${escapeHtml(String(trade.trade_id || "n/a").slice(0, 18))}</dd>
          <dt>Symbol</dt><dd>${escapeHtml(trade.symbol || "n/a")}</dd>
          <dt>Timeframe</dt><dd>${escapeHtml(displayTimeframe(trade.timeframe))}</dd>
          <dt>Fill assumption</dt><dd>${escapeHtml(trade.fill_timing || state.historicalReplay.fillAssumption || "n/a")}</dd>
          <dt>Entry fill</dt><dd>${escapeHtml(trade.entry_fill_time || "fill time n/a")}</dd>
          <dt>Exit fill</dt><dd>${escapeHtml(trade.exit_fill_time || "fill time n/a")}</dd>
          <dt>Entry price</dt><dd>${escapeHtml(`${compactNumber(trade.entry_price)} USDC`)}</dd>
          <dt>Exit price</dt><dd>${escapeHtml(`${compactNumber(trade.exit_price)} USDC`)}</dd>
          <dt>Net PnL</dt><dd class="${pnlClass}">${escapeHtml(money(trade.net_pnl))}</dd>
          <dt>Equity</dt><dd>${escapeHtml(`${money(trade.equity_before_trade)} -> ${money(trade.equity_after_trade)}`)}</dd>
          <dt>Drawdown</dt><dd>${escapeHtml(money(trade.drawdown_after_trade))}</dd>
          <dt>Exit reason</dt><dd>${escapeHtml(exitReason)}</dd>
          <dt>Mode</dt><dd>${escapeHtml(replayMode)}</dd>
          <dt>Boundary</dt><dd>${escapeHtml("not production approval / no orders")}</dd>
        </dl>

        <section class="trade-inspector-section">
          <h3>Why It Entered</h3>
          <div class="reason-chip-row">${reasonChips(entryReasons, "entry reason unavailable")}</div>
        </section>

        <section class="trade-inspector-section">
          <h3>Why It Exited</h3>
          <div class="reason-chip-row">${reasonChips(exitReasons, "exit reason unavailable")}</div>
        </section>

        <section class="trade-inspector-section">
          <h3>Entry Indicators</h3>
          <div class="trade-inspector-indicators">
            ${metricTile("RSI", compactNumber(entry.RSI))}
            ${metricTile("EMA5", compactNumber(entry.EMA5))}
            ${metricTile("EMA10", compactNumber(entry.EMA10))}
            ${metricTile("SMA20", compactNumber(entry.SMA20))}
            ${metricTile("MACD", compactNumber(entry.MACD))}
            ${metricTile("Signal", compactNumber(entry.MACD_signal))}
            ${metricTile("Histogram", compactNumber(entry.MACD_histogram))}
            ${metricTile("Regime", entry.market_regime || trade.market_regime || "n/a")}
          </div>
        </section>

        <section class="trade-inspector-section">
          <h3>Exit / Cost Context</h3>
          <div class="trade-inspector-indicators">
            ${metricTile("Exit RSI", compactNumber(exit.RSI))}
            ${metricTile("Fees", money(trade.fees), `${trade.fee_bps ?? "n/a"} bps`)}
            ${metricTile("Slippage", `${trade.slippage_bps ?? "n/a"} bps`)}
            ${metricTile("Gross PnL", trade.gross_pnl === null || trade.gross_pnl === undefined ? "n/a" : money(trade.gross_pnl))}
          </div>
        </section>
      </article>
    `;
  }

  function renderHistoricalEquityPanel(replay) {
    if (!elements.historicalReplayEquityPanel) return;
    const summary = replay?.summary || {};
    const curve = replay?.equity_curve || [];
    const selected = selectedHistoricalTrade(replay);
    elements.historicalReplayEquityPanel.innerHTML = `
      <article class="historical-equity-card">
        <span>Initial equity</span>
        <strong>${escapeHtml(money(summary.starting_equity || state.pt002HistoricalReplay?.initial_equity || 10000))}</strong>
        <small>${escapeHtml(historicalDateRange().active ? `fresh date-window replay: ${historicalDateRange().label}` : "historical paper replay")}</small>
      </article>
      <article class="historical-equity-card">
        <span>Ending equity</span>
        <strong>${escapeHtml(money(summary.ending_equity))}</strong>
        <small>dynamic equity path</small>
      </article>
      <article class="historical-equity-card">
        <span>Net PnL</span>
        <strong class="${decimal(summary.net_pnl) >= 0 ? "positive" : "negative"}">${escapeHtml(money(summary.net_pnl))}</strong>
        <small>fee/slippage included</small>
      </article>
      <article class="historical-equity-card">
        <span>Max drawdown</span>
        <strong>${escapeHtml(money(summary.max_drawdown))}</strong>
        <small>${escapeHtml(summary.max_drawdown_pct ? pct(summary.max_drawdown_pct) : "pct n/a")}</small>
      </article>
      <article class="historical-equity-card">
        <span>Trades</span>
        <strong>${escapeHtml(summary.trade_count ?? 0)}</strong>
        <small>win ${escapeHtml(summary.win_rate === null || summary.win_rate === undefined ? "n/a" : pct(summary.win_rate))}</small>
      </article>
      <article class="historical-equity-card">
        <span>Selected trade equity</span>
        <strong>${escapeHtml(selected ? `${money(selected.equity_before_trade)} -> ${money(selected.equity_after_trade)}` : "n/a")}</strong>
        <small>${escapeHtml(curve.length)} curve points / not live / not real capital</small>
      </article>
    `;
  }

  function renderHistoricalTradesTable(replay) {
    if (!elements.historicalReplayTradesTable) return;
    const trades = replay?.trades || [];
    if (!trades.length) {
      setEmpty(elements.historicalReplayTradesTable, "No trades in this replay scenario.");
      return;
    }
    elements.historicalReplayTradesTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Trade</th>
            <th>Entry Fill</th>
            <th>Exit Fill</th>
            <th>Entry</th>
            <th>Exit</th>
            <th>Net PnL</th>
            <th>Equity Before</th>
            <th>Equity After</th>
            <th>Exit Reason</th>
          </tr>
        </thead>
        <tbody>
          ${trades.slice(0, 80).map((trade) => `
            <tr class="${trade.trade_id === state.historicalReplay.selectedTradeId ? "active-row" : ""}" data-trade-id="${escapeHtml(trade.trade_id)}">
              <td><button class="text-row-button" type="button" data-trade-id="${escapeHtml(trade.trade_id)}">${escapeHtml(String(trade.trade_id || "").slice(0, 12))}</button></td>
              <td>${escapeHtml(trade.entry_fill_time || "n/a")}</td>
              <td>${escapeHtml(trade.exit_fill_time || "n/a")}</td>
              <td>${escapeHtml(compactNumber(trade.entry_price))}</td>
              <td>${escapeHtml(compactNumber(trade.exit_price))}</td>
              <td class="${decimal(trade.net_pnl) >= 0 ? "positive" : "negative"}">${escapeHtml(money(trade.net_pnl))}</td>
              <td>${escapeHtml(money(trade.equity_before_trade))}</td>
              <td>${escapeHtml(money(trade.equity_after_trade))}</td>
              <td>${escapeHtml((trade.exit_reason_codes || []).join(", "))}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
    elements.historicalReplayTradesTable.querySelectorAll("[data-trade-id]").forEach((target) => {
      target.addEventListener("click", () => {
        selectHistoricalReplayTrade(target.dataset.tradeId || null);
      });
    });
  }

  function renderHistoricalComparisonTable() {
    if (!elements.historicalComparisonTable) return;
    const rows = historicalReplays()
      .filter((row) => (row.strategy_id || "baseline_current_money_flow_rules") === state.historicalReplay.strategyId)
      .map((row) => sv202ComparisonRow(filteredHistoricalReplay(row)));
    if (!rows.length) {
      setEmpty(elements.historicalComparisonTable, "Historical comparison rows are not loaded.");
      return;
    }
    elements.historicalComparisonTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Timeframe</th>
            <th>Replay Strategy</th>
            <th>Status</th>
            <th>Ending Equity</th>
            <th>Net PnL</th>
            <th>Trades</th>
            <th>Win</th>
            <th>Max DD</th>
            <th>Primary Exit Reasons</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((row) => `
            <tr>
              <td>${escapeHtml(row.symbol)}</td>
              <td>${escapeHtml(displayTimeframe(row.timeframe))}</td>
              <td>${escapeHtml(dashboardStrategyLabel(row.strategy_label, row.strategy_id || "baseline_current_money_flow_rules"))}</td>
              <td>${escapeHtml(row.status)}</td>
              <td>${escapeHtml(money(row.ending_equity))}</td>
              <td class="${decimal(row.net_pnl) >= 0 ? "positive" : "negative"}">${escapeHtml(money(row.net_pnl))}</td>
              <td>${escapeHtml(row.trade_count ?? 0)}</td>
              <td>${escapeHtml(row.win_rate === null || row.win_rate === undefined ? "n/a" : pct(row.win_rate))}</td>
              <td>${escapeHtml(money(row.max_drawdown))}</td>
              <td>${escapeHtml((row.primary_exit_reasons || []).join(", ") || "n/a")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderHistoricalSandboxLedger() {
    if (!elements.historicalSandboxLedger) return;
    const rows = routedLedgerRecords();
    if (!rows.length) {
      setEmpty(elements.historicalSandboxLedger, "No sandbox execution ledger rows loaded. Historical replay remains independent.");
      return;
    }
    elements.historicalSandboxLedger.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Run</th>
            <th>Route</th>
            <th>Symbol</th>
            <th>Status</th>
            <th>Cancel</th>
            <th>Reconcile</th>
            <th>Sandbox / Not Live</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((row) => `
            <tr>
              <td>${escapeHtml(row.uat_run_id || row.run_id || "uat3.4")}</td>
              <td>${escapeHtml(String(row.route_id || "fixed_target_hyperliquid_testnet_eth").slice(0, 28))}</td>
              <td>${escapeHtml(row.symbol || "ETH")}</td>
              <td>${escapeHtml(row.lifecycle_status || "accepted_open -> canceled -> reconciled")}</td>
              <td>${escapeHtml(row.cancel_status || "success")}</td>
              <td>${escapeHtml(row.reconciliation_status || "reconciled")}</td>
              <td>${escapeHtml(row.no_live_no_paper_confirmation || "sandbox/testnet only; not live; not paper equity replay")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderHistoricalReplay() {
    renderHistoricalReplayFilters();
    renderHistoricalReplayBody();
  }

  function renderHistoricalReplayBody() {
    if (!historicalReplays().length) {
      [
        elements.historicalReplayChart,
        elements.historicalReplayDataHorizonPanel,
        elements.historicalTradeInspector,
        elements.historicalReplayTradesTable,
        elements.historicalComparisonTable,
        elements.historicalSandboxLedger,
      ].forEach((target) => {
        if (target) setEmpty(target, "Load regenerated SV2.0.2 dashboard chart data or PT historical replay JSON.");
      });
      return;
    }
    const baseReplay = selectedHistoricalReplay();
    if (baseReplay && (!state.historicalReplay.strategyId || !state.historicalReplay.symbol || !state.historicalReplay.timeframe)) {
      state.historicalReplay.strategyId = baseReplay.strategy_id || "money_flow_v1_2_canonical";
      state.historicalReplay.symbol = baseReplay.symbol || "ETH";
      state.historicalReplay.timeframe = canonicalTimeframe(baseReplay.timeframe || "1h");
    }
    const replay = filteredHistoricalReplay(baseReplay);
    renderHistoricalReplaySourceStatus(replay);
    renderHistoricalDataHorizonPanel();
    if (baseReplay && (!baseReplay.candles || !baseReplay.candles.length) && baseReplay.chart_data_path) {
      setEmpty(
        elements.historicalReplayChart,
        state.loadingHistoricalChartDataPaths.has(baseReplay.chart_data_path)
          ? "Loading selected MF-ORIG-EV2 chart data..."
          : "MF-ORIG-EV2 summary is loaded. Loading selected chart/trade JSON on demand.",
      );
      loadHistoricalReplayChartData(baseReplay.chart_data_path);
    } else if (replay) {
      renderHistoricalReplayChart(replay);
    } else {
      setEmpty(
        elements.historicalReplayChart,
        "No replay chart is loaded for this SV2.0 symbol/timeframe yet. Check the data horizon panel for support, import, and evidence readiness.",
      );
    }
    renderHistoricalTradeInspector(replay);
    renderHistoricalEquityPanel(replay);
    renderHistoricalTradesTable(replay);
    renderHistoricalComparisonTable();
    renderHistoricalSandboxLedger();
  }

  function sv202ComparisonRow(replay) {
    const exitReasons = {};
    (replay.trades || []).forEach((trade) => {
      (trade.exit_reason_codes || []).forEach((reason) => {
        exitReasons[reason] = (exitReasons[reason] || 0) + 1;
      });
    });
    const primaryExitReasons = Object.entries(exitReasons)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([reason]) => reason);
    return {
      symbol: replay.symbol,
      timeframe: replay.timeframe,
      strategy_id: replay.strategy_id,
      strategy_label: dashboardStrategyLabel(replay.strategy_label, replay.strategy_id),
      status: "canonical_evidence_ready",
      ending_equity: replay.summary?.ending_equity,
      net_pnl: replay.summary?.net_pnl,
      trade_count: replay.summary?.trade_count,
      win_rate: replay.summary?.win_rate,
      max_drawdown: replay.summary?.max_drawdown,
      primary_exit_reasons: primaryExitReasons,
    };
  }

  async function loadDefaultSv202DashboardChartData() {
    const sv202SummaryReplays = sv202SummaryReplaysFromBatches();
    const mfOrigSummaryReplays = mfOrigEv2SummaryReplays();
    const sorEv3Replays = sorEv3SummaryReplays();
    const allReplays = mergeReplayRows(mergeReplayRows(sv202SummaryReplays, mfOrigSummaryReplays), sorEv3Replays);
    if (!allReplays.length) return;
    const strategies = Array.from(
      new Map(
        allReplays
          .map((replay) => [
            replay.strategy_id || "money_flow_v1_2_canonical",
            {
              id: replay.strategy_id || "money_flow_v1_2_canonical",
              label: dashboardStrategyLabel(replay.strategy_label, replay.strategy_id || "money_flow_v1_2_canonical"),
              research_only: replay.research_only !== false,
            },
          ])
          .filter(([id]) => id),
      ).values(),
    );
    state.sv202HistoricalReplay = {
      report: "sv2_0_2_and_mf_orig_ev2_dashboard_historical_replay_combined",
      source: "SV2.0.2 regenerated canonical DB-imported evidence packs plus MF-ORIG-EV2 compact summaries with lazy selected-chart loading",
      symbols: Array.from(new Set(allReplays.map((row) => row.symbol).filter(Boolean))).sort(),
      timeframes: Array.from(new Set(allReplays.map((row) => canonicalTimeframe(row.timeframe)).filter(Boolean))),
      fill_assumptions: Array.from(new Set(allReplays.map((row) => row.fill_assumption).filter(Boolean))).map((id) => ({
        id,
        research_only: false,
      })),
      strategies,
      data_readiness: [],
      comparison: allReplays.map(sv202ComparisonRow),
      replays: allReplays,
    };
    if (!selectedHistoricalReplay() && allReplays.length) {
      state.historicalReplay.strategyId = allReplays[0].strategy_id || "money_flow_v1_2_canonical";
      state.historicalReplay.symbol = allReplays[0].symbol || "ETH";
      state.historicalReplay.timeframe = canonicalTimeframe(allReplays[0].timeframe || "4h");
      state.historicalReplay.fillAssumption = allReplays[0].fill_assumption || "next_candle_open";
    }
  }

  async function loadHistoricalReplayChartData(path) {
    if (!path || state.loadedHistoricalChartDataPaths.has(path) || state.loadingHistoricalChartDataPaths.has(path)) return;
    state.loadingHistoricalChartDataPaths.add(path);
    try {
      const response = await fetch(path, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      if (classifyJson(payload) !== "sv202_dashboard_chart_data") {
        throw new Error("Unsupported chart-data payload");
      }
      const existing = state.sv202HistoricalReplay?.replays || [];
      state.sv202HistoricalReplay = {
        ...(state.sv202HistoricalReplay || {}),
        data_readiness: [
          ...(state.sv202HistoricalReplay?.data_readiness || []),
          payload.dataset,
        ].filter(Boolean),
        comparison: mergeReplayRows(existing, payload.replays || []).map(sv202ComparisonRow),
        replays: mergeReplayRows(existing, (payload.replays || []).map((row) => ({
          ...row,
          chart_data_path: path,
          chart_data_lazy: false,
        }))),
      };
      state.loadedHistoricalChartDataPaths.add(path);
    } catch (error) {
      console.warn(`Could not load selected historical chart data ${path}`, error);
    } finally {
      state.loadingHistoricalChartDataPaths.delete(path);
      if (state.activeView === "evidence") {
        render();
      } else {
        renderHistoricalReplayBody();
      }
    }
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
        labels: "paper observation scanner; internal paper-equity scanner; sandbox/testnet only; not live; not real capital; no order artifact",
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

  function unavailable(value = "data_not_available_in_sor_ev_bundle") {
    return value;
  }

  function hasOwnValue(row, key) {
    return row && Object.prototype.hasOwnProperty.call(row, key) && row[key] !== null && row[key] !== undefined && row[key] !== "";
  }

  function formatEvidenceNumber(row, key, digits = 2) {
    if (!hasOwnValue(row, key)) return unavailable();
    return compactNumber(row[key], digits);
  }

  function formatEvidenceMoney(row, key) {
    if (!hasOwnValue(row, key)) return unavailable();
    return money(row[key]);
  }

  function sorVariantFamily(rowOrId) {
    const id = String(rowOrId?.variant_family || rowOrId?.variant_id || rowOrId || "").toLowerCase();
    if (id.includes("fixed_stop")) return "fixed_stop_loss";
    if (id.includes("atr")) return "atr_stop";
    if (id.includes("recent_low")) return "recent_low_stop";
    if (id.includes("large_bear") || id.includes("large_red")) return "large_bear_candle_exit";
    if (id.includes("chop") || id.includes("sideways")) return "chop_filter";
    if (id.includes("macd")) return "earlier_macd_entry";
    if (id.includes("lower_rsi") || id.includes("rsi")) return "lower_rsi_trend_intact_entry";
    if (id.includes("extension") || id.includes("ema10") || id.includes("sma20")) return "extension_filter";
    return unavailable("unknown_variant_family");
  }

  function sorOutcomeTaxonomy(row, ev2Summary) {
    const outcome = String(row?.outcome || "").toLowerCase();
    if (row?.candidate_evidence === true) return "candidate_for_more_evidence";
    if (outcome.includes("overfit")) return "overfit_risk";
    if (outcome.includes("insufficient")) return "insufficient_data";
    if (outcome.includes("no_op")) return "no_op";
    if (outcome.includes("deteriorated")) return "deteriorated_vs_baseline";
    if (outcome.includes("reject")) return "rejected_negative_aggregate";
    if (row?.production_approved === false) return "not_promoted";
    return unavailable("candidate_status_not_in_bundle");
  }

  function evidenceLabMetricValue(row, keys) {
    for (const key of keys) {
      if (hasOwnValue(row, key)) {
        const value = Number(row[key]);
        if (Number.isFinite(value)) return value;
      }
    }
    return null;
  }

  function evidenceLabVariantReview(row, control, taxonomy) {
    const methodology = String(row?.methodology || "");
    const family = sorVariantFamily(row);
    const pnl = evidenceLabMetricValue(row, [
      "net_pnl_delta_sum_across_independent_scenarios",
      "ending_equity_delta_sum_across_independent_scenarios",
      "net_pnl_delta_sum",
    ]);
    const drawdownDelta = evidenceLabMetricValue(row, ["max_drawdown_delta_worst", "max_drawdown_delta"]);
    const tradeDelta = evidenceLabMetricValue(row, ["trade_count_delta_sum"]) || 0;
    const damaged = Number(control?.damaged ?? 0);
    let label = "not_promoted_insufficient_data";
    if (row?.candidate_evidence === true) {
      label = "candidate_for_more_evidence";
    } else if (methodology === "deferred_requires_rejected_signal_replay") {
      label = "deferred_needs_true_forward_replay";
    } else if (methodology !== "true_forward_replay") {
      label = pnl && pnl > 0 ? "promising_diagnostic_only" : "not_promoted_insufficient_data";
    } else if (taxonomy === "no_op" || pnl === 0) {
      label = "not_promoted_no_op";
    } else if (pnl !== null && pnl < 0) {
      label = "rejected_negative_aggregate";
    } else if (pnl !== null && pnl >= 20000 && damaged === 0) {
      label = Math.abs(tradeDelta) >= 1000
        ? "promising_high_pnl_control_preserved_trade_count_risk"
        : "promising_high_pnl_control_preserved";
    } else if (pnl !== null && pnl >= 20000 && family === "extension_filter") {
      label = "promising_extension_filter_overfit_risk";
    } else if (pnl !== null && pnl > 0 && family === "chop_filter") {
      label = "promising_chop_filter_control_risk";
    } else if (pnl !== null && pnl > 0 && damaged > 0) {
      label = "mixed_positive_pnl_control_damage";
    } else if (pnl !== null && pnl > 0 && drawdownDelta !== null && drawdownDelta > 0) {
      label = pnl < 2500 ? "mixed_small_pnl_drawdown_risk" : "mixed_positive_pnl_drawdown_risk";
    } else if (taxonomy === "insufficient_data") {
      label = "not_promoted_insufficient_data";
    }
    const status = label === "candidate_for_more_evidence"
      ? "candidate_for_more_evidence"
      : label.startsWith("promising_")
        ? "promising_not_promoted"
        : label.startsWith("mixed_")
          ? "mixed_not_promoted"
          : label.startsWith("rejected_")
            ? "rejected"
            : label.startsWith("deferred_")
              ? "deferred"
              : "not_promoted";
    const blockers = [];
    if (methodology !== "true_forward_replay") blockers.push("not_true_forward_replay");
    if (drawdownDelta !== null && drawdownDelta > 0) blockers.push("worst_drawdown_worsened");
    if (damaged > 0) blockers.push("control_pockets_damaged");
    if (Math.abs(tradeDelta) >= 1000) blockers.push("large_trade_count_change");
    if (taxonomy === "overfit_risk") blockers.push("overfit_risk");
    if (taxonomy === "insufficient_data") blockers.push("insufficient_data");
    if (taxonomy === "no_op") blockers.push("no_op");
    if (label.startsWith("rejected_")) blockers.push("negative_aggregate_pnl");
    return {
      label,
      status,
      blockers: blockers.length ? blockers : ["strict_candidate_gate_not_passed"],
      explanation: SOR_EV3_FOUNDER_LABEL_HELP[label] || "Evidence-only review label; no production approval.",
    };
  }

  function sorVariantRows() {
    const ev1Rows = Array.isArray(state.sorEv1Summary?.variant_summary) ? state.sorEv1Summary.variant_summary : [];
    const ev2Rows = Array.isArray(state.sorEv2Summary?.variant_summary) ? state.sorEv2Summary.variant_summary : [];
    const ev1ById = new Map(ev1Rows.map((row) => [row.variant_id, row]));
    const ev2ById = new Map(ev2Rows.map((row) => [row.variant_id, row]));
    return Array.from(new Set([...ev1ById.keys(), ...ev2ById.keys()]))
      .sort()
      .map((id) => ({
        id,
        ev1: ev1ById.get(id) || null,
        ev2: ev2ById.get(id) || null,
        row: ev2ById.get(id) || ev1ById.get(id) || { variant_id: id },
      }));
  }

  function replayFillAssumption(replay) {
    return replay?.fill_assumption || replay?.trades?.[0]?.fill_timing || "next_candle_open";
  }

  function selectedEvidenceLabVariant() {
    return sorVariantRows().find(({ id }) => id === state.evidenceLabOverlay.variantId) || sorVariantRows()[0] || null;
  }

  function selectedEvidenceLabReplay() {
    return (state.sv202HistoricalReplay?.replays || []).find(
      (row) =>
        row.symbol === state.evidenceLabOverlay.symbol &&
        sameTimeframe(row.timeframe, state.evidenceLabOverlay.timeframe) &&
        replayFillAssumption(row) === state.evidenceLabOverlay.fillAssumption,
    ) || null;
  }

  function selectedEvidenceLabContextSamples() {
    return (state.sorEv2Summary?.large_loss_candle_context_samples || []).filter(
      (row) =>
        row.symbol === state.evidenceLabOverlay.symbol &&
        sameTimeframe(row.timeframe, state.evidenceLabOverlay.timeframe) &&
        row.fill_timing === state.evidenceLabOverlay.fillAssumption,
    );
  }

  function selectedEvidenceLabWorstTrades() {
    return (state.sorEv1Summary?.worst_trades || []).filter(
      (row) =>
        row.symbol === state.evidenceLabOverlay.symbol &&
        sameTimeframe(row.timeframe, state.evidenceLabOverlay.timeframe) &&
        row.fill_timing === state.evidenceLabOverlay.fillAssumption,
    );
  }

  function evidenceLabVariantResultForSelection() {
    return (state.sorEv2Summary?.variant_results || []).find(
      (row) =>
        row.variant_id === state.evidenceLabOverlay.variantId &&
        row.symbol === state.evidenceLabOverlay.symbol &&
        sameTimeframe(row.timeframe, state.evidenceLabOverlay.timeframe) &&
        row.fill_timing === state.evidenceLabOverlay.fillAssumption,
    ) || null;
  }

  function evidenceLabControlPocketForVariant() {
    return (state.sorEv2Summary?.control_pocket_impact || state.sorEv1Summary?.control_pocket_impact || []).find(
      (row) => row.variant_id === state.evidenceLabOverlay.variantId,
    ) || null;
  }

  function evidenceLabOverlayKey() {
    const overlay = state.evidenceLabOverlay;
    return [
      overlay.symbol,
      canonicalTimeframe(overlay.timeframe),
      overlay.fillAssumption,
      overlay.variantId,
      overlay.overlayMode,
      overlay.showLargeLossTrades,
      overlay.showStopExits,
      overlay.showLateExtensionEntries,
      overlay.showAdverseCandles,
      overlay.showMaBreaks,
      overlay.hideBaselineMarkers,
      overlay.selectedWorstTradeId || "none",
    ].join("|");
  }

  function renderSelectWithoutAll(select, values, activeValue) {
    if (!select) return;
    const normalized = values.map((value) =>
      typeof value === "object" && value !== null
        ? { value: value.value, label: value.label || value.value }
        : { value, label: displayTimeframe(value) },
    );
    select.innerHTML = normalized
      .map((row) => `<option value="${escapeHtml(row.value)}">${escapeHtml(row.label)}</option>`)
      .join("");
    if (normalized.some((row) => row.value === activeValue)) {
      select.value = activeValue;
    } else if (normalized[0]) {
      select.value = normalized[0].value;
    }
  }

  function evidenceLabOverlaySymbols() {
    const symbols = uniqueSorted([
      ...SV202_CANONICAL_SYMBOLS,
      ...(state.sv202HistoricalReplay?.symbols || []),
    ]);
    return symbols.length ? symbols : ["ETH"];
  }

  function evidenceLabOverlayTimeframes() {
    const timeframes = uniqueSorted([
      ...SV202_CANONICAL_TIMEFRAMES,
      ...(state.sv202HistoricalReplay?.timeframes || []),
    ].map(canonicalTimeframe));
    return timeframes.length ? timeframes : ["1h"];
  }

  function evidenceLabOverlayFillAssumptions() {
    const fills = uniqueSorted(
      (state.sv202HistoricalReplay?.replays || []).map(replayFillAssumption),
    );
    return fills.length ? fills : ["next_candle_open", "next_candle_close"];
  }

  function evidenceLabVariantOptions() {
    const variants = sorVariantRows().map(({ id }) => ({ value: id, label: id }));
    return variants.length ? variants : [{ value: "data_not_available_in_sor_ev_bundle", label: "data_not_available_in_sor_ev_bundle" }];
  }

  function syncEvidenceLabOverlaySelection() {
    const symbols = evidenceLabOverlaySymbols();
    const timeframes = evidenceLabOverlayTimeframes();
    const fills = evidenceLabOverlayFillAssumptions();
    const variants = evidenceLabVariantOptions().map((row) => row.value);
    if (!symbols.includes(state.evidenceLabOverlay.symbol)) state.evidenceLabOverlay.symbol = symbols[0] || "ETH";
    if (!timeframes.includes(canonicalTimeframe(state.evidenceLabOverlay.timeframe))) {
      state.evidenceLabOverlay.timeframe = timeframes.includes("1h") ? "1h" : timeframes[0] || "1h";
    }
    if (!fills.includes(state.evidenceLabOverlay.fillAssumption)) {
      state.evidenceLabOverlay.fillAssumption = fills[0] || "next_candle_open";
    }
    if (!variants.includes(state.evidenceLabOverlay.variantId)) {
      state.evidenceLabOverlay.variantId = variants[0] || "data_not_available_in_sor_ev_bundle";
    }
  }

  function renderEvidenceLabOverlayControls() {
    syncEvidenceLabOverlaySelection();
    renderSelectWithoutAll(elements.evidenceLabOverlaySymbol, evidenceLabOverlaySymbols(), state.evidenceLabOverlay.symbol);
    renderSelectWithoutAll(
      elements.evidenceLabOverlayTimeframe,
      evidenceLabOverlayTimeframes().map((value) => ({ value, label: displayTimeframe(value) })),
      canonicalTimeframe(state.evidenceLabOverlay.timeframe),
    );
    renderSelectWithoutAll(elements.evidenceLabOverlayFill, evidenceLabOverlayFillAssumptions(), state.evidenceLabOverlay.fillAssumption);
    renderSelectWithoutAll(elements.evidenceLabOverlayVariant, evidenceLabVariantOptions(), state.evidenceLabOverlay.variantId);
    if (elements.evidenceLabOverlayMode) elements.evidenceLabOverlayMode.value = state.evidenceLabOverlay.overlayMode;
    [
      [elements.evidenceLabToggleLargeLoss, "showLargeLossTrades"],
      [elements.evidenceLabToggleStopExits, "showStopExits"],
      [elements.evidenceLabToggleLateExtension, "showLateExtensionEntries"],
      [elements.evidenceLabToggleAdverseCandles, "showAdverseCandles"],
      [elements.evidenceLabToggleMaBreaks, "showMaBreaks"],
      [elements.evidenceLabToggleHideBaselineEntries, "hideBaselineMarkers"],
    ].forEach(([element, key]) => {
      if (element) element.checked = Boolean(state.evidenceLabOverlay[key]);
    });

    if (elements.evidenceLabOverlaySymbol) {
      elements.evidenceLabOverlaySymbol.onchange = () => {
        state.evidenceLabOverlay.symbol = elements.evidenceLabOverlaySymbol.value;
        state.evidenceLabOverlay.selectedWorstTradeId = null;
        renderEvidenceLabChartOverlay();
      };
    }
    if (elements.evidenceLabOverlayTimeframe) {
      elements.evidenceLabOverlayTimeframe.onchange = () => {
        state.evidenceLabOverlay.timeframe = canonicalTimeframe(elements.evidenceLabOverlayTimeframe.value);
        state.evidenceLabOverlay.selectedWorstTradeId = null;
        renderEvidenceLabChartOverlay();
      };
    }
    if (elements.evidenceLabOverlayFill) {
      elements.evidenceLabOverlayFill.onchange = () => {
        state.evidenceLabOverlay.fillAssumption = elements.evidenceLabOverlayFill.value;
        state.evidenceLabOverlay.selectedWorstTradeId = null;
        renderEvidenceLabChartOverlay();
      };
    }
    if (elements.evidenceLabOverlayVariant) {
      elements.evidenceLabOverlayVariant.onchange = () => {
        state.evidenceLabOverlay.variantId = elements.evidenceLabOverlayVariant.value;
        renderEvidenceLabChartOverlay();
      };
    }
    if (elements.evidenceLabOverlayMode) {
      elements.evidenceLabOverlayMode.onchange = () => {
        state.evidenceLabOverlay.overlayMode = elements.evidenceLabOverlayMode.value;
        renderEvidenceLabChartOverlay();
      };
    }
    [
      [elements.evidenceLabToggleLargeLoss, "showLargeLossTrades"],
      [elements.evidenceLabToggleStopExits, "showStopExits"],
      [elements.evidenceLabToggleLateExtension, "showLateExtensionEntries"],
      [elements.evidenceLabToggleAdverseCandles, "showAdverseCandles"],
      [elements.evidenceLabToggleMaBreaks, "showMaBreaks"],
      [elements.evidenceLabToggleHideBaselineEntries, "hideBaselineMarkers"],
    ].forEach(([element, key]) => {
      if (element) {
        element.onchange = () => {
          state.evidenceLabOverlay[key] = element.checked;
          renderEvidenceLabChartOverlay();
        };
      }
    });
    if (elements.evidenceLabClearFocus) {
      elements.evidenceLabClearFocus.disabled = !state.evidenceLabOverlay.selectedWorstTradeId;
      elements.evidenceLabClearFocus.onclick = () => {
        state.evidenceLabOverlay.selectedWorstTradeId = null;
        renderEvidenceLabChartOverlay();
      };
    }
  }

  function evidenceLabVariantMethodology() {
    const variant = selectedEvidenceLabVariant();
    return variant?.row?.methodology || unavailable();
  }

  function evidenceLabVariantIsTrueForward() {
    return evidenceLabVariantMethodology() === "true_forward_replay";
  }

  function renderEvidenceLabOverlayMethodology() {
    if (!elements.evidenceLabOverlayMethodology) return;
    const variant = selectedEvidenceLabVariant();
    const methodology = evidenceLabVariantMethodology();
    const diagnosticLabel = evidenceLabVariantIsTrueForward() ? "candidate methodology" : "diagnostic_only_not_candidate";
    elements.evidenceLabOverlayMethodology.innerHTML = `
      <strong>Selected variant:</strong> ${escapeHtml(variant?.id || unavailable())}
      <span>Methodology: ${escapeHtml(methodology)}</span>
      <span>${escapeHtml(diagnosticLabel)}</span>
      <span>Only true_forward_replay variants can become candidates for deeper evidence. Completed-trade overlays and lookahead diagnostics are not production candidates. No variant is approved for production, paper runtime, or live trading.</span>
    `;
  }

  function destroyEvidenceLabOverlayChart() {
    const chartState = state.evidenceLabOverlayChart;
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
    chartState.markerIds = new Map();
    chartState.key = null;
    chartState.ready = false;
  }

  function resizeEvidenceLabOverlayChart() {
    const chartState = state.evidenceLabOverlayChart;
    if (!chartState.chart || !chartState.mount) return;
    const { width, height } = chartDimensions(chartState.mount);
    chartState.chart.resize(width, height);
  }

  function scheduleEvidenceLabOverlayChartResize() {
    const chartState = state.evidenceLabOverlayChart;
    if (!chartState.chart || !chartState.mount) return;
    if (chartState.pendingResizeFrame) return;
    const raf = typeof window.requestAnimationFrame === "function"
      ? window.requestAnimationFrame
      : (callback) => window.setTimeout(callback, 16);
    chartState.pendingResizeFrame = raf(() => {
      chartState.pendingResizeFrame = null;
      resizeEvidenceLabOverlayChart();
    });
  }

  function evidenceLabTradeById(replay, tradeId) {
    if (!tradeId) return null;
    return (replay?.trades || []).find((trade) => trade.trade_id === tradeId) || null;
  }

  function evidenceLabSelectedWorstTrade() {
    const selectedId = state.evidenceLabOverlay.selectedWorstTradeId;
    const selected = selectedId
      ? (state.sorEv1Summary?.worst_trades || []).find((row) => row.trade_id === selectedId)
      : null;
    return selected || selectedEvidenceLabWorstTrades()[0] || (state.sorEv1Summary?.worst_trades || [])[0] || null;
  }

  function evidenceLabSelectedContextSample() {
    const tradeId = evidenceLabSelectedWorstTrade()?.trade_id;
    const rows = selectedEvidenceLabContextSamples();
    return rows.find((row) => row.trade_id === tradeId) || rows[0] || null;
  }

  function evidenceLabMarkerId(prefix, row, timestamp, index = 0) {
    const raw = [
      prefix,
      row?.trade_id || row?.variant_id || row?.marker_type || "context",
      timestamp,
      index,
    ].join("-");
    return `evidence-lab-marker-${raw.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
  }

  function evidenceLabBaselineMarkers(replay, candles, markerIds) {
    if (state.evidenceLabOverlay.overlayMode === "variant") return [];
    const firstTime = candles[0]?.time;
    const lastTime = candles.at(-1)?.time;
    if (!Number.isFinite(firstTime) || !Number.isFinite(lastTime)) return [];
    return (replay?.markers || [])
      .flatMap((marker, index) => {
        const parsed = chartTime(marker.time);
        if (parsed < firstTime || parsed > lastTime) return [];
        if (state.evidenceLabOverlay.hideBaselineMarkers) return [];
        const trade = evidenceLabTradeById(replay, marker.trade_id);
        const markerType = String(marker.marker_type || "");
        const isEntry = markerType.includes("entry") || marker.color_role === "green";
        const isForcedClose = Boolean(trade?.forced_exit) && markerType.includes("exit");
        const text = isEntry
          ? "baseline entry"
          : isForcedClose
            ? `baseline forced close ${money(trade?.net_pnl ?? marker.net_pnl)}`
            : `baseline exit ${money(trade?.net_pnl ?? marker.net_pnl)}`;
        const id = evidenceLabMarkerId("baseline", marker, parsed, index);
        if (marker.trade_id) markerIds.set(id, { type: "baseline", tradeId: marker.trade_id });
        return [{
          id,
          time: parsed,
          position: isEntry ? "belowBar" : "aboveBar",
          color: isEntry ? "#25d084" : isForcedClose ? "#f8c15c" : "#ff5a66",
          shape: isEntry ? "arrowUp" : isForcedClose ? "circle" : "arrowDown",
          text,
        }];
      });
  }

  function evidenceLabLateEntryMarkers(candles, markerIds) {
    if (!state.evidenceLabOverlay.showLateExtensionEntries) return [];
    const firstTime = candles[0]?.time;
    const lastTime = candles.at(-1)?.time;
    return selectedEvidenceLabWorstTrades()
      .filter((row) => String(row.entry_timing_classification || "").includes("late_extension"))
      .flatMap((row, index) => {
        const parsed = chartTime(row.entry_time);
        if (parsed < firstTime || parsed > lastTime) return [];
        const id = evidenceLabMarkerId("late-extension", row, parsed, index);
        markerIds.set(id, { type: "worst_trade", tradeId: row.trade_id });
        return [{
          id,
          time: parsed,
          position: "belowBar",
          color: FOUNDER_REVIEW_MARKER_COLOR,
          shape: "arrowUp",
          text: `late-extension entry ${money(row.net_pnl)}`,
        }];
      });
  }

  function evidenceLabAdverseContextMarkers(candles, markerIds) {
    const firstTime = candles[0]?.time;
    const lastTime = candles.at(-1)?.time;
    const selectedFamily = sorVariantFamily(selectedEvidenceLabVariant()?.row || state.evidenceLabOverlay.variantId);
    const supportsStopContext = [
      "fixed_stop_loss",
      "atr_stop",
      "recent_low_stop",
      "large_bear_candle_exit",
    ].includes(selectedFamily);
    return selectedEvidenceLabContextSamples().flatMap((row, index) => {
      const parsed = chartTime(row.largest_red_candle_close_time);
      if (parsed < firstTime || parsed > lastTime) return [];
      const markers = [];
      if (state.evidenceLabOverlay.showAdverseCandles) {
        const id = evidenceLabMarkerId("adverse-candle", row, parsed, index);
        markerIds.set(id, { type: "context", tradeId: row.trade_id });
        markers.push({
          id,
          time: parsed,
          position: "aboveBar",
          color: FOUNDER_REVIEW_MARKER_COLOR,
          shape: "arrowDown",
          text: "large adverse candle",
        });
      }
      if (state.evidenceLabOverlay.showStopExits && supportsStopContext && row.stop_would_have_triggered_before_current_exit) {
        const id = evidenceLabMarkerId("variant-stop-context", row, parsed, index);
        markerIds.set(id, { type: "context", tradeId: row.trade_id });
        markers.push({
          id,
          time: parsed,
          position: "aboveBar",
          color: FOUNDER_REVIEW_MARKER_COLOR,
          shape: "arrowDown",
          text: `${state.evidenceLabOverlay.variantId} stop context`,
        });
      }
      return markers;
    });
  }

  function evidenceLabWorstTradeFocusMarkers(candles, markerIds) {
    if (!state.evidenceLabOverlay.showLargeLossTrades) return [];
    const selected = evidenceLabSelectedWorstTrade();
    if (!selected) return [];
    const firstTime = candles[0]?.time;
    const lastTime = candles.at(-1)?.time;
    const entryTime = chartTime(selected.entry_time);
    const exitTime = chartTime(selected.exit_time);
    return [
      {
        time: entryTime,
        position: "belowBar",
        color: FOUNDER_REVIEW_MARKER_COLOR,
        shape: "arrowUp",
        text: `selected worst entry ${money(selected.net_pnl)}`,
      },
      {
        time: exitTime,
        position: "aboveBar",
        color: FOUNDER_REVIEW_MARKER_COLOR,
        shape: "arrowDown",
        text: `selected worst exit ${money(selected.net_pnl)}`,
      },
    ].flatMap((marker, index) => {
      if (marker.time < firstTime || marker.time > lastTime) return [];
      const id = evidenceLabMarkerId("worst-focus", selected, marker.time, index);
      markerIds.set(id, { type: "worst_trade", tradeId: selected.trade_id });
      return [{ ...marker, id }];
    });
  }

  function evidenceLabVariantMarkers(replay, candles, markerIds) {
    if (state.evidenceLabOverlay.overlayMode === "baseline") return [];
    return [
      ...evidenceLabWorstTradeFocusMarkers(candles, markerIds),
      ...evidenceLabAdverseContextMarkers(candles, markerIds),
      ...evidenceLabLateEntryMarkers(candles, markerIds),
    ].sort((a, b) => a.time - b.time);
  }

  function evidenceLabOverlayMarkers(replay, candles, markerIds = new Map()) {
    markerIds.clear();
    return [
      ...evidenceLabBaselineMarkers(replay, candles, markerIds),
      ...evidenceLabVariantMarkers(replay, candles, markerIds),
    ].sort((a, b) => a.time - b.time);
  }

  function evidenceLabOverlayClickTradeId(param, replay) {
    const objectId = param?.hoveredObjectId || param?.hoveredObject?.id || null;
    const markerRef = objectId ? state.evidenceLabOverlayChart.markerIds?.get(objectId) : null;
    if (markerRef?.tradeId) return markerRef.tradeId;
    const clickedTime = lightweightChartTimeToUnix(param?.time);
    if (!Number.isFinite(clickedTime)) return null;
    const marker = (replay?.markers || []).find((row) => row.trade_id && chartTime(row.time) === clickedTime);
    return marker?.trade_id || null;
  }

  function selectEvidenceLabWorstTrade(tradeId) {
    if (!tradeId) return;
    const worst = (state.sorEv1Summary?.worst_trades || []).find((row) => row.trade_id === tradeId);
    if (worst) {
      state.evidenceLabOverlay.symbol = worst.symbol || state.evidenceLabOverlay.symbol;
      state.evidenceLabOverlay.timeframe = canonicalTimeframe(worst.timeframe || state.evidenceLabOverlay.timeframe);
      state.evidenceLabOverlay.fillAssumption = worst.fill_timing || state.evidenceLabOverlay.fillAssumption;
    }
    state.evidenceLabOverlay.selectedWorstTradeId = tradeId;
    renderEvidenceLabChartOverlay();
  }

  function focusEvidenceLabOverlayWindow(replay) {
    const chartState = state.evidenceLabOverlayChart;
    const selected = evidenceLabSelectedWorstTrade();
    if (!chartState.chart || !selected || !state.evidenceLabOverlay.selectedWorstTradeId) return;
    const candles = historicalChartCandles(replay);
    if (!candles.length) return;
    const entryTime = chartTime(selected.entry_time);
    const exitTime = chartTime(selected.exit_time);
    const entryIndex = candles.findIndex((row) => row.time >= entryTime);
    const exitIndex = candles.findIndex((row) => row.time >= exitTime);
    if (entryIndex < 0 || exitIndex < 0) return;
    const from = Math.max(0, entryIndex - 24);
    const to = Math.min(candles.length - 1, exitIndex + 24);
    const timeScale = chartState.chart.timeScale?.();
    if (typeof timeScale?.setVisibleLogicalRange === "function") {
      timeScale.setVisibleLogicalRange({ from, to });
    }
  }

  function updateEvidenceLabOverlayChartData(replay, candles) {
    const chartState = state.evidenceLabOverlayChart;
    if (!chartState.candleSeries || !chartState.volumeSeries) return;
    chartState.candleSeries.setData(chartPriceRows(candles));
    chartState.volumeSeries.setData(chartVolumeRows(candles));
    ["EMA5", "EMA10", "SMA20"].forEach((label) => {
      chartState.indicatorSeries[label]?.setData(historicalIndicatorRows(replay, label));
    });
    const markers = evidenceLabOverlayMarkers(replay, candles, chartState.markerIds || new Map());
    if (chartState.markerHandle && typeof chartState.markerHandle.setMarkers === "function") {
      chartState.markerHandle.setMarkers(markers);
    } else if (typeof chartState.candleSeries.setMarkers === "function") {
      chartState.candleSeries.setMarkers(markers);
    }
    focusEvidenceLabOverlayWindow(replay);
    scheduleEvidenceLabOverlayChartResize();
  }

  function renderEvidenceLabOverlayChart() {
    const tv = lightweightCharts();
    if (!elements.evidenceLabChartOverlay || !tv) return false;
    const replay = selectedEvidenceLabReplay();
    const candles = historicalChartCandles(replay);
    if (!replay || !candles.length) {
      destroyEvidenceLabOverlayChart();
      setEmpty(elements.evidenceLabChartOverlay, "data_not_available_in_sor_ev_bundle");
      return false;
    }
    const chartState = state.evidenceLabOverlayChart;
    const chartKey = evidenceLabOverlayKey();
    if (chartState.ready && chartState.key === chartKey && chartState.chart && chartState.candleSeries && chartState.volumeSeries) {
      updateEvidenceLabOverlayChartData(replay, candles);
      return true;
    }

    destroyEvidenceLabOverlayChart();
    const priceStats = chartPriceStats(candles);
    elements.evidenceLabChartOverlay.innerHTML = `
      <div class="tradingview-chart-topline">
        <div>
          <strong>${escapeHtml(state.evidenceLabOverlay.symbol)}-PERP baseline vs variant overlay</strong>
          <span>${escapeHtml(displayTimeframe(state.evidenceLabOverlay.timeframe))} / ${escapeHtml(state.evidenceLabOverlay.fillAssumption)} / canonical SV2.0.2 visualization context</span>
        </div>
        <aside class="chart-price-axis-readout chart-price-axis-readout-inline" aria-label="Evidence Lab price scale">
          <span>Historical price USDC</span>
          <strong>${escapeHtml(priceStats.latest)}</strong>
          <small>H ${escapeHtml(priceStats.high)}</small>
          <small>L ${escapeHtml(priceStats.low)}</small>
          <small>O ${escapeHtml(priceStats.open)}</small>
          <small>C ${escapeHtml(priceStats.close)}</small>
        </aside>
      </div>
      <div class="tradingview-chart-stage evidence-lab-chart-stage">
        <div class="tradingview-lightweight-chart" role="img" aria-label="Evidence Lab baseline and variant marker overlay chart"></div>
      </div>
      <div class="historical-overlay-legend">
        <span><b class="legend-dot entry"></b>baseline entry</span>
        <span><b class="legend-dot exit"></b>baseline exit</span>
        <span><b class="legend-dot trim"></b>forced close</span>
        <span><b class="legend-dot founder-review"></b>founder-review feature</span>
        <span>Use Hide baseline entries/exits to review founder features without baseline marker noise.</span>
      </div>
      <div class="tradingview-attribution">Charts: TradingView Lightweight Charts v${TRADINGVIEW_LIGHTWEIGHT_CHARTS_VERSION} (Apache-2.0). Overlay data is display-only and does not regenerate canonical evidence.</div>
    `;
    const mount = elements.evidenceLabChartOverlay.querySelector(".tradingview-lightweight-chart");
    const { width, height } = chartDimensions(mount);
    const chartColors = dashboardChartColors();
    const chart = tv.createChart(mount, {
      width,
      height,
      layout: {
        background: { type: tv.ColorType.Solid, color: chartColors.background },
        textColor: chartColors.text,
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: chartColors.grid },
        horzLines: { color: chartColors.grid },
      },
      crosshair: { mode: tv.CrosshairMode.Normal },
      rightPriceScale: {
        visible: true,
        borderVisible: true,
        borderColor: chartColors.border,
        scaleMargins: { top: 0.05, bottom: 0.12 },
      },
      timeScale: {
        borderColor: chartColors.border,
        timeVisible: true,
        secondsVisible: false,
      },
    });
    const candleSeries = chart.addSeries(tv.CandlestickSeries, {
      upColor: chartColors.candleUp,
      downColor: chartColors.candleDown,
      borderVisible: true,
      borderUpColor: chartColors.candleBorder,
      borderDownColor: chartColors.candleBorder,
      wickUpColor: chartColors.candleWick,
      wickDownColor: chartColors.candleWick,
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
    chart.priceScale("volume").applyOptions({ scaleMargins: { top: 0.9, bottom: 0 } });
    volumeSeries.setData(chartVolumeRows(candles));
    const lineSeries = {};
    [
      ["EMA5", "#26c6da"],
      ["EMA10", "#f8c15c"],
      ["SMA20", "#b68cff"],
    ].forEach(([label, color]) => {
      const line = chart.addSeries(tv.LineSeries, {
        color,
        lineWidth: 2,
        priceFormat: chartPriceFormat(candles),
        priceLineVisible: false,
        lastValueVisible: true,
        title: label,
      });
      line.setData(historicalIndicatorRows(replay, label));
      lineSeries[label] = line;
    });
    chartState.markerIds = new Map();
    const markers = evidenceLabOverlayMarkers(replay, candles, chartState.markerIds);
    if (typeof tv.createSeriesMarkers === "function") {
      chartState.markerHandle = tv.createSeriesMarkers(candleSeries, markers);
    } else if (typeof candleSeries.setMarkers === "function") {
      candleSeries.setMarkers(markers);
    }
    if (typeof chart.subscribeClick === "function") {
      chart.subscribeClick((param) => {
        const tradeId = evidenceLabOverlayClickTradeId(param, replay);
        if (tradeId) selectEvidenceLabWorstTrade(tradeId);
      });
    }
    chart.timeScale().fitContent();
    chartState.chart = chart;
    chartState.mount = mount;
    chartState.candleSeries = candleSeries;
    chartState.volumeSeries = volumeSeries;
    chartState.indicatorSeries = lineSeries;
    chartState.key = chartKey;
    chartState.ready = true;
    focusEvidenceLabOverlayWindow(replay);
    if (typeof ResizeObserver !== "undefined") {
      const observer = new ResizeObserver(scheduleEvidenceLabOverlayChartResize);
      observer.observe(mount);
      chartState.resizeObserver = observer;
    }
    return true;
  }

  function renderEvidenceLabOverlayInspector() {
    if (!elements.evidenceLabOverlayInspector) return;
    const worst = evidenceLabSelectedWorstTrade();
    const context = evidenceLabSelectedContextSample();
    const scenario = evidenceLabVariantResultForSelection();
    if (!worst && !scenario) {
      setEmpty(elements.evidenceLabOverlayInspector, unavailable());
      return;
    }
    const stopStatus = context
      ? (context.stop_would_have_triggered_before_current_exit ? "stop would have triggered before current exit" : "stop timing not earlier in bundle")
      : "exact_overlay_unavailable_from_sor_ev_bundle";
    elements.evidenceLabOverlayInspector.innerHTML = `
      <article class="overlay-inspector-card">
        <span class="eyebrow">Worst Trade Focus Mode</span>
        <h3>${escapeHtml(worst ? `${worst.symbol} ${displayTimeframe(worst.timeframe)} #${worst.loss_rank}` : state.evidenceLabOverlay.variantId)}</h3>
        <dl class="overlay-inspector-grid">
          <dt>Rank</dt><dd>${escapeHtml(worst?.loss_rank ?? unavailable())}</dd>
          <dt>Symbol</dt><dd>${escapeHtml(worst?.symbol || state.evidenceLabOverlay.symbol)}</dd>
          <dt>Timeframe</dt><dd>${escapeHtml(displayTimeframe(worst?.timeframe || state.evidenceLabOverlay.timeframe))}</dd>
          <dt>Fill assumption</dt><dd>${escapeHtml(worst?.fill_timing || state.evidenceLabOverlay.fillAssumption)}</dd>
          <dt>Entry classification</dt><dd>${escapeHtml(worst?.entry_timing_classification || unavailable())}</dd>
          <dt>Net PnL</dt><dd class="${decimal(worst?.net_pnl) >= 0 ? "positive" : "negative"}">${escapeHtml(worst ? money(worst.net_pnl) : unavailable())}</dd>
          <dt>Max adverse excursion</dt><dd>${escapeHtml(worst ? compactNumber(worst.max_adverse_excursion, 2) : unavailable())}</dd>
          <dt>Large red candle</dt><dd>${escapeHtml(context?.classification || worst?.large_down_candle_classification || unavailable())}</dd>
          <dt>Stop helped/hurt</dt><dd>${escapeHtml(stopStatus)}</dd>
          <dt>Current exit reason</dt><dd>${escapeHtml(worst?.exit_reason || (worst?.exit_reason_codes || []).join(", ") || unavailable())}</dd>
          <dt>Variant result</dt><dd>${escapeHtml(scenario?.outcome || scenario?.candidate_status || unavailable())}</dd>
          <dt>Methodology</dt><dd>${escapeHtml(evidenceLabVariantMethodology())}</dd>
          <dt>Warning</dt><dd>${escapeHtml(evidenceLabVariantIsTrueForward() ? "true_forward_replay_candidate_methodology" : "diagnostic_only_not_candidate")}</dd>
        </dl>
      </article>
    `;
  }

  function renderEvidenceLabWorstFocusTable() {
    if (!elements.evidenceLabWorstFocusTable) return;
    const rows = state.sorEv1Summary?.worst_trades || [];
    if (!rows.length) {
      setEmpty(elements.evidenceLabWorstFocusTable, unavailable());
      return;
    }
    elements.evidenceLabWorstFocusTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Focus</th>
            <th>Rank</th>
            <th>Symbol</th>
            <th>TF</th>
            <th>Fill</th>
            <th>Entry Class</th>
            <th>Net PnL</th>
            <th>Large Red</th>
            <th>MAE</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((row) => `
            <tr class="${row.trade_id === state.evidenceLabOverlay.selectedWorstTradeId ? "active-row" : ""}">
              <td><button class="text-row-button" type="button" data-evidence-lab-focus-trade="${escapeHtml(row.trade_id || "")}">${row.trade_id === state.evidenceLabOverlay.selectedWorstTradeId ? "Focused" : "Focus"}</button></td>
              <td>${escapeHtml(row.loss_rank ?? unavailable())}</td>
              <td>${escapeHtml(row.symbol)}</td>
              <td>${escapeHtml(displayTimeframe(row.timeframe))}</td>
              <td>${escapeHtml(row.fill_timing)}</td>
              <td>${escapeHtml(row.entry_timing_classification || unavailable())}</td>
              <td class="${decimal(row.net_pnl) >= 0 ? "positive" : "negative"}">${escapeHtml(money(row.net_pnl))}</td>
              <td>${escapeHtml(row.large_down_candle_classification || row.large_red_candle_flag || unavailable())}</td>
              <td>${escapeHtml(compactNumber(row.max_adverse_excursion, 2))}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
    elements.evidenceLabWorstFocusTable.querySelectorAll("[data-evidence-lab-focus-trade]").forEach((button) => {
      button.addEventListener("click", () => selectEvidenceLabWorstTrade(button.dataset.evidenceLabFocusTrade));
    });
  }

  function renderEvidenceLabControlPocketView() {
    if (!elements.evidenceLabControlPocketView) return;
    const row = evidenceLabControlPocketForVariant();
    const scenario = evidenceLabVariantResultForSelection();
    if (!row && !scenario) {
      setEmpty(elements.evidenceLabControlPocketView, unavailable());
      return;
    }
    const tradeCountChange = [
      `increased ${row?.trade_count_increased ?? unavailable()}`,
      `decreased ${row?.trade_count_decreased ?? unavailable()}`,
    ].join("; ");
    const rows = [
      ["ETH 1h", row?.damaged === 0 ? "preserved" : "review_required", row?.drawdown_reduced, row?.return_reduced, tradeCountChange, scenario?.outcome || unavailable()],
      ["positive 1D pockets", row?.preserved ?? unavailable(), row?.drawdown_reduced, row?.return_reduced, tradeCountChange, "positive 1D pockets are evidence-only control pockets"],
      ["other positive baseline pockets", `preserved ${row?.preserved ?? unavailable()}; improved ${row?.improved ?? unavailable()}; damaged ${row?.damaged ?? unavailable()}`, row?.drawdown_reduced, row?.return_reduced, tradeCountChange, sorOutcomeTaxonomy(row || scenario, state.sorEv2Summary)],
    ];
    elements.evidenceLabControlPocketView.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Pocket</th>
            <th>Preserved / Improved / Damaged</th>
            <th>Drawdown Reduced</th>
            <th>Return Reduced</th>
            <th>Trade Count Changed</th>
            <th>Why candidate/rejected</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(([pocket, status, drawdown, returnImpact, tradeImpact, note]) => `
            <tr>
              <td>${escapeHtml(pocket)}</td>
              <td>${escapeHtml(status)}</td>
              <td>${escapeHtml(drawdown ?? unavailable())}</td>
              <td>${escapeHtml(returnImpact ?? unavailable())}</td>
              <td>${escapeHtml(tradeImpact)}</td>
              <td>${escapeHtml(note)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderEvidenceLabOverlayUnavailable(chartRendered) {
    if (!elements.evidenceLabOverlayUnavailable) return;
    const messages = [];
    if (!chartRendered) {
      messages.push("data_not_available_in_sor_ev_bundle");
    }
    const scenario = evidenceLabVariantResultForSelection();
    if (!scenario) {
      messages.push("data_not_available_in_sor_ev_bundle: selected variant scenario row is unavailable");
    }
    if (state.evidenceLabOverlay.showMaBreaks) {
      messages.push("exact_overlay_unavailable_from_sor_ev_bundle: SOR-EV2 has MA/SMA break flags, not exact break timestamps");
    }
    const selectedFamily = sorVariantFamily(selectedEvidenceLabVariant()?.row || state.evidenceLabOverlay.variantId);
    if (
      state.evidenceLabOverlay.showStopExits &&
      !["fixed_stop_loss", "atr_stop", "recent_low_stop", "large_bear_candle_exit"].includes(selectedFamily)
    ) {
      messages.push("data_not_available_in_sor_ev_bundle: selected variant is not a stop/exit family");
    }
    if (state.evidenceLabOverlay.showStopExits && !selectedEvidenceLabContextSamples().length) {
      messages.push("exact_overlay_unavailable_from_sor_ev_bundle: no linkable stop/adverse-candle context rows for this symbol/timeframe/fill");
    }
    if (!evidenceLabVariantIsTrueForward()) {
      messages.push("diagnostic_only_not_candidate: selected methodology is not true_forward_replay");
    }
    messages.push("Date filters are display-only recalculations from loaded trades. They do not regenerate canonical evidence packs.");
    elements.evidenceLabOverlayUnavailable.innerHTML = messages
      .map((message) => `<span>${escapeHtml(message)}</span>`)
      .join("");
  }

  function renderEvidenceLabSummary() {
    if (!elements.evidenceLabSummaryCards) return;
    const ev1 = state.sorEv1Summary;
    const ev2 = state.sorEv2Summary;
    const ev3 = state.sorEv3Summary;
    const mfOrig = state.mfOrigSummary;
    const variantCount = sorVariantRows().length;
    const parity = ev2?.baseline_parity_summary?.status_counts?.baseline_parity_passed ?? ev2?.baseline_parity_summary?.scenario_count;
    const ev3Candidates = Array.isArray(ev3?.candidate_variants) && ev3.candidate_variants.length
      ? ev3.candidate_variants.join(", ")
      : "none";
    const ev3Promising = Array.isArray(ev3?.promising_variants) && ev3.promising_variants.length
      ? ev3.promising_variants.join(", ")
      : "none";
    const cards = [
      ["Baseline", "SV2.0.2", `timestamp ${SV202_CANONICAL_TIMESTAMP}`],
      ["SOR-EV1 bundle", ev1 ? "loaded" : unavailable(), "loss anatomy and completed-trade overlays"],
      ["SOR-EV2 bundle", ev2 ? "loaded" : unavailable(), "true-forward stops and rejected-signal replay"],
      ["SOR-EV3 bundle", ev3 ? "loaded" : unavailable(), `candidates: ${ev3Candidates}; promising: ${ev3Promising}`],
      ["MF-ORIG latest run", mfOrig ? "loaded" : unavailable(), mfOrig?.phase || "corrected original Money Flow replay JSON"],
      ["Baseline parity", parity ?? unavailable(), "canonical SV2.0.2 scenarios"],
      ["Variants", variantCount || unavailable(), "evidence-only; none promoted"],
    ];
    elements.evidenceLabSummaryCards.innerHTML = cards.map(([label, value, detail]) => `
      <article class="metric-cell">
        <span class="metric-label">${escapeHtml(label)}</span>
        <strong>${escapeHtml(value)}</strong>
        <small>${escapeHtml(detail)}</small>
      </article>
    `).join("");
  }

  function evidenceLabFounderLabelClass(label) {
    const value = String(label || "");
    if (value === "candidate_for_more_evidence") return "candidate";
    if (value.startsWith("promising_")) return "promising";
    if (value.startsWith("mixed_")) return "mixed";
    if (value.startsWith("rejected_")) return "rejected";
    if (value.startsWith("deferred_")) return "neutral";
    return "neutral";
  }

  function evidenceLabFounderLabel(row) {
    const label = row?.founder_review_label || row?.outcome_taxonomy || unavailable();
    const help = row?.review_explanation || SOR_EV3_FOUNDER_LABEL_HELP[label] || "";
    return `<span class="evidence-label-badge ${escapeHtml(evidenceLabFounderLabelClass(label))}" title="${escapeHtml(help)}">${escapeHtml(label)}</span>`;
  }

  function evidenceLabFounderLabelRank(row) {
    const label = row?.founder_review_label || row?.outcome_taxonomy || "";
    if (Object.prototype.hasOwnProperty.call(FOUNDER_LABEL_RANK, label)) {
      return FOUNDER_LABEL_RANK[label];
    }
    if (label.startsWith("promising_")) return 30;
    if (label.startsWith("mixed_")) return 50;
    if (label.startsWith("not_promoted_")) return 70;
    if (label.startsWith("deferred_")) return 80;
    if (label.startsWith("rejected_")) return 100;
    return 90;
  }

  function renderEvidenceLabFounderCandidate() {
    if (!elements.evidenceLabFounderCandidate) return;
    const ev3 = state.sorEv3Summary;
    const rows = Array.isArray(ev3?.variant_summary) ? ev3.variant_summary : [];
    if (!ev3 || !rows.length) {
      setEmpty(elements.evidenceLabFounderCandidate, "data_not_available_in_sor_ev_bundle");
      return;
    }
    const controlById = new Map((ev3.control_pocket_impact || []).map((row) => [row.variant_id, row]));
    const parity = ev3.baseline_parity_summary?.status_counts
      ? Object.entries(ev3.baseline_parity_summary.status_counts).map(([key, value]) => `${key}: ${value}`).join("; ")
      : unavailable();
    const sortedRows = rows.slice().sort((left, right) =>
      evidenceLabFounderLabelRank(left) - evidenceLabFounderLabelRank(right) ||
      decimal(right.net_pnl_delta_sum_across_independent_scenarios) - decimal(left.net_pnl_delta_sum_across_independent_scenarios) ||
      String(left.variant_id || "").localeCompare(String(right.variant_id || "")),
    );
    elements.evidenceLabFounderCandidate.innerHTML = `
      <div class="metric-grid compact-grid">
        <article class="metric-cell">
          <span class="metric-label">Baseline parity</span>
          <strong>${escapeHtml(parity)}</strong>
          <small>canonical SV2.0.2 only</small>
        </article>
        <article class="metric-cell">
          <span class="metric-label">Candidate variants</span>
          <strong>${escapeHtml((ev3.candidate_variants || []).join(", ") || "none")}</strong>
          <small>no variant is approved for production</small>
        </article>
        <article class="metric-cell">
          <span class="metric-label">Blocked signals</span>
          <strong>${escapeHtml(compactNumber(ev3.blocked_entry_summary?.total_blocked_open_signals ?? unavailable(), 0))}</strong>
          <small>signals, not canonical trade-count reduction</small>
        </article>
        <article class="metric-cell">
          <span class="metric-label">Matched trades</span>
          <strong>${escapeHtml(compactNumber(ev3.blocked_entry_summary?.canonical_blocked_entries ?? unavailable(), 0))}</strong>
          <small>blocked entries with baseline PnL attribution</small>
        </article>
        <article class="metric-cell metric-cell-full-row">
          <span class="metric-label">Promising labels</span>
          <strong>${escapeHtml((ev3.promising_variants || []).join(", ") || "none")}</strong>
          <small>not promoted; needs narrower follow-up</small>
        </article>
      </div>
      <table>
        <thead>
          <tr>
            <th>Variant</th>
            <th>Founder Label</th>
            <th>Outcome</th>
            <th>Net PnL Delta</th>
            <th>Drawdown Delta</th>
            <th>Blocked Signals</th>
            <th>Matched Trades</th>
            <th>Avoided Losers</th>
            <th>Missed Winners</th>
            <th>Control Damage</th>
            <th>Promotion Status</th>
            <th>Gate Blockers</th>
          </tr>
        </thead>
        <tbody>
          ${sortedRows.map((row) => {
            const control = controlById.get(row.variant_id) || {};
            const blockers = Array.isArray(row.promotion_blockers) && row.promotion_blockers.length
              ? row.promotion_blockers.join(", ")
              : "none";
            return `
              <tr>
                <td>${escapeHtml(row.variant_id)}</td>
                <td>${evidenceLabFounderLabel(row)}</td>
                <td>${escapeHtml(row.outcome_taxonomy || unavailable())}</td>
                <td>${escapeHtml(formatEvidenceMoney(row, "net_pnl_delta_sum_across_independent_scenarios"))}</td>
                <td>${escapeHtml(formatEvidenceMoney(row, "max_drawdown_delta_worst"))}</td>
                <td>${escapeHtml(formatEvidenceNumber(row, "blocked_open_signals", 0))}</td>
                <td>${escapeHtml(formatEvidenceNumber(row, "blocked_entries", 0))}</td>
                <td>${escapeHtml(formatEvidenceNumber(row, "avoided_losers", 0))}</td>
                <td>${escapeHtml(formatEvidenceNumber(row, "missed_winners", 0))}</td>
                <td>${escapeHtml(control.damaged ?? unavailable())}</td>
                <td>${escapeHtml(row.promotion_status || "not_promoted")}</td>
                <td title="${escapeHtml(row.review_explanation || "")}">${escapeHtml(blockers)}</td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    `;
  }

  function renderEvidenceLabMfOrig() {
    if (!elements.evidenceLabMfOrig) return;
    const summary = state.mfOrigSummary;
    const rows = Array.isArray(summary?.hypothesis_summary)
      ? summary.hypothesis_summary.filter((row) => isVisibleMfOrigStrategyId(row.hypothesis_id))
      : [];
    if (!summary || !rows.length) {
      setEmpty(elements.evidenceLabMfOrig, "data_not_available_in_mf_orig_bundle");
      return;
    }
    const accounting = summary.accounting_invariant_summary || {};
    const parity = summary.baseline_parity_summary?.status_counts
      ? Object.entries(summary.baseline_parity_summary.status_counts).map(([key, value]) => `${key}: ${value}`).join("; ")
      : unavailable();
    const controls = Array.isArray(summary.control_pocket_results) ? summary.control_pocket_results : [];
    const damagedPositiveOneDay = controls.filter(
      (row) => row.control_pocket === "positive 1d pockets" && row.status === "damaged",
    ).length;
    const boundary = summary.boundary_flags || {};
    const allEvidenceOnly = boundary.evidence_only === true &&
      boundary.changes_production_money_flow_rules === false &&
      boundary.submits_orders === false &&
      boundary.approves_live_trading === false;
    const sortedRows = rows.slice().sort((left, right) =>
      decimal(right.net_pnl_delta_sum_across_independent_scenarios) -
        decimal(left.net_pnl_delta_sum_across_independent_scenarios) ||
      String(left.hypothesis_id || "").localeCompare(String(right.hypothesis_id || "")),
    );
    elements.evidenceLabMfOrig.innerHTML = `
      <div class="methodology-warning compact" role="note">
        ${escapeHtml(summary.phase || "MF-ORIG")} is an evidence-only Original Money Flow reconstruction loaded from
        <code>${escapeHtml(summary.phase === "MF-ORIG-EV2" ? "docs/mf_orig_ev2_multitimeframe_evidence_summary.json" : "docs/mf_orig_ev1_original_money_flow_reconstruction_summary.json")}</code>.
        ${escapeHtml(summary.phase === "MF-ORIG-EV2" ? "MF-ORIG-EV2 generated multi-timeframe evidence packs and dashboard replay JSON." : "MF-ORIG-EV1.1 is a corrected replay/report run, not a new canonical evidence-pack run.")}
        No original hypothesis is approved, and production Money Flow v1.2 is unchanged.
      </div>
      <div class="metric-grid compact-grid">
        <article class="metric-cell">
          <span class="metric-label">Run phase</span>
          <strong>${escapeHtml(summary.phase || unavailable())}</strong>
          <small>${escapeHtml(summary.supersedes_phase ? `supersedes ${summary.supersedes_phase}` : "latest MF-ORIG run")}</small>
        </article>
        <article class="metric-cell">
          <span class="metric-label">Accounting audit</span>
          <strong>${escapeHtml(accounting.status || unavailable())}</strong>
          <small>${escapeHtml(`${accounting.trade_count_checked ?? unavailable()} trades checked`)}</small>
        </article>
        <article class="metric-cell">
          <span class="metric-label">Drawdown method</span>
          <strong>${escapeHtml(summary.accounting_convention?.drawdown_method || unavailable())}</strong>
          <small>realized and mark-to-market curves</small>
        </article>
        <article class="metric-cell">
          <span class="metric-label">Baseline parity</span>
          <strong>${escapeHtml(parity)}</strong>
          <small>canonical SV2.0.2 comparison baseline</small>
        </article>
        <article class="metric-cell">
          <span class="metric-label">Positive 1D control damage</span>
          <strong>${escapeHtml(damagedPositiveOneDay)}</strong>
          <small>candidate gate blocker</small>
        </article>
        <article class="metric-cell">
          <span class="metric-label">Boundary</span>
          <strong>${escapeHtml(allEvidenceOnly ? "evidence_only" : "review_required")}</strong>
          <small>no orders / no live / no production approval</small>
        </article>
      </div>
      <table>
        <thead>
          <tr>
            <th>Hypothesis</th>
            <th>Outcome</th>
            <th>Performance Label</th>
            <th>Methodology</th>
            <th>Net PnL Delta</th>
            <th>Worst DD Delta</th>
            <th>1D Net PnL</th>
            <th>Trades</th>
            <th>Trims</th>
            <th>Stops</th>
            <th>Forced Closes</th>
            <th>Gate Blockers</th>
            <th>Production Approved</th>
          </tr>
        </thead>
        <tbody>
          ${sortedRows.map((row) => `
            <tr>
              <td>${escapeHtml(row.hypothesis_id)}</td>
              <td>${evidenceLabFounderLabel({ founder_review_label: row.outcome_label, review_explanation: "MF-ORIG candidate gate status; evidence-only." })}</td>
              <td>${escapeHtml(row.performance_label || unavailable())}</td>
              <td>${escapeHtml(row.methodology || unavailable())}</td>
              <td>${escapeHtml(formatEvidenceMoney(row, "net_pnl_delta_sum_across_independent_scenarios"))}</td>
              <td>${escapeHtml(formatEvidenceMoney(row, "worst_drawdown_delta_vs_v1_2"))}</td>
              <td>${escapeHtml(formatEvidenceMoney(row, "one_day_net_pnl_sum"))}</td>
              <td>${escapeHtml(formatEvidenceNumber(row, "trade_count_sum", 0))}</td>
              <td>${escapeHtml(formatEvidenceNumber(row, "trim_event_count_sum", 0))}</td>
              <td>${escapeHtml(formatEvidenceNumber(row, "stop_exit_count_sum", 0))}</td>
              <td>${escapeHtml(formatEvidenceNumber(row, "forced_close_count_sum", 0))}</td>
              <td>${escapeHtml((row.gate_blockers || []).join(", ") || "none")}</td>
              <td>${row.production_approved === true ? "yes" : "no"}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderEvidenceLabVariantMatrix() {
    if (!elements.evidenceLabVariantMatrix) return;
    const variants = sorVariantRows();
    if (!variants.length) {
      setEmpty(elements.evidenceLabVariantMatrix, "data_not_available_in_sor_ev_bundle");
      return;
    }
    const controlById = new Map((state.sorEv2Summary?.control_pocket_impact || []).map((row) => [row.variant_id, row]));
    const sortedVariants = variants
      .map(({ id, row }) => {
        const control = controlById.get(id);
        const taxonomy = sorOutcomeTaxonomy(row, state.sorEv2Summary);
        const review = evidenceLabVariantReview(row, control, taxonomy);
        return { id, row, control, taxonomy, review };
      })
      .sort((left, right) =>
        evidenceLabFounderLabelRank({ founder_review_label: left.review.label }) -
          evidenceLabFounderLabelRank({ founder_review_label: right.review.label }) ||
        decimal(right.row?.ending_equity_delta_sum_across_independent_scenarios) -
          decimal(left.row?.ending_equity_delta_sum_across_independent_scenarios) ||
        String(left.id || "").localeCompare(String(right.id || "")),
      );
    elements.evidenceLabVariantMatrix.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Variant ID</th>
            <th>Variant Family</th>
            <th>Methodology</th>
            <th>Founder Label</th>
            <th>Outcome Taxonomy</th>
            <th>Tested</th>
            <th>Candidate</th>
            <th>Review Status</th>
            <th>Hard Rejected</th>
            <th>Ending Equity Delta</th>
            <th>Drawdown Delta</th>
            <th>Trade Count Delta</th>
            <th>Largest Loss Delta</th>
            <th>Control Pocket Impact</th>
            <th>Gate Blockers</th>
          </tr>
        </thead>
        <tbody>
          ${sortedVariants.map(({ id, row, control, taxonomy, review }) => {
            const controlSummary = control
              ? `preserved ${control.preserved ?? 0}; improved ${control.improved ?? 0}; damaged ${control.damaged ?? 0}`
              : unavailable();
            return `
              <tr>
                <td>${escapeHtml(id)}</td>
                <td>${escapeHtml(sorVariantFamily(row))}</td>
                <td>${escapeHtml(row.methodology || unavailable())}</td>
                <td>${evidenceLabFounderLabel({ founder_review_label: review.label, review_explanation: review.explanation })}</td>
                <td>${escapeHtml(taxonomy)}</td>
                <td>${row ? "yes" : "no"}</td>
                <td>${row?.candidate_evidence ? "yes" : "no"}</td>
                <td>${escapeHtml(review.status)}</td>
                <td>${review.label.startsWith("rejected_") ? "yes" : "no"}</td>
                <td>${escapeHtml(formatEvidenceMoney(row, "ending_equity_delta_sum_across_independent_scenarios"))}</td>
                <td>${escapeHtml(formatEvidenceMoney(row, "max_drawdown_delta_worst"))}</td>
                <td>${escapeHtml(formatEvidenceNumber(row, "trade_count_delta_sum", 0))}</td>
                <td>${escapeHtml(unavailable())}</td>
                <td>${escapeHtml(controlSummary)}</td>
                <td title="${escapeHtml(review.explanation)}">${escapeHtml(review.blockers.join(", "))}</td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    `;
  }

  function renderEvidenceLabControlPockets() {
    if (!elements.evidenceLabControlPockets) return;
    const rows = state.sorEv2Summary?.control_pocket_impact || state.sorEv1Summary?.control_pocket_impact || [];
    if (!rows.length) {
      setEmpty(elements.evidenceLabControlPockets, unavailable());
      return;
    }
    elements.evidenceLabControlPockets.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Variant</th>
            <th>Control Pockets</th>
            <th>Preserved</th>
            <th>Improved</th>
            <th>Damaged</th>
            <th>Lowered Drawdown</th>
            <th>Lowered Return</th>
            <th>Trade Count Impact</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((row) => `
            <tr>
              <td>${escapeHtml(row.variant_id)}</td>
              <td>${escapeHtml(row.control_pocket_count ?? unavailable())}</td>
              <td>${escapeHtml(row.preserved ?? unavailable())}</td>
              <td>${escapeHtml(row.improved ?? unavailable())}</td>
              <td>${escapeHtml(row.damaged ?? unavailable())}</td>
              <td>${escapeHtml(row.drawdown_reduced ?? unavailable())}</td>
              <td>${escapeHtml(row.return_reduced ?? unavailable())}</td>
              <td>${escapeHtml(`increased ${row.trade_count_increased ?? unavailable()}; decreased ${row.trade_count_decreased ?? unavailable()}`)}</td>
              <td>ETH 1h and positive 1d pockets are preserved only when damaged = 0.</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderEvidenceLabWorstTrades() {
    if (!elements.evidenceLabWorstTrades) return;
    const rows = state.sorEv1Summary?.worst_trades || [];
    if (!rows.length) {
      setEmpty(elements.evidenceLabWorstTrades, unavailable());
      return;
    }
    elements.evidenceLabWorstTrades.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Symbol</th>
            <th>Timeframe</th>
            <th>Fill</th>
            <th>Entry Time</th>
            <th>Exit Time</th>
            <th>Net PnL</th>
            <th>Equity Before</th>
            <th>Equity After</th>
            <th>Entry Classification</th>
            <th>Exit Reason</th>
            <th>Large Red Candle</th>
            <th>MAE</th>
            <th>Variant Outcome</th>
          </tr>
        </thead>
        <tbody>
          ${rows.slice(0, 50).map((row) => `
            <tr>
              <td>${escapeHtml(row.loss_rank ?? unavailable())}</td>
              <td>${escapeHtml(row.symbol)}</td>
              <td>${escapeHtml(row.timeframe)}</td>
              <td>${escapeHtml(row.fill_timing)}</td>
              <td>${escapeHtml(row.entry_time)}</td>
              <td>${escapeHtml(row.exit_time)}</td>
              <td class="${decimal(row.net_pnl) >= 0 ? "positive" : "negative"}">${escapeHtml(money(row.net_pnl))}</td>
              <td>${escapeHtml(money(row.equity_before_trade))}</td>
              <td>${escapeHtml(money(row.equity_after_trade))}</td>
              <td>${escapeHtml(row.entry_timing_classification || unavailable())}</td>
              <td>${escapeHtml(row.exit_reason || (row.exit_reason_codes || []).join(", ") || unavailable())}</td>
              <td>${escapeHtml(row.large_down_candle_classification || row.large_red_candle_flag || unavailable())}</td>
              <td>${escapeHtml(compactNumber(row.max_adverse_excursion, 2))}</td>
              <td>${escapeHtml(row.variant_outcome || unavailable())}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderEvidenceLabLateEntry() {
    if (!elements.evidenceLabLateEntry) return;
    const counts = state.sorEv1Summary?.late_entry_classifications || {};
    const categories = [
      "early_trend_entry",
      "pullback_entry",
      "late_extension_entry",
      "chop_entry",
      "continuation_entry",
      "high_RSI_entry",
      "MACD_late_cross_entry",
      "overextended_ema_entry",
      "unknown",
    ];
    elements.evidenceLabLateEntry.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Classification</th>
            <th>Loss Count</th>
            <th>Founder Question</th>
          </tr>
        </thead>
        <tbody>
          ${categories.map((category) => `
            <tr>
              <td>${escapeHtml(category)}</td>
              <td>${escapeHtml(hasOwnValue(counts, category) ? counts[category] : unavailable())}</td>
              <td>${escapeHtml(category.includes("late") || category.includes("chop") || category.includes("overextended") ? "late/chop weakness check" : "context")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderEvidenceLabAdverseCandles() {
    if (!elements.evidenceLabAdverseCandles) return;
    const summary = state.sorEv2Summary?.large_loss_candle_context_summary || {};
    const ev1BigRed = state.sorEv1Summary?.big_red_candle_summary || {};
    const rows = [
      ["losses with large adverse candle", summary.classification_counts?.large_adverse_candle ?? ev1BigRed.losses_from_large_down_candles ?? unavailable()],
      ["losses where current exit was late", summary.late_exit_after_adverse_candle_count ?? unavailable()],
      ["losses where fixed stop would have helped", ev1BigRed.stop_would_have_helped ?? summary.stop_would_have_triggered_before_current_exit_count ?? unavailable()],
      ["losses where ATR stop would have helped", unavailable()],
      ["losses where recent-low stop would have helped", summary.recent_low_break_before_current_exit_count ?? unavailable()],
      ["losses where stop would have hurt", ev1BigRed.adverse_move_not_stop_solvable ?? unavailable()],
    ];
    elements.evidenceLabAdverseCandles.innerHTML = `
      <table>
        <thead>
          <tr><th>Question</th><th>Count / Status</th></tr>
        </thead>
        <tbody>
          ${rows.map(([label, value]) => `
            <tr>
              <td>${escapeHtml(label)}</td>
              <td>${escapeHtml(value)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderEvidenceLabRsiMacd() {
    if (!elements.evidenceLabRsiMacd) return;
    const summary = state.sorEv2Summary?.rejected_signal_replay_summary || state.sorEv1Summary?.rsi_macd_rejection_summary || {};
    const baselineCounts = summary.baseline_rejection_counts || summary.raw_no_trade_reason_counts || summary.first_failed_reason_counts || {};
    const admittedCounts = summary.variant_admitted_from_rejection_counts || {};
    const categories = [
      "rsi_not_constructive",
      "macd_not_constructive",
      "overextended_rsi",
      "entry_quality_not_constructive",
      "insufficient_history",
      "missing_indicator_field",
      "other",
    ];
    elements.evidenceLabRsiMacd.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Reason Category</th>
            <th>Baseline Rejections</th>
            <th>Variant-Admitted Count</th>
            <th>Bad Trades Admitted</th>
            <th>Good Trades Admitted</th>
            <th>Methodology</th>
          </tr>
        </thead>
        <tbody>
          ${categories.map((category) => `
            <tr>
              <td>${escapeHtml(category)}</td>
              <td>${escapeHtml(hasOwnValue(baselineCounts, category) ? baselineCounts[category] : unavailable())}</td>
              <td>${escapeHtml(hasOwnValue(admittedCounts, category) ? admittedCounts[category] : unavailable())}</td>
              <td>${escapeHtml(unavailable())}</td>
              <td>${escapeHtml(unavailable())}</td>
              <td>${escapeHtml(summary.methodology || unavailable())}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderEvidenceLabChartOverlay() {
    renderEvidenceLabOverlayControls();
    renderEvidenceLabOverlayMethodology();
    const chartRendered = renderEvidenceLabOverlayChart();
    renderEvidenceLabOverlayInspector();
    renderEvidenceLabWorstFocusTable();
    renderEvidenceLabControlPocketView();
    renderEvidenceLabOverlayUnavailable(chartRendered);
  }

  function renderEvidenceLab() {
    renderEvidenceLabSummary();
    renderEvidenceLabFounderCandidate();
    renderEvidenceLabMfOrig();
    renderEvidenceLabVariantMatrix();
    renderEvidenceLabControlPockets();
    renderEvidenceLabWorstTrades();
    renderEvidenceLabLateEntry();
    renderEvidenceLabAdverseCandles();
    renderEvidenceLabRsiMacd();
    renderEvidenceLabChartOverlay();
  }

  function auditReviewSummary() {
    return state.evAuditSummary || null;
  }

  function auditReviewRows(rows) {
    return Array.isArray(rows) ? rows : [];
  }

  function auditReviewText(value, fallback = "data_not_available_in_audit_bundle") {
    if (value === null || value === undefined || value === "") return fallback;
    if (Array.isArray(value)) return value.length ? value.join(", ") : fallback;
    return String(value);
  }

  function auditReviewPillClass(value) {
    const raw = String(value || "").toLowerCase();
    if (
      raw.includes("p0") ||
      raw.includes("p1") ||
      raw.includes("blocked") ||
      raw.includes("failed") ||
      raw.includes("damaged") ||
      raw.includes("rejected") ||
      raw.includes("no_strategy") ||
      raw.includes("none_cleanly") ||
      raw.includes("not_good_enough") ||
      raw.includes("not_production")
    ) return "result-bad";
    if (
      raw.includes("p2") ||
      raw.includes("p3") ||
      raw.includes("warning") ||
      raw.includes("condition") ||
      raw.includes("underperformed") ||
      raw.includes("candidate") ||
      raw.includes("needs_")
    ) return "result-warn";
    if (
      raw.includes("canonical") ||
      raw.includes("implemented") ||
      raw.includes("ready") ||
      raw.includes("good_enough") ||
      raw.includes("true_forward")
    ) return "result-good";
    return "result-unknown";
  }

  function auditReviewPill(value) {
    return `<span class="result-pill ${auditReviewPillClass(value)}">${escapeHtml(auditReviewText(value, "n/a"))}</span>`;
  }

  function auditReviewMetricCard(label, value, detail, className = "") {
    return `
      <article class="metric-cell ${escapeHtml(className)}">
        <span class="metric-label">${escapeHtml(label)}</span>
        <strong>${escapeHtml(auditReviewText(value, "n/a"))}</strong>
        <small>${escapeHtml(auditReviewText(detail, ""))}</small>
      </article>
    `;
  }

  function renderAuditReviewVerdictCards() {
    if (!elements.auditReviewVerdictCards) return;
    const summary = auditReviewSummary();
    if (!summary) {
      setEmpty(elements.auditReviewVerdictCards, "EV-AUDIT1 summary JSON not loaded.");
      return;
    }
    const verdict = summary.executive_verdict || {};
    const issues = summary.issue_counts || {};
    const backtest = summary.backtest_adequacy_decision || {};
    const paper = summary.paper_observation_readiness || {};
    const issueText = `P0 ${issues.P0 ?? 0} / P1 ${issues.P1 ?? 0} / P2 ${issues.P2 ?? 0} / P3 ${issues.P3 ?? 0}`;
    elements.auditReviewVerdictCards.innerHTML = [
      auditReviewMetricCard("Credible candidate", verdict.credible_evidence_candidate, "audit verdict"),
      auditReviewMetricCard("Best review candidate", verdict.best_review_candidate, verdict.best_review_candidate_reason),
      auditReviewMetricCard("Best full-equity review", verdict.best_full_equity_review_candidate, "not production approval"),
      auditReviewMetricCard("Backtest adequacy", backtest.decision, "visual review / hypothesis filtering only"),
      auditReviewMetricCard("Issue count", issueText, "open audit findings"),
      auditReviewMetricCard("Paper readiness", paper.decision, paper.required_next_phase),
    ].join("");
  }

  function renderAuditReviewScorecard() {
    if (!elements.auditReviewScorecard) return;
    const summary = auditReviewSummary();
    if (!summary) {
      setEmpty(elements.auditReviewScorecard, "EV-AUDIT1 methodology scorecard not loaded.");
      return;
    }
    const methodology = summary.methodology_audit || {};
    const scores = methodology.overall_scores || {};
    const rows = [
      ["Methodology", scores.methodology_confidence_0_to_5],
      ["Data", scores.data_confidence_0_to_5],
      ["Candidate", scores.candidate_confidence_0_to_5],
      ["Founder readiness", scores.founder_decision_readiness_0_to_5],
    ];
    elements.auditReviewScorecard.innerHTML = `
      <div class="audit-score-list">
        ${rows
          .map(([label, value]) => {
            const parsed = decimal(value, 0);
            const width = Math.max(0, Math.min(100, (parsed / 5) * 100));
            return `
              <div class="audit-score-row">
                <div>
                  <strong>${escapeHtml(label)}</strong>
                  <span>${escapeHtml(compactNumber(parsed, 1))} / 5</span>
                </div>
                <div class="audit-score-bar" aria-label="${escapeHtml(label)} confidence score">
                  <div class="audit-score-fill" style="width:${width}%"></div>
                </div>
              </div>
            `;
          })
          .join("")}
      </div>
      <p class="card-note">${escapeHtml(auditReviewText(methodology.score_explanation, "No score explanation available."))}</p>
    `;
  }

  function renderAuditReviewPaperReadiness() {
    if (!elements.auditReviewPaperReadiness) return;
    const summary = auditReviewSummary();
    const readiness = summary?.paper_observation_readiness;
    if (!readiness) {
      setEmpty(elements.auditReviewPaperReadiness, "Paper-observation readiness audit data not loaded.");
      return;
    }
    elements.auditReviewPaperReadiness.innerHTML = `
      <table>
        <tbody>
          <tr><th>Decision</th><td>${auditReviewPill(readiness.decision)}</td></tr>
          <tr><th>Approval</th><td>${escapeHtml(readiness.not_approval ? "not an approval" : "n/a")}</td></tr>
          <tr><th>Required next phase</th><td>${escapeHtml(auditReviewText(readiness.required_next_phase, "n/a"))}</td></tr>
          <tr><th>Conditions</th><td>${escapeHtml(auditReviewText(readiness.conditions, "n/a"))}</td></tr>
        </tbody>
      </table>
    `;
  }

  function renderAuditReviewHypothesisTable(target, rows, emptyMessage) {
    if (!target) return;
    const visibleRows = auditReviewRows(rows).filter(isVisibleDashboardStrategyRow).slice(0, 10);
    if (!visibleRows.length) {
      setEmpty(target, emptyMessage);
      return;
    }
    target.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Family</th>
            <th>Hypothesis</th>
            <th>Methodology</th>
            <th>PnL Delta</th>
            <th>Drawdown Delta</th>
            <th>Trades</th>
            <th>Status</th>
            <th>Reason</th>
          </tr>
        </thead>
        <tbody>
          ${visibleRows
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(auditReviewText(row.strategy_family, "n/a"))}</td>
                  <td>${escapeHtml(auditReviewText(row.hypothesis_id, "n/a"))}</td>
                  <td>${auditReviewPill(row.methodology_label)}</td>
                  <td>${escapeHtml(money(row.net_pnl_delta_vs_baseline))}</td>
                  <td>${escapeHtml(money(row.max_drawdown_delta))}</td>
                  <td>${escapeHtml(compactNumber(row.trade_count, 0))}</td>
                  <td>${auditReviewPill(row.candidate_status)}</td>
                  <td>${escapeHtml(auditReviewText(row.rejection_reason, "n/a"))}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderAuditReviewTradeTable(target, rows, emptyMessage) {
    if (!target) return;
    const visibleRows = auditReviewRows(rows).filter(isVisibleDashboardStrategyRow).slice(0, 10);
    if (!visibleRows.length) {
      setEmpty(target, emptyMessage);
      return;
    }
    target.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Strategy</th>
            <th>Market</th>
            <th>Fill</th>
            <th>Entry</th>
            <th>Exit</th>
            <th>Net PnL</th>
            <th>Context</th>
            <th>Exit reason</th>
          </tr>
        </thead>
        <tbody>
          ${visibleRows
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(auditReviewText(row.hypothesis_id, "n/a"))}</td>
                  <td>${escapeHtml(`${auditReviewText(row.symbol, "n/a")} ${displayTimeframe(row.timeframe)}`)}</td>
                  <td>${escapeHtml(auditReviewText(row.fill_assumption, "n/a"))}</td>
                  <td>${escapeHtml(auditReviewText(row.entry_time, "n/a"))}</td>
                  <td>${escapeHtml(auditReviewText(row.exit_time, "n/a"))}</td>
                  <td>${escapeHtml(money(row.net_pnl))}</td>
                  <td>${escapeHtml(auditReviewText(row.entry_classification || row.entry_volatility_regime, "unknown"))}</td>
                  <td>${escapeHtml(auditReviewText(row.exit_reason, "n/a"))}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderAuditReviewLosingStreaks() {
    if (!elements.auditReviewLosingStreaks) return;
    const rows = auditReviewRows(auditReviewSummary()?.losing_streaks).filter(isVisibleDashboardStrategyRow).slice(0, 10);
    if (!rows.length) {
      setEmpty(elements.auditReviewLosingStreaks, "Losing-streak audit data not loaded.");
      return;
    }
    elements.auditReviewLosingStreaks.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Losses</th>
            <th>Hypothesis</th>
            <th>Market</th>
            <th>Fill</th>
            <th>Streak PnL</th>
            <th>Window</th>
            <th>Primary exit</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(compactNumber(row.consecutive_losses, 0))}</td>
                  <td>${escapeHtml(auditReviewText(row.hypothesis_id, "n/a"))}</td>
                  <td>${escapeHtml(`${auditReviewText(row.symbol, "n/a")} ${displayTimeframe(row.timeframe)}`)}</td>
                  <td>${escapeHtml(auditReviewText(row.fill_assumption, "n/a"))}</td>
                  <td>${escapeHtml(money(row.streak_pnl))}</td>
                  <td>${escapeHtml(`${auditReviewText(row.start_time, "n/a")} -> ${auditReviewText(row.end_time, "n/a")}`)}</td>
                  <td>${escapeHtml(auditReviewText(row.primary_exit_reason, "n/a"))}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderAuditReviewIssues() {
    if (!elements.auditReviewIssues) return;
    const rows = auditReviewRows(auditReviewSummary()?.issue_list);
    if (!rows.length) {
      setEmpty(elements.auditReviewIssues, "Audit issue list not loaded.");
      return;
    }
    elements.auditReviewIssues.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Severity</th>
            <th>Issue</th>
            <th>Why it matters</th>
            <th>Required fix</th>
            <th>Decision impact</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  <td>${auditReviewPill(row.severity)}</td>
                  <td>${escapeHtml(auditReviewText(row.issue, "n/a"))}</td>
                  <td>${escapeHtml(auditReviewText(row.why_it_matters, "n/a"))}</td>
                  <td>${escapeHtml(auditReviewText(row.required_fix, "n/a"))}</td>
                  <td>${escapeHtml(auditReviewText(row.blocks_founder_decisions, "n/a"))}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderAuditReviewDataIntegrity() {
    if (!elements.auditReviewDataIntegrity) return;
    const summary = auditReviewSummary();
    const rows = auditReviewRows(summary?.data_integrity?.data_rows);
    if (!rows.length) {
      setEmpty(elements.auditReviewDataIntegrity, "Data-integrity audit rows not loaded.");
      return;
    }
    elements.auditReviewDataIntegrity.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Timeframe</th>
            <th>Status</th>
            <th>Earliest</th>
            <th>Latest</th>
            <th>Candles</th>
            <th>Coverage</th>
            <th>Limitations</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(auditReviewText(row.symbol, "n/a"))}</td>
                  <td>${escapeHtml(displayTimeframe(row.timeframe))}</td>
                  <td>${auditReviewPill(row.data_status)}</td>
                  <td>${escapeHtml(auditReviewText(row.earliest, "n/a"))}</td>
                  <td>${escapeHtml(auditReviewText(row.latest, "n/a"))}</td>
                  <td>${escapeHtml(compactNumber(row.candle_count, 0))}</td>
                  <td>${escapeHtml(pct(row.coverage_percent))}</td>
                  <td>${escapeHtml(auditReviewText(row.known_limitations, "n/a"))}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderAuditReviewInventory() {
    if (!elements.auditReviewInventory) return;
    const rows = auditReviewRows(auditReviewSummary()?.evidence_inventory).filter(isVisibleDashboardStrategyRow);
    if (!rows.length) {
      setEmpty(elements.auditReviewInventory, "Evidence inventory audit rows not loaded.");
      return;
    }
    elements.auditReviewInventory.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Family</th>
            <th>Hypothesis</th>
            <th>Evidence class</th>
            <th>Methodology</th>
            <th>Coverage</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(auditReviewText(row.strategy_family, "n/a"))}</td>
                  <td>${escapeHtml(auditReviewText(row.hypothesis_id, "n/a"))}</td>
                  <td>${auditReviewPill(row.evidence_classification)}</td>
                  <td>${auditReviewPill(row.methodology_label)}</td>
                  <td>${escapeHtml(`${auditReviewRows(row.symbols_covered).length || "n/a"} symbols / ${auditReviewRows(row.timeframes_covered).map(displayTimeframe).join(", ") || "n/a"}`)}</td>
                  <td>${auditReviewPill(row.candidate_status)}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderAuditReview() {
    renderAuditReviewVerdictCards();
    renderAuditReviewScorecard();
    renderAuditReviewPaperReadiness();
    renderAuditReviewHypothesisTable(
      elements.auditReviewTopHypotheses,
      auditReviewSummary()?.top_hypotheses_by_aggregate_delta,
      "Top hypothesis audit rows not loaded.",
    );
    renderAuditReviewHypothesisTable(
      elements.auditReviewWorstHypotheses,
      auditReviewSummary()?.worst_hypotheses_by_aggregate_delta,
      "Worst hypothesis audit rows not loaded.",
    );
    renderAuditReviewTradeTable(
      elements.auditReviewWinningTrades,
      auditReviewSummary()?.top_winning_trades,
      "Top winning trade audit rows not loaded.",
    );
    renderAuditReviewTradeTable(
      elements.auditReviewLosingTrades,
      auditReviewSummary()?.top_losing_trades,
      "Top losing trade audit rows not loaded.",
    );
    renderAuditReviewLosingStreaks();
    renderAuditReviewIssues();
    renderAuditReviewDataIntegrity();
    renderAuditReviewInventory();
  }

  function paperObservationSummary() {
    return state.ptRt1Summary || null;
  }

  function paperObservationRows(rows) {
    return Array.isArray(rows) ? rows : [];
  }

  function paperObservationText(value, fallback = "data_not_available_in_pt_rt1_bundle") {
    if (Array.isArray(value)) return value.join(", ") || fallback;
    if (value === null || value === undefined || value === "") return fallback;
    return String(value);
  }

  function renderPaperObservationControls() {
    const summary = paperObservationSummary();
    const symbols = paperObservationRows(summary?.symbols);
    const timeframes = paperObservationRows(summary?.timeframes);
    const laneIds = paperObservationRows(summary?.strategy_lanes).map((lane) => lane.strategy_id || lane.lane_id).filter(Boolean);
    renderSelect(elements.paperObservationSymbolFilter, symbols, state.paperObservation.symbol, "All symbols");
    renderSelect(elements.paperObservationTimeframeFilter, timeframes, state.paperObservation.timeframe, "All timeframes");
    renderSelect(elements.paperObservationLaneFilter, laneIds, state.paperObservation.laneId, "All lanes");
    if (elements.paperObservationSymbolFilter) {
      elements.paperObservationSymbolFilter.onchange = () => {
        state.paperObservation.symbol = elements.paperObservationSymbolFilter.value === "all" ? "all" : elements.paperObservationSymbolFilter.value;
        renderPaperObservation();
      };
    }
    if (elements.paperObservationTimeframeFilter) {
      elements.paperObservationTimeframeFilter.onchange = () => {
        state.paperObservation.timeframe =
          elements.paperObservationTimeframeFilter.value === "all" ? "all" : elements.paperObservationTimeframeFilter.value;
        renderPaperObservation();
      };
    }
    if (elements.paperObservationLaneFilter) {
      elements.paperObservationLaneFilter.onchange = () => {
        state.paperObservation.laneId =
          elements.paperObservationLaneFilter.value === "all" ? "all" : elements.paperObservationLaneFilter.value;
        renderPaperObservation();
      };
    }
    if (elements.paperObservationDateStart) {
      elements.paperObservationDateStart.value = state.paperObservation.dateStart;
      elements.paperObservationDateStart.onchange = () => {
        state.paperObservation.dateStart = elements.paperObservationDateStart.value;
        renderPaperObservation();
      };
    }
    if (elements.paperObservationDateEnd) {
      elements.paperObservationDateEnd.value = state.paperObservation.dateEnd;
      elements.paperObservationDateEnd.onchange = () => {
        state.paperObservation.dateEnd = elements.paperObservationDateEnd.value;
        renderPaperObservation();
      };
    }
    if (elements.paperObservationDateClear) {
      elements.paperObservationDateClear.onclick = () => {
        state.paperObservation.dateStart = "";
        state.paperObservation.dateEnd = "";
        renderPaperObservation();
      };
    }
  }

  function renderPaperObservationSummaryCards() {
    if (!elements.paperObservationSummaryCards) return;
    const summary = paperObservationSummary();
    if (!summary) {
      setEmpty(elements.paperObservationSummaryCards, "PT-RT1 summary JSON not loaded.");
      return;
    }
    const probe = summary.testnet_probe_policy || {};
    const truth = summary.strategy_truth_lane || {};
    const lanes = paperObservationRows(summary.strategy_lanes);
    const cards = [
      ["Strategy truth", truth.source || "public mainnet", "no private/signed/order endpoints"],
      ["Lanes", String(lanes.length), "independent 10,000 USDC ledgers"],
      ["Scanner symbols", String(paperObservationRows(summary.scanner_universe).length), "requested/resolved/block reasons visible"],
      ["Probe default", probe.PT_RT1_TESTNET_PROBES_ENABLED === false ? "disabled" : "review", "kill switch true by default"],
      ["Runtime state", "ignored local files", "reports/paper_runtime/"],
    ];
    elements.paperObservationSummaryCards.innerHTML = cards
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

  function renderPaperObservationConnectionStatus() {
    if (!elements.paperObservationConnectionStatus) return;
    const summary = paperObservationSummary();
    const status = summary?.connection_status || {};
    const endpointPolicy = summary?.market_data_endpoint_policy || summary?.strategy_truth_lane || {};
    elements.paperObservationConnectionStatus.innerHTML = `
      <div class="market-micro-grid">
        <div><span>Mainnet connection</span><strong>${escapeHtml(paperObservationText(status.hyperliquid_public_mainnet, "pending_runtime_refresh"))}</strong></div>
        <div><span>Endpoint category</span><strong>${escapeHtml(paperObservationText(status.endpoint_category || endpointPolicy.endpoint_category, "public_read_only"))}</strong></div>
        <div><span>Strategy endpoint</span><strong>${escapeHtml(paperObservationText(endpointPolicy.strategy_truth_endpoint || endpointPolicy.endpoint, "public_read_only_mainnet_info"))}</strong></div>
        <div><span>Last update</span><strong>${escapeHtml(paperObservationText(status.last_update_utc, "pending_runtime_refresh"))}</strong></div>
        <div><span>No private/signed/order endpoints</span><strong>${escapeHtml(String(status.no_private_signed_order_endpoints ?? true))}</strong></div>
        <div><span>No API keys</span><strong>${escapeHtml(String(status.no_api_keys ?? true))}</strong></div>
      </div>
      <div class="methodology-warning secondary" role="note">
        Public mainnet data is strategy truth. Synthetic paper results are forward observation only.
        Testnet probes are plumbing only; testnet fills do not update strategy PnL.
        Reason codes: ${escapeHtml(paperObservationText([...(status.meta_reason_codes || []), ...(status.mids_reason_codes || [])], "pending_runtime_refresh"))}
      </div>
    `;
  }

  function renderPaperObservationScanner() {
    if (!elements.paperObservationScannerTable) return;
    const summary = paperObservationSummary();
    const rows = paperObservationRows(summary?.scanner_universe);
    if (!rows.length) {
      setEmpty(elements.paperObservationScannerTable, "Top-20 scanner runtime rows not loaded.");
      return;
    }
    elements.paperObservationScannerTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Requested</th>
            <th>Venue symbol</th>
            <th>Sources</th>
            <th>Supported</th>
            <th>Blocked</th>
            <th>Precision</th>
            <th>Public mid</th>
            <th>Data health</th>
            <th>Eligible</th>
            <th>Reason codes</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(paperObservationText(row.requested_symbol, "n/a"))}</td>
                  <td>${escapeHtml(paperObservationText(row.resolved_venue_symbol, "n/a"))}</td>
                  <td>${escapeHtml(paperObservationText(row.sources || row.source, "n/a"))}</td>
                  <td>${auditReviewPill(row.supported_by_venue ? "yes" : "no")}</td>
                  <td>${auditReviewPill(row.blocked ? "yes" : "no")}</td>
                  <td>${escapeHtml(paperObservationText(row.precision_status || (row.precision_ready ? "precision_ready" : ""), "n/a"))}</td>
                  <td>${escapeHtml(paperObservationText(row.public_mid, "pending_runtime_refresh"))}</td>
                  <td>${auditReviewPill(row.data_health)}</td>
                  <td>${auditReviewPill(row.scanner_eligible ? "yes" : "no")}</td>
                  <td>${escapeHtml(paperObservationText(row.reason_codes, "n/a"))}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderPaperObservationHealth() {
    if (!elements.paperObservationHealthTable) return;
    const summary = paperObservationSummary();
    const selectedSymbol = state.paperObservation.symbol;
    const selectedTimeframe = state.paperObservation.timeframe;
    const rows = paperObservationRows(summary?.market_data_health).filter(
      (row) =>
        (selectedSymbol === "all" || row.symbol === selectedSymbol || row.requested_symbol === selectedSymbol || row.resolved_venue_symbol === selectedSymbol) &&
        (selectedTimeframe === "all" || sameTimeframe(row.timeframe, selectedTimeframe)),
    );
    if (!rows.length) {
      setEmpty(elements.paperObservationHealthTable, "Market-data health runtime rows not loaded.");
      return;
    }
    elements.paperObservationHealthTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Timeframe</th>
            <th>Source</th>
            <th>Status</th>
            <th>Closed candle</th>
            <th>Last update</th>
            <th>Reason codes</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .slice(0, 18)
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(paperObservationText(row.symbol, "n/a"))}</td>
                  <td>${escapeHtml(displayTimeframe(row.timeframe))}</td>
                  <td>${escapeHtml(paperObservationText(row.source, "n/a"))}</td>
                  <td>${auditReviewPill(row.status)}</td>
                  <td>${auditReviewPill(row.fully_closed_candle_status)}</td>
                  <td>${escapeHtml(paperObservationText(row.last_update_utc, "pending_runtime_refresh"))}</td>
                  <td>${escapeHtml(paperObservationText(row.reason_codes, "n/a"))}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderPaperObservationLanes() {
    if (!elements.paperObservationLaneTable) return;
    const selectedLane = state.paperObservation.laneId;
    const rows = paperObservationRows(paperObservationSummary()?.strategy_lanes).filter(
      (row) => selectedLane === "all" || row.strategy_id === selectedLane || row.lane_id === selectedLane,
    );
    if (!rows.length) {
      setEmpty(elements.paperObservationLaneTable, "Strategy lane config not loaded.");
      return;
    }
    elements.paperObservationLaneTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Lane</th>
            <th>Role</th>
            <th>Family</th>
            <th>Starting equity</th>
            <th>Realized equity</th>
            <th>Unrealized PnL</th>
            <th>Total equity</th>
            <th>Max drawdown</th>
            <th>Open / closed</th>
            <th>Losing streak</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(row.display_name || row.strategy_id)}</td>
                  <td>${auditReviewPill(row.role)}</td>
                  <td>${escapeHtml(paperObservationText(row.strategy_family, "n/a"))}</td>
                  <td>${escapeHtml(row.initial_equity || "10000")}</td>
                  <td>${escapeHtml(row.realized_equity || row.initial_equity || "10000")}</td>
                  <td>${escapeHtml(row.unrealized_pnl || "0")}</td>
                  <td>${escapeHtml(row.total_equity || row.initial_equity || "10000")}</td>
                  <td>${escapeHtml(row.max_drawdown || "0")}</td>
                  <td>${escapeHtml(`${row.open_positions || 0} / ${row.closed_trades || 0}`)}</td>
                  <td>${escapeHtml(`${row.current_losing_streak || 0} / ${row.max_losing_streak || 0}`)}</td>
                  <td>${auditReviewPill(row.production_approved || row.live_approved ? "review_required" : "not_production_approved")}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderPaperObservationLaneDetail() {
    if (!elements.paperObservationLaneDetail) return;
    const lanes = paperObservationRows(paperObservationSummary()?.strategy_lanes);
    const selectedLane = state.paperObservation.laneId === "all" ? lanes[0] : lanes.find(
      (lane) => lane.strategy_id === state.paperObservation.laneId || lane.lane_id === state.paperObservation.laneId,
    );
    if (!selectedLane) {
      setEmpty(elements.paperObservationLaneDetail, "Lane detail data_not_available_in_pt_rt1_bundle.");
      return;
    }
    elements.paperObservationLaneDetail.innerHTML = `
      <div class="market-micro-grid">
        <div><span>Lane</span><strong>${escapeHtml(selectedLane.strategy_id || selectedLane.lane_id)}</strong></div>
        <div><span>Family</span><strong>${escapeHtml(paperObservationText(selectedLane.strategy_family, "n/a"))}</strong></div>
        <div><span>Paper only</span><strong>${escapeHtml(String(selectedLane.paper_only !== false))}</strong></div>
        <div><span>Production approved</span><strong>${escapeHtml(String(Boolean(selectedLane.production_approved)))}</strong></div>
        <div><span>Live approved</span><strong>${escapeHtml(String(Boolean(selectedLane.live_approved || selectedLane.live_trading_approved)))}</strong></div>
        <div><span>Ledger</span><strong>${escapeHtml(paperObservationText(selectedLane.ledger_label, "independent synthetic paper ledger"))}</strong></div>
        <div><span>Latest decisions</span><strong>${escapeHtml(paperObservationText(selectedLane.last_decision_time, "data_not_available_in_pt_rt1_bundle"))}</strong></div>
        <div><span>Equity curve</span><strong>runtime_state_pending</strong></div>
      </div>
      <div class="methodology-warning secondary" role="note">
        ${escapeHtml(paperObservationText(selectedLane.rule_summary, "data_not_available_in_pt_rt1_bundle"))}
        Reason codes: ${escapeHtml(paperObservationText(selectedLane.reason_codes, "data_not_available_in_pt_rt1_bundle"))}
      </div>
    `;
  }

  function renderPaperObservationWildcardDiagnostics() {
    if (!elements.paperObservationWildcardDiagnostics) return;
    const definitions = paperObservationSummary()?.wildcard_definitions || {};
    const rows = Object.entries(definitions);
    if (!rows.length) {
      setEmpty(elements.paperObservationWildcardDiagnostics, "Wildcard diagnostics data_not_available_in_pt_rt1_bundle.");
      return;
    }
    elements.paperObservationWildcardDiagnostics.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Wildcard lane</th>
            <th>Purpose</th>
            <th>Methodology</th>
            <th>Reason codes</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              ([strategyId, definition]) => `
                <tr>
                  <td>${escapeHtml(strategyId)}</td>
                  <td>${escapeHtml(paperObservationText(definition.purpose, "n/a"))}</td>
                  <td>${auditReviewPill(definition.methodology || "forward_public_mainnet_paper_observation")}</td>
                  <td>${escapeHtml(paperObservationText(definition.reason_codes, "n/a"))}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderPaperObservationChart() {
    if (!elements.paperObservationLiveChart) return;
    const chart = paperObservationSummary()?.live_chart || {};
    const candles = paperObservationRows(chart.candles);
    const latest = candles.length ? candles[candles.length - 1] : null;
    const markerCount = paperObservationRows(chart.paper_markers).length;
    elements.paperObservationLiveChart.innerHTML = `
      <div class="tradingview-chart-topline">
        <strong>${escapeHtml(chart.symbol || (state.paperObservation.symbol === "all" ? "All symbols" : `${state.paperObservation.symbol}-PERP`))}</strong>
        <span>${escapeHtml(displayTimeframe(chart.timeframe || state.paperObservation.timeframe))} public-mainnet paper observation</span>
      </div>
      <div class="tradingview-chart-stage paper-observation-chart-stage">
        <div class="tradingview-lightweight-chart" role="img" aria-label="Paper Observation public-mainnet candle chart placeholder">
          <div class="empty-state">
            ${escapeHtml(candles.length ? `${candles.length} public-mainnet candles loaded. Latest close ${latest?.close || "n/a"} at ${latest?.time || "n/a"}. Paper markers: ${markerCount}.` : "Live public mainnet candles and paper markers load from ignored PT-RT1 runtime state during an observation run.")}
          </div>
        </div>
      </div>
      <div class="tradingview-attribution">Charts: TradingView Lightweight Charts v${TRADINGVIEW_LIGHTWEIGHT_CHARTS_VERSION}. Display-only filter; not canonical evidence; not backend replay.</div>
    `;
  }

  function renderPaperObservationProbeStatus() {
    if (!elements.paperObservationProbeStatus) return;
    const summary = paperObservationSummary();
    const policy = summary?.testnet_probe_policy || {};
    const plumbing = summary?.plumbing_lane || {};
    elements.paperObservationProbeStatus.innerHTML = `
      <div class="market-micro-grid">
        <div><span>Lane</span><strong>testnet plumbing only</strong></div>
        <div><span>Probes enabled</span><strong>${escapeHtml(String(policy.PT_RT1_TESTNET_PROBES_ENABLED ?? false))}</strong></div>
        <div><span>Kill switch</span><strong>${escapeHtml(String(policy.PT_RT1_TESTNET_KILL_SWITCH ?? true))}</strong></div>
        <div><span>Daily cap</span><strong>${escapeHtml(String(policy.PT_RT1_TESTNET_DAILY_PROBE_CAP ?? 1))}</strong></div>
        <div><span>Remaining probes</span><strong>${escapeHtml(String(policy.PT_RT1_TESTNET_DAILY_PROBE_CAP ?? 1))}</strong></div>
        <div><span>Notional cap</span><strong>${escapeHtml(String(policy.PT_RT1_TESTNET_PROBE_NOTIONAL_CAP ?? "10"))} USDC</strong></div>
        <div><span>Last lifecycle</span><strong>runtime_not_started</strong></div>
        <div><span>Open after reconcile</span><strong>none</strong></div>
        <div><span>Unknown state</span><strong>blocked_if_present</strong></div>
        <div><span>Strategy PnL update</span><strong>${escapeHtml(String(plumbing.testnet_fills_update_strategy_pnl ?? false))}</strong></div>
      </div>
    `;
  }

  function renderPaperObservationRuntimeTables() {
    const openMessage = "No open synthetic positions loaded from ignored PT-RT1 runtime state.";
    const closedMessage = "No closed synthetic trades loaded from ignored PT-RT1 runtime state.";
    const riskMessage = "No runtime drawdown or losing-streak rows loaded yet.";
    if (elements.paperObservationOpenPositions) setEmpty(elements.paperObservationOpenPositions, openMessage);
    if (elements.paperObservationClosedTrades) setEmpty(elements.paperObservationClosedTrades, closedMessage);
    if (elements.paperObservationRiskTable) setEmpty(elements.paperObservationRiskTable, riskMessage);
  }

  function renderPaperObservation() {
    renderPaperObservationControls();
    renderPaperObservationSummaryCards();
    renderPaperObservationConnectionStatus();
    renderPaperObservationScanner();
    renderPaperObservationHealth();
    renderPaperObservationLanes();
    renderPaperObservationLaneDetail();
    renderPaperObservationWildcardDiagnostics();
    renderPaperObservationChart();
    renderPaperObservationProbeStatus();
    renderPaperObservationRuntimeTables();
  }

  function render() {
    const summaries = allSummaries();
    const selected = activeSummaries();
    renderMetrics(summaries);
    renderFlags();
    renderFilters(summaries);
    renderEvidenceStrategyFilter();
    renderEvidenceReplayFillFilter();
    renderEvidenceDateControls();
    renderStrategyComparison();
    renderComponentCards(selected);
    renderDetail(selected);
    renderRunTable(selected);
    renderExperiments();
    renderEvidenceLab();
    renderAuditReview();
    renderPaperObservation();
    renderHistoricalReplay();
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
    if (payload?.report === "sv2_0_money_flow_1d_sleeve_expanded_universe_evidence_rebuild") return "sv20_summary";
    if (
      payload?.report === "sv2_0_2_dashboard_historical_replay_chart_data" ||
      payload?.report === "mf_orig_ev2_dashboard_chart_data"
    ) return "sv202_dashboard_chart_data";
    if (payload?.phase === "SOR-EV1") return "sor_ev1_summary";
    if (payload?.phase === "SOR-EV2") return "sor_ev2_summary";
    if (payload?.phase === "SOR-EV3") return "sor_ev3_summary";
    if (String(payload?.phase || "").startsWith("MF-ORIG-EV1")) return "mf_orig_summary";
    if (String(payload?.phase || "").startsWith("MF-ORIG-EV2")) return "mf_orig_summary";
    if (payload?.phase === "EV-AUDIT1" || payload?.audit_verdict === "no_strategy_has_clean_production_or_paper_candidate_status") {
      return "ev_audit_summary";
    }
    if (payload?.phase === "PT-RT1" || payload?.report === "pt_rt1_real_time_paper_observation_and_testnet_plumbing") {
      return "pt_rt1_summary";
    }
    if (
      payload?.report === "pt0_0_2_historical_strategy_replay_cockpit" ||
      payload?.report === "pt0_0_3_historical_data_horizon_and_1d_replay"
    ) return "pt002_historical_replay_summary";
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

    await loadDefaultUat2Summaries();
    await loadDefaultUat34Summaries();
    await loadDefaultUat42Summaries();
    await loadDefaultPt0Summaries();
    await loadDefaultSv20Summaries();
    await loadDefaultSorEvSummaries();
    await loadDefaultMfOrigSummaries();
    await loadDefaultEvAuditSummaries();
    await loadDefaultPtRt1Summaries();

    state.review = null;
    state.batches = [];
    loaded.forEach(({ payload }) => {
      const type = classifyJson(payload);
      if (type === "review") state.review = payload;
      if (type === "batch") state.batches.push(payload);
    });
    await loadDefaultSv202DashboardChartData();
    await loadDefaultPt002HistoricalReplaySummary();

    if (!loaded.length) {
      elements.sourceLabel.textContent = "Manual load";
      elements.sourceDetail.textContent = "Use the JSON loader to select local evidence files.";
      render();
      return;
    }
    const canonicalPackCount = loaded.filter(({ path }) =>
      path.includes("money_flow_sv2_0_2_hyperliquid_public_") &&
      path.includes(`/${SV202_CANONICAL_TIMESTAMP}/batch_report.json`)
    ).length;
    const fallbackCount = loaded.length - canonicalPackCount;
    if (canonicalPackCount > 0) {
      elements.sourceLabel.textContent = "SV2.0.2 canonical packs loaded";
      elements.sourceDetail.textContent =
        `${canonicalPackCount} regenerated canonical pack JSON files loaded` +
        (fallbackCount > 0 ? `; ${fallbackCount} noncanonical local files also loaded.` : ".");
    } else {
      elements.sourceLabel.textContent = "Local JSON reports loaded";
      elements.sourceDetail.textContent = `${loaded.length} local JSON files loaded.`;
    }
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
        if (type === "sv20_summary") state.sv20Summary = payload;
        if (type === "sor_ev1_summary") state.sorEv1Summary = payload;
        if (type === "sor_ev2_summary") state.sorEv2Summary = payload;
        if (type === "sor_ev3_summary") state.sorEv3Summary = payload;
        if (type === "mf_orig_summary") state.mfOrigSummary = payload;
        if (type === "ev_audit_summary") state.evAuditSummary = payload;
        if (type === "pt_rt1_summary") state.ptRt1Summary = payload;
        if (type === "pt002_historical_replay_summary") state.pt002HistoricalReplay = payload;
      });
      state.selectedComponent = defaultEvidenceComponent(allSummaries());
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

  async function loadDefaultSv20Summaries() {
    for (const path of DEFAULT_SV20_SUMMARY_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (classifyJson(payload) === "sv20_summary") {
          state.sv20Summary = payload;
        }
      } catch (error) {
        console.warn(`Could not load ${path}`, error);
      }
    }
  }

  async function loadDefaultSorEvSummaries() {
    for (const path of DEFAULT_SOR_EV_SUMMARY_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        const type = classifyJson(payload);
        if (type === "sor_ev1_summary") state.sorEv1Summary = payload;
        if (type === "sor_ev2_summary") state.sorEv2Summary = payload;
        if (type === "sor_ev3_summary") state.sorEv3Summary = payload;
      } catch (error) {
        console.warn(`Could not load ${path}`, error);
      }
    }
  }

  async function loadDefaultMfOrigSummaries() {
    for (const path of DEFAULT_MF_ORIG_SUMMARY_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (classifyJson(payload) === "mf_orig_summary") {
          state.mfOrigSummary = payload;
        }
      } catch (error) {
        console.warn(`Could not load ${path}`, error);
      }
    }
  }

  async function loadDefaultEvAuditSummaries() {
    for (const path of DEFAULT_EV_AUDIT_SUMMARY_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (classifyJson(payload) === "ev_audit_summary") {
          state.evAuditSummary = payload;
        }
      } catch (error) {
        console.warn(`Could not load ${path}`, error);
      }
    }
  }

  async function loadDefaultPtRt1Summaries() {
    for (const path of DEFAULT_PT_RT1_SUMMARY_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (classifyJson(payload) === "pt_rt1_summary") {
          state.ptRt1Summary = payload;
          break;
        }
      } catch (error) {
        console.warn(`Could not load ${path}`, error);
      }
    }
  }

  async function loadDefaultPt002HistoricalReplaySummary() {
    for (const path of DEFAULT_PT002_REPLAY_SUMMARY_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (classifyJson(payload) === "pt002_historical_replay_summary") {
          state.pt002HistoricalReplay = payload;
          break;
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

  if (elements.themeSelector) {
    elements.themeSelector.addEventListener("change", () => {
      applyDashboardTheme(elements.themeSelector.value);
      destroyTradingViewChart();
      destroyHistoricalReplayChart();
      destroyEvidenceLabOverlayChart();
      render();
    });
  }

  elements.viewTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      setActiveView(tab.dataset.view || "evidence");
    });
  });

  applyDashboardTheme(state.theme);
  setActiveView(state.activeView);
  render();
  loadDefaultFiles();
  startLiveMarketPolling();
})();
