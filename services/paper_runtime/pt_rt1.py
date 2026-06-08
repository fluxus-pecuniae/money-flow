"""PT-RT1 real-time paper-observation primitives.

The module is intentionally small and policy-heavy:

* strategy truth is public Hyperliquid mainnet ``/info`` data only;
* paper ledgers are synthetic and independent per strategy lane;
* testnet probes are plumbing-only, disabled by default, and never update paper
  PnL;
* no production ``OrderIntent``, ``PreparedVenueOrder``, or ``SubmittedOrder``
  artifacts are constructed here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Any, Mapping, Sequence

from services.exchange.hyperliquid.precision import HyperliquidPrecisionFormatter


PT_RT1_MAINNET_API_URL = "https://api.hyperliquid.xyz"
PT_RT1_TESTNET_API_URL = "https://api.hyperliquid-testnet.xyz"
PT_RT1_MAINNET_INFO_URL = f"{PT_RT1_MAINNET_API_URL}/info"
PT_RT1_TESTNET_INFO_URL = f"{PT_RT1_TESTNET_API_URL}/info"
PT_RT1_TESTNET_PROBE_NOTIONAL_USDC = Decimal("20")
PT_RT1_TESTNET_PROBE_NOTIONAL_CAP_USDC = Decimal("20")
PT_RT1_EXACT_TESTNET_PROBE_APPROVAL = (
    "I APPROVE PT-RT1 TESTNET PLUMBING PROBES ONLY. HYPERLIQUID TESTNET ONLY. "
    "POST-ONLY 20 USDC DEFAULT NOTIONAL. CANCEL/RECONCILE REQUIRED. "
    "TESTNET FILLS MUST NOT UPDATE STRATEGY PAPER PNL. LIVE TRADING IS NOT APPROVED."
)

ALLOWED_STRATEGY_TRUTH_INFO_TYPES = frozenset(
    {"meta", "metaAndAssetCtxs", "allMids", "candleSnapshot", "fundingHistory", "l2Book"}
)
FORBIDDEN_STRATEGY_TRUTH_INFO_TYPES = frozenset(
    {"clearinghouseState", "spotClearinghouseState", "openOrders", "orderStatus", "userFills"}
)
TIMEFRAME_DURATIONS = {
    "15m": timedelta(minutes=15),
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
}
PT_RT1_4_ACTIVE_REVIEW_START_UTC = "2026-05-17T09:47:55Z"
PT_RT1_4_ACTIVE_TIMEFRAMES = ("1h", "4h", "1d")
PT_RT1_4_DISABLED_TIMEFRAMES = ("15m",)
PT_RT1_4_DISABLED_TIMEFRAME_STATUS = "disabled_for_week1_noise_reduction"
PT_RT1_4_TIMEFRAME_REASON_CODES = (
    "timeframe_disabled_by_founder_for_week1",
    "timeframe_excluded_from_active_scoreboard",
    "legacy_15m_position_visible",
    "no_new_15m_entries",
)
PT_RT1_5_RUNTIME_SCOPE = "pt_rt1_5_week1_active"
PT_RT1_5_RUNTIME_OUTPUT_DIR = "reports/paper_runtime/pt_rt1_5_week1_active"
PT_RT1_5_ACTIVE_REVIEW_START_UTC = "2026-05-17T12:54:24Z"
PT_RT1_5_1_RUNTIME_SCOPE = "pt_rt1_5_1_smoke"
PT_RT1_5_1_RUNTIME_OUTPUT_DIR = "reports/paper_runtime/pt_rt1_5_1_smoke"
PT_RT1_5_1_ACTIVE_REVIEW_START_UTC = "2026-05-17T14:34:44Z"
PT_RT1_5_2_TRANSPORT_SMOKE_SCOPE = "pt_rt1_5_2_transport_smoke"
PT_RT1_5_2_TRANSPORT_SMOKE_OUTPUT_DIR = "reports/paper_runtime/pt_rt1_5_2_transport_smoke"
PT_RT1_5_2_RUNTIME_SCOPE = "pt_rt1_5_2_week1_active"
PT_RT1_5_2_RUNTIME_OUTPUT_DIR = "reports/paper_runtime/pt_rt1_5_2_week1_active"
PT_RT1_5_2_ACTIVE_REVIEW_START_UTC = "2026-05-17T16:24:49Z"
PT_RT1_5_3_TRANSPORT_SMOKE_SCOPE = "pt_rt1_5_3_transport_smoke"
PT_RT1_5_3_TRANSPORT_SMOKE_OUTPUT_DIR = "reports/paper_runtime/pt_rt1_5_3_transport_smoke"
PT_RT1_6_3_TRANSPORT_SMOKE_SCOPE = "pt_rt1_6_3_xrp_transport_smoke"
PT_RT1_6_3_TRANSPORT_SMOKE_OUTPUT_DIR = "reports/paper_runtime/pt_rt1_6_3_xrp_transport_smoke"
PT_RT1_6_RUNTIME_SCOPE = "pt_rt1_6_week2_active"
PT_RT1_6_RUNTIME_OUTPUT_DIR = "reports/paper_runtime/pt_rt1_6_week2_active"
PT_RT1_6_ACTIVE_REVIEW_START_UTC = "2026-06-07T00:00:00Z"
PT_RT1_5_ARCHIVED_RUNTIME_SCOPES = (
    "pre_pt_rt1_4_weekend_burn_in",
    "pt_rt1_1c_24h_dry_run",
    "pt_rt1_4_1_active_week",
    "pt_rt1_5_smoke_pre_warm_start_gate",
    "pt_rt1_5_1_smoke_archived",
    "pre_pt_rt1_5_2_runtime",
    "legacy_runtime",
)
PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS = (
    "money_flow_v1_2_baseline",
    "avoid_low_rolling_range_20",
    "mf_orig_1d_stage2_breakout_resistance_full_equity",
)
PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS = (
    "avoid_low_rolling_range_50",
    "mf_orig_stage_filter_only_full_equity",
    "mf_orig_stage2_pullback_reclaim_full_equity",
    "mf_orig_1d_stage2_5_20_crossover_full_equity",
    "wildcard_btc_regime_guard",
    "wildcard_multi_timeframe_alignment",
    "wildcard_volatility_expansion_breakout",
)
PT_RT1_6_ACTIVE_TIMEFRAMES = PT_RT1_4_ACTIVE_TIMEFRAMES
PT_RT1_6_DISABLED_TIMEFRAMES = PT_RT1_4_DISABLED_TIMEFRAMES
PT_RT1_6_ARCHIVE_REASON_CODES = (
    "founder_archived_from_week2",
    "not_default_active",
    "historical_reference_only",
    "synthetic_only_if_reenabled",
    "not_testnet_eligible",
    "not_production_eligible",
)
PT_RT1_5_ACTIVE_TIMEFRAMES = PT_RT1_4_ACTIVE_TIMEFRAMES
PT_RT1_5_DISABLED_TIMEFRAMES = PT_RT1_4_DISABLED_TIMEFRAMES
PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC = Decimal("25")
PT_RT1_5_TESTNET_DAILY_ORDER_CAP_DEFAULT = 25
PT_RT1_5_TESTNET_PER_SYMBOL_DAILY_CAP_DEFAULT = 3
PT_RT1_5_EXACT_BASELINE_TESTNET_ORDER_APPROVAL = (
    "I APPROVE PT-RT1.5 HYPERLIQUID TESTNET ORDER TRANSPORT FOR "
    "MONEY_FLOW_V1_2_BASELINE ONLY. TESTNET ONLY. FIXED 25 USDC NOTIONAL "
    "PER BASELINE OPEN SIGNAL. PUBLIC MAINNET DATA REMAINS STRATEGY TRUTH. "
    "TESTNET FILLS MUST NOT UPDATE SYNTHETIC STRATEGY PNL. CANDIDATE LANES "
    "MUST NOT SEND TESTNET ORDERS. LIVE TRADING IS NOT APPROVED."
)
PT_RT1_5_1_EXACT_BASELINE_TESTNET_ORDER_APPROVAL = (
    "I APPROVE PT-RT1.5.1 HYPERLIQUID TESTNET ORDER TRANSPORT FOR "
    "MONEY_FLOW_V1_2_BASELINE ONLY. TESTNET ONLY. FIXED 25 USDC NOTIONAL "
    "PER FRESH BASELINE OPEN SIGNAL. PUBLIC MAINNET DATA REMAINS STRATEGY TRUTH. "
    "TESTNET FILLS MUST NOT UPDATE SYNTHETIC STRATEGY PNL. CANDIDATE LANES MUST "
    "NOT SEND TESTNET ORDERS. LIVE TRADING IS NOT APPROVED."
)
PT_RT1_5_2_EXACT_TESTNET_TRANSPORT_SMOKE_APPROVAL = (
    "I APPROVE PT-RT1.5.2 HYPERLIQUID TESTNET ORDER TRANSPORT SMOKE FOR "
    "MONEY_FLOW_V1_2_BASELINE ONLY. TESTNET ONLY. FIXED 25 USDC NOTIONAL. "
    "PUBLIC MAINNET DATA REMAINS STRATEGY TRUTH. TESTNET FILLS MUST NOT UPDATE "
    "SYNTHETIC STRATEGY PNL. CANDIDATE LANES MUST NOT SEND TESTNET ORDERS. "
    "LIVE TRADING IS NOT APPROVED."
)
PT_RT1_5_3_EXACT_TESTNET_SIZE_HOTFIX_SMOKE_APPROVAL = (
    "I APPROVE PT-RT1.5.3 HYPERLIQUID TESTNET SIZE PRECISION HOTFIX SMOKE. "
    "TESTNET ONLY. FIXED 25 USDC NOTIONAL. PUBLIC MAINNET DATA REMAINS "
    "STRATEGY TRUTH. TESTNET FILLS MUST NOT UPDATE SYNTHETIC STRATEGY PNL. "
    "CANDIDATE LANES MUST NOT SEND TESTNET ORDERS. LIVE TRADING IS NOT APPROVED."
)
PT_RT1_6_3_EXACT_XRP_TESTNET_METADATA_SMOKE_APPROVAL = (
    "I APPROVE PT-RT1.6.3 HYPERLIQUID TESTNET METADATA RESOLVER SMOKE FOR XRP. "
    "TESTNET ONLY. FIXED 25 USDC NOTIONAL. PUBLIC MAINNET DATA REMAINS "
    "STRATEGY TRUTH. TESTNET FILLS MUST NOT UPDATE SYNTHETIC STRATEGY PNL. "
    "CANDIDATE LANES MUST NOT SEND TESTNET ORDERS. LIVE TRADING IS NOT APPROVED."
)
PT_RT1_5_2_TESTNET_SMOKE_PHASE_CAP = 1
PT_RT1_5_CANDLE_CLOSE_GRACE_SECONDS = {
    "1h": 90,
    "4h": 120,
    "1d": 180,
}
PT_RT1_5_CLOSED_CANDLE_RETRY_POLICY = {
    "1h": {"retry_seconds": 60, "max_retry_window_seconds": 600},
    "4h": {"retry_seconds": 60, "max_retry_window_seconds": 600},
    "1d": {"retry_seconds": 60, "max_retry_window_seconds": 1800},
}
PT_RT1_5_SCHEDULER_REASON_CODES = (
    "signal_evaluation_waiting_for_candle_close",
    "signal_evaluation_started_after_closed_candle",
    "expected_closed_candle_missing",
    "closed_candle_retry_scheduled",
    "closed_candle_unavailable_after_retry_window",
    "duplicate_candle_signal_ignored",
    "market_refresh_only_no_signal_evaluation",
    "intrabar_signal_evaluation_blocked",
    "timeframe_paused_no_signal_evaluation",
    "scheduler_close_time_unavailable",
    "scheduler_clock_invalid",
    "scheduler_candle_timestamp_invalid",
)
PT_RT1_5_TESTNET_ORDER_REASON_CODES = (
    "testnet_order_transport_disabled",
    "testnet_order_transport_kill_switch_active",
    "pt_rt1_5_exact_approval_required",
    "testnet_endpoint_required",
    "live_endpoint_forbidden",
    "testnet_order_blocked_non_baseline_lane",
    "testnet_order_blocked_non_open_action",
    "testnet_order_blocked_inactive_timeframe",
    "testnet_order_requires_scheduled_closed_candle_evaluation",
    "testnet_order_requires_fresh_post_start_signal",
    "testnet_duplicate_order_blocked",
    "testnet_order_symbol_blocked",
    "testnet_order_unit_semantics_deferred",
    "testnet_order_precision_missing",
    "testnet_metadata_unavailable",
    "testnet_metadata_alias_resolved",
    "testnet_metadata_symbol_not_on_testnet",
    "testnet_metadata_blocked_symbol_resolved",
    "testnet_transport_smoke_xrp_targeted",
    "testnet_order_invalid_size_preflight",
    "testnet_order_rejected_invalid_size",
    "venue_reject_order_has_invalid_size",
    "testnet_order_notional_must_be_25usdc",
    "testnet_daily_order_cap_exceeded",
    "testnet_per_symbol_daily_cap_exceeded",
    "unknown_testnet_state_blocks_new_orders",
    "vault_address_forbidden_for_main_user",
    "vault_address_required_for_subaccount_or_vault",
    "testnet_order_shape_ready",
    "fixed_testnet_plumbing_notional",
    "signed_testnet_transport_client_configured",
    "signed_testnet_transport_client_not_configured",
)
PT_RT1_5_1_WARM_START_REASON_CODES = (
    "warm_start_evaluation_completed",
    "signal_good_but_runtime_started_after_setup",
    "entry_context_already_true_at_runtime_start",
    "entry_context_already_true_waiting_for_reset",
    "entry_context_reset_observed",
    "fresh_entry_signal_after_runtime_start",
    "warm_start_blocked_late_entry",
)
PT_RT1_5_1_MTM_REASON_CODES = (
    "mtm_source_public_mainnet_mid",
    "mtm_source_latest_closed_candle",
    "mtm_price_unavailable",
    "mtm_unrealized_pnl_updated",
)
RUNTIME_STATE_PATHS = {
    "state": "reports/paper_runtime/pt_rt1_state.json",
    "decisions": "reports/paper_runtime/pt_rt1_decisions.jsonl",
    "trades": "reports/paper_runtime/pt_rt1_trades.jsonl",
    "equity_curves": "reports/paper_runtime/pt_rt1_equity_curves.json",
    "data_health": "reports/paper_runtime/pt_rt1_data_health.json",
    "testnet_probe_audit": "reports/paper_runtime/pt_rt1_testnet_probe_audit.jsonl",
}
SUPPORTED_CANONICAL_SYMBOLS = ("BTC", "ETH", "SOL", "XRP", "DOGE", "HYPE", "BNB", "SUI", "AVAX")
FOUNDER_REQUESTED_SYMBOLS = (
    "TRON",
    "ADA",
    "ZEC",
    "LINK",
    "XMR",
    "TON",
    "LTC",
    "UNI",
    "DOT",
    "ASTER",
    "AAVE",
    "POL",
    "FIL",
    "PEPE",
    "OKB",
)
PT_RT1_DEFERRED_RUNTIME_SYMBOLS = {
    "TRUMP": "runtime_noise_deferred_by_founder",
}
SYMBOL_ALIASES = {
    "TRON": "TRX",
    "PEPE": "kPEPE",
    "SHIB": "kSHIB",
    "KSHIB": "kSHIB",
}
STABLECOIN_SYMBOLS = {"USDT", "USDC", "DAI", "FDUSD", "TUSD", "USDE", "USDS"}
DEFAULT_SCANNER_SOURCES = {
    **{symbol: ("canonical_sv2_supported",) for symbol in SUPPORTED_CANONICAL_SYMBOLS},
    **{symbol: ("founder_requested",) for symbol in FOUNDER_REQUESTED_SYMBOLS},
}
PT_RT1_1A_STRATEGY_LANE_IDS = (
    "money_flow_v1_2_baseline",
    "avoid_low_rolling_range_20",
    "avoid_low_rolling_range_50",
    "mf_orig_stage_filter_only_full_equity",
    "mf_orig_stage2_pullback_reclaim_full_equity",
    "mf_orig_1d_stage2_5_20_crossover_full_equity",
    "mf_orig_1d_stage2_breakout_resistance_full_equity",
    "wildcard_btc_regime_guard",
    "wildcard_multi_timeframe_alignment",
    "wildcard_volatility_expansion_breakout",
)
PT_RT1_1B_RUNTIME_OUTPUT_PREFIX = "reports/paper_runtime/"
PT_RT1_REQUESTED_SCANNER_SYMBOLS = tuple(dict.fromkeys((*SUPPORTED_CANONICAL_SYMBOLS, *FOUNDER_REQUESTED_SYMBOLS)))
ROLLING_RANGE_20_MIN_PCT = Decimal("0.025")
ROLLING_RANGE_50_MIN_PCT = Decimal("0.040")
WILDCARD_STRATEGY_DEFINITIONS = {
    "wildcard_btc_regime_guard": {
        "purpose": "Stop alt entries when BTC 4h/1d market regime is hostile.",
        "methodology": "forward_public_mainnet_paper_observation",
        "rule_summary": (
            "Non-BTC entries require constructive BTC 4h and 1d context; BTC entries use BTC's own 4h/1d context."
        ),
        "reason_codes": (
            "btc_regime_guard_passed",
            "btc_regime_guard_blocked_bearish",
            "btc_regime_context_unavailable",
            "btc_regime_clear_bearish_alignment",
            "btc_regime_macd_histogram_not_constructive",
        ),
    },
    "wildcard_multi_timeframe_alignment": {
        "purpose": "Avoid isolated lower-timeframe entries against higher-timeframe structure.",
        "methodology": "forward_public_mainnet_paper_observation",
        "rule_summary": "15m requires 1h alignment, 1h requires 4h, 4h requires 1d, and 1d uses its own baseline rules.",
        "reason_codes": (
            "multi_timeframe_alignment_passed",
            "multi_timeframe_alignment_blocked",
            "higher_timeframe_context_unavailable",
            "higher_timeframe_bearish_alignment",
            "higher_timeframe_macd_not_constructive",
        ),
    },
    "wildcard_volatility_expansion_breakout": {
        "purpose": "Avoid dead sideways zones but allow re-entry when compression resolves upward.",
        "methodology": "forward_public_mainnet_paper_observation",
        "rule_summary": (
            "Block low rolling range entries unless range expansion and a close above the recent 20-candle high occur "
            "while baseline Money Flow trend alignment remains valid."
        ),
        "reason_codes": (
            "volatility_expansion_breakout_passed",
            "volatility_expansion_blocked_low_range",
            "volatility_expansion_missing_compression_context",
            "volatility_expansion_no_recent_high_breakout",
            "volatility_expansion_baseline_alignment_failed",
        ),
    },
}


class DataHealth(StrEnum):
    HEALTHY = "healthy"
    STALE = "stale"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class LaneRole(StrEnum):
    CONTROL = "control_lane"
    CANDIDATE = "evidence_only_candidate_lane"
    REFERENCE = "mf_orig_evidence_only_reference_lane"
    WILDCARD = "wildcard_expert_observation_lane"


@dataclass(frozen=True)
class StrategyLaneConfig:
    lane_id: str
    strategy_id: str
    role: LaneRole
    label: str
    display_name: str
    strategy_family: str
    rule_summary: str
    initial_equity: Decimal = Decimal("10000")
    allocation_pct: Decimal = Decimal("1")
    fill_model: str = "next_candle_open"
    paper_only: bool = True
    production_approved: bool = False
    live_approved: bool = False
    paper_runtime_approved_as_production: bool = False
    live_trading_approved: bool = False
    reason_codes: tuple[str, ...] = ()


PT_RT1_STRATEGY_LANES: tuple[StrategyLaneConfig, ...] = (
    StrategyLaneConfig(
        lane_id="money_flow_v1_2_baseline",
        strategy_id="money_flow_v1_2_baseline",
        role=LaneRole.CONTROL,
        label="Money Flow v1.2 baseline observation lane",
        display_name="Money Flow v1.2 baseline",
        strategy_family="current_money_flow_v1_2",
        rule_summary="Current production-derived Money Flow v1.2 rules unchanged; control lane only.",
        reason_codes=("production_derived_rules_unchanged", "not_production_approval", "independent_synthetic_paper_ledger"),
    ),
    StrategyLaneConfig(
        lane_id="avoid_low_rolling_range_20",
        strategy_id="avoid_low_rolling_range_20",
        role=LaneRole.CANDIDATE,
        label="avoid_low_rolling_range_20 evidence-only candidate lane",
        display_name="Avoid low rolling range 20",
        strategy_family="sor_ev3_avoid_sideways_low_volatility",
        rule_summary="Paper-only candidate that blocks entries when the 20-candle rolling range is too compressed.",
        reason_codes=("evidence_only_candidate_lane", "not_production_approved", "independent_synthetic_paper_ledger"),
    ),
    StrategyLaneConfig(
        lane_id="avoid_low_rolling_range_50",
        strategy_id="avoid_low_rolling_range_50",
        role=LaneRole.CANDIDATE,
        label="avoid_low_rolling_range_50 evidence-only candidate lane",
        display_name="Avoid low rolling range 50",
        strategy_family="sor_ev3_avoid_sideways_low_volatility",
        rule_summary="Paper-only candidate that blocks entries when the 50-candle rolling range is too compressed.",
        reason_codes=("evidence_only_candidate_lane", "not_production_approved", "independent_synthetic_paper_ledger"),
    ),
    StrategyLaneConfig(
        lane_id="mf_orig_stage_filter_only_full_equity",
        strategy_id="mf_orig_stage_filter_only_full_equity",
        role=LaneRole.REFERENCE,
        label="MF-ORIG stage filter full-equity evidence-only reference lane",
        display_name="MF-ORIG stage filter only full equity",
        strategy_family="mf_orig_evidence_only_reference",
        rule_summary="Current Money Flow-like entries with original-style Stage 2 filter, full-equity comparison sizing.",
        reason_codes=("mf_orig_reference_lane", "full_equity_reference", "not_production_approved", "independent_synthetic_paper_ledger"),
    ),
    StrategyLaneConfig(
        lane_id="mf_orig_stage2_pullback_reclaim_full_equity",
        strategy_id="mf_orig_stage2_pullback_reclaim_full_equity",
        role=LaneRole.REFERENCE,
        label="MF-ORIG Stage 2 pullback reclaim full-equity evidence-only reference lane",
        display_name="MF-ORIG Stage 2 pullback reclaim full equity",
        strategy_family="mf_orig_evidence_only_reference",
        rule_summary="Original Money Flow pullback/reclaim hypothesis, full-equity comparison sizing.",
        reason_codes=("mf_orig_reference_lane", "full_equity_reference", "not_production_approved", "independent_synthetic_paper_ledger"),
    ),
    StrategyLaneConfig(
        lane_id="mf_orig_1d_stage2_5_20_crossover_full_equity",
        strategy_id="mf_orig_1d_stage2_5_20_crossover_full_equity",
        role=LaneRole.REFERENCE,
        label="MF-ORIG 1d Stage 2 5/20 crossover full-equity evidence-only reference lane",
        display_name="MF-ORIG 1D Stage 2 5/20 crossover full equity",
        strategy_family="mf_orig_evidence_only_reference",
        rule_summary="Original Money Flow 5 EMA / 20 SMA Stage 2 crossover hypothesis, full-equity comparison sizing.",
        reason_codes=("mf_orig_reference_lane", "mf_orig_reference_lane_1d_primary", "full_equity_reference", "not_production_approved", "independent_synthetic_paper_ledger"),
    ),
    StrategyLaneConfig(
        lane_id="mf_orig_1d_stage2_breakout_resistance_full_equity",
        strategy_id="mf_orig_1d_stage2_breakout_resistance_full_equity",
        role=LaneRole.REFERENCE,
        label="MF-ORIG Stage 2 breakout resistance full-equity evidence-only reference lane",
        display_name="MF-ORIG 1D Stage 2 breakout resistance full equity",
        strategy_family="mf_orig_evidence_only_reference",
        rule_summary="Original Money Flow resistance-breakout hypothesis, full-equity comparison sizing.",
        reason_codes=("mf_orig_reference_lane", "mf_orig_reference_lane_1d_primary", "full_equity_reference", "not_production_approved", "independent_synthetic_paper_ledger"),
    ),
    StrategyLaneConfig(
        lane_id="wildcard_btc_regime_guard",
        strategy_id="wildcard_btc_regime_guard",
        role=LaneRole.WILDCARD,
        label="Wildcard BTC regime guard observation lane",
        display_name="Wildcard BTC regime guard",
        strategy_family="wildcard_expert_hypothesis",
        rule_summary=WILDCARD_STRATEGY_DEFINITIONS["wildcard_btc_regime_guard"]["rule_summary"],
        reason_codes=(*WILDCARD_STRATEGY_DEFINITIONS["wildcard_btc_regime_guard"]["reason_codes"], "wildcard_observation_only", "not_production_approved", "independent_synthetic_paper_ledger"),
    ),
    StrategyLaneConfig(
        lane_id="wildcard_multi_timeframe_alignment",
        strategy_id="wildcard_multi_timeframe_alignment",
        role=LaneRole.WILDCARD,
        label="Wildcard multi-timeframe alignment observation lane",
        display_name="Wildcard multi-timeframe alignment",
        strategy_family="wildcard_expert_hypothesis",
        rule_summary=WILDCARD_STRATEGY_DEFINITIONS["wildcard_multi_timeframe_alignment"]["rule_summary"],
        reason_codes=(*WILDCARD_STRATEGY_DEFINITIONS["wildcard_multi_timeframe_alignment"]["reason_codes"], "wildcard_observation_only", "not_production_approved", "independent_synthetic_paper_ledger"),
    ),
    StrategyLaneConfig(
        lane_id="wildcard_volatility_expansion_breakout",
        strategy_id="wildcard_volatility_expansion_breakout",
        role=LaneRole.WILDCARD,
        label="Wildcard volatility expansion breakout observation lane",
        display_name="Wildcard volatility expansion breakout",
        strategy_family="wildcard_expert_hypothesis",
        rule_summary=WILDCARD_STRATEGY_DEFINITIONS["wildcard_volatility_expansion_breakout"]["rule_summary"],
        reason_codes=(*WILDCARD_STRATEGY_DEFINITIONS["wildcard_volatility_expansion_breakout"]["reason_codes"], "wildcard_observation_only", "not_production_approved", "independent_synthetic_paper_ledger"),
    ),
)

PT_RT1_6_ACTIVE_STRATEGY_LANES: tuple[StrategyLaneConfig, ...] = tuple(
    lane for lane in PT_RT1_STRATEGY_LANES if lane.lane_id in PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS
)
PT_RT1_6_ARCHIVED_STRATEGY_LANES: tuple[StrategyLaneConfig, ...] = tuple(
    lane for lane in PT_RT1_STRATEGY_LANES if lane.lane_id in PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS
)


def pt_rt1_6_lane_status(lane_id: str) -> str:
    if lane_id in PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS:
        return "active_week2_default"
    if lane_id in PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS:
        return "archived_default_inactive"
    return "not_in_week2_slate"


def pt_rt1_6_lane_testnet_eligible(lane_id: str) -> bool:
    return lane_id == "money_flow_v1_2_baseline"


def strategy_lane_summary_payload(lane: StrategyLaneConfig) -> dict[str, Any]:
    lane_status = pt_rt1_6_lane_status(lane.lane_id)
    active_by_default = lane_status == "active_week2_default"
    archived_by_default = lane_status == "archived_default_inactive"
    reason_codes = list(lane.reason_codes)
    if archived_by_default:
        reason_codes = list(dict.fromkeys([*reason_codes, *PT_RT1_6_ARCHIVE_REASON_CODES]))
    if active_by_default:
        reason_codes = list(dict.fromkeys([*reason_codes, "founder_selected_week2_active", "not_production_eligible"]))
    return {
        **asdict(lane),
        "initial_equity": str(lane.initial_equity),
        "allocation_pct": str(lane.allocation_pct),
        "role": str(lane.role),
        "starting_equity": str(lane.initial_equity),
        "realized_equity": str(lane.initial_equity),
        "unrealized_pnl": "0",
        "total_equity": str(lane.initial_equity),
        "open_positions": 0,
        "closed_trades": 0,
        "drawdown": "0",
        "max_drawdown": "0",
        "current_losing_streak": 0,
        "max_losing_streak": 0,
        "data_health": "pending_runtime_refresh",
        "last_decision_time": None,
        "paper_only": lane.paper_only,
        "production_approved": False,
        "live_approved": False,
        "live_trading_approved": False,
        "paper_runtime_approved_as_production": False,
        "ledger_label": "independent synthetic paper ledger",
        "accounting_label": "not one combined account",
        "week2_default_status": lane_status,
        "active_by_default": active_by_default,
        "archived_by_default": archived_by_default,
        "week2_scoring_eligible": active_by_default,
        "testnet_eligible": pt_rt1_6_lane_testnet_eligible(lane.lane_id),
        "testnet_label": (
            "Baseline-only gated testnet eligible"
            if pt_rt1_6_lane_testnet_eligible(lane.lane_id)
            else "Synthetic-only / no testnet"
        ),
        "pnl_source": "Synthetic Ledger",
        "signal_truth": "Public Mainnet Candles",
        "reason_codes": tuple(reason_codes),
    }


def _dec(value: Any, *, field_name: str = "value") -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name}_not_decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{field_name}_not_finite")
    return result


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc_timestamp(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone_explicit_timestamp_required")
    return parsed.astimezone(UTC)


@dataclass(frozen=True)
class Candle:
    symbol: str
    timeframe: str
    open_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    close_time: datetime | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any], *, symbol: str, timeframe: str) -> "Candle":
        return cls(
            symbol=symbol.upper(),
            timeframe=timeframe,
            open_time=parse_utc_timestamp(payload.get("open_time") or payload.get("open_time_utc") or payload.get("t")),
            close_time=(
                parse_utc_timestamp(payload.get("close_time") or payload.get("close_time_utc"))
                if payload.get("close_time") or payload.get("close_time_utc")
                else None
            ),
            open=_dec(payload.get("open") or payload.get("o"), field_name="open"),
            high=_dec(payload.get("high") or payload.get("h"), field_name="high"),
            low=_dec(payload.get("low") or payload.get("l"), field_name="low"),
            close=_dec(payload.get("close") or payload.get("c"), field_name="close"),
            volume=_dec(payload.get("volume") or payload.get("v") or "0", field_name="volume"),
        )

    def validate(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if self.timeframe not in TIMEFRAME_DURATIONS:
            reasons.append("unsupported_timeframe")
        if min(self.open, self.high, self.low, self.close) <= 0:
            reasons.append("non_positive_ohlc")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close) or self.high < self.low:
            reasons.append("ohlc_high_low_inconsistent")
        if self.volume < 0:
            reasons.append("negative_volume")
        if self.close_time and self.timeframe in TIMEFRAME_DURATIONS and self.close_time != canonical_candle_close(self):
            reasons.append("close_time_not_canonical")
        return tuple(reasons)


def canonical_candle_close(candle: Candle) -> datetime:
    return candle.open_time + TIMEFRAME_DURATIONS[candle.timeframe]


@dataclass(frozen=True)
class CandleGateResult:
    accepted: bool
    canonical_close_time: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class PaperDecisionEvent:
    lane_id: str
    strategy_id: str
    symbol: str
    timeframe: str
    signal_candle_open_time: str | None
    signal_candle_close_time: str | None
    decision_time: str
    candle_closed: bool
    candle_status_reason: str
    action: str
    reason_codes: tuple[str, ...]
    indicator_snapshot: Mapping[str, Any]
    position_before: str
    position_after: str
    equity_before: Decimal
    equity_after: Decimal
    production_artifact_created: bool = False

    def as_json_dict(self) -> dict[str, Any]:
        return {
            "lane_id": self.lane_id,
            "strategy_id": self.strategy_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "signal_candle_open_time": self.signal_candle_open_time,
            "signal_candle_close_time": self.signal_candle_close_time,
            "decision_time": self.decision_time,
            "candle_closed": self.candle_closed,
            "candle_status_reason": self.candle_status_reason,
            "action": self.action,
            "reason_codes": list(self.reason_codes),
            "indicator_snapshot": dict(self.indicator_snapshot),
            "position_before": self.position_before,
            "position_after": self.position_after,
            "equity_before": str(self.equity_before),
            "equity_after": str(self.equity_after),
            "production_artifact_created": self.production_artifact_created,
        }


def evaluate_closed_candle_gate(
    candle: Candle,
    *,
    now: datetime,
    last_processed_close: datetime | None = None,
) -> CandleGateResult:
    reasons = list(candle.validate())
    now_utc = parse_utc_timestamp(now)
    close_time = canonical_candle_close(candle)
    if now_utc < close_time:
        reasons.append("candle_not_closed")
    if last_processed_close is not None:
        last_utc = parse_utc_timestamp(last_processed_close)
        if close_time == last_utc:
            reasons.append("duplicate_candle_ignored")
        elif close_time < last_utc:
            reasons.append("out_of_order_candle")
        elif close_time > last_utc + TIMEFRAME_DURATIONS[candle.timeframe]:
            reasons.append("missing_candle_gap_detected")
    return CandleGateResult(
        accepted=not reasons,
        canonical_close_time=_iso(close_time),
        reason_codes=tuple(reasons),
    )


def _floor_to_timeframe_close(now: datetime, timeframe: str) -> datetime:
    now_utc = parse_utc_timestamp(now)
    if timeframe == "1h":
        return now_utc.replace(minute=0, second=0, microsecond=0)
    if timeframe == "4h":
        return now_utc.replace(hour=(now_utc.hour // 4) * 4, minute=0, second=0, microsecond=0)
    if timeframe == "1d":
        return now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    raise ValueError("scheduler_close_time_unavailable")


def pt_rt1_5_previous_closed_candle_time(now: datetime, timeframe: str) -> datetime:
    """Return the closed candle whose grace-delayed evaluation is due or next due.

    The function is UTC-only and intentionally supports only active PT-RT1.5
    strategy timeframes. 15m remains display/legacy only for Week 1.
    """

    if timeframe not in PT_RT1_5_ACTIVE_TIMEFRAMES:
        raise ValueError("timeframe_paused_no_signal_evaluation")
    close_time = _floor_to_timeframe_close(now, timeframe)
    grace = timedelta(seconds=PT_RT1_5_CANDLE_CLOSE_GRACE_SECONDS[timeframe])
    if parse_utc_timestamp(now) < close_time + grace:
        close_time -= TIMEFRAME_DURATIONS[timeframe]
    return close_time


def pt_rt1_5_next_evaluation_time(now: datetime, timeframe: str) -> datetime:
    if timeframe not in PT_RT1_5_ACTIVE_TIMEFRAMES:
        raise ValueError("timeframe_paused_no_signal_evaluation")
    now_utc = parse_utc_timestamp(now)
    close_time = _floor_to_timeframe_close(now_utc, timeframe)
    candidate = close_time + timedelta(seconds=PT_RT1_5_CANDLE_CLOSE_GRACE_SECONDS[timeframe])
    if now_utc < candidate:
        return candidate
    return close_time + TIMEFRAME_DURATIONS[timeframe] + timedelta(
        seconds=PT_RT1_5_CANDLE_CLOSE_GRACE_SECONDS[timeframe]
    )


def build_pt_rt1_5_scheduler_status(
    *,
    now: datetime,
    last_evaluated_closed_candle_by_timeframe: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    now_utc = parse_utc_timestamp(now)
    last_evaluated = last_evaluated_closed_candle_by_timeframe or {}
    timeframes: dict[str, dict[str, Any]] = {}
    for timeframe in PT_RT1_5_ACTIVE_TIMEFRAMES:
        try:
            closed_time = pt_rt1_5_previous_closed_candle_time(now_utc, timeframe)
            next_eval = pt_rt1_5_next_evaluation_time(now_utc, timeframe)
        except ValueError as exc:
            timeframes[timeframe] = {
                "status": "blocked",
                "reason_codes": [str(exc)],
                "is_due": False,
            }
            continue
        closed_iso = _iso(closed_time)
        already_done = str(last_evaluated.get(timeframe) or "") == closed_iso
        is_due = now_utc >= closed_time + timedelta(seconds=PT_RT1_5_CANDLE_CLOSE_GRACE_SECONDS[timeframe])
        if already_done:
            reason_codes = ["duplicate_candle_signal_ignored", "market_refresh_only_no_signal_evaluation"]
        elif is_due:
            reason_codes = ["signal_evaluation_started_after_closed_candle"]
        else:
            reason_codes = ["signal_evaluation_waiting_for_candle_close", "market_refresh_only_no_signal_evaluation"]
        timeframes[timeframe] = {
            "timeframe": timeframe,
            "closed_candle_time": closed_iso,
            "next_evaluation_time": _iso(next_eval),
            "last_evaluated_closed_candle_time": last_evaluated.get(timeframe),
            "grace_delay_seconds": PT_RT1_5_CANDLE_CLOSE_GRACE_SECONDS[timeframe],
            "retry_policy": dict(PT_RT1_5_CLOSED_CANDLE_RETRY_POLICY[timeframe]),
            "is_due": bool(is_due and not already_done),
            "reason_codes": reason_codes,
        }
    return {
        "mode": "candle_close_only",
        "market_refresh_mode": "continuous_dashboard_refresh",
        "active_timeframes": list(PT_RT1_5_ACTIVE_TIMEFRAMES),
        "disabled_timeframes": list(PT_RT1_5_DISABLED_TIMEFRAMES),
        "now_utc": _iso(now_utc),
        "timeframes": timeframes,
        "reason_codes": list(PT_RT1_5_SCHEDULER_REASON_CODES),
    }


@dataclass(frozen=True)
class PT_RT15TestnetOrderCandidate:
    lane_id: str = "money_flow_v1_2_baseline"
    strategy_id: str = "money_flow_v1_2_baseline"
    action: str = "paper_opened"
    symbol: str = "ETH"
    timeframe: str = "1h"
    signal_candle_close_time: str = "2026-05-17T13:00:00Z"
    scheduled_closed_candle_evaluation: bool = True
    fresh_signal_after_runtime_start: bool = False
    warm_start_signal_blocked: bool = False
    duplicate_order_key_seen: bool = False
    scanner_signal_eligible: bool = True
    scanner_symbol_blocked: bool = False
    unit_semantics_deferred: bool = False
    precision_ready: bool = True
    order_transport_enabled: bool = False
    kill_switch: bool = True
    approval_text: str = ""
    base_url: str = PT_RT1_TESTNET_INFO_URL
    asset_id: int | None = 1
    sz_decimals: int | None = 4
    testnet_metadata_resolved: bool = True
    price: Decimal = Decimal("3000")
    synthetic_signal_notional: Decimal = Decimal("10000")
    fixed_notional: Decimal = PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC
    daily_order_count: int = 0
    daily_cap: int = PT_RT1_5_TESTNET_DAILY_ORDER_CAP_DEFAULT
    per_symbol_daily_count: int = 0
    per_symbol_daily_cap: int = PT_RT1_5_TESTNET_PER_SYMBOL_DAILY_CAP_DEFAULT
    unknown_or_open_testnet_state: bool = False
    account_mode: str = "main"
    account_address: str | None = None
    vault_address: str | None = None
    selected_equity_source: str = "not_checked_runtime_transport_gate"
    perp_margin_account_value: Decimal | None = None
    spot_usdc_total: Decimal | None = None
    spot_usdc_hold: Decimal | None = None
    unified_available_usdc: Decimal | None = None


@dataclass(frozen=True)
class PT_RT15TestnetOrderEligibility:
    eligible: bool
    reason_codes: tuple[str, ...]
    order_shape: dict[str, Any] | None
    lifecycle_row: dict[str, Any]


class PT_RT15BaselineTestnetOrderPolicy:
    """PT-RT1.5 baseline-only Hyperliquid testnet transport preflight.

    This policy creates a testnet-only order shape/lifecycle row. It does not
    submit signed requests and it never updates synthetic strategy PnL.
    """

    def evaluate(self, candidate: PT_RT15TestnetOrderCandidate) -> PT_RT15TestnetOrderEligibility:
        reasons: list[str] = []
        if not candidate.order_transport_enabled:
            reasons.append("testnet_order_transport_disabled")
        if candidate.kill_switch:
            reasons.append("testnet_order_transport_kill_switch_active")
        if candidate.approval_text not in {
            PT_RT1_5_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
            PT_RT1_5_1_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
            PT_RT1_5_2_EXACT_TESTNET_TRANSPORT_SMOKE_APPROVAL,
            PT_RT1_5_3_EXACT_TESTNET_SIZE_HOTFIX_SMOKE_APPROVAL,
            PT_RT1_6_3_EXACT_XRP_TESTNET_METADATA_SMOKE_APPROVAL,
        }:
            reasons.append("pt_rt1_5_exact_approval_required")
        base_url = candidate.base_url.rstrip("/")
        if base_url not in {PT_RT1_TESTNET_INFO_URL, PT_RT1_TESTNET_API_URL}:
            reasons.append("testnet_endpoint_required")
        if base_url in {PT_RT1_MAINNET_INFO_URL, PT_RT1_MAINNET_API_URL}:
            reasons.append("live_endpoint_forbidden")
        if candidate.lane_id != "money_flow_v1_2_baseline" or candidate.strategy_id != "money_flow_v1_2_baseline":
            reasons.append("testnet_order_blocked_non_baseline_lane")
        if candidate.action != "paper_opened":
            reasons.append("testnet_order_blocked_non_open_action")
        if candidate.timeframe not in PT_RT1_5_ACTIVE_TIMEFRAMES:
            reasons.append("testnet_order_blocked_inactive_timeframe")
        if not candidate.scheduled_closed_candle_evaluation:
            reasons.append("testnet_order_requires_scheduled_closed_candle_evaluation")
        if not candidate.fresh_signal_after_runtime_start or candidate.warm_start_signal_blocked:
            reasons.append("testnet_order_requires_fresh_post_start_signal")
        if candidate.duplicate_order_key_seen:
            reasons.append("testnet_duplicate_order_blocked")
        if not candidate.scanner_signal_eligible or candidate.scanner_symbol_blocked:
            reasons.append("testnet_order_symbol_blocked")
        if candidate.unit_semantics_deferred:
            reasons.append("testnet_order_unit_semantics_deferred")
        if not candidate.precision_ready or candidate.asset_id is None or candidate.sz_decimals is None:
            reasons.append("testnet_order_precision_missing")
        if not candidate.testnet_metadata_resolved:
            reasons.append("testnet_metadata_unavailable")
        if candidate.fixed_notional != PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC:
            reasons.append("testnet_order_notional_must_be_25usdc")
        if candidate.daily_order_count >= candidate.daily_cap:
            reasons.append("testnet_daily_order_cap_exceeded")
        if candidate.per_symbol_daily_count >= candidate.per_symbol_daily_cap:
            reasons.append("testnet_per_symbol_daily_cap_exceeded")
        if candidate.unknown_or_open_testnet_state:
            reasons.append("unknown_testnet_state_blocks_new_orders")
        account_mode = candidate.account_mode.lower()
        if account_mode == "main" and candidate.vault_address:
            reasons.append("vault_address_forbidden_for_main_user")
        if account_mode in {"subaccount", "vault"} and not candidate.vault_address:
            reasons.append("vault_address_required_for_subaccount_or_vault")
        if candidate.price <= 0:
            reasons.append("testnet_order_precision_missing")

        precision_details = self._precision_details(candidate)
        if precision_details["invalid_size"] and not precision_details["precision_unavailable"]:
            reasons.append("testnet_order_invalid_size_preflight")

        eligible = not reasons
        order_shape = self._order_shape(candidate, precision_details=precision_details) if eligible else None
        lifecycle_status = "preflight_passed" if eligible else "blocked"
        lifecycle_row = {
            "lane": "testnet_order_transport",
            "environment": "hyperliquid_testnet_only",
            "trigger_lane": candidate.lane_id,
            "strategy_id": candidate.strategy_id,
            "symbol": candidate.symbol,
            "timeframe": candidate.timeframe,
            "signal_candle_close_time": candidate.signal_candle_close_time,
            "fresh_signal_after_runtime_start": candidate.fresh_signal_after_runtime_start,
            "warm_start_signal_blocked": candidate.warm_start_signal_blocked,
            "trigger_reason": (
                "fresh_entry_signal_after_runtime_start"
                if candidate.fresh_signal_after_runtime_start and not candidate.warm_start_signal_blocked
                else "warm_start_or_late_signal_blocked"
            ),
            "status": lifecycle_status,
            "side": "buy",
            "notional": str(candidate.fixed_notional),
            "synthetic_signal_notional": str(candidate.synthetic_signal_notional),
            "testnet_fixed_notional": str(candidate.fixed_notional),
            "sizing_source": "fixed_testnet_plumbing_notional",
            "asset_id": candidate.asset_id,
            "szDecimals": candidate.sz_decimals,
            "max_price_decimals": precision_details["max_price_decimals"],
            "limit_price": str(candidate.price),
            "formatted_limit_price": precision_details["formatted_limit_price"],
            "raw_quantity": precision_details["raw_quantity"],
            "formatted_quantity": precision_details["formatted_quantity"],
            "quantity": precision_details["formatted_quantity"],
            "estimated_testnet_notional": precision_details["estimated_testnet_notional"],
            "price_format_reason": precision_details["price_format_reason"],
            "size_format_reason": precision_details["size_format_reason"],
            "venue_response": None,
            "cancel_status": "cancel_reconcile_required_after_submit" if eligible else "not_submitted",
            "reconcile_status": "required_after_submit" if eligible else "not_submitted",
            "reason_codes": reasons if reasons else ["testnet_order_shape_ready", "fixed_testnet_plumbing_notional"],
            "selected_equity_source": candidate.selected_equity_source,
            "perp_margin_account_value": str(candidate.perp_margin_account_value) if candidate.perp_margin_account_value is not None else None,
            "spot_usdc_total": str(candidate.spot_usdc_total) if candidate.spot_usdc_total is not None else None,
            "spot_usdc_hold": str(candidate.spot_usdc_hold) if candidate.spot_usdc_hold is not None else None,
            "unified_available_usdc": str(candidate.unified_available_usdc) if candidate.unified_available_usdc is not None else None,
            "testnet_fills_update_strategy_pnl": False,
            "strategy_pnl_updated": False,
            "signed_order_endpoint_called": False,
            "order_endpoint_called": False,
            "order_shape": order_shape,
        }
        return PT_RT15TestnetOrderEligibility(
            eligible=eligible,
            reason_codes=tuple(dict.fromkeys(reasons)),
            order_shape=order_shape,
            lifecycle_row=lifecycle_row,
        )

    def _precision_details(self, candidate: PT_RT15TestnetOrderCandidate) -> dict[str, Any]:
        raw_quantity = candidate.fixed_notional / candidate.price if candidate.price > 0 else Decimal("0")
        details: dict[str, Any] = {
            "raw_quantity": str(raw_quantity),
            "formatted_quantity": "0",
            "estimated_testnet_notional": "0",
            "formatted_limit_price": "0",
            "max_price_decimals": None,
            "price_format_reason": "price_precision_unavailable",
            "size_format_reason": "size_precision_unavailable",
            "invalid_size": True,
            "precision_unavailable": True,
        }
        if candidate.asset_id is None or candidate.sz_decimals is None or candidate.price <= 0:
            return details
        formatter = HyperliquidPrecisionFormatter(
            asset_id=int(candidate.asset_id or 0),
            symbol=candidate.symbol,
            sz_decimals=int(candidate.sz_decimals or 0),
        )
        formatted_price = formatter.format_price_down(candidate.price)
        formatted_size = formatter.format_size_down(raw_quantity)
        estimated_notional = formatted_size.formatted_value * formatted_price.formatted_value
        min_acceptable_notional = candidate.fixed_notional * Decimal("0.95")
        invalid_size = (
            formatted_size.formatted_value <= 0
            or estimated_notional <= 0
            or estimated_notional < min_acceptable_notional
        )
        return {
            "raw_quantity": str(raw_quantity),
            "formatted_quantity": formatted_size.wire_value,
            "estimated_testnet_notional": str(estimated_notional),
            "formatted_limit_price": formatted_price.wire_value,
            "max_price_decimals": formatter.max_price_decimals,
            "price_format_reason": formatted_price.reason,
            "size_format_reason": formatted_size.reason,
            "invalid_size": invalid_size,
            "precision_unavailable": False,
        }

    def _order_shape(self, candidate: PT_RT15TestnetOrderCandidate, *, precision_details: dict[str, Any]) -> dict[str, Any]:
        price = str(precision_details["formatted_limit_price"])
        size = str(precision_details["formatted_quantity"])
        action: dict[str, Any] = {
            "type": "order",
            "orders": [
                {
                    "a": candidate.asset_id,
                    "b": True,
                    "p": price,
                    "s": size,
                    "r": False,
                    "t": {"limit": {"tif": "Alo"}},
                }
            ],
            "grouping": "na",
        }
        order: dict[str, Any] = {
            "venue": "Hyperliquid",
            "environment": "testnet",
            "base_url": PT_RT1_TESTNET_INFO_URL,
            "asset_id": candidate.asset_id,
            "symbol": candidate.symbol,
            "szDecimals": candidate.sz_decimals,
            "action": action,
            "notional_usdc": str(candidate.fixed_notional),
            "testnet_fixed_notional": str(candidate.fixed_notional),
            "sizing_source": "fixed_testnet_plumbing_notional",
            "synthetic_signal_notional": str(candidate.synthetic_signal_notional),
            "raw_quantity": precision_details["raw_quantity"],
            "formatted_quantity": precision_details["formatted_quantity"],
            "estimated_testnet_notional": precision_details["estimated_testnet_notional"],
            "limit_price": price,
            "max_price_decimals": precision_details["max_price_decimals"],
            "price_format_reason": precision_details["price_format_reason"],
            "size_format_reason": precision_details["size_format_reason"],
            "testnet_price_is_strategy_truth": False,
            "public_mainnet_candles_are_strategy_truth": True,
            "testnet_fills_update_strategy_pnl": False,
        }
        if candidate.account_mode.lower() in {"subaccount", "vault"} and candidate.vault_address:
            order["vaultAddress"] = candidate.vault_address
        return order


@dataclass(frozen=True)
class IndicatorSnapshot:
    ema5: Decimal | None
    ema10: Decimal | None
    sma20: Decimal | None
    rsi14: Decimal | None
    macd: Decimal | None
    macd_signal: Decimal | None
    macd_histogram: Decimal | None
    atr14: Decimal | None
    sma50: Decimal | None
    sma200: Decimal | None
    rolling_range_20: Decimal | None
    rolling_range_50: Decimal | None
    reason_codes: tuple[str, ...]


def _sma(values: Sequence[Decimal], period: int) -> Decimal | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / Decimal(period)


def _ema(values: Sequence[Decimal], period: int) -> Decimal | None:
    if len(values) < period:
        return None
    multiplier = Decimal("2") / Decimal(period + 1)
    ema = sum(values[:period]) / Decimal(period)
    for value in values[period:]:
        ema = (value - ema) * multiplier + ema
    return ema


def _rsi(values: Sequence[Decimal], period: int = 14) -> Decimal | None:
    if len(values) <= period:
        return None
    gains: list[Decimal] = []
    losses: list[Decimal] = []
    for previous, current in zip(values[-(period + 1) : -1], values[-period:]):
        change = current - previous
        gains.append(max(change, Decimal("0")))
        losses.append(abs(min(change, Decimal("0"))))
    average_gain = sum(gains) / Decimal(period)
    average_loss = sum(losses) / Decimal(period)
    if average_loss == 0:
        return Decimal("100")
    rs = average_gain / average_loss
    return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))


def _atr(candles: Sequence[Candle], period: int = 14) -> Decimal | None:
    if len(candles) <= period:
        return None
    true_ranges: list[Decimal] = []
    for previous, current in zip(candles[-(period + 1) : -1], candles[-period:]):
        true_ranges.append(
            max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close),
            )
        )
    return sum(true_ranges) / Decimal(period)


def _macd(values: Sequence[Decimal]) -> tuple[Decimal | None, Decimal | None, Decimal | None]:
    if len(values) < 35:
        return None, None, None
    macd_values: list[Decimal] = []
    for index in range(26, len(values) + 1):
        window = values[:index]
        ema12 = _ema(window, 12)
        ema26 = _ema(window, 26)
        if ema12 is not None and ema26 is not None:
            macd_values.append(ema12 - ema26)
    signal = _ema(macd_values, 9)
    macd_value = macd_values[-1] if macd_values else None
    histogram = macd_value - signal if macd_value is not None and signal is not None else None
    return macd_value, signal, histogram


def _rolling_range(candles: Sequence[Candle], period: int) -> Decimal | None:
    if len(candles) < period:
        return None
    window = candles[-period:]
    low = min(c.low for c in window)
    high = max(c.high for c in window)
    close = window[-1].close
    if close <= 0:
        return None
    return (high - low) / close


def compute_indicator_snapshot(candles: Sequence[Candle]) -> IndicatorSnapshot:
    close_values = [c.close for c in candles]
    ema5 = _ema(close_values, 5)
    ema10 = _ema(close_values, 10)
    sma20 = _sma(close_values, 20)
    macd, macd_signal, macd_histogram = _macd(close_values)
    snapshot = IndicatorSnapshot(
        ema5=ema5,
        ema10=ema10,
        sma20=sma20,
        rsi14=_rsi(close_values, 14),
        macd=macd,
        macd_signal=macd_signal,
        macd_histogram=macd_histogram,
        atr14=_atr(candles, 14),
        sma50=_sma(close_values, 50),
        sma200=_sma(close_values, 200),
        rolling_range_20=_rolling_range(candles, 20),
        rolling_range_50=_rolling_range(candles, 50),
        reason_codes=(),
    )
    reasons = indicator_missing_reason_codes(snapshot)
    return IndicatorSnapshot(**{**asdict(snapshot), "reason_codes": reasons})


def indicator_missing_reason_codes(snapshot: IndicatorSnapshot) -> tuple[str, ...]:
    field_reasons = {
        "ema5": "missing_ema5",
        "ema10": "missing_ema10",
        "sma20": "missing_sma20",
        "rsi14": "missing_rsi",
        "macd": "missing_macd",
        "macd_signal": "missing_macd_signal",
        "macd_histogram": "missing_macd_histogram",
    }
    reasons = [reason for field_name, reason in field_reasons.items() if getattr(snapshot, field_name) is None]
    for field_name in field_reasons:
        value = getattr(snapshot, field_name)
        if value is not None and (not value.is_finite() or not isfinite(float(value))):
            reasons.append("missing_indicator_field")
            reasons.append(field_reasons[field_name])
    if reasons:
        reasons.insert(0, "missing_indicator_field")
        if any(reason.startswith("missing_") for reason in reasons):
            reasons.append("insufficient_history")
    return tuple(dict.fromkeys(reasons))


def _indicator_snapshot_json(snapshot: IndicatorSnapshot) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field_name, value in asdict(snapshot).items():
        if isinstance(value, Decimal):
            payload[field_name] = str(value)
        elif isinstance(value, tuple):
            payload[field_name] = list(value)
        else:
            payload[field_name] = value
    return payload


def _baseline_alignment_reasons(candle: Candle, snapshot: IndicatorSnapshot) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if snapshot.ema5 is None or snapshot.ema10 is None or snapshot.sma20 is None:
        reasons.append("baseline_alignment_indicator_unavailable")
        return False, tuple(reasons)
    if not (snapshot.ema5 > snapshot.ema10 > snapshot.sma20):
        reasons.append("baseline_alignment_failed")
    if candle.close < snapshot.sma20:
        reasons.append("price_below_sma20")
    if snapshot.macd_histogram is None:
        reasons.append("missing_macd_histogram")
    elif snapshot.macd_histogram < 0:
        reasons.append("macd_histogram_not_constructive")
    if snapshot.rsi14 is None:
        reasons.append("missing_rsi")
    elif snapshot.rsi14 >= Decimal("80"):
        reasons.append("rsi_overbought_for_paper_entry")
    return not reasons, tuple(reasons)


def evaluate_paper_decision(
    *,
    lane: StrategyLaneConfig,
    symbol: str,
    timeframe: str,
    candles: Sequence[Candle],
    now: datetime,
    data_health: DataHealth = DataHealth.HEALTHY,
    last_processed_close: datetime | None = None,
    position_open: bool = False,
    equity_before: Decimal | None = None,
    btc_regime_constructive: bool | None = None,
    higher_timeframe_constructive: bool | None = None,
) -> PaperDecisionEvent:
    decision_time = _iso(parse_utc_timestamp(now))
    equity = equity_before or lane.initial_equity
    position_before = "open" if position_open else "flat"
    if data_health != DataHealth.HEALTHY:
        return PaperDecisionEvent(
            lane_id=lane.lane_id,
            strategy_id=lane.strategy_id,
            symbol=symbol.upper(),
            timeframe=timeframe,
            signal_candle_open_time=None,
            signal_candle_close_time=None,
            decision_time=decision_time,
            candle_closed=False,
            candle_status_reason="public_market_data_unavailable",
            action="data_unavailable",
            reason_codes=("public_market_data_unavailable", f"data_health_{data_health.value}"),
            indicator_snapshot={},
            position_before=position_before,
            position_after=position_before,
            equity_before=equity,
            equity_after=equity,
        )
    if not candles:
        return PaperDecisionEvent(
            lane_id=lane.lane_id,
            strategy_id=lane.strategy_id,
            symbol=symbol.upper(),
            timeframe=timeframe,
            signal_candle_open_time=None,
            signal_candle_close_time=None,
            decision_time=decision_time,
            candle_closed=False,
            candle_status_reason="public_mainnet_candles_unavailable",
            action="data_unavailable",
            reason_codes=("public_mainnet_candles_unavailable", "insufficient_history"),
            indicator_snapshot={},
            position_before=position_before,
            position_after=position_before,
            equity_before=equity,
            equity_after=equity,
        )

    candle = candles[-1]
    gate = evaluate_closed_candle_gate(candle, now=now, last_processed_close=last_processed_close)
    if not gate.accepted:
        return PaperDecisionEvent(
            lane_id=lane.lane_id,
            strategy_id=lane.strategy_id,
            symbol=symbol.upper(),
            timeframe=timeframe,
            signal_candle_open_time=_iso(candle.open_time),
            signal_candle_close_time=gate.canonical_close_time,
            decision_time=decision_time,
            candle_closed=False,
            candle_status_reason=gate.reason_codes[0] if gate.reason_codes else "candle_not_closed",
            action="data_unavailable" if "candle_not_closed" not in gate.reason_codes else "no_trade",
            reason_codes=gate.reason_codes,
            indicator_snapshot={},
            position_before=position_before,
            position_after=position_before,
            equity_before=equity,
            equity_after=equity,
        )

    snapshot = compute_indicator_snapshot(candles)
    indicator_payload = _indicator_snapshot_json(snapshot)
    if snapshot.reason_codes:
        return PaperDecisionEvent(
            lane_id=lane.lane_id,
            strategy_id=lane.strategy_id,
            symbol=symbol.upper(),
            timeframe=timeframe,
            signal_candle_open_time=_iso(candle.open_time),
            signal_candle_close_time=gate.canonical_close_time,
            decision_time=decision_time,
            candle_closed=True,
            candle_status_reason="closed_candle_ready",
            action="data_unavailable",
            reason_codes=tuple(snapshot.reason_codes),
            indicator_snapshot=indicator_payload,
            position_before=position_before,
            position_after=position_before,
            equity_before=equity,
            equity_after=equity,
        )

    baseline_ok, baseline_reasons = _baseline_alignment_reasons(candle, snapshot)
    action = "paper_opened" if baseline_ok and not position_open else "paper_hold"
    position_after = "open" if position_open or action == "paper_opened" else "flat"
    reasons: list[str] = ["public_mainnet_data_connected", "closed_candle_ready"]

    if position_open and not baseline_ok:
        action = "paper_closed"
        position_after = "flat"
        reasons.extend(("baseline_exit_alignment_failed", *baseline_reasons))
    elif not baseline_ok:
        action = "no_trade"
        reasons.extend(baseline_reasons)
    else:
        reasons.append("baseline_alignment_passed")

    if lane.strategy_id == "avoid_low_rolling_range_20":
        if snapshot.rolling_range_20 is None:
            action = "data_unavailable"
            position_after = position_before
            reasons.append("volatility_expansion_missing_compression_context")
        elif snapshot.rolling_range_20 < ROLLING_RANGE_20_MIN_PCT and action == "paper_opened":
            action = "blocked_by_candidate_filter"
            position_after = "flat"
            reasons.extend(("blocked_low_rolling_range", "avoid_low_rolling_range_20"))
    elif lane.strategy_id == "avoid_low_rolling_range_50":
        if snapshot.rolling_range_50 is None:
            action = "data_unavailable"
            position_after = position_before
            reasons.append("volatility_expansion_missing_compression_context")
        elif snapshot.rolling_range_50 < ROLLING_RANGE_50_MIN_PCT and action == "paper_opened":
            action = "blocked_by_candidate_filter"
            position_after = "flat"
            reasons.extend(("blocked_low_rolling_range", "avoid_low_rolling_range_50"))
    elif lane.strategy_id.startswith("mf_orig_"):
        if snapshot.ema5 is not None and snapshot.sma20 is not None and candle.close > snapshot.sma20 and snapshot.ema5 > snapshot.sma20:
            reasons.append("mf_orig_stage2_context_observed")
        else:
            action = "no_trade"
            position_after = position_before
            reasons.append("mf_orig_stage2_context_not_confirmed")
    elif lane.strategy_id == "wildcard_btc_regime_guard":
        if btc_regime_constructive is None:
            action = "blocked_by_candidate_filter"
            position_after = position_before
            reasons.append("btc_regime_context_unavailable")
        elif btc_regime_constructive:
            reasons.append("btc_regime_guard_passed")
        else:
            action = "blocked_by_candidate_filter"
            position_after = position_before
            reasons.extend(("btc_regime_guard_blocked_bearish", "btc_regime_clear_bearish_alignment"))
    elif lane.strategy_id == "wildcard_multi_timeframe_alignment":
        if higher_timeframe_constructive is None:
            action = "blocked_by_candidate_filter"
            position_after = position_before
            reasons.append("higher_timeframe_context_unavailable")
        elif higher_timeframe_constructive:
            reasons.append("multi_timeframe_alignment_passed")
        else:
            action = "blocked_by_candidate_filter"
            position_after = position_before
            reasons.extend(("multi_timeframe_alignment_blocked", "higher_timeframe_bearish_alignment"))
    elif lane.strategy_id == "wildcard_volatility_expansion_breakout":
        recent_high: Decimal | None = None
        if snapshot.rolling_range_20 is None:
            action = "data_unavailable"
            position_after = position_before
            reasons.append("volatility_expansion_missing_compression_context")
        elif snapshot.rolling_range_20 < ROLLING_RANGE_20_MIN_PCT:
            action = "blocked_by_candidate_filter"
            position_after = position_before
            reasons.append("volatility_expansion_blocked_low_range")
        else:
            prior_window = candles[-21:-1] if len(candles) >= 21 else candles[:-1]
            if not prior_window:
                action = "data_unavailable"
                position_after = position_before
                reasons.append("volatility_expansion_missing_compression_context")
                recent_high = None
            else:
                recent_high = max(c.high for c in prior_window)
        if recent_high is not None:
            if candle.close <= recent_high:
                action = "blocked_by_candidate_filter"
                position_after = position_before
                reasons.append("volatility_expansion_no_recent_high_breakout")
            elif not baseline_ok:
                action = "blocked_by_candidate_filter"
                position_after = position_before
                reasons.append("volatility_expansion_baseline_alignment_failed")
            else:
                reasons.append("volatility_expansion_breakout_passed")

    return PaperDecisionEvent(
        lane_id=lane.lane_id,
        strategy_id=lane.strategy_id,
        symbol=symbol.upper(),
        timeframe=timeframe,
        signal_candle_open_time=_iso(candle.open_time),
        signal_candle_close_time=gate.canonical_close_time,
        decision_time=decision_time,
        candle_closed=True,
        candle_status_reason="closed_candle_ready",
        action=action,
        reason_codes=tuple(dict.fromkeys(reasons)),
        indicator_snapshot=indicator_payload,
        position_before=position_before,
        position_after=position_after,
        equity_before=equity,
        equity_after=equity,
    )


@dataclass(frozen=True)
class StrategyTruthPayloadValidation:
    allowed: bool
    endpoint: str
    info_type: str | None
    reason_codes: tuple[str, ...]


def validate_strategy_truth_payload(*, endpoint: str, payload: Mapping[str, Any], headers: Mapping[str, str] | None = None) -> StrategyTruthPayloadValidation:
    info_type = str(payload.get("type", "")) or None
    reasons: list[str] = []
    if endpoint != PT_RT1_MAINNET_INFO_URL:
        reasons.append("strategy_truth_requires_public_mainnet_info_endpoint")
    if info_type not in ALLOWED_STRATEGY_TRUTH_INFO_TYPES:
        reasons.append("strategy_truth_info_type_not_allowed")
    if info_type in FORBIDDEN_STRATEGY_TRUTH_INFO_TYPES:
        reasons.append("private_or_account_state_forbidden_for_strategy_truth")
    if any(key.lower() in {"authorization", "api-key", "x-api-key"} for key in (headers or {})):
        reasons.append("strategy_truth_uses_no_api_keys")
    return StrategyTruthPayloadValidation(
        allowed=not reasons,
        endpoint=endpoint,
        info_type=info_type,
        reason_codes=tuple(reasons),
    )


@dataclass(frozen=True)
class ScannerUniverseRow:
    requested_symbol: str
    resolved_venue_symbol: str | None
    canonical_symbol: str | None
    asset_id: int | None
    szDecimals: int | None
    isDelisted: bool | None
    public_mid: str | None
    sources: tuple[str, ...]
    source: str
    precision_status: str
    precision_ready: bool
    supported_by_venue: bool
    data_health: DataHealth
    scanner_eligible: bool
    blocked: bool
    reason_codes: tuple[str, ...]


def resolve_top20_universe(
    requested_symbols: Sequence[str],
    *,
    hyperliquid_meta: Sequence[Mapping[str, Any]],
    mids: Mapping[str, Any] | None = None,
    symbol_sources: Mapping[str, Sequence[str]] | None = None,
) -> tuple[ScannerUniverseRow, ...]:
    meta_by_symbol = {str(asset.get("name", "")).upper(): (index, asset) for index, asset in enumerate(hyperliquid_meta)}
    mids = {str(key).upper(): value for key, value in (mids or {}).items()}
    symbol_sources = {str(key).upper(): tuple(value) for key, value in (symbol_sources or {}).items()}
    merged_symbols: list[str] = []
    merged_sources: dict[str, set[str]] = {}
    for requested in requested_symbols:
        symbol = requested.upper()
        if symbol not in merged_sources:
            merged_symbols.append(symbol)
            merged_sources[symbol] = set()
        merged_sources[symbol].update(symbol_sources.get(symbol, ("top20_volume",)))
    rows: list[ScannerUniverseRow] = []
    for symbol in merged_symbols:
        reasons: list[str] = []
        if symbol in STABLECOIN_SYMBOLS:
            reasons.append("stablecoin_excluded")
        venue_symbol = SYMBOL_ALIASES.get(symbol, symbol)
        canonical_symbol = "TRX" if symbol == "TRON" else venue_symbol
        if symbol in {"SHIB", "KSHIB"}:
            reasons.extend(["unit_semantics_deferred", "venue_symbol_unit_semantics_deferred"])
        if symbol in {"PEPE", "KPEPE"}:
            reasons.extend(["unit_semantics_deferred", "pepe_kpepe_unit_semantics_deferred"])
        asset_tuple = meta_by_symbol.get(str(venue_symbol).upper())
        asset_id: int | None = None
        sz_decimals: int | None = None
        is_delisted: bool | None = None
        if asset_tuple is None:
            if symbol == "OKB":
                reasons.append("okb_support_not_confirmed")
            elif symbol == "POL" and (
                (matic_tuple := meta_by_symbol.get("MATIC")) is not None
                and bool(matic_tuple[1].get("isDelisted"))
            ):
                reasons.append("pol_matic_delisted_mapping_blocked")
            else:
                reasons.append("unsupported_by_hyperliquid")
        else:
            asset_id, asset = asset_tuple
            is_delisted = bool(asset.get("isDelisted", False))
            if is_delisted:
                reasons.append("delisted_symbol")
            try:
                sz_decimals = int(asset["szDecimals"])
            except (KeyError, TypeError, ValueError):
                reasons.append("precision_missing")
        mid_value = mids.get(str(venue_symbol).upper())
        mid_warning = False
        if mid_value is None:
            mid_warning = True
            reasons.extend(
                [
                    "mid_missing_or_nonpositive",
                    "public_mid_missing_or_nonpositive",
                    "mid_stale_or_thin_tick",
                    "mid_health_warning_non_blocking",
                ]
            )
        else:
            try:
                if _dec(mid_value, field_name="mid_price") <= 0:
                    mid_warning = True
                    reasons.extend(
                        [
                            "mid_missing_or_nonpositive",
                            "public_mid_missing_or_nonpositive",
                            "mid_stale_or_thin_tick",
                            "mid_health_warning_non_blocking",
                        ]
                    )
            except ValueError:
                mid_warning = True
                reasons.extend(
                    [
                        "mid_missing_or_nonpositive",
                        "public_mid_missing_or_nonpositive",
                        "mid_stale_or_thin_tick",
                        "mid_health_warning_non_blocking",
                    ]
                )
        if asset_tuple is not None and "delisted_symbol" not in reasons:
            reasons.append("symbol_supported")
        eligible = (
            asset_tuple is not None
            and sz_decimals is not None
            and not is_delisted
            and "stablecoin_excluded" not in reasons
            and "unit_semantics_deferred" not in reasons
            and "symbol_identity_ambiguous" not in reasons
        )
        precision_ready = sz_decimals is not None
        blocked = not eligible
        rows.append(
            ScannerUniverseRow(
                requested_symbol=symbol,
                resolved_venue_symbol=venue_symbol,
                canonical_symbol=canonical_symbol,
                asset_id=asset_id,
                szDecimals=sz_decimals,
                isDelisted=is_delisted,
                public_mid=str(mid_value) if mid_value is not None else None,
                sources=tuple(sorted(merged_sources[symbol])),
                source=tuple(sorted(merged_sources[symbol]))[0],
                precision_status="precision_ready" if sz_decimals is not None else "precision_missing",
                precision_ready=precision_ready,
                supported_by_venue=asset_tuple is not None and not bool(is_delisted),
                data_health=DataHealth.STALE if eligible and mid_warning else DataHealth.HEALTHY if eligible else DataHealth.UNAVAILABLE,
                scanner_eligible=eligible,
                blocked=blocked,
                reason_codes=tuple(dict.fromkeys(reasons)),
            )
        )
    return tuple(rows)


@dataclass(frozen=True)
class PaperSignalKey:
    lane_id: str
    strategy_id: str
    symbol: str
    timeframe: str
    signal_candle_time: str
    action: str

    def key(self) -> str:
        return "|".join(
            [
                self.lane_id,
                self.strategy_id,
                self.symbol.upper(),
                self.timeframe,
                self.signal_candle_time,
                self.action,
            ]
        )


@dataclass
class PaperPosition:
    paper_position_id: str
    lane_id: str
    strategy_id: str
    symbol: str
    timeframe: str
    side: str
    entry_signal_time: str
    entry_fill_time: str
    entry_price: Decimal
    quantity: Decimal
    notional: Decimal
    fees: Decimal
    slippage: Decimal
    open_reason_codes: tuple[str, ...]
    status: str = "open"
    current_unrealized_pnl: Decimal = Decimal("0")
    current_total_equity: Decimal = Decimal("10000")
    equity_before: Decimal = Decimal("10000")


@dataclass(frozen=True)
class PaperTrade:
    paper_trade_id: str
    lane_id: str
    strategy_id: str
    symbol: str
    timeframe: str
    entry_time: str
    exit_time: str
    entry_price: Decimal
    exit_price: Decimal
    quantity: Decimal
    gross_pnl: Decimal
    fees: Decimal
    slippage: Decimal
    net_pnl: Decimal
    equity_before: Decimal
    equity_after: Decimal
    entry_reason_codes: tuple[str, ...]
    exit_reason_codes: tuple[str, ...]


@dataclass
class PaperLedger:
    lane: StrategyLaneConfig
    realized_equity: Decimal = Decimal("10000")
    unrealized_pnl: Decimal = Decimal("0")
    max_equity: Decimal = Decimal("10000")
    min_equity: Decimal = Decimal("10000")
    max_drawdown: Decimal = Decimal("0")
    current_drawdown: Decimal = Decimal("0")
    total_fees: Decimal = Decimal("0")
    total_slippage: Decimal = Decimal("0")
    closed_trades: list[PaperTrade] = field(default_factory=list)
    open_positions: dict[str, PaperPosition] = field(default_factory=dict)
    processed_signal_keys: set[str] = field(default_factory=set)
    skipped_trades: int = 0
    data_health_blocks: int = 0
    duplicate_signal_blocks: int = 0
    consecutive_losses: int = 0
    max_consecutive_losses: int = 0
    current_losing_streak_pnl: Decimal = Decimal("0")
    worst_losing_streak_pnl: Decimal = Decimal("0")
    created_execution_artifacts: bool = False

    def __post_init__(self) -> None:
        self.realized_equity = self.lane.initial_equity
        self.max_equity = self.lane.initial_equity
        self.min_equity = self.lane.initial_equity

    @property
    def total_equity(self) -> Decimal:
        return self.realized_equity + self.unrealized_pnl

    def _update_drawdown(self) -> None:
        equity = self.total_equity
        self.max_equity = max(self.max_equity, equity)
        self.min_equity = min(self.min_equity, equity)
        self.current_drawdown = self.max_equity - equity
        self.max_drawdown = max(self.max_drawdown, self.current_drawdown)

    def _record_trade_outcome(self, net_pnl: Decimal) -> None:
        if net_pnl < 0:
            self.consecutive_losses += 1
            self.max_consecutive_losses = max(self.max_consecutive_losses, self.consecutive_losses)
            self.current_losing_streak_pnl += net_pnl
            self.worst_losing_streak_pnl = min(self.worst_losing_streak_pnl, self.current_losing_streak_pnl)
        elif net_pnl > 0:
            self.consecutive_losses = 0
            self.current_losing_streak_pnl = Decimal("0")

    def register_signal(self, signal_key: PaperSignalKey) -> tuple[bool, tuple[str, ...]]:
        key = signal_key.key()
        if key in self.processed_signal_keys:
            self.duplicate_signal_blocks += 1
            return False, ("duplicate_ignored",)
        self.processed_signal_keys.add(key)
        return True, ()

    def apply_closed_trade_result(
        self,
        *,
        net_pnl: Decimal,
        fees: Decimal = Decimal("0"),
        slippage: Decimal = Decimal("0"),
    ) -> None:
        self.realized_equity += net_pnl
        self.total_fees += fees
        self.total_slippage += slippage
        self._record_trade_outcome(net_pnl)
        self._update_drawdown()

    def position_key(self, symbol: str, timeframe: str) -> str:
        return f"{self.lane.lane_id}|{symbol.upper()}|{timeframe}"

    def open_synthetic_position(
        self,
        *,
        symbol: str,
        timeframe: str,
        signal_time: str,
        fill_time: str,
        fill_price: Decimal,
        fee_bps: Decimal = Decimal("5"),
        slippage_bps: Decimal = Decimal("0"),
        reason_codes: Sequence[str] = (),
    ) -> tuple[PaperPosition | None, tuple[str, ...]]:
        key = self.position_key(symbol, timeframe)
        if key in self.open_positions:
            self.skipped_trades += 1
            return None, ("open_position_exists",)
        equity_before = self.realized_equity
        notional = equity_before * self.lane.allocation_pct
        fee = notional * fee_bps / Decimal("10000")
        slippage = notional * slippage_bps / Decimal("10000")
        quantity = (notional - fee - slippage) / fill_price
        self.realized_equity -= fee + slippage
        self.total_fees += fee
        self.total_slippage += slippage
        position = PaperPosition(
            paper_position_id=f"pt_rt1_pos_{len(self.open_positions) + len(self.closed_trades) + 1}",
            lane_id=self.lane.lane_id,
            strategy_id=self.lane.strategy_id,
            symbol=symbol.upper(),
            timeframe=timeframe,
            side="long",
            entry_signal_time=signal_time,
            entry_fill_time=fill_time,
            entry_price=fill_price,
            quantity=quantity,
            notional=notional,
            fees=fee,
            slippage=slippage,
            open_reason_codes=tuple(reason_codes),
            current_total_equity=self.total_equity,
            equity_before=equity_before,
        )
        self.open_positions[key] = position
        self._update_drawdown()
        return position, ()

    def update_unrealized(self, *, symbol: str, timeframe: str, current_price: Decimal) -> tuple[Decimal, tuple[str, ...]]:
        position = self.open_positions.get(self.position_key(symbol, timeframe))
        if position is None:
            return Decimal("0"), ("paper_position_missing",)
        position.current_unrealized_pnl = (current_price - position.entry_price) * position.quantity
        self.unrealized_pnl = sum(item.current_unrealized_pnl for item in self.open_positions.values())
        position.current_total_equity = self.total_equity
        self._update_drawdown()
        return position.current_unrealized_pnl, ()

    def close_synthetic_position(
        self,
        *,
        symbol: str,
        timeframe: str,
        exit_time: str,
        exit_price: Decimal,
        fee_bps: Decimal = Decimal("5"),
        slippage_bps: Decimal = Decimal("0"),
        reason_codes: Sequence[str] = (),
    ) -> tuple[PaperTrade | None, tuple[str, ...]]:
        key = self.position_key(symbol, timeframe)
        position = self.open_positions.pop(key, None)
        if position is None:
            return None, ("paper_position_missing",)
        gross = (exit_price - position.entry_price) * position.quantity
        exit_notional = exit_price * position.quantity
        exit_fee = exit_notional * fee_bps / Decimal("10000")
        exit_slippage = exit_notional * slippage_bps / Decimal("10000")
        net_close = gross - exit_fee - exit_slippage
        self.realized_equity += net_close
        self.total_fees += exit_fee
        self.total_slippage += exit_slippage
        self.unrealized_pnl = sum(item.current_unrealized_pnl for item in self.open_positions.values())
        trade = PaperTrade(
            paper_trade_id=f"pt_rt1_trade_{len(self.closed_trades) + 1}",
            lane_id=self.lane.lane_id,
            strategy_id=self.lane.strategy_id,
            symbol=position.symbol,
            timeframe=position.timeframe,
            entry_time=position.entry_fill_time,
            exit_time=exit_time,
            entry_price=position.entry_price,
            exit_price=exit_price,
            quantity=position.quantity,
            gross_pnl=gross,
            fees=position.fees + exit_fee,
            slippage=position.slippage + exit_slippage,
            net_pnl=self.realized_equity - position.equity_before,
            equity_before=position.equity_before,
            equity_after=self.realized_equity,
            entry_reason_codes=position.open_reason_codes,
            exit_reason_codes=tuple(reason_codes),
        )
        self.closed_trades.append(trade)
        self._record_trade_outcome(trade.net_pnl)
        self._update_drawdown()
        return trade, ()

    def block_for_data_health(self) -> None:
        self.data_health_blocks += 1
        self.skipped_trades += 1


@dataclass(frozen=True)
class TestnetProbeCandidate:
    approval_text: str = ""
    probes_enabled: bool = False
    kill_switch: bool = True
    base_url: str = PT_RT1_TESTNET_INFO_URL
    account_mode: str = "main"
    account_address: str = ""
    vault_address: str | None = None
    symbol: str = "ETH"
    asset_id: int | None = 0
    sz_decimals: int | None = 4
    price: Decimal = Decimal("1000")
    quantity: Decimal = Decimal("0.02")
    notional: Decimal = PT_RT1_TESTNET_PROBE_NOTIONAL_USDC
    scanner_signal_eligible: bool = True
    daily_probe_count: int = 0
    daily_cap: int = 1
    notional_cap: Decimal = PT_RT1_TESTNET_PROBE_NOTIONAL_CAP_USDC
    post_only: bool = True
    tif: str = "Alo"
    submit_lease_acquired: bool = True
    artifact_label: str = "pt_rt1_testnet_only"
    unknown_or_open_probe_state: bool = False
    scanner_symbol_blocked: bool = False
    unit_semantics_deferred: bool = False
    precision_ready: bool = True


@dataclass(frozen=True)
class ProbeEligibilityResult:
    eligible: bool
    reason_codes: tuple[str, ...]
    order_shape: Mapping[str, Any] | None
    audit_row: Mapping[str, Any]


@dataclass(frozen=True)
class TestnetProbePolicy:
    probes_enabled_default: bool = False
    daily_probe_cap_default: int = 1
    notional_cap_default: Decimal = PT_RT1_TESTNET_PROBE_NOTIONAL_CAP_USDC
    kill_switch_default: bool = True

    def evaluate(self, candidate: TestnetProbeCandidate) -> ProbeEligibilityResult:
        reasons: list[str] = []
        if not candidate.probes_enabled:
            reasons.append("testnet_probes_disabled")
        if candidate.kill_switch:
            reasons.append("testnet_probe_kill_switch_enabled")
        if candidate.approval_text != PT_RT1_EXACT_TESTNET_PROBE_APPROVAL:
            reasons.append("testnet_probe_approval_missing")
        if candidate.base_url != PT_RT1_TESTNET_INFO_URL:
            reasons.append("testnet_endpoint_required")
        if "api.hyperliquid.xyz" in candidate.base_url and "testnet" not in candidate.base_url:
            reasons.append("live_endpoint_forbidden")
        if candidate.account_mode in {"subaccount", "vault"} and not candidate.vault_address:
            reasons.append("vault_address_required_for_subaccount_or_vault")
        if candidate.account_mode == "main" and candidate.vault_address:
            reasons.append("vault_address_forbidden_for_main_user")
        if candidate.asset_id is None or candidate.sz_decimals is None:
            reasons.append("symbol_or_precision_missing")
        if candidate.scanner_symbol_blocked:
            reasons.append("testnet_probe_symbol_blocked")
        if candidate.unit_semantics_deferred:
            reasons.append("testnet_probe_unit_semantics_deferred")
        if not candidate.precision_ready:
            reasons.append("testnet_probe_precision_missing")
        if not candidate.scanner_signal_eligible:
            reasons.append("scanner_signal_not_eligible")
        if candidate.daily_probe_count >= candidate.daily_cap:
            reasons.append("testnet_daily_probe_cap_exceeded")
        if candidate.notional > candidate.notional_cap:
            reasons.append("testnet_probe_notional_cap_exceeded")
        if not candidate.post_only or candidate.tif != "Alo":
            reasons.append("post_only_alo_required")
        if not candidate.submit_lease_acquired:
            reasons.append("submit_lease_required")
        if "testnet" not in candidate.artifact_label:
            reasons.append("testnet_only_artifact_label_required")
        if candidate.unknown_or_open_probe_state:
            reasons.append("unknown_probe_state_blocks_future_probes")
        order_shape = self._order_shape(candidate) if not reasons else None
        return ProbeEligibilityResult(
            eligible=not reasons,
            reason_codes=tuple(reasons),
            order_shape=order_shape,
            audit_row={
                "lane": "testnet_plumbing_probe",
                "environment": "hyperliquid_testnet_only",
                "eligible": not reasons,
                "reason_codes": reasons,
                "post_only": candidate.post_only,
                "tif": candidate.tif,
                "notional_usdc": str(candidate.notional),
                "notional_cap_usdc": str(candidate.notional_cap),
                "cancel_reconcile_required": True,
                "testnet_fills_update_strategy_pnl": False,
                "strategy_pnl_updated": False,
                "signed_order_endpoint_called": False,
                "order_endpoint_called": False,
            },
        )

    def _order_shape(self, candidate: TestnetProbeCandidate) -> Mapping[str, Any]:
        formatter = HyperliquidPrecisionFormatter(
            asset_id=int(candidate.asset_id or 0),
            symbol=candidate.symbol.upper(),
            sz_decimals=int(candidate.sz_decimals or 0),
        )
        price = formatter.format_price_down(candidate.price)
        size = formatter.format_size_down(candidate.quantity)
        payload: dict[str, Any] = {
            "action": {
                "type": "order",
                "orders": [
                    {
                        "a": candidate.asset_id,
                        "b": True,
                        "p": price.wire_value,
                        "s": size.wire_value,
                        "r": False,
                        "t": {"limit": {"tif": "Alo"}},
                    }
                ],
                "grouping": "na",
            },
            "environment": "hyperliquid_testnet_only",
        }
        if candidate.account_mode in {"subaccount", "vault"} and candidate.vault_address:
            payload["vaultAddress"] = candidate.vault_address
        return payload


def _configured_scanner_universe_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for requested in PT_RT1_REQUESTED_SCANNER_SYMBOLS:
        resolved = SYMBOL_ALIASES.get(requested, requested)
        sources = list(DEFAULT_SCANNER_SOURCES.get(requested, ("founder_requested",)))
        reason_codes: list[str] = ["runtime_market_data_health_pending"]
        blocked = False
        supported_by_venue = requested in SUPPORTED_CANONICAL_SYMBOLS
        if requested in SUPPORTED_CANONICAL_SYMBOLS:
            reason_codes.append("canonical_sv2_supported")
        else:
            reason_codes.append("runtime_meta_confirmation_required")
        if requested == "TRON":
            reason_codes.append("alias_tron_resolves_to_trx")
        if requested == "PEPE":
            blocked = True
            supported_by_venue = False
            reason_codes.extend(["pepe_kpepe_unit_semantics_deferred", "unit_semantics_deferred"])
        if requested == "OKB":
            blocked = True
            supported_by_venue = False
            reason_codes.append("okb_support_not_confirmed")
        if requested == "POL":
            reason_codes.append("pol_must_resolve_to_active_pol_not_delisted_matic")
        rows.append(
            {
                "requested_symbol": requested,
                "resolved_venue_symbol": resolved,
                "canonical_symbol": "TRX" if requested == "TRON" else resolved,
                "asset_id": None,
                "szDecimals": None,
                "isDelisted": None,
                "public_mid": None,
                "sources": sources,
                "source": sources[0],
                "supported_by_venue": supported_by_venue,
                "precision_status": "pending_runtime_meta",
                "precision_ready": False,
                "data_health": "pending_runtime_refresh",
                "scanner_eligible": False,
                "blocked": blocked,
                "reason_codes": tuple(dict.fromkeys(reason_codes)),
            }
        )
    rows.append(
        {
            "requested_symbol": "SHIB",
            "resolved_venue_symbol": "kSHIB",
            "canonical_symbol": "kSHIB",
            "asset_id": None,
            "szDecimals": None,
            "isDelisted": None,
            "public_mid": None,
            "sources": ["deferred_legacy_request"],
            "source": "deferred_legacy_request",
            "supported_by_venue": False,
            "precision_status": "unit_semantics_deferred",
            "precision_ready": False,
            "data_health": "unavailable",
            "scanner_eligible": False,
            "blocked": True,
            "reason_codes": ("unit_semantics_deferred", "venue_symbol_unit_semantics_deferred"),
        }
    )
    return rows


def build_pt_rt1_summary() -> dict[str, Any]:
    lanes = [strategy_lane_summary_payload(lane) for lane in PT_RT1_STRATEGY_LANES]
    active_week2_lanes = [strategy_lane_summary_payload(lane) for lane in PT_RT1_6_ACTIVE_STRATEGY_LANES]
    archived_week2_lanes = [strategy_lane_summary_payload(lane) for lane in PT_RT1_6_ARCHIVED_STRATEGY_LANES]
    scanner_rows = _configured_scanner_universe_rows()
    return {
        "phase": "PT-RT1.1A",
        "report": "pt_rt1_real_time_paper_observation_and_testnet_plumbing",
        "status": "implemented_readiness_expansion",
        "revision": "PT-RT1.1A",
        "latest_readiness_phase": "PT-RT1.4",
        "latest_readiness_report": "docs/pt_rt1_4_paper_trading_command_center_cleanup.md",
        "latest_readiness_summary": "docs/pt_rt1_4_paper_trading_command_center_cleanup_summary.json",
        "latest_hotfix_phase": "PT-RT1.6",
        "latest_hotfix_report": "docs/pt_rt1_6_founder_selected_week2_paper_slate.md",
        "latest_hotfix_summary": "docs/pt_rt1_6_founder_selected_week2_paper_slate_summary.json",
        "strategy_truth_lane": {
            "source": "Hyperliquid public mainnet info endpoint",
            "endpoint": PT_RT1_MAINNET_INFO_URL,
            "allowed_info_types": sorted(ALLOWED_STRATEGY_TRUTH_INFO_TYPES),
            "forbidden_info_types": sorted(FORBIDDEN_STRATEGY_TRUTH_INFO_TYPES),
            "uses_api_keys": False,
            "calls_private_signed_order_endpoints": False,
            "creates_execution_artifacts": False,
            "testnet_prices_are_strategy_truth": False,
        },
        "plumbing_lane": {
            "source": "Hyperliquid testnet only",
            "strategy_truth": False,
            "testnet_fills_update_strategy_pnl": False,
            "approval_text_required": PT_RT1_EXACT_TESTNET_PROBE_APPROVAL,
            "cancel_reconcile_required": True,
        },
        "symbols": list(PT_RT1_REQUESTED_SCANNER_SYMBOLS),
        "requested_symbols": list(PT_RT1_REQUESTED_SCANNER_SYMBOLS),
        "alias_mappings": SYMBOL_ALIASES,
        "deferred_runtime_symbols": PT_RT1_DEFERRED_RUNTIME_SYMBOLS,
        "blocked_symbol_policy": {
            "PEPE": "PEPE resolves to kPEPE and is blocked by default pending unit-semantics review.",
            "OKB": "OKB is blocked unless Hyperliquid public mainnet metadata confirms active support.",
            "SHIB": "SHIB/kSHIB remains deferred pending unit-semantics acceptance.",
            "POL": "POL must resolve to active POL; delisted MATIC mapping is blocked.",
            "TRUMP": "TRUMP is deferred from fresh PT-RT paper-observation scanner runs because it created excessive runtime noise.",
        },
        "timeframes": list(TIMEFRAME_DURATIONS),
        "active_timeframes": list(PT_RT1_4_ACTIVE_TIMEFRAMES),
        "disabled_timeframes": list(PT_RT1_4_DISABLED_TIMEFRAMES),
        "active_review_start_utc": PT_RT1_4_ACTIVE_REVIEW_START_UTC,
        "pt_rt1_6_week2_active_scope": {
            "scope": PT_RT1_6_RUNTIME_SCOPE,
            "output_dir": PT_RT1_6_RUNTIME_OUTPUT_DIR,
            "active_review_start_utc": PT_RT1_6_ACTIVE_REVIEW_START_UTC,
            "default_active_lane_ids": list(PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS),
            "archived_default_inactive_lane_ids": list(PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS),
            "active_timeframes": list(PT_RT1_6_ACTIVE_TIMEFRAMES),
            "disabled_timeframes": list(PT_RT1_6_DISABLED_TIMEFRAMES),
            "default_show_archived_lanes": False,
            "default_show_archived_rows": False,
            "runtime_started_by_pt_rt1_6": False,
            "no_active_paper_run_assumed_without_control_server_status": True,
            "reason_codes": [
                "founder_selected_week2_active_slate",
                "founder_archived_from_week2",
                "active_week_scoring_only",
                "not_default_active",
            ],
        },
        "pt_rt1_5_active_review_scope": {
            "scope": PT_RT1_5_RUNTIME_SCOPE,
            "output_dir": PT_RT1_5_RUNTIME_OUTPUT_DIR,
            "active_review_start_utc": PT_RT1_5_ACTIVE_REVIEW_START_UTC,
            "archived_runtime_scopes": list(PT_RT1_5_ARCHIVED_RUNTIME_SCOPES),
            "default_show_archived_rows": False,
            "active_week_ledgers_start_at_usdc": "10000",
            "old_runtime_rows_archived_not_deleted": True,
            "reason_codes": [
                "pre_week1_runtime_archived",
                "archived_position_hidden_by_default",
                "active_week_ui_reset",
                "active_week_scoring_only",
            ],
        },
        "pt_rt1_5_1_smoke_scope": {
            "scope": PT_RT1_5_1_RUNTIME_SCOPE,
            "output_dir": PT_RT1_5_1_RUNTIME_OUTPUT_DIR,
            "active_review_start_utc": PT_RT1_5_1_ACTIVE_REVIEW_START_UTC,
            "archived_runtime_scopes": list(PT_RT1_5_ARCHIVED_RUNTIME_SCOPES),
            "default_show_archived_rows": False,
            "fresh_signal_only_after_runtime_start": True,
            "old_runtime_rows_archived_not_deleted": True,
            "reason_codes": [
                "pre_warm_start_gate_runtime_archived",
                "archived_smoke_rows_hidden_by_default",
                "active_week_reset_after_warm_start_hotfix",
            ],
        },
        "active_timeframe_policy": {
            "status": "pt_rt1_4_week1_cutover",
            "active_timeframes": list(PT_RT1_4_ACTIVE_TIMEFRAMES),
            "disabled_timeframes": [
                {
                    "timeframe": timeframe,
                    "status": PT_RT1_4_DISABLED_TIMEFRAME_STATUS,
                    "reason_codes": list(PT_RT1_4_TIMEFRAME_REASON_CODES),
                }
                for timeframe in PT_RT1_4_DISABLED_TIMEFRAMES
            ],
            "default_lane_comparison_scope": "selected_timeframe_only",
            "default_selected_timeframe": "1h",
            "all_active_timeframes_label": "sum across active paper timeframes only: 1h + 4h + 1d",
            "not_one_combined_account": True,
            "pre_cutover_label": "weekend_burn_in_or_pre_cutover",
            "legacy_15m_policy": "existing 15m records remain visible under paused/legacy filters; no new 15m entries after cutover",
        },
        "scanner_universe": scanner_rows,
        "scanner_eligibility_rules": [
            "exists_in_current_hyperliquid_public_meta",
            "isDelisted_is_not_true",
            "szDecimals_present",
            "allMids_positive_public_market_data",
            "symbol_identity_not_ambiguous",
            "unit_semantics_accepted",
            "precision_formatting_available",
            "data_health_healthy",
        ],
        "market_data_health": [
            {
                "symbol": row["canonical_symbol"],
                "requested_symbol": row["requested_symbol"],
                "resolved_venue_symbol": row["resolved_venue_symbol"],
                "timeframe": timeframe,
                "source": "Hyperliquid public mainnet",
                "status": (
                    PT_RT1_4_DISABLED_TIMEFRAME_STATUS
                    if timeframe in PT_RT1_4_DISABLED_TIMEFRAMES
                    else "pending_runtime_refresh"
                ),
                "fully_closed_candle_status": (
                    "paused_legacy_timeframe"
                    if timeframe in PT_RT1_4_DISABLED_TIMEFRAMES
                    else "pending_runtime_refresh"
                ),
                "last_update_utc": None,
                "reason_codes": (
                    list(PT_RT1_4_TIMEFRAME_REASON_CODES)
                    if timeframe in PT_RT1_4_DISABLED_TIMEFRAMES
                    else ["runtime_not_started"]
                ),
            }
            for row in scanner_rows
            if not row["blocked"]
            for timeframe in TIMEFRAME_DURATIONS
        ],
        "strategy_lanes": lanes,
        "active_strategy_lanes": active_week2_lanes,
        "archived_strategy_lanes": archived_week2_lanes,
        "week2_active_strategy_lanes": active_week2_lanes,
        "week2_archived_strategy_lanes": archived_week2_lanes,
        "default_active_strategy_lane_ids": list(PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS),
        "archived_default_inactive_strategy_lane_ids": list(PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS),
        "wildcard_definitions": WILDCARD_STRATEGY_DEFINITIONS,
        "paper_equity_policy": {
            "starting_equity_usdc_per_lane": "10000",
            "sizing_basis": "current_realized_synthetic_equity",
            "compounds_wins_and_losses": True,
            "does_not_reset_after_losses": True,
            "runtime_state_paths": RUNTIME_STATE_PATHS,
        },
        "fill_model": {
            "default": "next_candle_open",
            "comparison_metadata": ["next_candle_close"],
            "same_candle_optimistic_fills": False,
        },
        "data_health_policy": {
            "states": [item.value for item in DataHealth],
            "blocks_new_entries_when_not_healthy": True,
            "reason_codes": [
                "public_fetch_failure",
                "stale_candle",
                "missing_candle_gap_detected",
                "out_of_order_candle",
                "insufficient_history",
                "precision_unavailable",
                "market_metadata_mismatch",
            ],
        },
        "signal_evaluation_policy": {
            "mode": "candle_close_only",
            "market_refresh_mode": "continuous_display_refresh",
            "fresh_signal_only_after_runtime_start": True,
            "active_strategy_timeframes": list(PT_RT1_5_ACTIVE_TIMEFRAMES),
            "paused_strategy_timeframes": list(PT_RT1_5_DISABLED_TIMEFRAMES),
            "one_hour_grace_delay_seconds": PT_RT1_5_CANDLE_CLOSE_GRACE_SECONDS["1h"],
            "four_hour_grace_delay_seconds": PT_RT1_5_CANDLE_CLOSE_GRACE_SECONDS["4h"],
            "one_day_grace_delay_seconds": PT_RT1_5_CANDLE_CLOSE_GRACE_SECONDS["1d"],
            "closed_candle_retry_policy": PT_RT1_5_CLOSED_CANDLE_RETRY_POLICY,
            "duplicate_candle_signal_policy": "duplicate_candle_signal_ignored",
            "reason_codes": [*PT_RT1_5_SCHEDULER_REASON_CODES, *PT_RT1_5_1_WARM_START_REASON_CODES],
        },
        "warm_start_gate_policy": {
            "status": "enabled_for_pt_rt1_5_1",
            "fresh_signal_only_after_runtime_start": True,
            "startup_valid_signals_create_synthetic_opens": False,
            "startup_valid_signals_create_testnet_orders": False,
            "requires_false_then_true_transition": True,
            "applies_to_all_synthetic_lanes": True,
            "baseline_testnet_transport_requires_fresh_post_start_open": True,
            "reason_codes": list(PT_RT1_5_1_WARM_START_REASON_CODES),
        },
        "open_position_mtm_policy": {
            "status": "enabled_for_pt_rt1_5_1",
            "preferred_source": "public_mainnet_allMids",
            "fallback_source": "latest_fully_closed_public_mainnet_candle_close",
            "missing_price_displays_zero": False,
            "market_refresh_updates_mtm_without_signal_evaluation": True,
            "reason_codes": list(PT_RT1_5_1_MTM_REASON_CODES),
        },
        "testnet_probe_policy": {
            "PT_RT1_TESTNET_PROBES_ENABLED": False,
            "PT_RT1_TESTNET_DAILY_PROBE_CAP": 1,
            "PT_RT1_TESTNET_PROBE_NOTIONAL_USDC": str(PT_RT1_TESTNET_PROBE_NOTIONAL_USDC),
            "PT_RT1_TESTNET_PROBE_NOTIONAL_CAP": str(PT_RT1_TESTNET_PROBE_NOTIONAL_CAP_USDC),
            "PT_RT1_TESTNET_KILL_SWITCH": True,
            "default_blocks_probes": True,
            "order_type": "post_only_limit",
            "tif": "Alo",
        },
        "pt_rt1_5_testnet_order_policy": {
            "order_transport_scope": "Money Flow v1.2 baseline opens only",
            "approval_text_required": PT_RT1_5_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
            "pt_rt1_5_1_approval_text_required": PT_RT1_5_1_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
            "fixed_notional_usdc": str(PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC),
            "daily_order_cap_default": PT_RT1_5_TESTNET_DAILY_ORDER_CAP_DEFAULT,
            "per_symbol_daily_cap_default": PT_RT1_5_TESTNET_PER_SYMBOL_DAILY_CAP_DEFAULT,
            "active_timeframes": list(PT_RT1_5_ACTIVE_TIMEFRAMES),
            "fresh_signal_after_runtime_start_required": True,
            "startup_valid_signals_can_send_testnet_orders": False,
            "candidate_lanes_can_send_testnet_orders": False,
            "mf_orig_lanes_can_send_testnet_orders": False,
            "wildcard_lanes_can_send_testnet_orders": False,
            "week2_testnet_eligible_lane_ids": ["money_flow_v1_2_baseline"],
            "week2_synthetic_only_lane_ids": [
                "avoid_low_rolling_range_20",
                "mf_orig_1d_stage2_breakout_resistance_full_equity",
                *PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS,
            ],
            "testnet_prices_are_strategy_truth": False,
            "testnet_fills_update_strategy_pnl": False,
            "lifecycle_table": "testnet_order_lifecycle.jsonl",
            "reason_codes": list(PT_RT1_5_TESTNET_ORDER_REASON_CODES),
        },
        "dashboard_status": {
            "view": "Paper Observation",
            "status": "implemented_with_pt_rt1_6_week2_slate",
            "strategy_lanes_visible": len(active_week2_lanes),
            "historical_strategy_lanes_available": len(lanes),
            "archived_lanes_visible_as_separate_reference": True,
            "default_active_lanes_visible": list(PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS),
            "default_archived_lanes_hidden_from_active_scoreboard": True,
            "expanded_scanner_universe_visible": True,
            "blocked_symbols_visible": True,
            "wildcard_diagnostics_visible": False,
            "public_mainnet_connection_status_visible": True,
            "runtime_summary_preferred_paths": [
                "reports/paper_runtime/pt_rt1_6_week2_active/summary.json",
                "reports/paper_runtime/pt_rt1_5_2_week1_active/summary.json",
                "reports/paper_runtime/pt_rt1_5_3_transport_smoke/summary.json",
                "reports/paper_runtime/pt_rt1_5_1_smoke/summary.json",
                "reports/paper_runtime/pt_rt1_5_week1_active/summary.json",
                "reports/paper_runtime/pt_rt1_1b_smoke/summary.json",
                "reports/paper_runtime/pt_rt1_1b_24h_dry_run/summary.json",
                "docs/pt_rt1_1b_hyperliquid_live_market_data_and_runtime_readiness_summary.json",
            ],
            "date_filters": "display-only filter; not canonical evidence; not backend replay",
            "stale_or_no_active_run_warning": "No active paper run detected unless local control server reports running; stale runtime artifacts are labeled.",
        },
        "runtime_command": {
            "smoke_example": ".venv/bin/python scripts/run_pt_rt1_paper_observation.py --duration-minutes 1 --output-dir reports/paper_runtime/pt_rt1_1b_smoke --disable-testnet-probes --public-mainnet-only",
            "duration_hours_example": ".venv/bin/python scripts/run_pt_rt1_paper_observation.py --duration-hours 24 --output-dir reports/paper_runtime/pt_rt1_1c_24h_dry_run --enable-testnet-probes --founder-approved-testnet-probes-20usdc --testnet-probe-notional-usdc 20 --public-mainnet-only",
            "pt_rt1_5_week1_active_example": ".venv/bin/python scripts/run_pt_rt1_paper_observation.py --duration-hours 24 --output-dir reports/paper_runtime/pt_rt1_5_week1_active --pt-rt1-5-week1-active --enable-pt-rt1-5-baseline-testnet-orders --founder-approved-pt-rt1-5-baseline-testnet-orders-25usdc --pt-rt1-5-testnet-order-notional-usdc 25 --disable-testnet-probes --public-mainnet-only",
            "pt_rt1_5_1_smoke_example": ".venv/bin/python scripts/run_pt_rt1_paper_observation.py --duration-hours 1 --output-dir reports/paper_runtime/pt_rt1_5_1_smoke --pt-rt1-5-week1-active --signal-evaluation-mode candle_close_only --fresh-signal-only-after-runtime-start --enable-baseline-testnet-transport --founder-approved-pt-rt1-5-1-baseline-testnet-orders-25usdc --pt-rt1-5-testnet-order-notional-usdc 25 --disable-legacy-testnet-probes --public-mainnet-only",
            "pt_rt1_6_week2_active_example": ".venv/bin/python scripts/run_pt_rt1_paper_observation.py --duration-hours 24 --output-dir reports/paper_runtime/pt_rt1_6_week2_active --pt-rt1-5-week1-active --signal-evaluation-mode candle_close_only --fresh-signal-only-after-runtime-start --enable-baseline-testnet-transport --founder-approved-pt-rt1-5-2-baseline-testnet-orders-25usdc --pt-rt1-5-testnet-order-notional-usdc 25 --public-mainnet-only",
        },
        "next_phase": {
            "decision": "Founder may start the PT-RT1.6 Week 2 three-lane paper run after review",
            "conditions": [
                "testnet_probe_transport_not_submitted_by_pt_rt1_runtime",
                "public_mainnet_strategy_truth_only",
                "expanded_scanner_rows_remain_reason_coded",
                "week2_active_slate_exactly_three_lanes",
                "archived_lanes_hidden_from_default_active_scoring",
                "fifteen_minute_timeframe_paused_for_week2",
                "baseline_only_testnet_eligible",
                "no_production_rule_changes",
            ],
        },
        "runbooks": {
            "dry_run_24h_probes_disabled": "docs/pt_rt1_24h_dry_run_probes_disabled.md",
            "testnet_plumbing_24h_probe_run": "docs/pt_rt1_24h_testnet_plumbing_probe_run.md",
            "forward_observation_60_day_plan": "docs/pt_rt1_60_day_forward_observation_plan.md",
        },
        "boundaries": {
            "production_money_flow_rules_changed": False,
            "live_trading_approved": False,
            "paper_runtime_approved_as_production": False,
            "live_exchange_orders_submitted": False,
            "historical_evidence_packs_regenerated": False,
            "sor_fanout_cbbo_added": False,
            "testnet_probes_submit_signed_transport": False,
        },
    }


def ensure_runtime_state_directory() -> Path:
    path = Path(RUNTIME_STATE_PATHS["state"]).parent
    path.mkdir(parents=True, exist_ok=True)
    return path
