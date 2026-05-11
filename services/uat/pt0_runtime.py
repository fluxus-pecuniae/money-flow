"""PT0 paper/sandbox runtime foundation helpers.

PT0 is still sandbox/testnet only. The helpers in this module are deterministic
by default and do not call network, private, signed, order, cancel, amend, retry,
or live endpoints. They model the paper-equity ledger, broad Hyperliquid
testnet-supported universe eligibility, risk limits, and route-candidate gates
needed before a later supervised runtime can be enabled.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
import json
from typing import Any, Mapping, Sequence

from services.exchange.safety import ExchangeEndpointCategory
from services.uat.live_monitor import (
    UAT42_ALLOWED_PUBLIC_INFO_TYPES,
    UAT42_BALANCE_POLL_INTERVAL_SECONDS,
    UAT42_HYPERLIQUID_PUBLIC_INFO_URL,
    UAT42_TIMEFRAMES,
    UAT42_WATCHLIST,
    UAT42BalancePollingPolicy,
    UAT42PaperEquityLedger,
    UAT42PublicMarketDataPolicy,
    build_paper_equity_ledger,
)


PT0_REPORT_NAME = "pt0_tradingview_charts_and_top20_paper_sandbox_runtime"
PT0_APPROVAL_STATEMENT = "PAPER TRADING IS APPROVED."
PT0_TOP20_APPROVAL_STATEMENT = (
    "BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED."
)
PT0_WATCHLIST: tuple[str, ...] = UAT42_WATCHLIST
PT0_TIMEFRAMES: tuple[str, ...] = UAT42_TIMEFRAMES
PT0_INITIAL_PAPER_EQUITY = Decimal("10000")
PT0_LEVERAGE_ASSUMPTION = Decimal("10")
PT0_SANDBOX_BALANCE_REFERENCE = Decimal("1000")
PT0_SANDBOX_ORDER_ROUTING_ENABLED_ENV = "PT0_SANDBOX_ORDER_ROUTING_ENABLED"


@dataclass(frozen=True)
class PT0SizingPolicy:
    sizing_basis: str = "realized_equity"
    risk_display_basis: str = "realized_plus_unrealized"
    use_static_initial_equity: bool = False

    def sizing_equity(self, ledger: UAT42PaperEquityLedger) -> Decimal:
        if self.sizing_basis == "realized_equity":
            return ledger.realized_equity
        if self.sizing_basis == "realized_plus_unrealized":
            return ledger.current_paper_equity
        raise ValueError(f"unsupported PT0 sizing basis: {self.sizing_basis}")

    def to_dict(self, ledger: UAT42PaperEquityLedger) -> dict[str, Any]:
        return {
            "sizing_basis": self.sizing_basis,
            "risk_display_basis": self.risk_display_basis,
            "use_static_initial_equity": self.use_static_initial_equity,
            "sizing_equity": _decimal_to_string(self.sizing_equity(ledger)),
            "risk_display_equity": _decimal_to_string(ledger.current_paper_equity),
            "policy": (
                "PT0 sizing uses current realized internal paper equity, not the static "
                "initial 10,000 USDC. Realized plus unrealized PnL is displayed for risk."
            ),
        }


@dataclass(frozen=True)
class PT0RuntimeLimits:
    max_order_notional_pct_of_paper_equity: Decimal = Decimal("0.01")
    max_order_notional_absolute: Decimal = Decimal("100")
    max_orders_per_day: int = 5
    max_open_positions: int = 3
    max_open_positions_per_symbol: int = 1
    allowed_venue: str = "hyperliquid"
    allowed_environment: str = "testnet"
    allowed_universe: str = "top20_hyperliquid_supported"
    kill_switch_enabled: bool = False
    live_endpoint_access: bool = False
    smart_routing_sor_fanout_allowed: bool = False
    cross_venue_routing_allowed: bool = False

    def max_notional_for(self, ledger: UAT42PaperEquityLedger, sizing_policy: PT0SizingPolicy) -> Decimal:
        pct_limit = sizing_policy.sizing_equity(ledger) * self.max_order_notional_pct_of_paper_equity
        return min(pct_limit, self.max_order_notional_absolute)

    def to_dict(self, ledger: UAT42PaperEquityLedger, sizing_policy: PT0SizingPolicy) -> dict[str, Any]:
        return {
            **{
                key: _decimal_to_string(value) if isinstance(value, Decimal) else value
                for key, value in asdict(self).items()
            },
            "computed_max_order_notional": _decimal_to_string(self.max_notional_for(ledger, sizing_policy)),
        }


@dataclass(frozen=True)
class PT0UniverseAssetEligibility:
    symbol: str
    paper_eligibility: str
    supported_on_testnet: bool
    market_identity_available: bool
    precision_metadata_available: bool
    precision_validation_passed: bool
    reason_codes: tuple[str, ...]
    asset_id: int | None = None
    sz_decimals: int | None = None
    max_price_decimals: int | None = None
    formatted_sample_post_only_buy_price: str | None = None
    formatted_sample_size: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"reason_codes": list(self.reason_codes)}


@dataclass(frozen=True)
class PT0RouteCandidate:
    symbol: str
    venue: str = "hyperliquid"
    environment: str = "testnet"
    route_type: str = "fixed_single_venue_testnet"
    order_notional: Decimal = Decimal("0")
    routing_enabled: bool = False
    daily_order_count: int = 0
    open_positions_count: int = 0
    open_positions_for_symbol: int = 0
    kill_switch_enabled: bool = False
    live_endpoint_access: bool = False
    sor_requested: bool = False
    fanout_requested: bool = False
    target_reselection_requested: bool = False
    cross_venue_requested: bool = False
    market_identity_available: bool = True
    precision_metadata_available: bool = True
    price_precision_valid: bool = True
    size_precision_valid: bool = True
    supported_on_testnet: bool = True


@dataclass(frozen=True)
class PT0RouteCandidateDecision:
    allowed: bool
    risk_blocked: bool
    reason_codes: tuple[str, ...]
    calls_exchange: bool = False
    creates_strategy_decision: bool = False
    creates_order_intent: bool = False
    creates_prepared_order: bool = False
    creates_submitted_order: bool = False
    creates_executable_approval: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"reason_codes": list(self.reason_codes)}


def build_pt0_paper_equity_ledger(
    *,
    realized_pnl: Decimal | str | int = Decimal("0"),
    unrealized_pnl: Decimal | str | int = Decimal("0"),
    open_paper_exposure: Decimal | str | int = Decimal("0"),
) -> UAT42PaperEquityLedger:
    return build_paper_equity_ledger(
        realized_pnl=realized_pnl,
        unrealized_pnl=unrealized_pnl,
        open_paper_exposure=open_paper_exposure,
        initial_paper_equity=PT0_INITIAL_PAPER_EQUITY,
        confirmation_source="Hyperliquid sandbox/testnet balance polled every 60 seconds",
    )


def build_pt0_paper_universe(
    *,
    precision_validation: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[PT0UniverseAssetEligibility, ...]:
    precision_by_symbol = {
        str(row.get("symbol") or "").upper(): dict(row)
        for row in (precision_validation or [])
    }
    assets: list[PT0UniverseAssetEligibility] = []
    for symbol in PT0_WATCHLIST:
        row = precision_by_symbol.get(symbol)
        if row is None:
            assets.append(
                PT0UniverseAssetEligibility(
                    symbol=symbol,
                    paper_eligibility="blocked_missing_metadata",
                    supported_on_testnet=False,
                    market_identity_available=False,
                    precision_metadata_available=False,
                    precision_validation_passed=False,
                    reason_codes=(
                        "paper_market_identity_missing",
                        "paper_precision_metadata_missing",
                    ),
                )
            )
            continue

        passed = bool(row.get("precision_validation_passed"))
        raw_reasons = tuple(str(reason) for reason in row.get("reason_codes") or ())
        supported = not any(
            reason
            in {
                "unsupported_by_hyperliquid_meta",
                "source_unsupported_by_hyperliquid_meta",
                "paper_symbol_not_supported_on_testnet",
            }
            for reason in raw_reasons
        )
        reason_codes: list[str] = []
        if not supported:
            reason_codes.extend(
                [
                    "paper_universe_unavailable_current_testnet_metadata",
                    "paper_symbol_not_supported_on_testnet",
                ]
            )
        if not passed and supported:
            reason_codes.extend(
                [
                    "paper_precision_metadata_missing",
                    "paper_price_precision_invalid",
                    "paper_size_precision_invalid",
                ]
            )
        if raw_reasons:
            reason_codes.extend(f"source_{reason}" for reason in raw_reasons)

        assets.append(
            PT0UniverseAssetEligibility(
                symbol=symbol,
                paper_eligibility="eligible"
                if passed
                else "blocked_not_supported_on_testnet"
                if not supported
                else "blocked_precision_unavailable",
                supported_on_testnet=supported,
                market_identity_available=supported,
                precision_metadata_available=passed,
                precision_validation_passed=passed,
                reason_codes=tuple(reason_codes),
                asset_id=_optional_int(row.get("asset_id")),
                sz_decimals=_optional_int(row.get("sz_decimals")),
                max_price_decimals=_optional_int(row.get("max_price_decimals")),
                formatted_sample_post_only_buy_price=_optional_str(
                    row.get("formatted_sample_post_only_buy_price")
                ),
                formatted_sample_size=_optional_str(row.get("formatted_sample_size")),
            )
        )
    return tuple(assets)


def evaluate_pt0_route_candidate(
    candidate: PT0RouteCandidate,
    *,
    ledger: UAT42PaperEquityLedger | None = None,
    sizing_policy: PT0SizingPolicy | None = None,
    limits: PT0RuntimeLimits | None = None,
    universe_assets: Sequence[PT0UniverseAssetEligibility] | None = None,
) -> PT0RouteCandidateDecision:
    ledger = ledger or build_pt0_paper_equity_ledger()
    sizing_policy = sizing_policy or PT0SizingPolicy()
    limits = limits or PT0RuntimeLimits()
    universe_assets = universe_assets or build_pt0_paper_universe()
    by_symbol = {asset.symbol: asset for asset in universe_assets}
    asset = by_symbol.get(candidate.symbol)
    reasons: list[str] = []

    if not candidate.routing_enabled:
        reasons.append("pt0_sandbox_order_routing_disabled_by_default")
    if candidate.venue.lower() != limits.allowed_venue:
        reasons.append("pt0_allowed_venue_hyperliquid_testnet_required")
    if candidate.environment not in {"sandbox", "testnet", "uat_sandbox"}:
        reasons.append("pt0_allowed_environment_sandbox_testnet_required")
    if candidate.symbol not in PT0_WATCHLIST:
        reasons.append("paper_symbol_not_in_approved_top20_universe")
    if asset and asset.paper_eligibility != "eligible":
        reasons.extend(asset.reason_codes)
    if not candidate.supported_on_testnet:
        reasons.append("paper_symbol_not_supported_on_testnet")
    if not candidate.market_identity_available:
        reasons.append("paper_market_identity_missing")
    if not candidate.precision_metadata_available:
        reasons.append("paper_precision_metadata_missing")
    if not candidate.price_precision_valid:
        reasons.append("paper_price_precision_invalid")
    if not candidate.size_precision_valid:
        reasons.append("paper_size_precision_invalid")
    if candidate.order_notional <= 0:
        reasons.append("pt0_positive_order_notional_required")
    if candidate.order_notional > limits.max_notional_for(ledger, sizing_policy):
        reasons.append("pt0_max_order_notional_exceeded")
    if candidate.daily_order_count >= limits.max_orders_per_day:
        reasons.append("pt0_max_daily_order_count_exceeded")
    if candidate.open_positions_count >= limits.max_open_positions:
        reasons.append("pt0_max_open_positions_exceeded")
    if candidate.open_positions_for_symbol >= limits.max_open_positions_per_symbol:
        reasons.append("pt0_max_open_positions_per_symbol_exceeded")
    if candidate.kill_switch_enabled or limits.kill_switch_enabled:
        reasons.append("pt0_kill_switch_enabled")
    if candidate.live_endpoint_access or limits.live_endpoint_access:
        reasons.append("pt0_live_endpoint_forbidden")
    if candidate.sor_requested:
        reasons.append("pt0_sor_forbidden")
    if candidate.fanout_requested:
        reasons.append("pt0_top20_broad_fanout_forbidden")
    if candidate.target_reselection_requested:
        reasons.append("pt0_target_reselection_forbidden")
    if candidate.cross_venue_requested:
        reasons.append("pt0_cross_venue_routing_forbidden")

    unique_reasons = tuple(dict.fromkeys(reasons))
    return PT0RouteCandidateDecision(
        allowed=not unique_reasons,
        risk_blocked=bool(unique_reasons),
        reason_codes=unique_reasons,
    )


def build_pt0_scanner_records(
    *,
    uat42_summary: Mapping[str, Any] | None,
    universe_assets: Sequence[PT0UniverseAssetEligibility],
    recorded_at_utc: str,
) -> list[dict[str, Any]]:
    uat42_records = {
        (str(row.get("symbol") or ""), str(row.get("timeframe") or "")): dict(row)
        for row in ((uat42_summary or {}).get("strategy_scanner", {}).get("records") or [])
    }
    assets = {asset.symbol: asset for asset in universe_assets}
    records: list[dict[str, Any]] = []
    for symbol in PT0_WATCHLIST:
        asset = assets[symbol]
        for timeframe in PT0_TIMEFRAMES:
            source_row = uat42_records.get((symbol, timeframe)) or uat42_records.get((symbol, "1h")) or {}
            if asset.paper_eligibility != "eligible":
                status = "invalid"
                reasons = list(asset.reason_codes)
            elif timeframe != "1h" and (symbol, timeframe) not in uat42_records:
                status = "would_hold"
                reasons = ["pt0_secondary_timeframe_public_refresh_pending"]
            else:
                status = str(source_row.get("status") or "no_trade")
                reasons = list(source_row.get("reason_codes") or ["pt0_paper_scanner_foundation_record"])
            records.append(
                {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "component": f"sleeve_{timeframe}",
                    "source": "paper_signal",
                    "status": status,
                    "reason_codes": reasons,
                    "indicators": source_row.get("indicators") or {},
                    "candle_close_time": source_row.get("timestamp_utc") or recorded_at_utc,
                    "next_candle_open_context": source_row.get("next_candle_open_assumption") or "observation_only",
                    "next_candle_close_context": source_row.get("next_candle_close_assumption") or "observation_only",
                    "same_candle_close_research_only": "research only",
                    "operator_explanation": (
                        "PT0 paper/sandbox scanner record only; creates no live StrategyDecision, "
                        "OrderIntent, PreparedVenueOrder, SubmittedOrder, or executable approval."
                    ),
                    "creates_strategy_decision": False,
                    "creates_order_intent": False,
                    "creates_prepared_order": False,
                    "creates_submitted_order": False,
                    "creates_executable_approval": False,
                }
            )
    return records


def build_pt0_runtime_summary(
    *,
    recorded_at: datetime | None = None,
    uat42_summary: Mapping[str, Any] | None = None,
    uat33_summary: Mapping[str, Any] | None = None,
    uat34_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    observed_at = recorded_at or datetime.now(UTC)
    timestamp = observed_at.isoformat().replace("+00:00", "Z")
    precision_validation = (uat33_summary or {}).get("precision_validation") or []
    universe_assets = build_pt0_paper_universe(precision_validation=precision_validation)
    ledger = build_pt0_paper_equity_ledger()
    sizing_policy = PT0SizingPolicy()
    limits = PT0RuntimeLimits()
    polling_policy = UAT42BalancePollingPolicy()
    polling_allowed, polling_reasons = polling_policy.evaluate()
    eth_candidate = PT0RouteCandidate(symbol="ETH", order_notional=Decimal("15"))
    eth_decision = evaluate_pt0_route_candidate(
        eth_candidate,
        ledger=ledger,
        sizing_policy=sizing_policy,
        limits=limits,
        universe_assets=universe_assets,
    )

    return {
        "report": PT0_REPORT_NAME,
        "recorded_at_utc": timestamp,
        "approval_statements": {
            "paper_trading": PT0_APPROVAL_STATEMENT,
            "broader_top20": PT0_TOP20_APPROVAL_STATEMENT,
            "scope": (
                "Hyperliquid testnet/sandbox only; internal 10,000 USDC paper-equity "
                "ledger; top-20 Hyperliquid-supported paper/sandbox scanning and "
                "approval/risk-gated sandbox routing foundation."
            ),
            "live_trading": "LIVE TRADING IS NOT APPROVED.",
            "real_capital": "REAL-CAPITAL TRADING IS NOT APPROVED.",
        },
        "charting": {
            "library": "TradingView Lightweight Charts",
            "version": "5.2.0",
            "bundle_path": "apps/dashboard/vendor/lightweight-charts.standalone.production.js",
            "license_path": "apps/dashboard/vendor/LICENSE",
            "advanced_charts_used": False,
            "hosted_tradingview_widget_used": False,
            "custom_chart_shell_status": "bypassed_by_official_lightweight_charts",
            "attribution": "Charts use TradingView Lightweight Charts v5.2.0 under Apache-2.0.",
        },
        "public_market_data_policy": {
            **asdict(UAT42PublicMarketDataPolicy()),
            "endpoint": UAT42_HYPERLIQUID_PUBLIC_INFO_URL,
            "allowed_public_info_types": list(UAT42_ALLOWED_PUBLIC_INFO_TYPES),
            "refresh_interval_seconds": 15,
            "source": "hyperliquid_testnet_public_read_only",
            "live_endpoint_access": False,
        },
        "watchlist": list(PT0_WATCHLIST),
        "timeframes": list(PT0_TIMEFRAMES),
        "paper_universe": [asset.to_dict() for asset in universe_assets],
        "paper_scanner": {
            "mode": "paper_sandbox_observation",
            "symbols": list(PT0_WATCHLIST),
            "timeframes": list(PT0_TIMEFRAMES),
            "records": build_pt0_scanner_records(
                uat42_summary=uat42_summary,
                universe_assets=universe_assets,
                recorded_at_utc=timestamp,
            ),
            "forbidden_outputs": [
                "live StrategyDecision",
                "live OrderIntent",
                "live PreparedVenueOrder",
                "live SubmittedOrder",
                "live executable approval",
            ],
        },
        "paper_equity": {
            **ledger.to_dict(),
            "leverage_assumption": f"{PT0_LEVERAGE_ASSUMPTION}x",
            "sandbox_balance_reference": _decimal_to_string(PT0_SANDBOX_BALANCE_REFERENCE),
        },
        "sizing_policy": sizing_policy.to_dict(ledger),
        "balance_position_polling": {
            "policy": polling_policy.to_dict(),
            "poll_interval_seconds": UAT42_BALANCE_POLL_INTERVAL_SECONDS,
            "polling_allowed": polling_allowed,
            "reason_codes": list(polling_reasons),
            "source": "sandbox_private_read_only",
            "not_live_account": True,
            "order_endpoints_called": False,
            "cancel_amend_retry_endpoints_called": False,
        },
        "runtime_limits": limits.to_dict(ledger, sizing_policy),
        "routing_foundation": {
            "route_scope": "hyperliquid_testnet_supported_top20_fixed_single_venue",
            "routing_enabled_env": PT0_SANDBOX_ORDER_ROUTING_ENABLED_ENV,
            "routing_enabled_default": False,
            "default_eth_candidate_decision": eth_decision.to_dict(),
            "existing_uat3_4_records_visible": bool((uat34_summary or {}).get("ledger_records")),
            "smart_routing_sor_fanout_added": False,
            "cross_venue_routing_added": False,
            "production_auto_submit_added": False,
        },
        "routed_orders_paper_trades": {
            "source": "paper scanner and UAT3.4 routed sandbox ledger summaries",
            "records": _paper_trade_rows(uat34_summary, ledger),
        },
        "side_effect_flags": {
            "api_keys_used": False,
            "private_order_endpoints_called": False,
            "signed_endpoints_called": False,
            "order_endpoints_called": False,
            "cancel_amend_retry_endpoints_called": False,
            "live_endpoint_called": False,
            "sandbox_orders_submitted_by_pt0": False,
            "live_orders_submitted": False,
            "order_controls_added": False,
            "live_real_capital_trading_added": False,
            "money_flow_rules_changed": False,
            "smart_routing_sor_fanout_added": False,
            "evidence_packs_generated": False,
        },
        "pt0_1_roadmap_status": "captured_for_supervised_top20_paper_sandbox_runtime_week",
    }


def write_pt0_runtime_summary(
    output_path: str,
    *,
    recorded_at: datetime | None = None,
    uat42_summary: Mapping[str, Any] | None = None,
    uat33_summary: Mapping[str, Any] | None = None,
    uat34_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    summary = build_pt0_runtime_summary(
        recorded_at=recorded_at,
        uat42_summary=uat42_summary,
        uat33_summary=uat33_summary,
        uat34_summary=uat34_summary,
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return summary


def validate_pt0_public_market_payload(payload: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    category = ExchangeEndpointCategory.PUBLIC_READ_ONLY
    policy = UAT42PublicMarketDataPolicy()
    return policy.validate_payload(dict(payload)) if category == ExchangeEndpointCategory.PUBLIC_READ_ONLY else (False, ())


def _paper_trade_rows(
    uat34_summary: Mapping[str, Any] | None,
    ledger: UAT42PaperEquityLedger,
) -> list[dict[str, Any]]:
    records = []
    for row in ((uat34_summary or {}).get("ledger_records") or []):
        records.append(
            {
                "time": (uat34_summary or {}).get("recorded_at_utc"),
                "symbol": row.get("symbol"),
                "route": row.get("route_id"),
                "source": "manual sandbox lifecycle probe",
                "status": row.get("lifecycle_status"),
                "side": row.get("side"),
                "price": row.get("limit_price"),
                "size": row.get("size"),
                "notional": row.get("estimated_notional"),
                "paper_equity_before": _decimal_to_string(ledger.initial_paper_equity),
                "paper_equity_after": _decimal_to_string(ledger.current_paper_equity),
                "realized_pnl": _decimal_to_string(ledger.realized_pnl),
                "unrealized_pnl": _decimal_to_string(ledger.unrealized_pnl),
                "sandbox_order_id": row.get("order_id"),
                "cancel_status": row.get("cancel_status"),
                "reconciliation_status": row.get("reconciliation_status"),
                "labels": {
                    "sandbox": True,
                    "not_live": True,
                    "paper_equity": True,
                    "not_real_capital": True,
                },
            }
        )
    return records


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _decimal_to_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value.normalize(), "f")
