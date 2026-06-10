(function () {
  "use strict";

  const MF_ORIG_FULL_EQUITY_STRATEGY_IDS = new Set([
    "mf_orig_stage_filter_only_full_equity",
    "mf_orig_stage2_pullback_reclaim_full_equity",
    "mf_orig_1d_stage2_5_20_crossover_full_equity",
    "mf_orig_1d_stage2_breakout_resistance_full_equity",
  ]);
  const HIDDEN_DASHBOARD_STRATEGY_IDS = new Set([
    "baseline_current_money_flow_rules",
  ]);
  const HIDDEN_DASHBOARD_SYMBOLS = new Set([
    "SHIB",
    "KSHIB",
    "PEPE",
    "KPEPE",
    "OKB",
  ]);

  const DASHBOARD_THEME_STORAGE_KEY = "money-flow-dashboard-theme";
  const DASHBOARD_THEMES = new Set(["dark", "light", "red-zone"]);

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

  const DEFAULT_EV_AUDIT_SUMMARY_FILES = [
    "../../docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review_summary.json",
  ];

  const DEFAULT_PT_RT1_SUMMARY_FILES = [
    "../../reports/paper_runtime/pt_rt1_6_week2_active/summary.json",
    "../../docs/pt_rt1_6_founder_selected_week2_paper_slate_summary.json",
    "../../reports/paper_runtime/pt_rt1_5_2_week1_active/summary.json",
    "../../reports/paper_runtime/pt_rt1_5_3_transport_smoke/summary.json",
    "../../reports/paper_runtime/pt_rt1_5_2_transport_smoke/summary.json",
    "../../docs/pt_rt1_5_3_hyperliquid_testnet_size_precision_hotfix_summary.json",
    "../../docs/pt_rt1_5_2_signed_testnet_transport_smoke_and_active_restart_summary.json",
    "../../docs/pt_rt1_5_1_signed_testnet_transport_warm_start_and_mtm_summary.json",
  ];
  const DEFAULT_PT_RT1_DECISION_LOG_FILES = [
    "../../reports/paper_runtime/pt_rt1_6_week2_active/decisions.jsonl",
    "../../reports/paper_runtime/pt_rt1_5_2_week1_active/decisions.jsonl",
  ];
  const DEFAULT_PT_RT1_TRADE_LOG_FILES = [
    "../../reports/paper_runtime/pt_rt1_6_week2_active/trades.jsonl",
    "../../reports/paper_runtime/pt_rt1_5_2_week1_active/trades.jsonl",
  ];
  const DEFAULT_PT_RT1_TESTNET_LIFECYCLE_FILES = [
    "../../reports/paper_runtime/pt_rt1_6_week2_active/testnet_order_lifecycle.jsonl",
    "../../reports/paper_runtime/pt_rt1_5_2_week1_active/testnet_order_lifecycle.jsonl",
    "../../reports/paper_runtime/pt_rt1_5_3_transport_smoke/testnet_order_lifecycle.jsonl",
    "../../reports/paper_runtime/pt_rt1_5_2_transport_smoke/testnet_order_lifecycle.jsonl",
  ];
  const DEFAULT_PT_RT1_DAILY_REVIEW_FILES = [
    "../../reports/paper_reviews/pt_rt1_6_week2_active/latest_review.json",
  ];
  const PAPER_OBSERVATION_DECISION_LOG_LIMIT = 10000;
  const PAPER_OBSERVATION_TRADE_LOG_LIMIT = 10000;
  const COMPONENT_RESULTS_PAGE_SIZE = 10;
  const HISTORICAL_COMPARISON_PAGE_SIZE = 25;
  const PAPER_OBSERVATION_PAGE_SIZE = 25;
  const PAPER_OBSERVATION_ACTIVE_TIMEFRAMES = ["1h", "4h", "1d"];
  const PAPER_OBSERVATION_DISABLED_TIMEFRAMES = ["15m"];
  const PAPER_OBSERVATION_ACTIVE_REVIEW_START_UTC = "2026-06-07T00:00:00Z";
  const PAPER_OBSERVATION_ACTIVE_RUNTIME_SCOPE = "pt_rt1_6_week2_active";
  const PAPER_OBSERVATION_15M_STATUS = "disabled_for_week1_noise_reduction / diagnostic_only / not_active_paper_scoring";
  const PAPER_OBSERVATION_WEEK2_ACTIVE_LANE_IDS = [
    "money_flow_v1_2_baseline",
    "avoid_low_rolling_range_20",
    "mf_orig_1d_stage2_breakout_resistance_full_equity",
  ];
  const PAPER_OBSERVATION_WEEK2_ARCHIVED_LANE_IDS = [
    "avoid_low_rolling_range_50",
    "mf_orig_stage_filter_only_full_equity",
    "mf_orig_stage2_pullback_reclaim_full_equity",
    "mf_orig_1d_stage2_5_20_crossover_full_equity",
    "wildcard_btc_regime_guard",
    "wildcard_multi_timeframe_alignment",
    "wildcard_volatility_expansion_breakout",
  ];
  const PAPER_OBSERVATION_WEEK2_LANE_LABELS = {
    money_flow_v1_2_baseline: "Control / Baseline",
    avoid_low_rolling_range_20: "Diagnostic Comparator",
    mf_orig_1d_stage2_breakout_resistance_full_equity: "MF-ORIG Source-Faithful Candidate",
  };
  // DASH-PT2 display-only lane accent mapping (per-lane terminal colors).
  // Mapped to the current_truth.json active lane ids; unknown lanes stay neutral.
  const PAPER_OBSERVATION_LANE_ACCENTS = {
    money_flow_v1_2_baseline: "baseline",
    avoid_low_rolling_range_20: "diagnostic",
    mf_orig_1d_stage2_breakout_resistance_full_equity: "candidate",
  };
  const PAPER_OBSERVATION_CONFIGURED_SYMBOLS = ["AVAX", "BNB", "BTC", "DOGE", "ETH", "HYPE", "SOL", "SUI", "XRP"];
  const PAPER_OBSERVATION_WEEK2_LANE_POLICIES = {
    money_flow_v1_2_baseline: {
      display_name: "money_flow_v1_2_baseline",
      strategy_family: "money_flow_v1_2",
      role: "Control / Baseline",
      testnet_label: "Baseline-only gated testnet eligible",
      testnet_eligible: true,
      reason_codes: ["founder_selected_week2_active", "keep_as_control"],
    },
    avoid_low_rolling_range_20: {
      display_name: "avoid_low_rolling_range_20",
      strategy_family: "sor_ev3_diagnostic",
      role: "Diagnostic Comparator",
      testnet_label: "Synthetic-only / no testnet",
      testnet_eligible: false,
      reason_codes: ["founder_selected_week2_active", "candidate_synthetic_only"],
    },
    mf_orig_1d_stage2_breakout_resistance_full_equity: {
      display_name: "mf_orig_1d_stage2_breakout_resistance_full_equity",
      strategy_family: "mf_orig_source_faithful",
      role: "MF-ORIG Source-Faithful Candidate",
      testnet_label: "Synthetic-only / no testnet",
      testnet_eligible: false,
      reason_codes: ["founder_selected_week2_active", "candidate_synthetic_only"],
    },
  };
  const SV22_REPLAY_PERIOD = "SV2.2";
  const SV22_REPLAY_STRATEGY_IDS = new Set(PAPER_OBSERVATION_WEEK2_ACTIVE_LANE_IDS);
  const SV22_REPLAY_TIMEFRAMES = new Set(PAPER_OBSERVATION_ACTIVE_TIMEFRAMES);
  const SV22_REPLAY_FILL_ASSUMPTIONS = new Set(["next_candle_open", "next_candle_close"]);
  const RUN_LEDGER_DISPLAY_FILTER_BOUNDARY = "date filters are display-only, not canonical pack regeneration";

  const HYPERLIQUID_MAINNET_PUBLIC_INFO_URL = "https://api.hyperliquid.xyz/info";
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
  const PAPER_OBSERVATION_MARKET_REFRESH_MS = 1000;
  const PAPER_OBSERVATION_MARKET_STALE_MS = 120000;
  const LIVE_CHART_CANDLE_COUNT = 96;
  const LIVE_TIMEFRAME_MINUTES = {
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
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
    theme: initialDashboardTheme(),
    activeView: "paper-observation",
    experimentMode: "sv115_overlays",
    sv117FullSuiteRows: null,
    uat2Summary: null,
    uat34Summary: null,
    uat42Summary: null,
    pt0Summary: null,
    evAuditSummary: null,
    ptRt1Summary: null,
    ptRt1DecisionRows: [],
    ptRt1DecisionSource: "",
    ptRt1TradeRows: [],
    ptRt1TradeSource: "",
    ptRt1TestnetLifecycleRows: [],
    ptRt1TestnetLifecycleSource: "",
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
    paperObservationMarketData: {
      enabled: !livePollingDisabledByQuery(),
      status: livePollingDisabledByQuery() ? "paper_observation_public_mainnet_polling_disabled" : "not_started",
      disabledReason: livePollingDisabledByQuery() ? "query_flag" : null,
      endpoint: HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
      refreshMs: PAPER_OBSERVATION_MARKET_REFRESH_MS,
      lastUpdatedUtc: null,
      error: null,
      mids: {},
      previousMids: {},
      candles: [],
      indicatorSnapshot: null,
      selectedSymbol: "ETH",
      selectedTimeframe: "1h",
      privateSignedOrderEndpointsCalled: false,
      orderEndpointsCalled: false,
      liveEndpointCalled: false,
      timer: null,
      inFlight: false,
    },
    paperObservationChart: {
      chart: null,
      mount: null,
      candleSeries: null,
      volumeSeries: null,
      indicatorSeries: {},
      markerHandle: null,
      key: null,
      ready: false,
      pendingResizeFrame: null,
      resizeObserver: null,
      lastVisibleRange: null,
      fitContentApplied: false,
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
      symbol: "all",
      timeframe: "1h",
      laneId: "all",
      reviewWindow: "active_week",
      signalCategory: "entry_activity",
      terminalTab: "open",
      chartTarget: { symbol: "ETH", timeframe: "1h" },
      pagination: {
        signals: 1,
        openPositions: 1,
        closedTrades: 1,
      },
    },
    paperRuntimeControl: {
      available: false,
      running: false,
      status: "checking",
      duration: "24h",
      output: "pt_rt1_6_week2_active",
      pid: null,
      startedAtUtc: null,
      updatedAtUtc: null,
      outputDir: null,
      logPath: null,
      runtimeLogFiles: [],
      runtimeLogFilesRenderKey: "",
      safeFlags: ["--pt-rt1-5-week1-active", "--fresh-signal-only-after-runtime-start", "--enable-baseline-testnet-transport", "--pt-rt1-5-testnet-order-notional-usdc", "25", "--signal-evaluation-mode", "candle_close_only", "--disable-legacy-testnet-probes", "--public-mainnet-only"],
      message: "checking_local_control_server",
      inFlight: false,
      timer: null,
    },
    ptRtDailyReview: null,
    researchLog: { rows: [], loaded: false },
  };

  const elements = {
    viewTabs: Array.from(document.querySelectorAll("[data-view]")),
    viewPanels: Array.from(document.querySelectorAll("[data-view-panel]")),
    paperTerminalTabs: Array.from(document.querySelectorAll("[data-paper-terminal-tab]")),
    paperTerminalPanels: Array.from(document.querySelectorAll("[data-paper-terminal-panel]")),
    status: document.querySelector("#review-status"),
    sourceLabel: document.querySelector("#data-source-label"),
    sourceDetail: document.querySelector("#data-source-detail"),
    fileInput: document.querySelector("#json-file-input"),
    themeSelector: document.querySelector("#dashboard-theme-selector"),
    researchLogVerdictList: document.querySelector("#research-log-verdict-list"),
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
    paperObservationReviewWindowFilter: document.querySelector("#paper-observation-review-window-filter"),
    paperObservationSignalCategoryFilter: document.querySelector("#paper-observation-signal-category-filter"),
    paperRuntimeDuration: document.querySelector("#paper-runtime-duration"),
    paperRuntimeOutput: document.querySelector("#paper-runtime-output"),
    paperRuntimeStart: document.querySelector("#paper-runtime-start"),
    paperRuntimeStop: document.querySelector("#paper-runtime-stop"),
    paperRuntimeControlMessage: document.querySelector("#paper-runtime-control-message"),
    paperRuntimeControlStatus: document.querySelector("#paper-runtime-control-status"),
    paperRuntimeLogFiles: document.querySelector("#paper-runtime-log-files"),
    paperObservationHealthBanner: document.querySelector("#paper-observation-health-banner"),
    paperObservationTimeframeBreakdown: document.querySelector("#paper-observation-timeframe-breakdown"),
    paperObservationConnectionStatus: document.querySelector("#paper-observation-connection-status"),
    paperObservationScannerTable: document.querySelector("#paper-observation-scanner-table"),
    paperObservationSignalTable: document.querySelector("#paper-observation-signal-table"),
    paperObservationLaneTable: document.querySelector("#paper-observation-lane-table"),
    paperObservationLaneDetail: document.querySelector("#paper-observation-lane-detail"),
    paperObservationLiveChart: document.querySelector("#paper-observation-live-chart"),
    paperObservationProbeStatus: document.querySelector("#paper-observation-probe-status"),
    paperObservationTestnetLifecycle: document.querySelector("#paper-observation-testnet-lifecycle"),
    paperObservationDailyReview: document.querySelector("#paper-observation-daily-review"),
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
    const symbol = String(row?.symbol || row?.currency || row?.asset || "").toUpperCase();
    return (
      !HIDDEN_DASHBOARD_SYMBOLS.has(symbol) &&
      !HIDDEN_DASHBOARD_STRATEGY_IDS.has(String(strategyId || "")) &&
      isVisibleMfOrigStrategyId(strategyId)
    );
  }

  function isVisibleDashboardSymbol(symbol) {
    return !HIDDEN_DASHBOARD_SYMBOLS.has(String(symbol || "").toUpperCase());
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

  function setEmpty(target, message) {
    target.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
  }

  function setActiveView(view) {
    state.activeView = ["research-log", "paper-observation", "uat-cockpit", "uat-shadow"].includes(view)
      ? view
      : "paper-observation";
    elements.viewTabs.forEach((tab) => {
      tab.setAttribute("aria-selected", String(tab.dataset.view === state.activeView));
    });
    elements.viewPanels.forEach((panel) => {
      panel.hidden = panel.dataset.viewPanel !== state.activeView;
    });
    if (state.activeView === "uat-cockpit") {
      scheduleTradingViewResize();
    }
    syncPaperRuntimeControlPolling();
  }

  function setPaperObservationTerminalTab(tabName) {
    const allowedTabs = new Set(["open", "closed", "signals", "lifecycle", "logs", "scoreboard", "diagnostics"]);
    state.paperObservation.terminalTab = allowedTabs.has(tabName) ? tabName : "open";
    elements.paperTerminalTabs.forEach((tab) => {
      const selected = tab.dataset.paperTerminalTab === state.paperObservation.terminalTab;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
    });
    elements.paperTerminalPanels.forEach((panel) => {
      panel.hidden = panel.dataset.paperTerminalPanel !== state.paperObservation.terminalTab;
    });
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

  async function postHyperliquidPublicInfo(endpoint, payload) {
    if (![HYPERLIQUID_MAINNET_PUBLIC_INFO_URL, HYPERLIQUID_TESTNET_PUBLIC_INFO_URL].includes(endpoint)) {
      throw new Error("dashboard_live_chart_public_info_endpoint_not_allowlisted");
    }
    if (!payload || !LIVE_PUBLIC_INFO_TYPES.has(payload.type)) {
      throw new Error("dashboard_live_chart_public_info_type_not_allowlisted");
    }
    const body = JSON.stringify(payload);
    if (/\"user\"|\"action\"|\"signature\"|\"vaultAddress\"/i.test(body)) {
      throw new Error("dashboard_live_chart_private_or_order_payload_forbidden");
    }
    const response = await fetch(endpoint, {
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
        postHyperliquidPublicInfo(HYPERLIQUID_TESTNET_PUBLIC_INFO_URL, { type: "allMids" }),
        postHyperliquidPublicInfo(HYPERLIQUID_TESTNET_PUBLIC_INFO_URL, liveCandlePayload(symbol, timeframe)),
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

  async function refreshPaperObservationMarketData({ force = false } = {}) {
    const live = state.paperObservationMarketData;
    if (!live.enabled || live.inFlight || typeof fetch !== "function") return;
    live.inFlight = true;
    live.status = "paper_observation_public_mainnet_refreshing";
    renderPaperObservationConnectionStatus();
    try {
      const selectedRow = paperObservationSelectedRow();
      const selectedSymbol = selectedRow.resolved_venue_symbol || selectedRow.requested_symbol || "ETH";
      const selectedTimeframe = selectedPaperObservationTimeframe();
      const blocked = selectedRow.blocked || selectedRow.scanner_eligible === false;
      const staleSelection =
        live.selectedSymbol !== selectedSymbol ||
        !sameTimeframe(live.selectedTimeframe, selectedTimeframe) ||
        !Array.isArray(live.candles) ||
        !live.candles.length;
      const shouldLoadCandles = force || staleSelection || live.refreshMs <= 1000 || !live.lastUpdatedUtc;
      const midsPromise = postHyperliquidPublicInfo(HYPERLIQUID_MAINNET_PUBLIC_INFO_URL, { type: "allMids" });
      const candlePromise = blocked || !shouldLoadCandles
        ? Promise.resolve(null)
        : postHyperliquidPublicInfo(HYPERLIQUID_MAINNET_PUBLIC_INFO_URL, liveCandlePayload(selectedSymbol, selectedTimeframe));
      const [mids, candlePayload] = await Promise.all([midsPromise, candlePromise]);
      live.previousMids = live.mids || {};
      live.mids = mids || {};
      if (candlePayload) {
        live.candles = normalizeLiveCandles(candlePayload);
        live.indicatorSnapshot = live.candles.length
          ? computeDashboardIndicators(live.candles, selectedSymbol, selectedTimeframe)
          : null;
      }
      live.selectedSymbol = selectedSymbol;
      live.selectedTimeframe = selectedTimeframe;
      live.status = blocked ? "paper_observation_selected_symbol_blocked" : "paper_observation_public_mainnet_connected";
      live.lastUpdatedUtc = new Date().toISOString();
      live.error = blocked
        ? paperObservationText(selectedRow.reason_codes, "selected_symbol_blocked")
        : null;
      live.privateSignedOrderEndpointsCalled = false;
      live.orderEndpointsCalled = false;
      live.liveEndpointCalled = false;
    } catch (error) {
      live.status = "paper_observation_public_mainnet_unavailable";
      live.error = sanitizeLiveChartError(error);
    } finally {
      live.inFlight = false;
      renderPaperObservation();
    }
  }

  function startPaperObservationMarketPolling() {
    const live = state.paperObservationMarketData;
    if (!live.enabled || live.timer || typeof fetch !== "function") return;
    refreshPaperObservationMarketData({ force: true });
    live.timer = window.setInterval(refreshPaperObservationMarketData, PAPER_OBSERVATION_MARKET_REFRESH_MS);
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

  function paperObservationLaneId(row) {
    return row?.strategy_id || row?.lane_id || row?.strategy || "";
  }

  function paperObservationIsWeek2ActiveLane(laneId) {
    return PAPER_OBSERVATION_WEEK2_ACTIVE_LANE_IDS.includes(String(laneId || ""));
  }

  function paperObservationIsWeek2ArchivedLane(laneId) {
    return PAPER_OBSERVATION_WEEK2_ARCHIVED_LANE_IDS.includes(String(laneId || ""));
  }

  function paperObservationActiveLaneRows(summary = paperObservationSummary()) {
    const explicit = paperObservationRows(summary?.active_strategy_lanes || summary?.week2_active_strategy_lanes);
    const source = explicit.length ? explicit : paperObservationRows(summary?.strategy_lanes);
    const rows = source.filter((lane) => paperObservationIsWeek2ActiveLane(paperObservationLaneId(lane)));
    if (rows.length) return rows;
    return PAPER_OBSERVATION_WEEK2_ACTIVE_LANE_IDS.map(paperObservationConfiguredLaneRow);
  }

  function paperObservationArchivedLaneRows(summary = paperObservationSummary()) {
    const explicit = paperObservationRows(summary?.archived_strategy_lanes || summary?.week2_archived_strategy_lanes);
    const source = explicit.length ? explicit : paperObservationRows(summary?.strategy_lanes);
    const rows = source.filter((lane) => paperObservationIsWeek2ArchivedLane(paperObservationLaneId(lane)));
    if (rows.length) return rows;
    return PAPER_OBSERVATION_WEEK2_ARCHIVED_LANE_IDS.map((laneId) => ({
      lane_id: laneId,
      strategy_id: laneId,
      display_name: laneId,
      paper_only: true,
      production_approved: false,
      live_approved: false,
      testnet_eligible: false,
      reason_codes: ["founder_archived_from_week2", "not_default_active", "historical_reference_only"],
    }));
  }

  function paperObservationWeek2LaneLabel(laneId) {
    return PAPER_OBSERVATION_WEEK2_LANE_LABELS[laneId] || "Archived / historical reference";
  }

  function paperObservationLaneAccent(laneId) {
    return PAPER_OBSERVATION_LANE_ACCENTS[String(laneId || "")] || "neutral";
  }

  function paperObservationLaneChip(laneId, label) {
    // DASH-PT2 display-only lane chip: color-codes lane cells consistently
    // across watchlist/blotter/scoreboard/lane detail. Markup/visual only —
    // no data, filter, polling, or handler behavior changes.
    const text = label === undefined || label === null ? laneId : label;
    if (!text) return escapeHtml("n/a");
    return `<span class="paper-lane-chip" data-lane-accent="${escapeHtml(paperObservationLaneAccent(laneId))}">${escapeHtml(String(text))}</span>`;
  }

  function paperObservationConfiguredLaneRow(laneId) {
    const policy = PAPER_OBSERVATION_WEEK2_LANE_POLICIES[laneId] || {};
    return {
      lane_id: laneId,
      strategy_id: laneId,
      display_name: policy.display_name || laneId,
      strategy_family: policy.strategy_family || "paper_observation",
      paper_only: true,
      production_approved: false,
      live_approved: false,
      starting_equity: 10000,
      initial_equity: 10000,
      pnl_source: "Synthetic Ledger",
      signal_truth: "Public Mainnet Candles",
      testnet_label: policy.testnet_label || "Synthetic-only / no testnet",
      testnet_eligible: Boolean(policy.testnet_eligible),
      role: policy.role || paperObservationWeek2LaneLabel(laneId),
      reason_codes: policy.reason_codes || ["founder_selected_week2_active"],
      rule_summary: "Configured Week 2 lane metadata; runtime rows appear after the paper run starts.",
    };
  }

  function paperObservationActiveTimeframes(summary = paperObservationSummary()) {
    const active = paperObservationRows(summary?.active_timeframes);
    return active.length ? active.map(canonicalTimeframe) : PAPER_OBSERVATION_ACTIVE_TIMEFRAMES;
  }

  function paperObservationDisabledTimeframes(summary = paperObservationSummary()) {
    const disabled = paperObservationRows(summary?.disabled_timeframes);
    return disabled.length ? disabled.map(canonicalTimeframe) : PAPER_OBSERVATION_DISABLED_TIMEFRAMES;
  }

  function paperObservationActiveReviewStart(summary = paperObservationSummary()) {
    return summary?.active_review_start_utc || PAPER_OBSERVATION_ACTIVE_REVIEW_START_UTC;
  }

  function paperObservationIsActiveTimeframe(timeframe, summary = paperObservationSummary()) {
    const canonical = canonicalTimeframe(timeframe);
    return paperObservationActiveTimeframes(summary).includes(canonical);
  }

  function paperObservationIsDisabledTimeframe(timeframe, summary = paperObservationSummary()) {
    const canonical = canonicalTimeframe(timeframe);
    return paperObservationDisabledTimeframes(summary).includes(canonical);
  }

  function paperObservationTimeframeScopeLabel(value = state.paperObservation.timeframe) {
    if (value === "all_active") return "sum across active paper timeframes only: 1h + 4h + 1d";
    if (value === "15m_legacy") return "15m paused / legacy";
    return `${displayTimeframe(value)} selected timeframe only`;
  }

  function paperObservationPrice(value) {
    return compactNumber(value, 8);
  }

  function paperObservationUsdc(value) {
    return compactNumber(value, 2);
  }

  function paperObservationDecisionTime(row) {
    return row?.decision_time || row?.signal_candle_close_time || row?.signal_candle_open_time || row?.exit_time || row?.entry_time || row?.entry_signal_time || "";
  }

  function paperObservationSignalKey(row) {
    return [
      row?.action || "paper_opened",
      row?.strategy_id || row?.lane_id || "",
      row?.symbol || row?.requested_symbol || row?.resolved_venue_symbol || "",
      canonicalTimeframe(row?.timeframe || ""),
      row?.signal_candle_close_time || row?.signal_candle_open_time || row?.decision_time || "",
    ].join("|");
  }

  function paperObservationRecentSignalRows(summary) {
    const seen = new Set();
    const rows = [
      ...paperObservationRows(summary?.intended_entry_signals),
      ...paperObservationRows(state.ptRt1DecisionRows).filter((row) => row.action === "paper_opened"),
      ...paperObservationRows(summary?.latest_decisions).filter((row) => row.action === "paper_opened"),
    ]
      .filter((row) => row && (row.action === "paper_opened" || !row.action))
      .filter((row) => {
        const key = paperObservationSignalKey(row);
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .sort((left, right) => String(paperObservationDecisionTime(right)).localeCompare(String(paperObservationDecisionTime(left))));
    return rows;
  }

  function paperObservationDecisionRows(summary) {
    const seen = new Set();
    return [
      ...paperObservationRows(summary?.intended_entry_signals),
      ...paperObservationRows(state.ptRt1DecisionRows),
      ...paperObservationRows(summary?.latest_decisions),
    ]
      .filter(Boolean)
      .filter((row) => {
        const key = paperObservationSignalKey(row);
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .sort((left, right) => String(paperObservationDecisionTime(right)).localeCompare(String(paperObservationDecisionTime(left))));
  }

  function paperObservationDecisionCategoryMatches(row) {
    const action = String(row?.action || "paper_opened");
    const reasons = paperObservationRows(row?.reason_codes).map(String);
    const category = state.paperObservation.signalCategory || "entry_activity";
    if (category === "entry_activity") return action === "paper_opened" || reasons.includes("intended_entry");
    if (category === "intended_entries") return action === "paper_opened" || reasons.includes("intended_entry");
    if (category === "actual_opens") return action === "paper_opened";
    if (category === "blocked") {
      return action === "no_trade" || action === "blocked_by_candidate_filter" || reasons.some((reason) => reason.includes("blocked"));
    }
    if (category === "exits") return action === "paper_closed" || action === "paper_trim";
    if (category === "duplicates") return action === "duplicate_ignored" || reasons.includes("duplicate_ignored") || reasons.includes("duplicate_signal_ignored");
    if (category === "data_unavailable") return action === "data_unavailable" || reasons.some((reason) => reason.includes("unavailable"));
    return true;
  }

  function paperObservationDateFilterMatches(row) {
    const start = state.paperObservation.dateStart;
    const end = state.paperObservation.dateEnd;
    const timestamp = paperObservationDecisionTime(row);
    const reviewWindow = state.paperObservation.reviewWindow || "active_week";
    const activeStart = paperObservationActiveReviewStart();
    if (reviewWindow !== "all_runtime") {
      if (!timestamp) return false;
      if (reviewWindow === "pre_cutover" && String(timestamp) >= activeStart) return false;
      if (reviewWindow === "active_week" && String(timestamp) < activeStart) return false;
    }
    if (!start && !end) return true;
    if (!timestamp) return false;
    const day = String(timestamp).slice(0, 10);
    if (start && day < start) return false;
    if (end && day > end) return false;
    return true;
  }

  function paperObservationRowSymbol(row) {
    return row?.symbol || row?.resolved_venue_symbol || row?.requested_symbol || row?.canonical_symbol || "";
  }

  function paperObservationRowTimeframe(row) {
    return canonicalTimeframe(row?.timeframe || row?.component_timeframe || "");
  }

  function paperObservationRowLane(row) {
    return paperObservationLaneId(row);
  }

  function paperObservationSymbolMatchesSelection(row, selectedSymbol) {
    if (!selectedSymbol || selectedSymbol === "all") return true;
    const rowSymbol = paperObservationRowSymbol(row);
    if (rowSymbol === selectedSymbol || row?.requested_symbol === selectedSymbol || row?.resolved_venue_symbol === selectedSymbol) return true;
    const selectedRow = paperObservationBaseScannerRows().find((candidate) =>
      candidate.requested_symbol === selectedSymbol ||
      candidate.resolved_venue_symbol === selectedSymbol ||
      candidate.canonical_symbol === selectedSymbol,
    );
    return Boolean(selectedRow && (
      rowSymbol === selectedRow.requested_symbol ||
      rowSymbol === selectedRow.resolved_venue_symbol ||
      row?.requested_symbol === selectedRow.requested_symbol ||
      row?.resolved_venue_symbol === selectedRow.resolved_venue_symbol
    ));
  }

  function paperObservationFiltersMatch(row, { includeDate = true, ignoreSymbol = false, ignoreTimeframe = false } = {}) {
    const selectedSymbol = state.paperObservation.symbol;
    const selectedTimeframe = state.paperObservation.timeframe;
    const selectedLane = state.paperObservation.laneId;
    const rowTimeframe = paperObservationRowTimeframe(row);
    const rowLane = paperObservationRowLane(row);
    const laneMatches =
      selectedLane === "all"
        ? (!rowLane || paperObservationIsWeek2ActiveLane(rowLane))
        : rowLane === selectedLane;
    const activeTimeframes = paperObservationActiveTimeframes();
    const timeframeMatches =
      ignoreTimeframe ||
      (selectedTimeframe === "all" && activeTimeframes.includes(rowTimeframe)) ||
      (selectedTimeframe === "all_active" && activeTimeframes.includes(rowTimeframe)) ||
      (selectedTimeframe === "15m_legacy" && paperObservationIsDisabledTimeframe(rowTimeframe)) ||
      sameTimeframe(rowTimeframe, selectedTimeframe);
    return (
      (ignoreSymbol || paperObservationSymbolMatchesSelection(row, selectedSymbol)) &&
      timeframeMatches &&
      laneMatches &&
      (!includeDate || paperObservationDateFilterMatches(row))
    );
  }

  function resetPaperObservationPagination() {
    state.paperObservation.pagination = {
      signals: 1,
      openPositions: 1,
      closedTrades: 1,
    };
  }

  function paperObservationPageRows(rows, pageKey) {
    const totalPages = Math.max(1, Math.ceil(rows.length / PAPER_OBSERVATION_PAGE_SIZE));
    const currentPage = Math.min(Math.max(1, state.paperObservation.pagination?.[pageKey] || 1), totalPages);
    state.paperObservation.pagination[pageKey] = currentPage;
    const start = (currentPage - 1) * PAPER_OBSERVATION_PAGE_SIZE;
    return {
      currentPage,
      totalPages,
      totalRows: rows.length,
      rows: rows.slice(start, start + PAPER_OBSERVATION_PAGE_SIZE),
    };
  }

  function paperObservationPaginationControls(pageKey, page) {
    return `
      <div class="paper-observation-pagination" data-paper-pagination="${escapeHtml(pageKey)}">
        <button class="segment-button" type="button" data-paper-page-prev="${escapeHtml(pageKey)}" ${page.currentPage <= 1 ? "disabled" : ""}>Previous</button>
        <span>Page ${escapeHtml(String(page.currentPage))} / ${escapeHtml(String(page.totalPages))}</span>
        <span>${escapeHtml(String(page.totalRows))} rows</span>
        <button class="segment-button" type="button" data-paper-page-next="${escapeHtml(pageKey)}" ${page.currentPage >= page.totalPages ? "disabled" : ""}>Next</button>
      </div>
    `;
  }

  function attachPaperObservationPagination(target, pageKey) {
    if (!target) return;
    target.querySelectorAll(`[data-paper-page-prev="${pageKey}"]`).forEach((button) => {
      button.addEventListener("click", () => {
        state.paperObservation.pagination[pageKey] = Math.max(1, (state.paperObservation.pagination[pageKey] || 1) - 1);
        renderPaperObservation();
      });
    });
    target.querySelectorAll(`[data-paper-page-next="${pageKey}"]`).forEach((button) => {
      button.addEventListener("click", () => {
        state.paperObservation.pagination[pageKey] = (state.paperObservation.pagination[pageKey] || 1) + 1;
        renderPaperObservation();
      });
    });
  }

  function paperObservationClosedRowComplete(row) {
    if (!row) return false;
    const entryTime = row.entry_time || row.entry_fill_time || row.entry_signal_time;
    const exitTime = row.exit_time || row.exit_fill_time || row.exit_signal_time;
    return Boolean(
      entryTime &&
      exitTime &&
      Number.isFinite(decimal(row.entry_price, NaN)) &&
      Number.isFinite(decimal(row.exit_price, NaN)) &&
      Number.isFinite(decimal(row.quantity, NaN)) &&
      Number.isFinite(decimal(row.net_pnl, NaN)) &&
      Number.isFinite(decimal(row.equity_after, NaN)),
    );
  }

  function paperObservationClosedRows(summary) {
    const seen = new Set();
    return [
      ...paperObservationRows(summary?.closed_trades || summary?.latest_trades),
      ...paperObservationRows(state.ptRt1TradeRows),
      ...paperObservationRows(state.ptRt1DecisionRows).filter((row) => row.action === "paper_closed" && paperObservationClosedRowComplete(row)),
      ...paperObservationRows(summary?.latest_decisions).filter((row) => row.action === "paper_closed" && paperObservationClosedRowComplete(row)),
    ]
      .filter(Boolean)
      .filter(paperObservationClosedRowComplete)
      .filter((row) => {
        const key = [
          row.paper_trade_id || row.trade_id || "",
          "paper_closed",
          paperObservationRowLane(row),
          paperObservationRowSymbol(row),
          paperObservationRowTimeframe(row),
          row.exit_time || row.exit_fill_time || row.decision_time || row.signal_candle_close_time || "",
        ].join("|");
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .sort((left, right) => String(left.exit_time || left.exit_fill_time || left.decision_time || "").localeCompare(String(right.exit_time || right.exit_fill_time || right.decision_time || "")) * -1);
  }

  function paperObservationText(value, fallback = "data_not_available_in_pt_rt1_bundle") {
    if (Array.isArray(value)) return value.join(", ") || fallback;
    if (value === null || value === undefined || value === "") return fallback;
    return String(value);
  }

  function paperObservationBytes(value) {
    const bytes = decimal(value, NaN);
    if (!Number.isFinite(bytes)) return "n/a";
    if (bytes >= 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    if (bytes >= 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${bytes} bytes`;
  }

  function normalizePaperRuntimeControlStatus(payload, available = true) {
    const safeFlags = Array.isArray(payload?.safe_flags) && payload.safe_flags.length
      ? payload.safe_flags
      : ["--pt-rt1-5-week1-active", "--pt-rt1-5-testnet-order-notional-usdc", "25", "--disable-testnet-probes", "--public-mainnet-only"];
    state.paperRuntimeControl = {
      ...state.paperRuntimeControl,
      available,
      running: Boolean(payload?.running),
      status: payload?.status || (available ? "idle" : "unavailable"),
      pid: payload?.pid || null,
      startedAtUtc: payload?.started_at_utc || null,
      updatedAtUtc: payload?.updated_at_utc || null,
      duration: payload?.duration || state.paperRuntimeControl.duration,
      output: payload?.output || state.paperRuntimeControl.output,
      outputDir: payload?.output_dir || null,
      logPath: payload?.log_path || null,
      runtimeLogFiles: Array.isArray(payload?.runtime_log_files) ? payload.runtime_log_files : [],
      safeFlags,
      message: payload?.message || (available ? "local_control_server_ready" : "local_control_server_unavailable"),
      inFlight: false,
    };
  }

  async function paperRuntimeControlRequest(path, options = {}) {
    const response = await fetch(path, {
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!response.ok) {
      let message = `HTTP ${response.status}`;
      try {
        const payload = await response.json();
        message = payload?.message || message;
      } catch (_error) {
        // Static file servers return HTML/404 here; render the explicit unavailable state.
      }
      throw new Error(message);
    }
    return response.json();
  }

  async function refreshPaperRuntimeControlStatus() {
    try {
      const payload = await paperRuntimeControlRequest("/api/paper-runtime/status");
      normalizePaperRuntimeControlStatus(payload, true);
    } catch (error) {
      normalizePaperRuntimeControlStatus(
        {
          running: false,
          status: "unavailable",
          message: "Start/stop requires launching the local control server.",
          safe_flags: ["--pt-rt1-5-week1-active", "--fresh-signal-only-after-runtime-start", "--enable-baseline-testnet-transport", "--pt-rt1-5-testnet-order-notional-usdc", "25", "--signal-evaluation-mode", "candle_close_only", "--disable-legacy-testnet-probes", "--public-mainnet-only"],
        },
        false,
      );
      console.warn("Paper runtime control unavailable", error);
    }
    renderPaperRuntimeControl();
  }

  function startPaperRuntimeControlPolling() {
    if (state.paperRuntimeControl.timer) return;
    refreshPaperRuntimeControlStatus();
    state.paperRuntimeControl.timer = window.setInterval(refreshPaperRuntimeControlStatus, 10000);
  }

  function stopPaperRuntimeControlPolling() {
    if (!state.paperRuntimeControl.timer) return;
    window.clearInterval(state.paperRuntimeControl.timer);
    state.paperRuntimeControl.timer = null;
  }

  function syncPaperRuntimeControlPolling() {
    if (state.activeView === "paper-observation") {
      startPaperRuntimeControlPolling();
    } else {
      stopPaperRuntimeControlPolling();
    }
  }

  async function startPaperRuntime() {
    if (state.paperRuntimeControl.inFlight) return;
    state.paperRuntimeControl.inFlight = true;
    renderPaperRuntimeControl();
    try {
      const payload = await paperRuntimeControlRequest("/api/paper-runtime/start", {
        method: "POST",
        body: JSON.stringify({
          duration: state.paperRuntimeControl.duration,
          output: state.paperRuntimeControl.output,
        }),
      });
      normalizePaperRuntimeControlStatus(payload, true);
    } catch (error) {
      state.paperRuntimeControl = {
        ...state.paperRuntimeControl,
        inFlight: false,
        message: error?.message || "paper_runtime_start_failed",
      };
    }
    renderPaperRuntimeControl();
  }

  async function stopPaperRuntime() {
    if (state.paperRuntimeControl.inFlight) return;
    state.paperRuntimeControl.inFlight = true;
    renderPaperRuntimeControl();
    try {
      const payload = await paperRuntimeControlRequest("/api/paper-runtime/stop", {
        method: "POST",
        body: JSON.stringify({}),
      });
      normalizePaperRuntimeControlStatus(payload, true);
    } catch (error) {
      state.paperRuntimeControl = {
        ...state.paperRuntimeControl,
        inFlight: false,
        message: error?.message || "paper_runtime_stop_failed",
      };
    }
    renderPaperRuntimeControl();
  }

  function renderPaperRuntimeLogFiles(control) {
    if (!elements.paperRuntimeLogFiles) return;
    const files = Array.isArray(control.runtimeLogFiles) ? control.runtimeLogFiles : [];
    const renderKey = JSON.stringify(files.map((file) => ({
      key: file?.key,
      path: file?.path,
      exists: Boolean(file?.exists),
      size: file?.size_bytes,
      modified: file?.modified_at_utc,
    })));
    if (state.paperRuntimeControl.runtimeLogFilesRenderKey === renderKey && elements.paperRuntimeLogFiles.innerHTML) {
      return;
    }
    const previousLogList = elements.paperRuntimeLogFiles.querySelector(".paper-runtime-log-list");
    const previousScrollTop = previousLogList ? previousLogList.scrollTop : 0;
    state.paperRuntimeControl.runtimeLogFilesRenderKey = renderKey;
    if (!files.length) {
      elements.paperRuntimeLogFiles.innerHTML = `
        <div class="methodology-warning compact">Runtime log metadata is unavailable. Start the local dashboard control server to expose log paths.</div>
      `;
      return;
    }
    const latestFile = files
      .filter((file) => file?.modified_at_utc)
      .sort((left, right) => String(right.modified_at_utc).localeCompare(String(left.modified_at_utc)))[0];
    const rows = files.map((file) => {
      const size = Number.isFinite(Number(file?.size_bytes)) ? paperObservationBytes(Number(file.size_bytes)) : "n/a";
      const existsLabel = file?.exists ? "present" : "missing";
      const command = file?.tail_command || (file?.absolute_path ? `tail -n 50 -F ${file.absolute_path}` : "tail command unavailable");
      return `
        <article class="paper-runtime-log-row">
          <div>
            <strong>${escapeHtml(file?.label || file?.key || "runtime log")}</strong>
            <span>${escapeHtml(file?.role || "runtime log file")}</span>
            <code>${escapeHtml(file?.path || "path_unavailable")}</code>
          </div>
          <div class="paper-runtime-log-meta">
            <span class="${file?.exists ? "status-good" : "status-waiting"}">${escapeHtml(existsLabel)}</span>
            <span>${escapeHtml(size)}</span>
            <span>${escapeHtml(file?.modified_at_utc || "not_written")}</span>
          </div>
          <code class="paper-runtime-tail-command">${escapeHtml(command)}</code>
          <p>${escapeHtml(file?.empty_hint || "tail -F waits for newly appended lines; use -n to show existing rows.")}</p>
        </article>
      `;
    }).join("");
    elements.paperRuntimeLogFiles.innerHTML = `
      <div class="paper-runtime-log-heading">
        <div>
          <p class="eyebrow">Runtime Logs</p>
          <h3>Read-only log files</h3>
        </div>
        <span>${escapeHtml(latestFile ? `latest: ${latestFile.label || latestFile.key} @ ${latestFile.modified_at_utc}` : "no modified files yet")}</span>
      </div>
      <div class="methodology-warning compact">
        Use <code>.venv/bin/python scripts/watch_pt_rt1_runtime.py --status</code> for exact terminal status. Testnet lifecycle is separate from Synthetic PnL.
      </div>
      <div class="paper-runtime-log-list">${rows}</div>
    `;
    const nextLogList = elements.paperRuntimeLogFiles.querySelector(".paper-runtime-log-list");
    if (nextLogList) nextLogList.scrollTop = previousScrollTop;
  }

  function renderPaperRuntimeControl() {
    const control = state.paperRuntimeControl;
    if (elements.paperRuntimeDuration) {
      elements.paperRuntimeDuration.value = control.duration;
      elements.paperRuntimeDuration.disabled = control.running || control.inFlight;
      elements.paperRuntimeDuration.onchange = () => {
        state.paperRuntimeControl.duration = elements.paperRuntimeDuration.value;
        renderPaperRuntimeControl();
      };
    }
    if (elements.paperRuntimeOutput) {
      elements.paperRuntimeOutput.value = control.output;
      elements.paperRuntimeOutput.disabled = control.running || control.inFlight;
      elements.paperRuntimeOutput.onchange = () => {
        state.paperRuntimeControl.output = elements.paperRuntimeOutput.value;
        renderPaperRuntimeControl();
      };
    }
    if (elements.paperRuntimeStart) {
      elements.paperRuntimeStart.disabled = control.running || control.inFlight;
      elements.paperRuntimeStart.onclick = startPaperRuntime;
    }
    if (elements.paperRuntimeStop) {
      elements.paperRuntimeStop.disabled = !control.available || !control.running || control.inFlight;
      elements.paperRuntimeStop.onclick = stopPaperRuntime;
    }
    if (!elements.paperRuntimeControlStatus) return;
    const statusLabel = control.available ? (control.running ? "running" : control.status || "idle") : "unavailable";
    const caffeinateLabel = control.running ? "active" : "waiting_for_start";
    const latestRuntimeFile = (control.runtimeLogFiles || [])
      .filter((file) => file?.modified_at_utc)
      .sort((left, right) => String(right.modified_at_utc).localeCompare(String(left.modified_at_utc)))[0];
    const exactSafeFlags = (control.safeFlags || []).join(" ");
    const safeProfile = [
      "Week 2 active scope",
      "fresh-signal gate",
      "candle-close only",
      "public-mainnet truth",
      "baseline-only 25 USDC testnet gate",
      "legacy probes disabled",
    ].join(" / ");
    const serverMessage =
      control.message === "paper_runtime_started_with_caffeinate"
        ? "runtime_started_with_mac_caffeinate"
        : control.message || "local_control_server_ready";
    if (elements.paperRuntimeControlMessage) {
      elements.paperRuntimeControlMessage.innerHTML = `
        <span>Control server message</span>
        <strong>${escapeHtml(serverMessage)}</strong>
      `;
    }
    const logStats = paperObservationSummary()?.decision_log_stats || {};
    elements.paperRuntimeControlStatus.innerHTML = `
      <div class="micro-grid paper-runtime-details-grid">
        <div><span>Runtime status</span><strong>${escapeHtml(statusLabel)}</strong></div>
        <div><span>PID</span><strong>${escapeHtml(control.pid || "n/a")}</strong></div>
        <div><span>Latest runtime artifact</span><strong>${escapeHtml(latestRuntimeFile ? `${latestRuntimeFile.label || latestRuntimeFile.key} @ ${latestRuntimeFile.modified_at_utc}` : "not_written")}</strong></div>
        <div class="paper-runtime-caffeinate-detail"><span>Caffeinate</span><strong class="${control.running ? "status-good" : "status-waiting"}">${escapeHtml(caffeinateLabel)}</strong></div>
        <div class="paper-runtime-safety-flags"><span>Safety profile</span><strong title="${escapeHtml(exactSafeFlags)}">${escapeHtml(safeProfile)}</strong></div>
      </div>
      ${logStats.decisions_jsonl_warning ? '<div class="methodology-warning compact">Decision log size is above the review threshold. Stop the run or keep compact logging enabled before another long run.</div>' : ""}
    `;
    renderPaperRuntimeLogFiles(control);
  }

  function paperObservationBaseScannerRows() {
    const summary = paperObservationSummary();
    const rows = paperObservationRows(summary?.scanner_universe);
    if (rows.length) return rows;
    const symbols = paperObservationRows(summary?.symbols).length
      ? paperObservationRows(summary?.symbols)
      : PAPER_OBSERVATION_CONFIGURED_SYMBOLS;
    return symbols.map((symbol) => ({
      requested_symbol: symbol,
      resolved_venue_symbol: symbol,
      canonical_symbol: symbol,
      sources: ["configured_paper_symbols"],
      supported_by_venue: true,
      precision_ready: true,
      data_health: "pending_runtime_refresh",
      scanner_eligible: true,
      blocked: false,
      reason_codes: ["configured_paper_symbol_universe"],
    }));
  }

  function paperObservationSelectedRow() {
    const rows = paperObservationBaseScannerRows();
    const selected = paperObservationChartTarget().symbol || state.paperObservation.symbol;
    if (selected && selected !== "all") {
      const match = rows.find((row) =>
        row.requested_symbol === selected ||
        row.resolved_venue_symbol === selected ||
        row.canonical_symbol === selected,
      );
      if (match) return match;
    }
    return rows.find((row) => row.scanner_eligible && !row.blocked && row.resolved_venue_symbol === "ETH") ||
      rows.find((row) => row.scanner_eligible && !row.blocked) ||
      rows[0] ||
      { requested_symbol: "ETH", resolved_venue_symbol: "ETH", scanner_eligible: true, blocked: false, reason_codes: [] };
  }

  function paperObservationChartCandidates() {
    const summary = paperObservationSummary();
    const openRows = Object.values(summary?.paper_runtime_state?.open_positions_by_key || {});
    return [
      ...paperObservationRecentSignalRows(summary),
      ...openRows,
      ...paperObservationClosedRows(summary),
    ]
      .filter((row) => paperObservationRowSymbol(row) && paperObservationRowTimeframe(row))
      .filter((row) =>
        paperObservationFiltersMatch(row, {
          ignoreSymbol: state.paperObservation.symbol === "all",
          ignoreTimeframe: state.paperObservation.timeframe === "all",
        }),
      )
      .sort((left, right) => String(paperObservationDecisionTime(right) || right.exit_time || right.entry_time || "").localeCompare(String(paperObservationDecisionTime(left) || left.exit_time || left.entry_time || "")));
  }

  function paperObservationChartTarget() {
    const explicitSymbol = state.paperObservation.symbol !== "all" ? state.paperObservation.symbol : "";
    const selectedScope = state.paperObservation.timeframe;
    const explicitTimeframe =
      selectedScope === "15m_legacy"
        ? "15m"
        : selectedScope === "all_active" || selectedScope === "all"
        ? "1h"
        : selectedScope || "";
    const previous = state.paperObservation.chartTarget || {};
    const latest = paperObservationChartCandidates()[0] || {};
    const symbol = explicitSymbol || paperObservationRowSymbol(latest) || previous.symbol || "ETH";
    const timeframe = explicitTimeframe || paperObservationRowTimeframe(latest) || previous.timeframe || "1h";
    state.paperObservation.chartTarget = { symbol, timeframe };
    return state.paperObservation.chartTarget;
  }

  function selectedPaperObservationVenueSymbol() {
    const target = paperObservationChartTarget();
    const row = paperObservationBaseScannerRows().find((candidate) =>
      candidate.requested_symbol === target.symbol ||
      candidate.resolved_venue_symbol === target.symbol ||
      candidate.canonical_symbol === target.symbol,
    );
    return row?.resolved_venue_symbol || target.symbol || "ETH";
  }

  function selectedPaperObservationTimeframe() {
    return paperObservationChartTarget().timeframe || "1h";
  }

  function paperObservationSymbolOptions() {
    const rows = paperObservationBaseScannerRows();
    const options = rows.map((row) => {
      const requested = row.requested_symbol || row.resolved_venue_symbol || row.canonical_symbol;
      const resolved = row.resolved_venue_symbol && row.resolved_venue_symbol !== requested ? ` -> ${row.resolved_venue_symbol}` : "";
      const blocked = row.blocked ? " blocked" : "";
      return {
        value: requested,
        label: `${requested}${resolved}${blocked}`,
      };
    });
    return options.length ? options : [{ value: "ETH", label: "ETH" }];
  }

  function paperObservationLiveMid(row) {
    const venueSymbol = row.resolved_venue_symbol || row.requested_symbol;
    const mids = state.paperObservationMarketData.mids || {};
    const liveMid = Object.prototype.hasOwnProperty.call(mids, venueSymbol) ? mids[venueSymbol] : null;
    return liveMid ?? row.public_mid ?? null;
  }

  function paperObservationTickClass(row) {
    const venueSymbol = row.resolved_venue_symbol || row.requested_symbol;
    const current = decimal((state.paperObservationMarketData.mids || {})[venueSymbol], NaN);
    const previous = decimal((state.paperObservationMarketData.previousMids || {})[venueSymbol], NaN);
    if (!Number.isFinite(current) || !Number.isFinite(previous) || current === previous) return "tick-flat";
    return current > previous ? "tick-up" : "tick-down";
  }

  function paperObservationMdHealth(row) {
    if (row.mid_health_status === "mid_unavailable_but_candles_available") return "mid_unavailable_but_candles_available";
    if (row.mid_health_status === "mid_warning_non_blocking") return "mid_stale_or_thin_tick";
    if (row.candle_strategy_ready === true || row.strategy_data_status === "candle_ready") return "healthy";
    const lastTick = Date.parse(row.last_live_tick_utc || "");
    const mid = decimal(row.public_mid, NaN);
    if (!Number.isFinite(mid) || !Number.isFinite(lastTick)) return "mid_stale_or_thin_tick";
    return Date.now() - lastTick > PAPER_OBSERVATION_MARKET_STALE_MS ? "mid_stale_or_thin_tick" : "healthy";
  }

  function paperObservationScannerRows() {
    const live = state.paperObservationMarketData || {};
    return paperObservationBaseScannerRows().map((row) => ({
      ...row,
      public_mid: paperObservationLiveMid(row),
      live_tick_status: live.status || "not_started",
      last_live_tick_utc: live.lastUpdatedUtc,
      endpoint_category: "public_read_only",
      mid_health_status: row.data_health === "stale" ? "mid_warning_non_blocking" : row.mid_health_status,
    }));
  }

  function paperObservationRuntimeMarkers() {
    const summary = paperObservationSummary();
    const target = paperObservationChartTarget();
    const chartSymbolMatches = (row) => {
      const rowSymbol = paperObservationRowSymbol(row);
      if (rowSymbol === target.symbol || row?.requested_symbol === target.symbol || row?.resolved_venue_symbol === target.symbol) return true;
      const targetRow = paperObservationBaseScannerRows().find((candidate) =>
        candidate.requested_symbol === target.symbol ||
        candidate.resolved_venue_symbol === target.symbol ||
        candidate.canonical_symbol === target.symbol,
      );
      return Boolean(targetRow && (
        rowSymbol === targetRow.resolved_venue_symbol ||
        rowSymbol === targetRow.requested_symbol ||
        row?.requested_symbol === targetRow.requested_symbol ||
        row?.resolved_venue_symbol === targetRow.resolved_venue_symbol
      ));
    };
    const openSignals = paperObservationRecentSignalRows(summary)
      .filter((row) => paperObservationFiltersMatch(row, { includeDate: true }))
      .filter((row) => chartSymbolMatches(row) && sameTimeframe(paperObservationRowTimeframe(row), target.timeframe))
      .map((row) => ({
        ...row,
        marker_type: "paper_opened",
        time: row.signal_candle_close_time || row.entry_time || row.decision_time,
        label: `${paperObservationRowLane(row) || "paper"} opened`,
      }));
    const openPositions = Object.values(summary?.paper_runtime_state?.open_positions_by_key || {})
      .filter((row) => paperObservationFiltersMatch(row, { includeDate: true }))
      .filter((row) => chartSymbolMatches(row) && sameTimeframe(paperObservationRowTimeframe(row), target.timeframe))
      .map((row) => ({
        ...row,
        marker_type: "paper_opened",
        time: row.entry_signal_time || row.entry_time || row.decision_time,
        label: `${paperObservationRowLane(row) || "paper"} opened`,
      }));
    const closedTrades = paperObservationClosedRows(summary)
      .filter((row) => paperObservationFiltersMatch(row, { includeDate: true }))
      .filter((row) => chartSymbolMatches(row) && sameTimeframe(paperObservationRowTimeframe(row), target.timeframe))
      .flatMap((row) => [
        {
          ...row,
          marker_type: "paper_opened",
          time: row.entry_time || row.entry_signal_time,
          label: `${paperObservationRowLane(row) || "paper"} opened`,
        },
        {
          ...row,
          marker_type: "paper_closed",
          time: row.exit_time || row.decision_time,
          label: `${paperObservationRowLane(row) || "paper"} closed`,
        },
      ]);
    const seen = new Set();
    return [...openSignals, ...openPositions, ...closedTrades]
      .filter((marker) => marker.time)
      .filter((marker) => {
        const key = [
          marker.marker_type,
          paperObservationRowLane(marker),
          paperObservationRowSymbol(marker),
          paperObservationRowTimeframe(marker),
          marker.time,
        ].join("|");
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .sort((left, right) => String(left.time).localeCompare(String(right.time)));
  }

  function paperObservationChartSource() {
    const live = state.paperObservationMarketData || {};
    const selectedSymbol = selectedPaperObservationVenueSymbol();
    const selectedTimeframe = selectedPaperObservationTimeframe();
    const runtimeMarkers = paperObservationRuntimeMarkers();
    if (
      Array.isArray(live.candles) &&
      live.candles.length &&
      live.selectedSymbol === selectedSymbol &&
      sameTimeframe(live.selectedTimeframe, selectedTimeframe)
    ) {
      return {
        symbol: selectedSymbol,
        timeframe: selectedTimeframe,
        candles: live.candles,
        paper_markers: runtimeMarkers,
        source: "hyperliquid_mainnet_candleSnapshot_browser_poll",
        status: live.status,
        lastUpdatedUtc: live.lastUpdatedUtc,
        error: live.error,
      };
    }
    const chart = paperObservationSummary()?.live_chart || {};
    return {
      symbol: chart.symbol || selectedSymbol,
      timeframe: chart.timeframe || selectedTimeframe,
      candles: paperObservationRows(chart.candles).map((row) => ({
        timestamp_utc: row.timestamp_utc || row.time,
        open: row.open,
        high: row.high,
        low: row.low,
        close: row.close,
        volume: row.volume || "0",
      })),
      paper_markers: [...paperObservationRows(chart.paper_markers), ...runtimeMarkers],
      source: "pt_rt1_runtime_summary_fallback",
      status: live.status || "runtime_summary_fallback",
      lastUpdatedUtc: live.lastUpdatedUtc || paperObservationSummary()?.connection_status?.last_update_utc,
      error: live.error,
    };
  }

  function paperObservationChartCandles(candles) {
    return paperObservationRows(candles)
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
      .sort((left, right) => left.time - right.time);
  }

  function renderPaperObservationControls() {
    const summary = paperObservationSummary();
    const symbols = paperObservationSymbolOptions();
    const activeTimeframes = paperObservationActiveTimeframes(summary);
    const timeframeOptions = [
      ...activeTimeframes.map((timeframe) => ({ value: timeframe, label: `${displayTimeframe(timeframe)} selected timeframe only` })),
      { value: "all_active", label: "All active timeframes: 1h + 4h + 1d" },
      { value: "15m_legacy", label: "15m paused / legacy" },
    ];
    const reviewWindowOptions = [
      { value: "active_week", label: "Active week only" },
      { value: "pre_cutover", label: "Archived / weekend burn-in rows" },
      { value: "all_runtime", label: "All runtime data" },
    ];
    const signalCategoryOptions = [
      { value: "entry_activity", label: "Actual opens + intended entries" },
      { value: "intended_entries", label: "Intended entries" },
      { value: "actual_opens", label: "Actual synthetic opens" },
      { value: "blocked", label: "No-trade / blocked" },
      { value: "exits", label: "Exits" },
      { value: "duplicates", label: "Duplicate ignored" },
      { value: "data_unavailable", label: "Data unavailable" },
    ];
    const laneIds = paperObservationActiveLaneRows(summary).map((lane) => paperObservationLaneId(lane)).filter(Boolean);
    renderSelect(elements.paperObservationSymbolFilter, symbols, state.paperObservation.symbol, "All configured symbols");
    renderSelectWithoutAll(elements.paperObservationTimeframeFilter, timeframeOptions, state.paperObservation.timeframe);
    const laneOptions = laneIds.map((laneId) => ({ value: laneId, label: `${paperObservationWeek2LaneLabel(laneId)}: ${laneId}` }));
    renderSelect(elements.paperObservationLaneFilter, laneOptions, state.paperObservation.laneId, "All active lanes");
    if (elements.paperObservationLaneFilter && elements.paperObservationLaneFilter.value !== state.paperObservation.laneId) {
      state.paperObservation.laneId = elements.paperObservationLaneFilter.value || "all";
    }
    renderSelectWithoutAll(elements.paperObservationReviewWindowFilter, reviewWindowOptions, state.paperObservation.reviewWindow);
    renderSelectWithoutAll(elements.paperObservationSignalCategoryFilter, signalCategoryOptions, state.paperObservation.signalCategory);
    if (elements.paperObservationSymbolFilter) {
      elements.paperObservationSymbolFilter.onchange = () => {
        state.paperObservation.symbol = elements.paperObservationSymbolFilter.value === "all" ? "all" : elements.paperObservationSymbolFilter.value;
        resetPaperObservationPagination();
        refreshPaperObservationMarketData({ force: true });
        renderPaperObservation();
      };
    }
    if (elements.paperObservationTimeframeFilter) {
      elements.paperObservationTimeframeFilter.onchange = () => {
        state.paperObservation.timeframe = elements.paperObservationTimeframeFilter.value || "1h";
        resetPaperObservationPagination();
        refreshPaperObservationMarketData({ force: true });
        renderPaperObservation();
      };
    }
    if (elements.paperObservationReviewWindowFilter) {
      elements.paperObservationReviewWindowFilter.onchange = () => {
        state.paperObservation.reviewWindow = elements.paperObservationReviewWindowFilter.value || "active_week";
        resetPaperObservationPagination();
        renderPaperObservation();
      };
    }
    if (elements.paperObservationSignalCategoryFilter) {
      elements.paperObservationSignalCategoryFilter.onchange = () => {
        state.paperObservation.signalCategory = elements.paperObservationSignalCategoryFilter.value || "entry_activity";
        resetPaperObservationPagination();
        renderPaperObservation();
      };
    }
    if (elements.paperObservationLaneFilter) {
      elements.paperObservationLaneFilter.onchange = () => {
        state.paperObservation.laneId =
          elements.paperObservationLaneFilter.value === "all" ? "all" : elements.paperObservationLaneFilter.value;
        resetPaperObservationPagination();
        refreshPaperObservationMarketData({ force: true });
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
    const lanes = paperObservationActiveLaneRows(summary);
    const archivedLanes = paperObservationArchivedLaneRows(summary);
    const runtimeState = summary.paper_runtime_state || {};
    const unavailable = summary.data_unavailable_summary || {};
    const cards = [
      ["Strategy truth", truth.source || "public mainnet", "no private/signed/order endpoints"],
      ["Active Week 2 lanes", String(lanes.length), "founder-selected synthetic ledgers"],
      ["Archived lanes", String(archivedLanes.length), "hidden from default active scoring"],
      ["Scanner symbols", String(paperObservationBaseScannerRows().length), "configured paper symbols / runtime rows"],
      ["Probe default", probe.PT_RT1_TESTNET_PROBES_ENABLED === false ? "disabled" : "review", "kill switch true by default"],
      ["Runtime state", `${runtimeState.open_positions_count ?? 0} open`, "persisted local paper state"],
      ["Duplicate opens blocked", String(runtimeState.duplicate_signal_blocks_this_cycle ?? 0), "same-candle signals become held/blocked"],
      ["Candle unavailable", `${unavailable.candle_unavailable_blocking ?? unavailable.market_rows_unavailable ?? 0} blocking rows`, `${unavailable.lane_expanded_data_unavailable_decisions ?? 0} lane decisions`],
      ["Mid warnings", `${unavailable.mid_warning_non_blocking ?? 0} warning rows`, "thin/stale mids do not block candle scans"],
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

  function renderPaperObservationDailyReview() {
    if (!elements.paperObservationDailyReview) return;
    const review = state.ptRtDailyReview;
    if (!review) {
      elements.paperObservationDailyReview.innerHTML = `
        <div class="empty-state">
          No generated OBS-OS1 daily review loaded yet.
          Run <code>.venv/bin/python scripts/build_pt_rt_week2_daily_review.py --generate</code> to create a read-only founder review pack.
        </div>
      `;
      return;
    }
    const flags = Array.isArray(review.anomaly_flags) ? review.anomaly_flags : [];
    const criticalCount = flags.filter((flag) => flag?.severity === "critical").length;
    const warningCount = flags.filter((flag) => flag?.severity === "warning").length;
    const decisionSummary = review.decision_summary || {};
    const tradeSummary = review.closed_trade_summary || {};
    const testnetSummary = review.testnet_lifecycle_summary || {};
    const runtime = review.runtime || {};
    const reviewWindow = review.review_window || {};
    const flagMarkup = flags.length
      ? `
        <ul class="paper-observation-anomaly-list">
          ${flags.slice(0, 8).map((flag) => `
            <li>
              <span>${auditReviewPill(flag.severity || "info")}</span>
              <strong>${escapeHtml(flag.code || "unknown_flag")}</strong>
              <span>${escapeHtml(flag.detail || "")}</span>
            </li>
          `).join("")}
        </ul>
      `
      : `<p class="muted-inline">No anomaly flags were raised in the latest generated daily review.</p>`;
    elements.paperObservationDailyReview.innerHTML = `
      <div class="paper-observation-daily-review-grid">
        <div><span>Generated</span><strong>${escapeHtml(paperObservationText(review.generated_at_utc, "not generated"))}</strong></div>
        <div><span>Scope</span><strong>${escapeHtml(paperObservationText(reviewWindow.scope, PAPER_OBSERVATION_ACTIVE_RUNTIME_SCOPE))}</strong></div>
        <div><span>Go / no-go</span><strong>${escapeHtml(paperObservationText(review.go_no_go, "review_missing"))}</strong></div>
        <div><span>Runtime process count</span><strong>${escapeHtml(String(runtime.process_count ?? "unknown"))}</strong></div>
        <div><span>Review window</span><strong>${escapeHtml(`${paperObservationText(reviewWindow.window_start_utc, "n/a")} -> ${paperObservationText(reviewWindow.window_end_utc, "n/a")}`)}</strong></div>
        <div><span>Decision rows</span><strong>${escapeHtml(String(decisionSummary.count ?? 0))}</strong></div>
        <div><span>Closed synthetic trades</span><strong>${escapeHtml(String(tradeSummary.count ?? 0))}</strong></div>
        <div><span>Testnet lifecycle rows</span><strong>${escapeHtml(String(testnetSummary.count ?? 0))}</strong></div>
        <div><span>Critical flags</span><strong>${escapeHtml(String(criticalCount))}</strong></div>
        <div><span>Warning flags</span><strong>${escapeHtml(String(warningCount))}</strong></div>
        <div><span>Synthetic PnL</span><strong>Synthetic Ledger only</strong></div>
        <div><span>Testnet PnL effect</span><strong>${escapeHtml(String(review.week2_truth?.testnet_fills_update_synthetic_pnl === true))}</strong></div>
      </div>
      ${flagMarkup}
      <div class="methodology-warning secondary" role="note">
        OBS-OS1 is read-only. It reads runtime files and generated review JSON only; it does not start/stop the runtime, submit orders, update synthetic ledgers, approve live trading, or approve production.
        Source: ${escapeHtml(review.__source_path || "generated latest_review.json")}.
      </div>
    `;
  }

  function renderPaperObservationHealthBanner() {
    if (!elements.paperObservationHealthBanner) return;
    const summary = paperObservationSummary();
    const status = summary?.connection_status || {};
    const cadence = summary?.signal_evaluation_cadence || summary?.signal_evaluation_policy || {};
    const testnetPolicy = summary?.testnet_order_policy || summary?.pt_rt1_5_testnet_order_policy || {};
    const activeStart = paperObservationActiveReviewStart(summary);
    const disabled = paperObservationDisabledTimeframes(summary);
    const control = state.paperRuntimeControl || {};
    const runtimeStateLabel = control.running
      ? `active run: ${control.output || PAPER_OBSERVATION_ACTIVE_RUNTIME_SCOPE}`
      : "No active paper run detected";
    const activeLanes = paperObservationActiveLaneRows(summary).map((lane) => paperObservationLaneId(lane));
    elements.paperObservationHealthBanner.innerHTML = `
      <div class="paper-observation-command-banner">
        <div><span>Public mainnet data</span><strong>${escapeHtml(paperObservationText(status.hyperliquid_public_mainnet, "pending_runtime_refresh"))}</strong></div>
        <div class="${control.running ? "banner-cell-ok" : "banner-cell-warn"}"><span>Runtime state</span><strong>${escapeHtml(runtimeStateLabel)}</strong></div>
        <div><span>Run scope</span><strong>${escapeHtml(control.output || summary?.active_review_scope || PAPER_OBSERVATION_ACTIVE_RUNTIME_SCOPE)}</strong></div>
        <div><span>Active review window</span><strong>${escapeHtml(activeStart)} to now</strong></div>
        <div><span>Active timeframes</span><strong>1h / 4h / 1D</strong></div>
        <div class="banner-cell-warn"><span>15m</span><strong>${escapeHtml(PAPER_OBSERVATION_15M_STATUS)}</strong></div>
        <div><span>Active lanes</span><strong class="paper-lane-chip-row">${activeLanes.map((laneId) => paperObservationLaneChip(laneId)).join("")}</strong></div>
        <div><span>Signal evaluation</span><strong>${escapeHtml(paperObservationText(cadence.strategy_signal_evaluation || cadence.mode, "candle-close only"))}</strong></div>
        <div><span>Market refresh</span><strong>${escapeHtml(paperObservationText(cadence.market_refresh || cadence.market_refresh_mode, "active"))}</strong></div>
        <div class="banner-cell-testnet"><span>Testnet order transport</span><strong>${escapeHtml(testnetPolicy.order_transport_enabled ? "baseline-only gates enabled" : "baseline-only gates ready")}</strong></div>
        <div><span>Fixed notional</span><strong>${escapeHtml(paperObservationText(testnetPolicy.fixed_notional_usdc, "25"))} USDC</strong></div>
        <div><span>Synthetic PnL</span><strong>Synthetic Ledger</strong></div>
        <div><span>Testnet lifecycle</span><strong>Separate from synthetic PnL</strong></div>
        <div class="banner-cell-no"><span>Live trading</span><strong>not approved</strong></div>
      </div>
      <div class="methodology-warning compact">
        Paper Trading is the Week 2 runtime review surface. Historical Replay, Evidence, The Lab, and Strategy remain reference surfaces.
        Default active slate: ${escapeHtml(activeLanes.join(", "))}.
        Disabled timeframes: ${escapeHtml(disabled.join(", ") || "none")}. Existing 15m records remain visible only under the paused/legacy filter.
        Stale runtime artifacts are not proof of an active run; the local control server must report running.
        Frequent market refresh is display-only; strategy signals are evaluated only after fully closed 1h / 4h / 1d candles.
      </div>
    `;
  }

  function renderPaperObservationTimeframeBreakdown() {
    if (!elements.paperObservationTimeframeBreakdown) return;
    const summary = paperObservationSummary();
    const frames = ["1h", "4h", "1d", "15m"];
    const decisions = paperObservationDecisionRows(summary).filter((row) => paperObservationDateFilterMatches(row));
    const openPositions = Object.values(summary?.paper_runtime_state?.open_positions_by_key || {});
    const closedTrades = paperObservationClosedRows(summary).filter((row) => paperObservationDateFilterMatches(row));
    const rows = frames.map((timeframe) => {
      const isPaused = paperObservationIsDisabledTimeframe(timeframe, summary);
      const rowDecisions = decisions.filter((row) => sameTimeframe(paperObservationRowTimeframe(row), timeframe));
      const rowOpens = rowDecisions.filter((row) => row.action === "paper_opened");
      const rowCloses = rowDecisions.filter((row) => row.action === "paper_closed");
      const rowOpenPositions = openPositions.filter((row) => sameTimeframe(paperObservationRowTimeframe(row), timeframe));
      const rowClosedTrades = closedTrades.filter((row) => sameTimeframe(paperObservationRowTimeframe(row), timeframe));
      const netPnl = rowClosedTrades.reduce((total, row) => total + decimal(row.net_pnl, 0), 0);
      const dataBlocks = rowDecisions.filter((row) => {
        const reasons = paperObservationRows(row.reason_codes).map(String);
        return row.action === "data_unavailable" || reasons.some((reason) => reason.includes("unavailable"));
      }).length;
      return {
        timeframe,
        decisions: rowDecisions.length,
        opens: rowOpens.length,
        closes: rowCloses.length,
        openPositions: rowOpenPositions.length,
        closedTrades: rowClosedTrades.length,
        netPnl,
        maxDrawdown: "n/a",
        dataBlocks,
        status: isPaused ? "paused_legacy_timeframe_excluded_from_active_week_scoring" : "active_week_timeframe",
      };
    });
    elements.paperObservationTimeframeBreakdown.innerHTML = `
      <table>
        <thead>
          <tr><th>Timeframe</th><th>Decisions</th><th>Opens</th><th>Closes</th><th>Open positions</th><th>Closed trades</th><th>Net PnL</th><th>Max drawdown</th><th>Data blocks</th><th>Status</th></tr>
        </thead>
        <tbody>
          ${rows.map((row) => `
            <tr>
              <td>${escapeHtml(displayTimeframe(row.timeframe))}</td>
              <td>${escapeHtml(String(row.decisions))}</td>
              <td>${escapeHtml(String(row.opens))}</td>
              <td>${escapeHtml(String(row.closes))}</td>
              <td>${escapeHtml(String(row.openPositions))}</td>
              <td>${escapeHtml(String(row.closedTrades))}</td>
              <td class="${row.netPnl >= 0 ? "positive" : "negative"}">${escapeHtml(paperObservationUsdc(row.netPnl))}</td>
              <td>${escapeHtml(row.maxDrawdown)}</td>
              <td>${escapeHtml(String(row.dataBlocks))}</td>
              <td>${auditReviewPill(row.status)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderPaperObservationConnectionStatus() {
    if (!elements.paperObservationConnectionStatus) return;
    const summary = paperObservationSummary();
    const status = summary?.connection_status || {};
    const endpointPolicy = summary?.market_data_endpoint_policy || summary?.strategy_truth_lane || {};
    const live = state.paperObservationMarketData || {};
    elements.paperObservationConnectionStatus.innerHTML = `
      <div class="market-micro-grid">
        <div><span>Mainnet connection</span><strong>${escapeHtml(paperObservationText(status.hyperliquid_public_mainnet, "pending_runtime_refresh"))}</strong></div>
        <div><span>Endpoint category</span><strong>${escapeHtml(paperObservationText(status.endpoint_category || endpointPolicy.endpoint_category, "public_read_only"))}</strong></div>
        <div><span>Strategy endpoint</span><strong>${escapeHtml(paperObservationText(endpointPolicy.strategy_truth_endpoint || endpointPolicy.endpoint, "public_read_only_mainnet_info"))}</strong></div>
        <div><span>Last update</span><strong>${escapeHtml(paperObservationText(status.last_update_utc, "pending_runtime_refresh"))}</strong></div>
        <div><span>Browser MD tick</span><strong>${escapeHtml(paperObservationText(live.status, "not_started"))}</strong></div>
        <div><span>Latest MD tick</span><strong>${escapeHtml(paperObservationText(live.lastUpdatedUtc, "waiting"))}</strong></div>
        <div><span>Selected chart</span><strong>${escapeHtml(`${selectedPaperObservationVenueSymbol()} ${displayTimeframe(selectedPaperObservationTimeframe())}`)}</strong></div>
        <div><span>No private/signed/order endpoints</span><strong>${escapeHtml(String(status.no_private_signed_order_endpoints ?? true))}</strong></div>
        <div><span>No API keys</span><strong>${escapeHtml(String(status.no_api_keys ?? true))}</strong></div>
        <div><span>Blocking candle rows</span><strong>${escapeHtml(String(summary?.data_unavailable_summary?.candle_unavailable_blocking ?? summary?.data_unavailable_summary?.market_rows_unavailable ?? "n/a"))}</strong></div>
        <div><span>Mid warning rows</span><strong>${escapeHtml(String(summary?.data_unavailable_summary?.mid_warning_non_blocking ?? "n/a"))}</strong></div>
        <div><span>Lane-expanded unavailable</span><strong>${escapeHtml(String(summary?.data_unavailable_summary?.lane_expanded_data_unavailable_decisions ?? "n/a"))}</strong></div>
        <div><span>Mid blocks strategy</span><strong>${escapeHtml(String(summary?.mid_health_blocks_strategy ?? endpointPolicy.mid_health_blocks_strategy ?? false))}</strong></div>
        <div><span>Candles block strategy</span><strong>${escapeHtml(String(summary?.candle_health_blocks_strategy ?? endpointPolicy.candle_health_blocks_strategy ?? true))}</strong></div>
      </div>
      <div class="methodology-warning secondary" role="note">
        Public mainnet data is strategy truth. Synthetic paper results are forward observation only.
        Testnet probes are plumbing only; testnet fills do not update strategy PnL.
        Browser ticker uses Hyperliquid public mainnet allMids/candleSnapshot only.
        Data unavailable is candle-truth based: closed candle/indicator blockers can create lane-expanded decisions, while stale or missing mids are warning-only when candles are available.
        Reason codes: ${escapeHtml(paperObservationText([...(status.meta_reason_codes || []), ...(status.mids_reason_codes || [])], "pending_runtime_refresh"))}
        ${live.error ? ` Live polling status: ${escapeHtml(live.error)}.` : ""}
      </div>
    `;
  }

  function renderPaperObservationScanner() {
    if (!elements.paperObservationScannerTable) return;
    const rows = paperObservationScannerRows();
    if (!rows.length) {
      setEmpty(elements.paperObservationScannerTable, "Top-20 scanner runtime rows not loaded.");
      return;
    }
    elements.paperObservationScannerTable.innerHTML = `
      <table class="paper-observation-watchlist-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Mid price</th>
            <th>Health</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr
                  class="${row.requested_symbol === state.paperObservation.symbol || row.resolved_venue_symbol === selectedPaperObservationVenueSymbol() ? "selected-row" : ""}"
                  title="${escapeHtml(paperObservationText(row.reason_codes, "n/a"))}"
                >
                  <td>
                    <button class="link-button paper-observation-symbol-button" type="button" data-paper-observation-symbol="${escapeHtml(row.requested_symbol || row.resolved_venue_symbol || "")}">
                      ${escapeHtml(paperObservationText(row.resolved_venue_symbol || row.requested_symbol, "n/a"))}
                    </button>
                  </td>
                  <td><span class="paper-observation-tick ${paperObservationTickClass(row)}">${escapeHtml(paperObservationText(row.public_mid, row.blocked ? "blocked" : "pending"))}</span></td>
                  <td>${auditReviewPill(paperObservationMdHealth(row))}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
    elements.paperObservationScannerTable.querySelectorAll("[data-paper-observation-symbol]").forEach((button) => {
      button.addEventListener("click", () => {
        state.paperObservation.symbol = button.dataset.paperObservationSymbol || "all";
        refreshPaperObservationMarketData({ force: true });
        renderPaperObservation();
      });
    });
  }

  function renderPaperObservationSignalGeneration() {
    if (!elements.paperObservationSignalTable) return;
    const summary = paperObservationSummary();
    const sourceRows = paperObservationDecisionRows(summary);
    const rows = sourceRows
      .filter((row) => paperObservationDecisionCategoryMatches(row))
      .filter((row) => paperObservationFiltersMatch(row, { includeDate: true }));
    if (!rows.length) {
      const sourceMessage = sourceRows.length
        ? "No paper decisions match the selected signal category, active review window, timeframe, symbol, and lane filters."
        : "No paper decisions recorded yet. Decisions are recorded in the ignored PT-RT1 decisions stream and appear here when present.";
      setEmpty(elements.paperObservationSignalTable, sourceMessage);
      return;
    }
    const page = paperObservationPageRows(rows, "signals");
    elements.paperObservationSignalTable.innerHTML = `
      <div class="methodology-warning compact">
        Showing paper decisions from ${escapeHtml(state.ptRt1DecisionSource || "runtime summary / decisions stream")}. Labels: paper decision, synthetic entry, not exchange order.
      </div>
      ${paperObservationPaginationControls("signals", page)}
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Lane</th>
            <th>Symbol</th>
            <th>Timeframe</th>
            <th>Action</th>
            <th>Paper state</th>
            <th>Indicator snapshot</th>
            <th>Reason codes</th>
          </tr>
        </thead>
        <tbody>
          ${page.rows
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(paperObservationText(paperObservationDecisionTime(row), "pending_runtime_refresh"))}</td>
                  <td>${paperObservationLaneChip(row.strategy_id || row.lane_id)}</td>
                  <td>${escapeHtml(paperObservationText(row.symbol, "n/a"))}</td>
                  <td>${escapeHtml(displayTimeframe(row.timeframe))}</td>
                  <td>${auditReviewPill(row.action || "paper_opened")}</td>
                  <td>${auditReviewPill(row.action === "paper_opened" ? "synthetic_entry" : row.position_after || row.paper_state_transition || "paper_decision")}</td>
                  <td>${escapeHtml(paperObservationText(row.indicator_snapshot?.timeframe_status || row.indicator_snapshot?.trend_alignment || row.candle_status_reason, "snapshot_available_if_recorded"))}</td>
                  <td>${escapeHtml(paperObservationText(row.reason_codes, "n/a"))}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
      ${paperObservationPaginationControls("signals", page)}
    `;
    attachPaperObservationPagination(elements.paperObservationSignalTable, "signals");
  }

  function paperObservationLaneRuntimeRollup(summary) {
    const runtimeState = summary?.paper_runtime_state || {};
    const rollup = new Map();
    const ensure = (laneId) => {
      const key = laneId || "unknown_lane";
      if (!rollup.has(key)) {
        rollup.set(key, {
          laneId: key,
          realizedEquity: undefined,
          unrealizedPnl: 0,
          openPositions: 0,
          closedTrades: 0,
          decisions: 0,
          opens: 0,
          closes: 0,
          wins: 0,
          losses: 0,
          netPnl: 0,
          largestWin: null,
          largestLoss: null,
          averageWin: null,
          averageLoss: null,
          duplicateBlocks: 0,
          dataHealthBlocks: 0,
          latestTrade: null,
          latestDecisionTime: "",
        });
      }
      return rollup.get(key);
    };
    Object.values(runtimeState.open_positions_by_key || {}).forEach((position) => {
      if (!paperObservationFiltersMatch(position, { includeDate: true })) return;
      const lane = ensure(paperObservationRowLane(position));
      lane.openPositions += 1;
      lane.unrealizedPnl += decimal(position.current_unrealized_pnl, 0);
    });
    paperObservationClosedRows(summary)
      .filter((trade) => paperObservationFiltersMatch(trade, { includeDate: true }))
      .forEach((trade) => {
      const lane = ensure(paperObservationRowLane(trade));
      lane.closedTrades += 1;
      lane.closes += 1;
      const netPnl = decimal(trade.net_pnl, 0);
      lane.netPnl += netPnl;
      if (netPnl > 0) {
        lane.wins += 1;
        lane.largestWin = lane.largestWin === null ? netPnl : Math.max(lane.largestWin, netPnl);
      }
      if (netPnl < 0) {
        lane.losses += 1;
        lane.largestLoss = lane.largestLoss === null ? netPnl : Math.min(lane.largestLoss, netPnl);
      }
      const isLatestTrade = !lane.latestTrade ||
        String(trade.exit_time || trade.decision_time || "").localeCompare(String(lane.latestTrade.exit_time || lane.latestTrade.decision_time || "")) > 0;
      if (isLatestTrade) {
        lane.latestTrade = trade;
      }
    });
    paperObservationDecisionRows(summary)
      .filter((row) => paperObservationFiltersMatch(row, { includeDate: true }))
      .forEach((row) => {
        const lane = ensure(paperObservationRowLane(row));
        const action = row.action || "";
        const reasons = paperObservationRows(row.reason_codes).map(String);
        lane.decisions += 1;
        if (action === "paper_opened") lane.opens += 1;
        if (action === "paper_closed") lane.closes += 1;
        if (reasons.some((reason) => reason.includes("duplicate"))) lane.duplicateBlocks += 1;
        if (action === "data_unavailable" || reasons.some((reason) => reason.includes("unavailable"))) lane.dataHealthBlocks += 1;
        if (String(paperObservationDecisionTime(row)).localeCompare(String(lane.latestDecisionTime || "")) > 0) {
          lane.latestDecisionTime = paperObservationDecisionTime(row);
        }
      });
    rollup.forEach((lane) => {
      const winTotal = paperObservationClosedRows(summary)
        .filter((trade) => paperObservationFiltersMatch(trade, { includeDate: true }))
        .filter((trade) => paperObservationRowLane(trade) === lane.laneId)
        .map((trade) => decimal(trade.net_pnl, 0))
        .filter((net) => net > 0)
        .reduce((total, net) => total + net, 0);
      const lossTotal = paperObservationClosedRows(summary)
        .filter((trade) => paperObservationFiltersMatch(trade, { includeDate: true }))
        .filter((trade) => paperObservationRowLane(trade) === lane.laneId)
        .map((trade) => decimal(trade.net_pnl, 0))
        .filter((net) => net < 0)
        .reduce((total, net) => total + net, 0);
      lane.averageWin = lane.wins ? winTotal / lane.wins : null;
      lane.averageLoss = lane.losses ? lossTotal / lane.losses : null;
    });
    return rollup;
  }

  function renderPaperObservationLanes() {
    if (!elements.paperObservationLaneTable) return;
    const summary = paperObservationSummary();
    const laneRows = paperObservationActiveLaneRows(summary);
    const archivedRows = paperObservationArchivedLaneRows(summary);
    const selectedLane = elements.paperObservationLaneFilter?.value || state.paperObservation.laneId || "all";
    const laneIds = laneRows.map((row) => paperObservationLaneId(row)).filter(Boolean);
    const normalizedSelectedLane = selectedLane === "all" || !laneIds.includes(selectedLane) ? "all" : selectedLane;
    if (normalizedSelectedLane !== state.paperObservation.laneId) state.paperObservation.laneId = normalizedSelectedLane;
    if (elements.paperObservationLaneFilter && elements.paperObservationLaneFilter.value !== normalizedSelectedLane) {
      elements.paperObservationLaneFilter.value = normalizedSelectedLane;
    }
    const rows = laneRows.filter(
      (row) => normalizedSelectedLane === "all" || row.strategy_id === normalizedSelectedLane || row.lane_id === normalizedSelectedLane,
    );
    if (!rows.length) {
      setEmpty(elements.paperObservationLaneTable, "Strategy lane config not loaded.");
      return;
    }
    const runtimeRollup = paperObservationLaneRuntimeRollup(summary);
    const scopeLabel = paperObservationTimeframeScopeLabel();
    elements.paperObservationLaneTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Lane</th>
            <th>Timeframe scope</th>
            <th>Starting equity</th>
            <th>Realized equity</th>
            <th>Net PnL</th>
            <th>Unrealized PnL</th>
            <th>Total equity</th>
            <th>Max drawdown</th>
            <th>Open</th>
            <th>Closed</th>
            <th>Win rate</th>
            <th>Avg win</th>
            <th>Avg loss</th>
            <th>Largest win</th>
            <th>Largest loss</th>
            <th>Data / duplicate blocks</th>
            <th>Latest decision</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map((row) => {
              const laneId = paperObservationLaneId(row);
              const runtime = runtimeRollup.get(laneId) || {};
              const startingEquity = decimal(row.initial_equity || row.starting_equity, 10000);
              const netPnl = decimal(runtime.netPnl, 0);
              const realizedEquity = startingEquity + netPnl;
              const unrealizedPnl = decimal(runtime.unrealizedPnl ?? row.unrealized_pnl, 0);
              const totalEquity = realizedEquity + unrealizedPnl;
              const openPositions = runtime.openPositions ?? row.open_positions ?? 0;
              const closedTrades = runtime.closedTrades ?? row.closed_trades ?? 0;
              const activity = (runtime.decisions || 0) + openPositions + closedTrades;
              const winRate = closedTrades ? `${((runtime.wins || 0) / closedTrades * 100).toFixed(1)}%` : "n/a";
              return `
                <tr>
                  <td><span class="paper-lane-chip-row">${paperObservationLaneChip(laneId, paperObservationWeek2LaneLabel(laneId))}<span class="paper-lane-chip-name">${escapeHtml(row.display_name || laneId)}</span></span></td>
                  <td>${auditReviewPill(scopeLabel)}</td>
                  <td>${escapeHtml(paperObservationUsdc(startingEquity))}</td>
                  <td>${escapeHtml(paperObservationUsdc(realizedEquity))}</td>
                  <td class="${netPnl >= 0 ? "positive" : "negative"}">${escapeHtml(paperObservationUsdc(netPnl))}</td>
                  <td>${escapeHtml(paperObservationUsdc(unrealizedPnl))}</td>
                  <td>${escapeHtml(paperObservationUsdc(totalEquity))}</td>
                  <td>${escapeHtml(paperObservationUsdc(row.max_drawdown || row.drawdown || "0"))}</td>
                  <td>${escapeHtml(String(openPositions))}</td>
                  <td>${escapeHtml(String(closedTrades))}</td>
                  <td>${escapeHtml(winRate)}</td>
                  <td>${escapeHtml(runtime.averageWin === null || runtime.averageWin === undefined ? "n/a" : paperObservationUsdc(runtime.averageWin))}</td>
                  <td>${escapeHtml(runtime.averageLoss === null || runtime.averageLoss === undefined ? "n/a" : paperObservationUsdc(runtime.averageLoss))}</td>
                  <td>${escapeHtml(runtime.largestWin === null || runtime.largestWin === undefined ? "n/a" : paperObservationUsdc(runtime.largestWin))}</td>
                  <td>${escapeHtml(runtime.largestLoss === null || runtime.largestLoss === undefined ? "n/a" : paperObservationUsdc(runtime.largestLoss))}</td>
                  <td>${escapeHtml(`${runtime.dataHealthBlocks || 0} / ${runtime.duplicateBlocks || 0}`)}</td>
                  <td>${escapeHtml(paperObservationText(runtime.latestDecisionTime, "n/a"))}</td>
                  <td>${auditReviewPill(activity ? "active_scope" : "no_activity_for_selected_timeframe")}</td>
                </tr>
              `;
            })
            .join("")}
        </tbody>
      </table>
      <div class="methodology-warning compact">
        Archived/default-inactive lanes are hidden from active Week 2 scoring:
        ${escapeHtml(archivedRows.map((lane) => paperObservationLaneId(lane)).join(", ") || "none")}.
        Archived means historical/research reference only, not deleted.
      </div>
    `;
  }

  function renderPaperObservationLaneDetail() {
    if (!elements.paperObservationLaneDetail) return;
    const lanes = paperObservationActiveLaneRows(paperObservationSummary());
    const selectedLane = state.paperObservation.laneId === "all" ? lanes[0] : lanes.find(
      (lane) => paperObservationLaneId(lane) === state.paperObservation.laneId,
    );
    if (!selectedLane) {
      setEmpty(elements.paperObservationLaneDetail, "Lane detail data_not_available_in_pt_rt1_bundle.");
      return;
    }
    const laneId = paperObservationLaneId(selectedLane);
    elements.paperObservationLaneDetail.innerHTML = `
      <div class="market-micro-grid">
        <div><span>Lane</span><strong>${paperObservationLaneChip(laneId)}</strong></div>
        <div><span>Week 2 label</span><strong>${escapeHtml(paperObservationWeek2LaneLabel(laneId))}</strong></div>
        <div><span>Family</span><strong>${escapeHtml(paperObservationText(selectedLane.strategy_family, "n/a"))}</strong></div>
        <div><span>PNL source</span><strong>${escapeHtml(selectedLane.pnl_source || "Synthetic Ledger")}</strong></div>
        <div><span>Signal truth</span><strong>${escapeHtml(selectedLane.signal_truth || "Public Mainnet Candles")}</strong></div>
        <div><span>Testnet</span><strong>${escapeHtml(selectedLane.testnet_label || (laneId === "money_flow_v1_2_baseline" ? "Baseline-only gated testnet eligible" : "Synthetic-only / no testnet"))}</strong></div>
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

  function paperObservationEmaValues(values, period) {
    const rows = Array(values.length).fill(NaN);
    if (values.length < period) return rows;
    const multiplier = 2 / (period + 1);
    let current = values.slice(0, period).reduce((sum, value) => sum + value, 0) / period;
    rows[period - 1] = current;
    for (let index = period; index < values.length; index += 1) {
      current = (values[index] - current) * multiplier + current;
      rows[index] = current;
    }
    return rows;
  }

  function paperObservationRsiRows(candles, period = 14) {
    const closes = candles.map((candle) => Number(candle.close));
    if (closes.length <= period) return [];
    let avgGain = 0;
    let avgLoss = 0;
    for (let index = 1; index <= period; index += 1) {
      const delta = closes[index] - closes[index - 1];
      avgGain += Math.max(delta, 0);
      avgLoss += Math.abs(Math.min(delta, 0));
    }
    avgGain /= period;
    avgLoss /= period;
    const valueFromAverage = () => (avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss));
    const rows = [{ time: candles[period].time, value: roundDisplay(valueFromAverage()) }];
    for (let index = period + 1; index < closes.length; index += 1) {
      const delta = closes[index] - closes[index - 1];
      avgGain = (avgGain * (period - 1) + Math.max(delta, 0)) / period;
      avgLoss = (avgLoss * (period - 1) + Math.abs(Math.min(delta, 0))) / period;
      rows.push({ time: candles[index].time, value: roundDisplay(valueFromAverage()) });
    }
    return rows.filter((row) => Number.isFinite(row.time) && Number.isFinite(row.value));
  }

  function paperObservationMacdSeries(candles) {
    const closes = candles.map((candle) => Number(candle.close));
    const ema12 = paperObservationEmaValues(closes, 12);
    const ema26 = paperObservationEmaValues(closes, 26);
    const macdPoints = [];
    for (let index = 0; index < candles.length; index += 1) {
      if (Number.isFinite(ema12[index]) && Number.isFinite(ema26[index])) {
        macdPoints.push({
          time: candles[index].time,
          value: ema12[index] - ema26[index],
        });
      }
    }
    const signalValues = paperObservationEmaValues(macdPoints.map((point) => point.value), 9);
    const macdRows = [];
    const signalRows = [];
    const histogramRows = [];
    macdPoints.forEach((point, index) => {
      const macdValue = roundDisplay(point.value);
      macdRows.push({ time: point.time, value: macdValue });
      if (Number.isFinite(signalValues[index])) {
        const signalValue = roundDisplay(signalValues[index]);
        const histogramValue = roundDisplay(point.value - signalValues[index]);
        signalRows.push({ time: point.time, value: signalValue });
        histogramRows.push({
          time: point.time,
          value: histogramValue,
          color: histogramValue >= 0 ? "rgba(37, 208, 132, 0.52)" : "rgba(255, 90, 102, 0.52)",
        });
      }
    });
    return { macdRows, signalRows, histogramRows };
  }

  function paperObservationLatestSeriesValue(rows) {
    const row = rows.at(-1);
    return row && Number.isFinite(row.value) ? compactNumber(row.value) : "indicator_unavailable";
  }

  function renderPaperObservationIndicatorLegend(candles) {
    const rsiRows = paperObservationRsiRows(candles);
    const macdRows = paperObservationMacdSeries(candles);
    return `
      <span><b class="legend-dot rsi"></b>RSI 14 ${escapeHtml(paperObservationLatestSeriesValue(rsiRows))}</span>
      <span><b class="legend-dot macd"></b>MACD ${escapeHtml(paperObservationLatestSeriesValue(macdRows.macdRows))}</span>
      <span><b class="legend-dot macd-signal"></b>Signal ${escapeHtml(paperObservationLatestSeriesValue(macdRows.signalRows))}</span>
      <span><b class="legend-dot macd-histogram"></b>Hist ${escapeHtml(paperObservationLatestSeriesValue(macdRows.histogramRows))}</span>
      <span>Pane order: RSI, candles, MACD. Public mainnet display only.</span>
    `;
  }

  function historicalConstantRows(candles, value) {
    if (!candles.length) return [];
    return [
      { time: candles[0].time, value },
      { time: candles.at(-1).time, value },
    ];
  }

  const PAPER_OBSERVATION_RSI_PANE = 0;
  const PAPER_OBSERVATION_PRICE_PANE = 1;
  const PAPER_OBSERVATION_MACD_PANE = 2;

  function setPaperObservationPaneHeights(chart, height) {
    if (!chart || typeof chart.panes !== "function") return;
    const panes = chart.panes();
    if (!Array.isArray(panes) || panes.length < 3) return;
    [
      [PAPER_OBSERVATION_RSI_PANE, 15, Math.round(height * 0.15)],
      [PAPER_OBSERVATION_PRICE_PANE, 70, Math.round(height * 0.7)],
      [PAPER_OBSERVATION_MACD_PANE, 15, Math.max(1, Math.round(height * 0.15))],
    ].forEach(([paneIndex, stretchFactor, fallbackHeight]) => {
      if (typeof panes[paneIndex]?.setStretchFactor === "function") {
        panes[paneIndex].setStretchFactor(stretchFactor);
      } else if (typeof panes[paneIndex]?.setHeight === "function") {
        panes[paneIndex].setHeight(fallbackHeight);
      }
    });
  }

  function applyPaperObservationPaneScale(chart, paneIndex) {
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

  function destroyPaperObservationChart() {
    const chartState = state.paperObservationChart;
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

  function resizePaperObservationChart() {
    const chartState = state.paperObservationChart;
    if (!chartState.chart || !chartState.mount) return;
    const { width, height } = chartDimensions(chartState.mount);
    chartState.chart.resize(width, height);
    setPaperObservationPaneHeights(chartState.chart, height);
  }

  function schedulePaperObservationResize() {
    const chartState = state.paperObservationChart;
    if (!chartState.chart || !chartState.mount) return;
    if (chartState.pendingResizeFrame) return;
    const raf = typeof window.requestAnimationFrame === "function"
      ? window.requestAnimationFrame
      : (callback) => window.setTimeout(callback, 16);
    chartState.pendingResizeFrame = raf(() => {
      chartState.pendingResizeFrame = null;
      resizePaperObservationChart();
    });
  }

  function paperObservationChartMarkers(candles, rawMarkers) {
    if (!candles.length) return [];
    const firstTime = candles[0].time;
    const lastTime = candles.at(-1).time;
    const markers = paperObservationRows(rawMarkers).slice(-60);
    return markers.map((marker) => {
      const parsed = chartTime(marker.time || marker.timestamp || marker.entry_time || marker.exit_time);
      let time = parsed;
      if (!Number.isFinite(time)) return null;
      if (time < firstTime || time > lastTime) return null;
      const exact = candles.find((candle) => candle.time === time);
      if (!exact) {
        time = candles.reduce((nearest, candle) =>
          Math.abs(candle.time - parsed) < Math.abs(nearest.time - parsed) ? candle : nearest,
        candles[0]).time;
      }
      const action = String(marker.action || marker.type || marker.marker_type || "").toLowerCase();
      const isExit = action.includes("exit") || action.includes("close") || action.includes("sell") || action.includes("paper_closed");
      const lane = paperObservationRowLane(marker);
      const laneLabel =
        lane === "money_flow_v1_2_baseline"
          ? "MF"
          : lane === "avoid_low_rolling_range_20"
          ? "RR20"
          : lane === "mf_orig_1d_stage2_breakout_resistance_full_equity"
          ? "MF-O"
          : "paper";
      return {
        time,
        position: isExit ? "aboveBar" : "belowBar",
        color: isExit ? "#ff5a66" : "#25d084",
        shape: isExit ? "arrowDown" : "arrowUp",
        text: `${laneLabel} ${isExit ? "close" : "open"}`,
      };
    }).filter(Boolean);
  }

  function updatePaperObservationChartData(candles, rawMarkers) {
    const chartState = state.paperObservationChart;
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
    const macdRows = paperObservationMacdSeries(candles);
    chartState.indicatorSeries.RSI?.setData(paperObservationRsiRows(candles));
    chartState.indicatorSeries.RSI_floor?.setData(historicalConstantRows(candles, 0));
    chartState.indicatorSeries.RSI_ceiling?.setData(historicalConstantRows(candles, 100));
    chartState.indicatorSeries.MACD?.setData(macdRows.macdRows);
    chartState.indicatorSeries.MACD_signal?.setData(macdRows.signalRows);
    chartState.indicatorSeries.MACD_histogram?.setData(macdRows.histogramRows);
    const markers = paperObservationChartMarkers(candles, rawMarkers);
    if (chartState.markerHandle && typeof chartState.markerHandle.setMarkers === "function") {
      chartState.markerHandle.setMarkers(markers);
    } else if (typeof chartState.candleSeries.setMarkers === "function") {
      chartState.candleSeries.setMarkers(markers);
    }
    const updatedTimeScale = chartState.chart?.timeScale?.();
    if (chartState.lastVisibleRange && typeof updatedTimeScale?.setVisibleLogicalRange === "function") {
      updatedTimeScale.setVisibleLogicalRange(chartState.lastVisibleRange);
    }
    const legend = elements.paperObservationLiveChart?.querySelector("[data-paper-observation-indicator-legend]");
    if (legend) {
      legend.innerHTML = renderPaperObservationIndicatorLegend(candles);
    }
    schedulePaperObservationResize();
  }

  function renderPaperObservationLightweightChart(chartPayload, candles) {
    const tv = lightweightCharts();
    if (!elements.paperObservationLiveChart || !tv || !candles.length) return false;
    const chartState = state.paperObservationChart;
    const chartKey = `${chartPayload.symbol}|${canonicalTimeframe(chartPayload.timeframe)}`;
    const priceStats = chartPriceStats(candles);
    if (chartState.ready && chartState.key === chartKey && chartState.chart && chartState.candleSeries && chartState.volumeSeries) {
      const latestTarget = elements.paperObservationLiveChart.querySelector("[data-paper-chart-latest]");
      const candleTarget = elements.paperObservationLiveChart.querySelector("[data-paper-chart-candle]");
      const statusTarget = elements.paperObservationLiveChart.querySelector("[data-paper-chart-status]");
      if (latestTarget) latestTarget.textContent = priceStats.latest;
      if (candleTarget) candleTarget.textContent = `${displayTimeframe(chartPayload.timeframe)} latest candle ${candles.at(-1)?.time ? new Date(candles.at(-1).time * 1000).toISOString() : "n/a"}`;
      if (statusTarget) statusTarget.textContent = `${chartPayload.status || "connected"}; ${chartPayload.lastUpdatedUtc || "waiting"}`;
      updatePaperObservationChartData(candles, chartPayload.paper_markers);
      return true;
    }

    destroyPaperObservationChart();
    elements.paperObservationLiveChart.innerHTML = `
      <div class="tradingview-chart-topline">
        <div>
          <strong>${escapeHtml(chartPayload.symbol)}-PERP</strong>
          <span data-paper-chart-candle>${escapeHtml(displayTimeframe(chartPayload.timeframe))} latest candle ${escapeHtml(candles.at(-1)?.time ? new Date(candles.at(-1).time * 1000).toISOString() : "n/a")}</span>
        </div>
        <div class="chart-price-tape">
          <span>Latest</span>
          <strong data-paper-chart-latest>${escapeHtml(priceStats.latest)}</strong>
        </div>
      </div>
      <div class="tradingview-chart-stage paper-observation-chart-stage">
        <div class="tradingview-lightweight-chart" role="img" aria-label="Paper Observation TradingView Lightweight Charts public-mainnet candlestick chart"></div>
        <aside class="chart-price-axis-readout" aria-label="Selected paper observation price scale">
          <span>Price USDC</span>
          <strong>${escapeHtml(priceStats.latest)}</strong>
          <small>H ${escapeHtml(priceStats.high)}</small>
          <small>L ${escapeHtml(priceStats.low)}</small>
          <small>O ${escapeHtml(priceStats.open)}</small>
          <small>C ${escapeHtml(priceStats.close)}</small>
        </aside>
      </div>
      <div class="historical-overlay-legend paper-observation-indicator-legend" data-paper-observation-indicator-legend>${renderPaperObservationIndicatorLegend(candles)}</div>
      <div class="tradingview-attribution">
        Charts: TradingView Lightweight Charts v${TRADINGVIEW_LIGHTWEIGHT_CHARTS_VERSION}. Public mainnet allMids/candleSnapshot only; no API keys, private endpoints, signed endpoints, order endpoints, testnet strategy truth, or live trading.
        <span data-paper-chart-status>${escapeHtml(chartPayload.status || "connected")}; ${escapeHtml(chartPayload.lastUpdatedUtc || "waiting")}</span>
      </div>
    `;
    const mount = elements.paperObservationLiveChart.querySelector(".tradingview-lightweight-chart");
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
    const lineSeries = {};
    const rsiSeries = chart.addSeries(tv.LineSeries, {
      color: "#22d3ee",
      lineWidth: 2,
      priceScaleId: "right",
      priceFormat: { type: "price", precision: 2, minMove: 0.01 },
      priceLineVisible: true,
      lastValueVisible: true,
      title: "RSI 14",
    }, PAPER_OBSERVATION_RSI_PANE);
    rsiSeries.setData(paperObservationRsiRows(candles));
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
    }, PAPER_OBSERVATION_RSI_PANE);
    rsiFloor.setData(historicalConstantRows(candles, 0));
    const rsiCeiling = chart.addSeries(tv.LineSeries, {
      color: "rgba(0, 0, 0, 0)",
      lineWidth: 1,
      priceScaleId: "right",
      priceFormat: { type: "price", precision: 2, minMove: 0.01 },
      priceLineVisible: false,
      lastValueVisible: false,
      title: "RSI ceiling",
    }, PAPER_OBSERVATION_RSI_PANE);
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
    }, PAPER_OBSERVATION_PRICE_PANE);
    candleSeries.setData(chartPriceRows(candles));
    const volumeSeries = chart.addSeries(tv.HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
      color: "rgba(107, 132, 145, 0.35)",
    }, PAPER_OBSERVATION_PRICE_PANE);
    chart.priceScale("volume", PAPER_OBSERVATION_PRICE_PANE).applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
    volumeSeries.setData(chartVolumeRows(candles));
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
      }, PAPER_OBSERVATION_PRICE_PANE);
      line.setData(indicatorSeries(candles, label, period));
      lineSeries[label] = line;
    });
    const macdRows = paperObservationMacdSeries(candles);
    const macdHistogram = chart.addSeries(tv.HistogramSeries, {
      priceScaleId: "right",
      priceFormat: { type: "price", precision: 4, minMove: 0.0001 },
      base: 0,
      color: "rgba(37, 208, 132, 0.42)",
      title: "MACD histogram",
    }, PAPER_OBSERVATION_MACD_PANE);
    macdHistogram.setData(macdRows.histogramRows);
    const macdLine = chart.addSeries(tv.LineSeries, {
      color: "#22d3ee",
      lineWidth: 2,
      priceScaleId: "right",
      priceFormat: { type: "price", precision: 4, minMove: 0.0001 },
      priceLineVisible: true,
      lastValueVisible: true,
      title: "MACD",
    }, PAPER_OBSERVATION_MACD_PANE);
    macdLine.setData(macdRows.macdRows);
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
    }, PAPER_OBSERVATION_MACD_PANE);
    macdSignalLine.setData(macdRows.signalRows);
    lineSeries.MACD = macdLine;
    lineSeries.MACD_signal = macdSignalLine;
    lineSeries.MACD_histogram = macdHistogram;
    applyPaperObservationPaneScale(chart, PAPER_OBSERVATION_RSI_PANE);
    applyPaperObservationPaneScale(chart, PAPER_OBSERVATION_PRICE_PANE);
    applyPaperObservationPaneScale(chart, PAPER_OBSERVATION_MACD_PANE);
    const markers = paperObservationChartMarkers(candles, chartPayload.paper_markers);
    if (typeof tv.createSeriesMarkers === "function") {
      chartState.markerHandle = tv.createSeriesMarkers(candleSeries, markers);
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
      const observer = new ResizeObserver(schedulePaperObservationResize);
      observer.observe(mount);
      chartState.resizeObserver = observer;
    }
    setPaperObservationPaneHeights(chart, height);
    return true;
  }

  function renderPaperObservationChart() {
    if (!elements.paperObservationLiveChart) return;
    const chart = paperObservationChartSource();
    const candles = paperObservationChartCandles(chart.candles);
    const latest = candles.length ? candles[candles.length - 1] : null;
    const markerCount = paperObservationRows(chart.paper_markers).length;
    if (renderPaperObservationLightweightChart(chart, candles)) return;
    elements.paperObservationLiveChart.innerHTML = `
      <div class="tradingview-chart-topline">
        <strong>${escapeHtml(chart.symbol || selectedPaperObservationVenueSymbol())}-PERP</strong>
        <span>${escapeHtml(displayTimeframe(chart.timeframe || selectedPaperObservationTimeframe()))} public-mainnet paper observation</span>
      </div>
      <div class="tradingview-chart-stage paper-observation-chart-stage">
        <div class="tradingview-lightweight-chart" role="img" aria-label="Paper Observation public-mainnet candle chart placeholder">
          <div class="empty-state">
            ${escapeHtml(candles.length ? `${candles.length} public-mainnet candles loaded. Latest close ${latest?.close || "n/a"} at ${latest?.time ? new Date(latest.time * 1000).toISOString() : "n/a"}. Paper markers: ${markerCount}.` : "Live public mainnet candles load from browser allMids/candleSnapshot polling or ignored PT-RT1 runtime state during an observation run.")}
          </div>
        </div>
      </div>
      <div class="tradingview-attribution">Charts: TradingView Lightweight Charts v${TRADINGVIEW_LIGHTWEIGHT_CHARTS_VERSION}. Display-only filter; not canonical evidence; not backend replay; ${escapeHtml(chart.status || "waiting")} ${escapeHtml(chart.error || "")}</div>
    `;
  }

  function renderPaperObservationProbeStatus() {
    if (!elements.paperObservationProbeStatus) return;
    const summary = paperObservationSummary();
    const policy = summary?.testnet_probe_policy || {};
    const orderPolicy = {
      ...(summary?.pt_rt1_5_testnet_order_policy || {}),
      ...(summary?.testnet_order_policy || {}),
    };
    const plumbing = summary?.plumbing_lane || {};
    const runtime = summary?.testnet_plumbing_status || {};
    const lifecycleRows = paperObservationTestnetLifecycleRows(summary);
    const warmStart = summary?.warm_start_gate || {};
    const signedLifecycleRows = lifecycleRows.filter((row) => row.signed_order_endpoint_called === true || row.order_endpoint_called === true);
    const submittedCount = signedLifecycleRows.length || orderPolicy.submitted_this_cycle || 0;
    const cancelCount = lifecycleRows.filter((row) => row.cancel_endpoint_called === true || row.cancel_status === "canceled").length;
    const reconciledCount = lifecycleRows.filter((row) => row.reconcile_status === "reconciled" || row.status === "reconciled").length;
    const latestLifecycle = lifecycleRows[0] || {};
    const signedCalled = Boolean(signedLifecycleRows.length || orderPolicy.signed_order_endpoint_called || runtime.signed_order_endpoint_called || runtime.order_endpoint_called);
    const auditShapeEnabled = runtime.status === "enabled_audit_only" || Number(runtime.probe_audit_rows_this_cycle || 0) > 0;
    const orderTransportEnabled = Boolean(orderPolicy.order_transport_enabled || (runtime.transport_mode && runtime.transport_mode !== "audit_only" && signedCalled));
    const signedClient = Boolean(orderPolicy.signed_testnet_transport_client_configured || orderPolicy.transport_submit_configured);
    const openAfterReconcile = lifecycleRows.some((row) => row.open_order_remains === true);
    const unknownState = lifecycleRows.some((row) => row.unknown_state === true || row.status === "unknown_state");
    elements.paperObservationProbeStatus.innerHTML = `
      <div class="market-micro-grid">
        <div><span>Lane</span><strong>testnet plumbing only</strong></div>
        <div><span>Testnet order transport</span><strong>${escapeHtml(String(orderTransportEnabled))}</strong></div>
        <div><span>Signed transport client</span><strong>${escapeHtml(signedClient ? "configured" : "missing")}</strong></div>
        <div><span>Audit-only shapes</span><strong>${escapeHtml(String(auditShapeEnabled || policy.PT_RT1_TESTNET_PROBES_ENABLED || false))}</strong></div>
        <div><span>Order kill switch</span><strong>${escapeHtml(String(orderPolicy.kill_switch_active ?? policy.PT_RT1_TESTNET_KILL_SWITCH ?? true))}</strong></div>
        <div><span>Daily cap</span><strong>${escapeHtml(String(orderPolicy.daily_order_cap_default ?? runtime.daily_cap ?? policy.PT_RT1_TESTNET_DAILY_PROBE_CAP ?? 25))}</strong></div>
        <div><span>Eligible trigger</span><strong>Money Flow v1.2 fresh baseline opens only</strong></div>
        <div><span>Transport mode</span><strong>${escapeHtml(orderTransportEnabled ? "baseline_only_testnet" : runtime.transport_mode || "ready_but_gated")}</strong></div>
        <div><span>Audit/order-shape rows</span><strong>${escapeHtml(String(runtime.probe_audit_rows_this_cycle ?? 0))}</strong></div>
        <div><span>Signed testnet orders</span><strong>${escapeHtml(String(signedCalled ? submittedCount : 0))}</strong></div>
        <div><span>Cancel / reconcile</span><strong>${escapeHtml(`${cancelCount || runtime.transport_cancel_attempted_this_cycle || 0} / ${reconciledCount || runtime.transport_reconciled_this_cycle || 0}`)}</strong></div>
        <div><span>Notional per order</span><strong>${escapeHtml(String(orderPolicy.fixed_notional_usdc ?? runtime.probe_notional_cap_usdc ?? "25"))} USDC</strong></div>
        <div><span>Lifecycle rows</span><strong>${escapeHtml(String(lifecycleRows.length || orderPolicy.lifecycle_rows_this_cycle || 0))}</strong></div>
        <div><span>Last lifecycle</span><strong>${escapeHtml(latestLifecycle.status ? `${latestLifecycle.symbol || "n/a"} ${displayTimeframe(latestLifecycle.timeframe)} ${latestLifecycle.status}` : runtime.transport_status || "runtime_not_started")}</strong></div>
        <div><span>Open after reconcile</span><strong>${escapeHtml(openAfterReconcile ? "present" : "none")}</strong></div>
        <div><span>Unknown state</span><strong>${escapeHtml(unknownState ? "present" : "none")}</strong></div>
        <div><span>Strategy PnL update</span><strong>${escapeHtml(String(runtime.testnet_fills_do_not_update_strategy_pnl === true ? false : plumbing.testnet_fills_update_strategy_pnl ?? false))}</strong></div>
        <div><span>Candidate transport</span><strong>blocked</strong></div>
        <div><span>Warm-start gate</span><strong>${escapeHtml(warmStart.active ? "active" : "inactive")}</strong></div>
        <div><span>Startup-valid blocked</span><strong>${escapeHtml(String(warmStart.startup_valid_signals_blocked_total ?? warmStart.startup_valid_signals_blocked_this_cycle ?? 0))}</strong></div>
        <div><span>Waiting for reset</span><strong>${escapeHtml(String(warmStart.waiting_for_reset_signals_total ?? warmStart.waiting_for_reset_signals_this_cycle ?? 0))}</strong></div>
        <div><span>Fresh post-start opens</span><strong>${escapeHtml(String(warmStart.fresh_post_start_opens_total ?? warmStart.fresh_post_start_opens_this_cycle ?? 0))}</strong></div>
      </div>
    `;
  }

  function paperObservationTestnetLifecycleRows(summary) {
    const rows = [
      ...paperObservationRows(summary?.testnet_order_lifecycle?.rows),
      ...paperObservationRows(state.ptRt1TestnetLifecycleRows),
    ];
    const seen = new Set();
    return rows
      .filter(Boolean)
      .filter((row) => {
        const key = [
          row.testnet_order_key || row.oid || row.testnet_order_id || "",
          row.created_at_utc || row.time || row.signal_candle_close_time || "",
          row.symbol || "",
          row.timeframe || "",
          row.status || "",
        ].join("|");
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .sort((left, right) => String(right.created_at_utc || right.time || right.signal_candle_close_time || "").localeCompare(String(left.created_at_utc || left.time || left.signal_candle_close_time || "")));
  }

  function renderPaperObservationTestnetLifecycle() {
    if (!elements.paperObservationTestnetLifecycle) return;
    const summary = paperObservationSummary();
    const rows = paperObservationTestnetLifecycleRows(summary);
    if (!rows.length) {
      setEmpty(elements.paperObservationTestnetLifecycle, "No PT-RT1.5 testnet order lifecycle rows yet. Baseline-only lifecycle rows appear after scheduled Money Flow v1.2 synthetic opens.");
      return;
    }
    elements.paperObservationTestnetLifecycle.innerHTML = `
      <div class="methodology-warning compact">
        Testnet lifecycle rows are plumbing-only. They are separate from synthetic closed trades and never update strategy PnL.
      </div>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Symbol</th>
            <th>Timeframe</th>
            <th>Trigger lane</th>
            <th>Trigger reason</th>
            <th>Signal candle</th>
            <th>Fresh signal</th>
            <th>Asset</th>
            <th>szDec</th>
            <th>OID</th>
            <th>Status</th>
            <th>Side</th>
            <th>Notional</th>
            <th>Limit</th>
            <th>Raw qty</th>
            <th>Formatted qty</th>
            <th>Est. notional</th>
            <th>Endpoint called</th>
            <th>Signed called</th>
            <th>Venue response</th>
            <th>Cancel</th>
            <th>Reconcile</th>
            <th>Strategy PnL update</th>
            <th>Reason codes</th>
          </tr>
        </thead>
        <tbody>
          ${rows.slice(0, 50).map((row) => `
            <tr>
              <td>${escapeHtml(paperObservationText(row.created_at_utc || row.time, "n/a"))}</td>
              <td>${escapeHtml(paperObservationText(row.symbol, "n/a"))}</td>
              <td>${escapeHtml(displayTimeframe(row.timeframe))}</td>
              <td>${paperObservationLaneChip(row.trigger_lane || row.lane_id || row.strategy_id)}</td>
              <td>${escapeHtml(paperObservationText(row.trigger_reason || row.trigger_reason_codes, "n/a"))}</td>
              <td>${escapeHtml(paperObservationText(row.signal_candle_close_time || row.signal_candle, "n/a"))}</td>
              <td>${escapeHtml(String(row.fresh_signal_after_runtime_start === true))}</td>
              <td>${escapeHtml(paperObservationText(row.asset_id, "n/a"))}</td>
              <td>${escapeHtml(paperObservationText(row.szDecimals ?? row.sz_decimals, "n/a"))}</td>
              <td>${escapeHtml(paperObservationText(row.oid || row.venue_order_id || row.testnet_order_id, "not_submitted"))}</td>
              <td>${auditReviewPill(row.status || "created")}</td>
              <td>${escapeHtml(paperObservationText(row.side, "buy"))}</td>
              <td>${escapeHtml(paperObservationUsdc(row.notional || row.testnet_fixed_notional || 25))}</td>
              <td>${escapeHtml(paperObservationPrice(row.formatted_limit_price || row.limit_price))}</td>
              <td>${escapeHtml(paperObservationPrice(row.raw_quantity))}</td>
              <td>${escapeHtml(paperObservationPrice(row.formatted_quantity || row.quantity))}</td>
              <td>${escapeHtml(paperObservationUsdc(row.estimated_testnet_notional))}</td>
              <td>${escapeHtml(String(row.order_endpoint_called === true))}</td>
              <td>${escapeHtml(String(row.signed_order_endpoint_called === true))}</td>
              <td>${escapeHtml(paperObservationText(row.venue_response || row.sanitized_response, "n/a"))}</td>
              <td>${escapeHtml(paperObservationText(row.cancel_status, "required_after_submit"))}</td>
              <td>${escapeHtml(paperObservationText(row.reconcile_status, "required_after_submit"))}</td>
              <td>${escapeHtml(String(row.strategy_pnl_updated === true ? true : false))}</td>
              <td>${escapeHtml(paperObservationText(row.reason_codes, "n/a"))}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderPaperObservationRuntimeTables() {
    const summary = paperObservationSummary();
    const runtimeState = summary?.paper_runtime_state || {};
    const openRows = Object.entries(runtimeState.open_positions_by_key || {})
      .map(([key, position]) => ({ key, ...position }))
      .filter((row) => paperObservationFiltersMatch(row, { includeDate: false }))
      .sort((left, right) => decimal(left.current_unrealized_pnl, 0) - decimal(right.current_unrealized_pnl, 0) || String(paperObservationDecisionTime(right)).localeCompare(String(paperObservationDecisionTime(left))));
    const closedRows = paperObservationClosedRows(summary)
      .filter((row) => paperObservationFiltersMatch(row, { includeDate: true }));
    if (elements.paperObservationOpenPositions && openRows.length) {
      const page = paperObservationPageRows(openRows, "openPositions");
      elements.paperObservationOpenPositions.innerHTML = `
        <div class="methodology-warning compact">Default view shows active timeframes only. Quick filters: All active, Losing only, Winning only, Legacy 15m, By lane, By symbol, By timeframe.</div>
        ${paperObservationPaginationControls("openPositions", page)}
        <table>
          <thead><tr><th>Lane</th><th>Symbol</th><th>Timeframe</th><th>Entry time</th><th>Age</th><th>Entry price</th><th>Current price</th><th>Quantity</th><th>Notional</th><th>Unrealized PnL</th><th>Unrealized PnL %</th><th>Entry reason</th><th>Data health</th><th>Status</th></tr></thead>
          <tbody>
            ${page.rows.map((row) => {
              const entryTime = row.entry_fill_time || row.entry_signal_time || "";
              const entryMs = Date.parse(entryTime);
              const age = Number.isFinite(entryMs) ? `${Math.max(0, Math.floor((Date.now() - entryMs) / 3600000))}h` : "n/a";
              const mtmAvailable = row.current_price !== null && row.current_price !== undefined && row.current_unrealized_pnl !== null && row.current_unrealized_pnl !== undefined;
              const unrealized = mtmAvailable ? decimal(row.current_unrealized_pnl, 0) : null;
              const notional = decimal(row.notional || row.equity_before, 0);
              const unrealizedPct = mtmAvailable && notional ? `${(unrealized / notional * 100).toFixed(2)}%` : "MTM unavailable";
              const timeframe = paperObservationRowTimeframe(row);
              const roleBadge = paperObservationIsDisabledTimeframe(timeframe) ? "legacy_15m" : "active";
              const mtmReason = mtmAvailable ? row.current_price_source || "public_mainnet_mid" : "MTM unavailable";
              return `
                <tr>
                  <td>${paperObservationLaneChip(row.strategy_id || row.lane_id)}</td>
                  <td>${escapeHtml(row.symbol || "n/a")}</td>
                  <td>${escapeHtml(displayTimeframe(row.timeframe))}</td>
                  <td>${escapeHtml(entryTime || "n/a")}</td>
                  <td>${escapeHtml(age)}</td>
                  <td>${escapeHtml(paperObservationPrice(row.entry_price))}</td>
                  <td>${escapeHtml(mtmAvailable ? `${paperObservationPrice(row.current_price || row.mark_price)} (${mtmReason})` : "MTM unavailable")}</td>
                  <td>${escapeHtml(paperObservationPrice(row.quantity))}</td>
                  <td>${escapeHtml(paperObservationUsdc(notional))}</td>
                  <td class="${mtmAvailable && unrealized >= 0 ? "positive" : mtmAvailable ? "negative" : ""}">${escapeHtml(mtmAvailable ? paperObservationUsdc(unrealized) : "MTM unavailable")}</td>
                  <td>${escapeHtml(unrealizedPct)}</td>
                  <td>${escapeHtml(paperObservationText(row.open_reason_codes, "n/a"))}</td>
                  <td>${auditReviewPill(row.data_health || "healthy_or_pending")}</td>
                  <td>${auditReviewPill(`${roleBadge} ${row.status || "open"}`)}</td>
                </tr>
              `;
            }).join("")}
          </tbody>
        </table>
        ${paperObservationPaginationControls("openPositions", page)}
      `;
      attachPaperObservationPagination(elements.paperObservationOpenPositions, "openPositions");
    } else {
      const openMessage = "No open synthetic positions loaded from ignored PT-RT1 runtime state.";
      if (elements.paperObservationOpenPositions) setEmpty(elements.paperObservationOpenPositions, openMessage);
    }
    const closedMessage = "No closed synthetic trades loaded from ignored PT-RT1 runtime state.";
    const riskMessage = "No runtime drawdown or losing-streak rows loaded yet.";
    if (elements.paperObservationClosedTrades && closedRows.length) {
      const page = paperObservationPageRows(closedRows, "closedTrades");
      const wins = closedRows.filter((row) => decimal(row.net_pnl, 0) > 0);
      const losses = closedRows.filter((row) => decimal(row.net_pnl, 0) < 0);
      const largestWin = wins.length ? Math.max(...wins.map((row) => decimal(row.net_pnl, 0))) : 0;
      const largestLoss = losses.length ? Math.min(...losses.map((row) => decimal(row.net_pnl, 0))) : 0;
      const avgWin = wins.length ? wins.reduce((total, row) => total + decimal(row.net_pnl, 0), 0) / wins.length : 0;
      const avgLoss = losses.length ? losses.reduce((total, row) => total + decimal(row.net_pnl, 0), 0) / losses.length : 0;
      const totalNet = closedRows.reduce((total, row) => total + decimal(row.net_pnl, 0), 0);
      elements.paperObservationClosedTrades.innerHTML = `
        <div class="methodology-warning compact">
          Showing closed synthetic trades from ${escapeHtml(state.ptRt1TradeSource || "runtime summary / trades stream")}. These rows are synthetic public-mainnet paper PnL, not exchange fills.
        </div>
        <div class="paper-observation-trade-summary-cards">
          <span>Closed ${escapeHtml(String(closedRows.length))}</span>
          <span>Winning ${escapeHtml(String(wins.length))}</span>
          <span>Losing ${escapeHtml(String(losses.length))}</span>
          <span>Largest win ${escapeHtml(paperObservationUsdc(largestWin))}</span>
          <span>Largest loss ${escapeHtml(paperObservationUsdc(largestLoss))}</span>
          <span>Average win ${escapeHtml(paperObservationUsdc(avgWin))}</span>
          <span>Average loss ${escapeHtml(paperObservationUsdc(avgLoss))}</span>
          <span>Total net PnL ${escapeHtml(paperObservationUsdc(totalNet))}</span>
        </div>
        <div class="methodology-warning compact">Quick filters: Recent closes, Winners, Losers, Largest losses, Largest wins, Legacy 15m.</div>
        ${paperObservationPaginationControls("closedTrades", page)}
        <table>
          <thead><tr><th>Lane</th><th>Symbol</th><th>Timeframe</th><th>Entry time</th><th>Exit time</th><th>Duration</th><th>Entry price</th><th>Exit price</th><th>Quantity</th><th>Net PnL</th><th>Net PnL %</th><th>Equity after</th><th>Exit reason</th><th>Fees/slippage</th></tr></thead>
          <tbody>
            ${page.rows.map((row) => {
              const entryTime = row.entry_time || row.entry_fill_time || row.entry_signal_time || "";
              const exitTime = row.exit_time || row.exit_fill_time || row.exit_signal_time || "";
              const durationMs = Date.parse(exitTime) - Date.parse(entryTime);
              const duration = Number.isFinite(durationMs) ? `${Math.max(0, Math.round(durationMs / 3600000))}h` : "n/a";
              const netPnl = decimal(row.net_pnl, 0);
              const equityBefore = decimal(row.equity_before, 0);
              const netPct = equityBefore ? `${(netPnl / equityBefore * 100).toFixed(2)}%` : "n/a";
              return `
                <tr>
                  <td>${paperObservationLaneChip(row.strategy_id || row.lane_id)}</td>
                  <td>${escapeHtml(row.symbol || "n/a")}</td>
                  <td>${escapeHtml(displayTimeframe(row.timeframe))}</td>
                  <td>${escapeHtml(entryTime || "n/a")}</td>
                  <td>${escapeHtml(exitTime || "n/a")}</td>
                  <td>${escapeHtml(duration)}</td>
                  <td>${escapeHtml(paperObservationPrice(row.entry_price))}</td>
                  <td>${escapeHtml(paperObservationPrice(row.exit_price))}</td>
                  <td>${escapeHtml(paperObservationPrice(row.quantity))}</td>
                  <td class="${netPnl >= 0 ? "positive" : "negative"}">${escapeHtml(paperObservationUsdc(netPnl))}</td>
                  <td>${escapeHtml(netPct)}</td>
                  <td>${escapeHtml(paperObservationUsdc(row.equity_after))}</td>
                  <td>${escapeHtml(paperObservationText(row.exit_reason_codes || row.reason_codes, "n/a"))}</td>
                  <td>${escapeHtml(`${paperObservationUsdc(row.fees || 0)} / ${paperObservationUsdc(row.slippage || 0)}`)}</td>
                </tr>
              `;
            }).join("")}
          </tbody>
        </table>
        ${paperObservationPaginationControls("closedTrades", page)}
      `;
      attachPaperObservationPagination(elements.paperObservationClosedTrades, "closedTrades");
    } else if (elements.paperObservationClosedTrades) {
      setEmpty(elements.paperObservationClosedTrades, closedMessage);
    }
    if (elements.paperObservationRiskTable) {
      elements.paperObservationRiskTable.innerHTML = `
        <div class="market-micro-grid">
          <div><span>Processed signal keys</span><strong>${escapeHtml(String(runtimeState.processed_signal_keys_total ?? "n/a"))}</strong></div>
          <div><span>Opens this cycle</span><strong>${escapeHtml(String(runtimeState.paper_opens_this_cycle ?? "n/a"))}</strong></div>
          <div><span>Closes this cycle</span><strong>${escapeHtml(String(runtimeState.paper_closes_this_cycle ?? "n/a"))}</strong></div>
          <div><span>Duplicate blocks</span><strong>${escapeHtml(String(runtimeState.duplicate_signal_blocks_this_cycle ?? "n/a"))}</strong></div>
          <div><span>Paper PnL source</span><strong>${escapeHtml(runtimeState.paper_pnl_source || "synthetic_public_mainnet_paper_ledger")}</strong></div>
          <div><span>Testnet fills update PnL</span><strong>${escapeHtml(String(runtimeState.testnet_fills_update_strategy_pnl === true))}</strong></div>
        </div>
        ${closedRows.length ? "" : `<p class="muted-inline">${escapeHtml(riskMessage)}</p>`}
      `;
    }
  }

  function renderPaperObservation() {
    renderPaperObservationControls();
    renderPaperRuntimeControl();
    renderPaperObservationHealthBanner();
    renderPaperObservationConnectionStatus();
    renderPaperObservationSummaryCards();
    renderPaperObservationDailyReview();
    renderPaperObservationLanes();
    renderPaperObservationTimeframeBreakdown();
    renderPaperObservationLaneDetail();
    renderPaperObservationChart();
    renderPaperObservationScanner();
    renderPaperObservationRuntimeTables();
    renderPaperObservationSignalGeneration();
    renderPaperObservationProbeStatus();
    renderPaperObservationTestnetLifecycle();
  }

  // ---------------------------------------------------------------------------
  // DASH-IA1 Research Log placeholder — institutional memory of what has been
  // tested. Reads the committed docs/*_summary.json evidence summaries only
  // (no hand-coded data); absent summaries are omitted gracefully. The full
  // post-mortem view lands in RLOG1.
  // ---------------------------------------------------------------------------

  const RESEARCH_LOG_SUMMARY_SOURCES = [
    "../../docs/sel_ev1_selection_evidence_summary.json",
    "../../docs/exec_ev1_execution_quality_evidence_summary.json",
    "../../docs/sv2_3_realistic_backtest_summary.json",
    "../../docs/sv2_2_hyperliquid_research_refresh_summary.json",
    "../../docs/goal_strat2_two_non_existing_strategies_summary.json",
    "../../docs/goal_strat1_strategy_discovery_summary.json",
    "../../docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review_summary.json",
    "../../docs/mf_orig_ev2_multitimeframe_evidence_summary.json",
    "../../docs/mf_orig_ev1_original_money_flow_reconstruction_summary.json",
    "../../docs/sor_ev3_avoid_sideways_low_volatility_summary.json",
    "../../docs/sor_ev2_true_forward_stop_and_rejected_signal_replay_summary.json",
    "../../docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants_summary.json",
  ];

  function researchLogVerdict(payload) {
    return (
      payload?.verdict ||
      payload?.conclusion ||
      payload?.audit_verdict ||
      payload?.gate_status ||
      payload?.status ||
      "verdict_not_recorded"
    );
  }

  function researchLogDate(payload) {
    const value = payload?.generated_at_utc || payload?.generated_at || payload?.run_timestamp || "";
    return value ? String(value).slice(0, 10) : "";
  }

  async function loadResearchLogSummaries() {
    const rows = [];
    for (const path of RESEARCH_LOG_SUMMARY_SOURCES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (!payload || typeof payload !== "object") continue;
        rows.push({
          phase: String(payload.phase || path.split("/").pop()),
          date: researchLogDate(payload),
          verdict: String(researchLogVerdict(payload)),
          source: path.replace("../../", ""),
        });
      } catch (error) {
        // Absent summaries are omitted gracefully; the row list stays data-driven.
        console.warn(`Research Log: could not load ${path}`, error);
      }
    }
    rows.sort((left, right) => String(right.date).localeCompare(String(left.date)) || left.phase.localeCompare(right.phase));
    state.researchLog = { rows, loaded: true };
  }

  function renderResearchLog() {
    if (!elements.researchLogVerdictList) return;
    const { rows, loaded } = state.researchLog || { rows: [], loaded: false };
    if (!loaded) {
      setEmpty(elements.researchLogVerdictList, "Loading committed research summaries from docs/ ...");
      return;
    }
    if (!rows.length) {
      setEmpty(elements.researchLogVerdictList, "No committed research summaries were found under docs/.");
      return;
    }
    elements.researchLogVerdictList.innerHTML = `
      <table class="research-log-table">
        <thead>
          <tr><th>Phase</th><th>Date</th><th>Verdict</th><th>Committed summary</th></tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  <td><span class="research-log-phase">${escapeHtml(row.phase)}</span></td>
                  <td>${escapeHtml(row.date || "date_not_recorded")}</td>
                  <td>${auditReviewPill(row.verdict)}</td>
                  <td class="research-log-source">${escapeHtml(row.source)}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  function render() {
    renderResearchLog();
    renderExperiments();
    renderAuditReview();
    renderPaperObservation();
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
    if (payload?.phase === "SV2.1" && Array.isArray(payload?.evidence_pack_paths)) return "sv21_broad_summary";
    if (payload?.phase === "SV2.2" && payload?.report === "sv2_2_hyperliquid_research_refresh") return "sv22_refresh_summary";
    if (payload?.phase === "SV2.3" && payload?.report === "sv2_3_realistic_backtest") return "sv23_realistic_summary";
    if (
      payload?.report === "sv2_0_2_dashboard_historical_replay_chart_data" ||
      payload?.report === "mf_orig_ev2_dashboard_chart_data" ||
      payload?.report === "sv2_1_broad_1d_dashboard_chart_data" ||
      payload?.report === "sv2_2_week2_replay_dashboard_chart_data"
    ) return "sv202_dashboard_chart_data";
    if (payload?.phase === "SOR-EV1") return "sor_ev1_summary";
    if (payload?.phase === "SOR-EV2") return "sor_ev2_summary";
    if (payload?.phase === "SOR-EV3") return "sor_ev3_summary";
    if (String(payload?.phase || "").startsWith("MF-ORIG-EV1")) return "mf_orig_summary";
    if (String(payload?.phase || "").startsWith("MF-ORIG-EV2")) return "mf_orig_summary";
    if (payload?.phase === "EV-AUDIT1" || payload?.audit_verdict === "no_strategy_has_clean_production_or_paper_candidate_status") {
      return "ev_audit_summary";
    }
    if (
      String(payload?.phase || "").startsWith("PT-RT1") ||
      payload?.report === "pt_rt1_real_time_paper_observation_and_testnet_plumbing" ||
      payload?.active_review_scope?.scope === PAPER_OBSERVATION_ACTIVE_RUNTIME_SCOPE
    ) {
      return "pt_rt1_summary";
    }
    if (
      payload?.report === "pt0_0_2_historical_strategy_replay_cockpit" ||
      payload?.report === "pt0_0_3_historical_data_horizon_and_1d_replay"
    ) return "pt002_historical_replay_summary";
    return "unknown";
  }

  async function loadDefaultFiles() {
    await loadDefaultUat2Summaries();
    await loadDefaultUat34Summaries();
    await loadDefaultUat42Summaries();
    await loadDefaultPt0Summaries();
    await loadDefaultEvAuditSummaries();
    await loadDefaultPtRt1Summaries();
    await loadDefaultPtRt1DecisionRows();
    await loadDefaultPtRt1TradeRows();
    await loadDefaultPtRt1TestnetLifecycleRows();
    await loadDefaultPtRt1DailyReview();
    await loadResearchLogSummaries();
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
      valid.forEach(({ name, payload }) => {
        const type = classifyJson(payload);
        if (type === "review") state.review = payload;
        if (type === "batch") state.batches.push({ ...payload, __source_path: name });
        if (type === "experiment_summary") state.sv117FullSuiteRows = normalizeReplayRows(payload.summary_rows);
        if (type === "uat2_shadow_summary") state.uat2Summary = payload;
        if (type === "uat34_routed_orders_summary") state.uat34Summary = payload;
        if (type === "uat42_live_monitor_summary") state.uat42Summary = payload;
        if (type === "pt0_runtime_summary") state.pt0Summary = payload;
        if (type === "ev_audit_summary") state.evAuditSummary = payload;
        if (type === "pt_rt1_summary") state.ptRt1Summary = payload;
      });
      if (elements.sourceLabel) elements.sourceLabel.textContent = "Manual JSON loaded";
      if (elements.sourceDetail) elements.sourceDetail.textContent = `${valid.length} local files selected.`;
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

  function parsePaperObservationDecisionLog(text, sourcePath) {
    return String(text || "")
      .split(/\r?\n/)
      .filter(Boolean)
      .slice(-PAPER_OBSERVATION_DECISION_LOG_LIMIT)
      .map((line) => {
        try {
          const row = JSON.parse(line);
          return row && typeof row === "object" ? { ...row, __source_path: sourcePath } : null;
        } catch (error) {
          return null;
        }
      })
      .filter(Boolean);
  }

  function parsePaperObservationTradeLog(text, sourcePath) {
    return String(text || "")
      .split(/\r?\n/)
      .filter(Boolean)
      .slice(-PAPER_OBSERVATION_TRADE_LOG_LIMIT)
      .map((line) => {
        try {
          const row = JSON.parse(line);
          return row && typeof row === "object" ? { ...row, __source_path: sourcePath } : null;
        } catch (error) {
          return null;
        }
      })
      .filter(Boolean);
  }

  function parsePaperObservationTestnetLifecycleLog(text, sourcePath) {
    return String(text || "")
      .split(/\r?\n/)
      .filter(Boolean)
      .slice(-PAPER_OBSERVATION_DECISION_LOG_LIMIT)
      .map((line) => {
        try {
          const row = JSON.parse(line);
          return row && typeof row === "object" ? { ...row, __source_path: sourcePath } : null;
        } catch (error) {
          return null;
        }
      })
      .filter(Boolean);
  }

  async function loadDefaultPtRt1DecisionRows() {
    for (const path of DEFAULT_PT_RT1_DECISION_LOG_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const text = await response.text();
        const rows = parsePaperObservationDecisionLog(text, path);
        state.ptRt1DecisionRows = rows;
        state.ptRt1DecisionSource = path;
        break;
      } catch (error) {
        console.warn(`Could not load ${path}`, error);
      }
    }
  }

  async function loadDefaultPtRt1TradeRows() {
    for (const path of DEFAULT_PT_RT1_TRADE_LOG_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const text = await response.text();
        const rows = parsePaperObservationTradeLog(text, path);
        state.ptRt1TradeRows = rows;
        state.ptRt1TradeSource = path;
        break;
      } catch (error) {
        console.warn(`Could not load ${path}`, error);
      }
    }
  }

  async function loadDefaultPtRt1TestnetLifecycleRows() {
    for (const path of DEFAULT_PT_RT1_TESTNET_LIFECYCLE_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const text = await response.text();
        const rows = parsePaperObservationTestnetLifecycleLog(text, path);
        state.ptRt1TestnetLifecycleRows = rows;
        state.ptRt1TestnetLifecycleSource = path;
        break;
      } catch (error) {
        console.warn(`Could not load ${path}`, error);
      }
    }
  }

  async function loadDefaultPtRt1DailyReview() {
    for (const path of DEFAULT_PT_RT1_DAILY_REVIEW_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (payload?.report === "obs_os1_week2_paper_observation_daily_review") {
          state.ptRtDailyReview = { ...payload, __source_path: path };
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

  if (elements.fileInput) {
    elements.fileInput.addEventListener("change", (event) => {
      handleFiles(event.target.files || []);
    });
  }

  if (elements.themeSelector) {
    elements.themeSelector.addEventListener("change", () => {
      applyDashboardTheme(elements.themeSelector.value);
      destroyTradingViewChart();
      destroyPaperObservationChart();
      render();
    });
  }

  elements.viewTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      setActiveView(tab.dataset.view || "paper-observation");
    });
  });

  elements.paperTerminalTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      setPaperObservationTerminalTab(tab.dataset.paperTerminalTab || "open");
    });
  });

  applyDashboardTheme(state.theme);
  setActiveView(state.activeView);
  setPaperObservationTerminalTab(state.paperObservation.terminalTab);
  render();
  loadDefaultFiles();
  startLiveMarketPolling();
  startPaperObservationMarketPolling();
})();
