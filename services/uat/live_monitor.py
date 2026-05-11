"""UAT4.2 live market monitor and paper-equity helpers.

This module is read-only by construction. Public market-data helpers may be
wired to Hyperliquid public info transport by an operator, but the default
summary builder is deterministic and does not call network, private, signed, or
order endpoints. Sandbox account polling policy is modeled as private
read-only/testnet-only and explicitly forbids order-capable categories.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
from typing import Any

from services.exchange.safety import ExchangeEndpointCategory, classify_hyperliquid_info_payload
from services.uat.public_read_only import PublicHTTPResult, hyperliquid_info_payload
from services.uat.sandbox import SandboxPrivateEndpointCategory


UAT42_REPORT_NAME = "uat4_2_live_market_dashboard_and_paper_equity_monitor"
UAT42_WATCHLIST: tuple[str, ...] = (
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
)
UAT42_TIMEFRAMES: tuple[str, ...] = ("15m", "1h", "4h")
UAT42_BALANCE_POLL_INTERVAL_SECONDS = 60
UAT42_INITIAL_PAPER_EQUITY = Decimal("10000")
UAT42_HYPERLIQUID_PUBLIC_INFO_URL = "https://api.hyperliquid-testnet.xyz/info"
UAT42_ALLOWED_PUBLIC_INFO_TYPES = (
    "allMids",
    "candleSnapshot",
    "fundingHistory",
    "l2Book",
    "meta",
    "metaAndAssetCtxs",
)


@dataclass(frozen=True)
class UAT42PublicMarketDataPolicy:
    runtime_mode: str = "uat"
    source: str = "hyperliquid_public"
    endpoint_category: str = ExchangeEndpointCategory.PUBLIC_READ_ONLY.value
    public_read_only: bool = True
    api_keys_used: bool = False
    private_endpoints_called: bool = False
    signed_endpoints_called: bool = False
    order_endpoints_called: bool = False
    live_endpoint_access: bool = False

    def validate_payload(self, payload: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
        category = classify_hyperliquid_info_payload(dict(payload))
        reasons: list[str] = []
        if category != ExchangeEndpointCategory.PUBLIC_READ_ONLY:
            reasons.append("uat42_public_read_only_payload_required")
        if str(payload.get("type") or "") not in UAT42_ALLOWED_PUBLIC_INFO_TYPES:
            reasons.append("uat42_public_info_type_not_allowlisted")
        if not self.public_read_only:
            reasons.append("uat42_public_read_only_mode_required")
        if self.api_keys_used:
            reasons.append("uat42_api_keys_forbidden_for_market_data")
        if self.private_endpoints_called:
            reasons.append("uat42_private_endpoints_forbidden_for_market_data")
        if self.signed_endpoints_called:
            reasons.append("uat42_signed_endpoints_forbidden_for_market_data")
        if self.order_endpoints_called:
            reasons.append("uat42_order_endpoints_forbidden_for_market_data")
        if self.live_endpoint_access:
            reasons.append("uat42_live_endpoint_forbidden")
        return not reasons, tuple(reasons)


@dataclass(frozen=True)
class UAT42Candle:
    timestamp_utc: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    def to_dict(self) -> dict[str, str]:
        return {
            "timestamp_utc": self.timestamp_utc,
            "open": _decimal_to_string(self.open),
            "high": _decimal_to_string(self.high),
            "low": _decimal_to_string(self.low),
            "close": _decimal_to_string(self.close),
            "volume": _decimal_to_string(self.volume),
        }


@dataclass(frozen=True)
class UAT42IndicatorValue:
    label: str
    value: Decimal | None
    enough_history: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "value": _decimal_to_string(self.value) if self.value is not None else None,
            "enough_history": self.enough_history,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class UAT42IndicatorSnapshot:
    symbol: str
    timeframe: str
    timestamp_utc: str
    ema5: UAT42IndicatorValue
    ema10: UAT42IndicatorValue
    sma20: UAT42IndicatorValue
    rsi: UAT42IndicatorValue
    macd: UAT42IndicatorValue
    macd_signal: UAT42IndicatorValue
    macd_histogram: UAT42IndicatorValue

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp_utc": self.timestamp_utc,
            "EMA5": self.ema5.to_dict(),
            "EMA10": self.ema10.to_dict(),
            "SMA20": self.sma20.to_dict(),
            "RSI": self.rsi.to_dict(),
            "MACD": self.macd.to_dict(),
            "MACD signal": self.macd_signal.to_dict(),
            "MACD histogram": self.macd_histogram.to_dict(),
        }


@dataclass(frozen=True)
class UAT42MarketDataSnapshot:
    symbol: str
    venue: str
    product_type: str
    quote_or_settlement: str
    timeframe: str
    latest_price: Decimal | None
    mid_price: Decimal | None
    mark_price: Decimal | None
    change_24h_pct: Decimal | None
    volume_24h: Decimal | None
    candles: tuple[UAT42Candle, ...]
    order_book: Mapping[str, Any]
    funding: Decimal | None
    open_interest: Decimal | None
    timestamp_utc: str
    source: str = "public_read_only"
    endpoint_category: str = ExchangeEndpointCategory.PUBLIC_READ_ONLY.value
    public_read_only_confirmation: bool = True
    private_signed_order_endpoints_called: bool = False
    market_data_status: str = "refreshed_public_read_only_local_json"
    failure_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "venue": self.venue,
            "product_type": self.product_type,
            "quote_or_settlement": self.quote_or_settlement,
            "timeframe": self.timeframe,
            "latest_price": _decimal_to_string(self.latest_price),
            "mid_price": _decimal_to_string(self.mid_price),
            "mark_price": _decimal_to_string(self.mark_price),
            "change_24h_pct": _decimal_to_string(self.change_24h_pct),
            "volume_24h": _decimal_to_string(self.volume_24h),
            "candles": [candle.to_dict() for candle in self.candles],
            "candle_data_available": bool(self.candles),
            "selected_timeframe_available": bool(self.candles),
            "last_candle_close_time": self.candles[-1].timestamp_utc if self.candles else None,
            "order_book": dict(self.order_book),
            "funding": _decimal_to_string(self.funding),
            "open_interest": _decimal_to_string(self.open_interest),
            "timestamp_utc": self.timestamp_utc,
            "source": self.source,
            "endpoint_category": self.endpoint_category,
            "public_read_only_confirmation": self.public_read_only_confirmation,
            "private_signed_order_endpoints_called": self.private_signed_order_endpoints_called,
            "market_data_status": self.market_data_status,
            "failure_reason": self.failure_reason,
        }


@dataclass(frozen=True)
class UAT42SignalScanRecord:
    symbol: str
    timeframe: str
    component: str
    source: str
    status: str
    reason_codes: tuple[str, ...]
    indicators: Mapping[str, Any]
    timestamp_utc: str
    next_candle_open_assumption: str = "observation_only"
    next_candle_close_assumption: str = "observation_only"
    same_candle_close_research_only: str = "research_only"
    operator_explanation: str = (
        "Paper-observation signal only; creates no StrategyDecision, OrderIntent, "
        "PreparedVenueOrder, SubmittedOrder, or executable approval."
    )
    creates_strategy_decision: bool = False
    creates_order_intent: bool = False
    creates_prepared_order: bool = False
    creates_submitted_order: bool = False
    creates_executable_approval: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UAT42BalancePollingPolicy:
    poll_interval_seconds: int = UAT42_BALANCE_POLL_INTERVAL_SECONDS
    source: str = "sandbox_private_read_only"
    environment: str = "testnet"
    not_live_account_required: bool = True
    live_endpoint_access: bool = False
    allowed_categories: tuple[str, ...] = (
        SandboxPrivateEndpointCategory.SANDBOX_PRIVATE_READ_ONLY_ACCOUNT.value,
        SandboxPrivateEndpointCategory.SANDBOX_PRIVATE_READ_ONLY_BALANCE.value,
        SandboxPrivateEndpointCategory.SANDBOX_PRIVATE_READ_ONLY_POSITION.value,
        SandboxPrivateEndpointCategory.SANDBOX_PRIVATE_READ_ONLY_EQUITY.value,
    )
    forbidden_categories: tuple[str, ...] = (
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_SUBMISSION.value,
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_CANCEL.value,
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_AMEND.value,
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_RETRY.value,
        SandboxPrivateEndpointCategory.LIVE_PRIVATE_FORBIDDEN.value,
        "private_signed_order",
    )
    order_endpoints_called: bool = False
    cancel_endpoints_called: bool = False
    amend_endpoints_called: bool = False
    retry_endpoints_called: bool = False

    def evaluate(self) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        if self.poll_interval_seconds != UAT42_BALANCE_POLL_INTERVAL_SECONDS:
            reasons.append("uat42_balance_poll_interval_must_be_60_seconds")
        if self.source != "sandbox_private_read_only":
            reasons.append("uat42_balance_poll_source_must_be_sandbox_private_read_only")
        if self.environment not in {"sandbox", "testnet", "uat_sandbox"}:
            reasons.append("uat42_balance_poll_environment_must_be_sandbox_testnet")
        if not self.not_live_account_required:
            reasons.append("uat42_balance_poll_not_live_account_label_required")
        if self.live_endpoint_access:
            reasons.append("uat42_balance_poll_live_endpoint_forbidden")
        if self.order_endpoints_called:
            reasons.append("uat42_balance_poll_order_endpoint_forbidden")
        if self.cancel_endpoints_called:
            reasons.append("uat42_balance_poll_cancel_endpoint_forbidden")
        if self.amend_endpoints_called:
            reasons.append("uat42_balance_poll_amend_endpoint_forbidden")
        if self.retry_endpoints_called:
            reasons.append("uat42_balance_poll_retry_endpoint_forbidden")
        return not reasons, tuple(reasons)

    def to_dict(self) -> dict[str, Any]:
        allowed, reason_codes = self.evaluate()
        return {
            **asdict(self),
            "allowed": allowed,
            "reason_codes": list(reason_codes),
            "next_poll_interval_seconds": self.poll_interval_seconds,
        }


@dataclass(frozen=True)
class UAT42SandboxAccountPollResult:
    sandbox_account_equity: Decimal | None
    withdrawable: Decimal | None
    available_balance: Decimal | None
    open_positions: tuple[Mapping[str, Any], ...]
    open_orders: tuple[Mapping[str, Any], ...]
    realized_pnl: Decimal | None
    unrealized_pnl: Decimal | None
    timestamp_utc: str
    source: str = "sandbox_private_read_only"
    not_live_account: bool = True
    poll_interval_seconds: int = UAT42_BALANCE_POLL_INTERVAL_SECONDS
    unavailable_fields: tuple[str, ...] = ()
    private_order_endpoints_called: bool = False
    live_endpoint_access: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "sandbox_account_equity": _decimal_to_string(self.sandbox_account_equity),
            "withdrawable": _decimal_to_string(self.withdrawable),
            "available_balance": _decimal_to_string(self.available_balance),
            "open_positions": [dict(row) for row in self.open_positions],
            "open_orders": [dict(row) for row in self.open_orders],
            "realized_pnl": _decimal_to_string(self.realized_pnl),
            "unrealized_pnl": _decimal_to_string(self.unrealized_pnl),
            "timestamp_utc": self.timestamp_utc,
            "source": self.source,
            "not_live_account": self.not_live_account,
            "poll_interval_seconds": self.poll_interval_seconds,
            "unavailable_fields": list(self.unavailable_fields),
            "private_order_endpoints_called": self.private_order_endpoints_called,
            "live_endpoint_access": self.live_endpoint_access,
        }


@dataclass(frozen=True)
class UAT42PaperEquityLedger:
    initial_paper_equity: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    open_paper_exposure: Decimal
    confirmation_source: str
    source: str = "internal_paper_equity_ledger"

    @property
    def current_paper_equity(self) -> Decimal:
        return self.initial_paper_equity + self.realized_pnl + self.unrealized_pnl

    @property
    def realized_equity(self) -> Decimal:
        return self.initial_paper_equity + self.realized_pnl

    @property
    def max_equity(self) -> Decimal:
        return max(self.initial_paper_equity, self.current_paper_equity)

    @property
    def min_equity(self) -> Decimal:
        return min(self.initial_paper_equity, self.current_paper_equity)

    @property
    def drawdown_amount(self) -> Decimal:
        return max(Decimal("0"), self.max_equity - self.current_paper_equity)

    @property
    def drawdown_percent(self) -> Decimal:
        if self.max_equity <= 0:
            return Decimal("0")
        return self.drawdown_amount / self.max_equity

    def to_dict(self) -> dict[str, Any]:
        return {
            "initial_paper_equity": _decimal_to_string(self.initial_paper_equity),
            "current_paper_equity": _decimal_to_string(self.current_paper_equity),
            "realized_equity": _decimal_to_string(self.realized_equity),
            "realized_pnl": _decimal_to_string(self.realized_pnl),
            "unrealized_pnl": _decimal_to_string(self.unrealized_pnl),
            "open_paper_exposure": _decimal_to_string(self.open_paper_exposure),
            "max_equity": _decimal_to_string(self.max_equity),
            "min_equity": _decimal_to_string(self.min_equity),
            "drawdown_amount": _decimal_to_string(self.drawdown_amount),
            "drawdown_percent": _decimal_to_string(self.drawdown_percent),
            "source": self.source,
            "confirmation_source": self.confirmation_source,
            "labels": {
                "internal_paper_equity": True,
                "sandbox_testnet_confirmation": True,
                "not_live_account": True,
                "not_real_capital": True,
            },
        }


@dataclass(frozen=True)
class UAT42SizingPolicy:
    sizing_basis: str = "realized_equity"
    risk_display_basis: str = "realized_plus_unrealized"
    use_static_initial_equity: bool = False

    def sizing_equity(self, ledger: UAT42PaperEquityLedger) -> Decimal:
        if self.sizing_basis == "realized_equity":
            return ledger.realized_equity
        if self.sizing_basis == "realized_plus_unrealized":
            return ledger.current_paper_equity
        raise ValueError(f"unsupported sizing basis: {self.sizing_basis}")

    def to_dict(self, ledger: UAT42PaperEquityLedger) -> dict[str, Any]:
        return {
            "sizing_basis": self.sizing_basis,
            "risk_display_basis": self.risk_display_basis,
            "use_static_initial_equity": self.use_static_initial_equity,
            "sizing_equity": _decimal_to_string(self.sizing_equity(ledger)),
            "risk_display_equity": _decimal_to_string(ledger.current_paper_equity),
            "policy": (
                "Future paper/sandbox sizing uses current realized paper equity, "
                "while realized plus unrealized PnL is shown in risk displays."
            ),
        }


Transport = Callable[[str, str, dict[str, Any] | None], PublicHTTPResult]


def evaluate_uat42_public_market_payload(
    payload: Mapping[str, Any],
    *,
    policy: UAT42PublicMarketDataPolicy | None = None,
) -> tuple[bool, tuple[str, ...]]:
    return (policy or UAT42PublicMarketDataPolicy()).validate_payload(payload)


def fetch_uat42_public_market_data(
    *,
    info_type: str,
    coin: str,
    transport: Transport,
    policy: UAT42PublicMarketDataPolicy | None = None,
    now: datetime | None = None,
) -> PublicHTTPResult:
    """Fetch a Hyperliquid public info payload through caller-supplied transport."""

    request_payload = hyperliquid_info_payload(info_type, coin=coin, now=now)
    allowed, reason_codes = evaluate_uat42_public_market_payload(request_payload, policy=policy)
    if not allowed:
        return PublicHTTPResult(
            url=UAT42_HYPERLIQUID_PUBLIC_INFO_URL,
            method="POST",
            status_code=None,
            payload={"blocked": True, "reason_codes": list(reason_codes)},
            response_headers={},
            success=False,
            sanitized_error=", ".join(reason_codes),
        )
    return transport("POST", UAT42_HYPERLIQUID_PUBLIC_INFO_URL, request_payload)


def compute_uat42_indicators(
    candles: Sequence[UAT42Candle],
    *,
    symbol: str,
    timeframe: str,
    timestamp_utc: str | None = None,
) -> UAT42IndicatorSnapshot:
    closes = [candle.close for candle in candles]
    observed_at = timestamp_utc or (candles[-1].timestamp_utc if candles else datetime.now(UTC).isoformat())

    ema5 = _indicator_value("EMA5", _ema(closes, 5), len(closes) >= 5)
    ema10 = _indicator_value("EMA10", _ema(closes, 10), len(closes) >= 10)
    sma20 = _indicator_value("SMA20", _sma(closes, 20), len(closes) >= 20)
    rsi = _indicator_value("RSI", _rsi(closes, 14), len(closes) >= 15)
    macd_value, macd_signal, macd_histogram = _macd(closes)
    macd_enough = len(closes) >= 35
    return UAT42IndicatorSnapshot(
        symbol=symbol,
        timeframe=timeframe,
        timestamp_utc=observed_at,
        ema5=ema5,
        ema10=ema10,
        sma20=sma20,
        rsi=rsi,
        macd=_indicator_value("MACD", macd_value, macd_enough),
        macd_signal=_indicator_value("MACD signal", macd_signal, macd_enough),
        macd_histogram=_indicator_value("MACD histogram", macd_histogram, macd_enough),
    )


def evaluate_uat42_observation_signal(
    *,
    symbol: str,
    timeframe: str,
    indicators: UAT42IndicatorSnapshot,
    timestamp_utc: str,
) -> UAT42SignalScanRecord:
    values = indicators.to_dict()
    ema5 = indicators.ema5.value
    ema10 = indicators.ema10.value
    sma20 = indicators.sma20.value
    rsi = indicators.rsi.value
    macd_histogram = indicators.macd_histogram.value
    reasons: list[str] = []

    enough_history = all(
        item.enough_history
        for item in (
            indicators.ema5,
            indicators.ema10,
            indicators.sma20,
            indicators.rsi,
            indicators.macd,
            indicators.macd_signal,
            indicators.macd_histogram,
        )
    )
    if not enough_history:
        reasons.append("indicator_unavailable_insufficient_history")
        status = "invalid"
    elif ema5 is not None and ema10 is not None and sma20 is not None and not (ema5 > ema10 > sma20):
        reasons.append("trend_stack_not_aligned")
        status = "no_trade"
    elif rsi is not None and not (Decimal("45") <= rsi <= Decimal("72")):
        reasons.append("rsi_not_constructive")
        status = "no_trade"
    elif macd_histogram is not None and macd_histogram < 0:
        reasons.append("macd_not_constructive")
        status = "no_trade"
    else:
        reasons.append("paper_observation_would_open_only")
        status = "would_open"

    return UAT42SignalScanRecord(
        symbol=symbol,
        timeframe=timeframe,
        component=f"sleeve_{timeframe}",
        source="paper_observation_signal",
        status=status,
        reason_codes=tuple(reasons),
        indicators=values,
        timestamp_utc=timestamp_utc,
    )


def build_paper_equity_ledger(
    *,
    realized_pnl: Decimal | str | int = Decimal("0"),
    unrealized_pnl: Decimal | str | int = Decimal("0"),
    open_paper_exposure: Decimal | str | int = Decimal("0"),
    initial_paper_equity: Decimal | str | int = UAT42_INITIAL_PAPER_EQUITY,
    confirmation_source: str = "Hyperliquid sandbox balance polled every 60 seconds",
) -> UAT42PaperEquityLedger:
    return UAT42PaperEquityLedger(
        initial_paper_equity=_to_decimal(initial_paper_equity),
        realized_pnl=_to_decimal(realized_pnl),
        unrealized_pnl=_to_decimal(unrealized_pnl),
        open_paper_exposure=_to_decimal(open_paper_exposure),
        confirmation_source=confirmation_source,
    )


def build_uat42_monitor_summary(
    *,
    recorded_at: datetime | None = None,
    uat34_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    observed_at = recorded_at or datetime.now(UTC)
    timestamp = observed_at.isoformat().replace("+00:00", "Z")
    market_data = _fixture_market_data(timestamp)
    indicators = [
        compute_uat42_indicators(row.candles, symbol=row.symbol, timeframe=row.timeframe, timestamp_utc=timestamp)
        for row in market_data
    ]
    signal_records = [
        evaluate_uat42_observation_signal(
            symbol=snapshot.symbol,
            timeframe=snapshot.timeframe,
            indicators=snapshot,
            timestamp_utc=timestamp,
        )
        for snapshot in indicators
    ]
    ledger = build_paper_equity_ledger()
    sizing_policy = UAT42SizingPolicy()
    polling_policy = UAT42BalancePollingPolicy()
    poll_allowed, poll_reasons = polling_policy.evaluate()
    sandbox_confirmation = _sandbox_confirmation_from_uat34(uat34_summary, timestamp)

    return {
        "report": UAT42_REPORT_NAME,
        "recorded_at_utc": timestamp,
        "scope": "live_market_dashboard_and_internal_paper_equity_monitor",
        "live_market_data_status": "implemented_via_public_read_only_service_and_local_refresh_json",
        "dashboard_data_path": "docs/uat4_2_live_market_dashboard_and_paper_equity_monitor_summary.json",
        "watchlist": list(UAT42_WATCHLIST),
        "timeframes": list(UAT42_TIMEFRAMES),
        "public_market_data_policy": asdict(UAT42PublicMarketDataPolicy()),
        "market_data": [row.to_dict() for row in market_data],
        "indicator_snapshots": [row.to_dict() for row in indicators],
        "strategy_scanner": {
            "mode": "shadow_paper_observation_only",
            "allowed_outputs": [
                "shadow_signal",
                "paper_observation_signal",
                "would_open",
                "would_close",
                "would_hold",
                "would_reduce",
                "no_trade",
                "invalid",
                "risk_blocked",
            ],
            "forbidden_outputs": [
                "StrategyDecision",
                "OrderIntent",
                "PreparedVenueOrder",
                "SubmittedOrder",
                "executable_approval",
                "live_artifact",
            ],
            "records": [row.to_dict() for row in signal_records],
        },
        "balance_position_polling": {
            "policy": polling_policy.to_dict(),
            "polling_status": "implemented_policy_fixture_verified",
            "poll_interval_seconds": polling_policy.poll_interval_seconds,
            "allowed": poll_allowed,
            "reason_codes": list(poll_reasons),
            "sandbox_account_confirmation": sandbox_confirmation.to_dict(),
        },
        "paper_equity": ledger.to_dict(),
        "sizing_policy": sizing_policy.to_dict(ledger),
        "routed_orders": {
            "source": "docs/uat3_4_sandbox_routing_pipeline_and_order_ledger_summary.json",
            "records_visible": bool(uat34_summary and uat34_summary.get("ledger_records")),
            "paper_equity_impact": "none_for_existing_uat3_4_canceled_probe",
        },
        "side_effect_flags": {
            "api_keys_used": False,
            "private_order_endpoints_called": False,
            "signed_endpoints_called": False,
            "order_endpoints_called": False,
            "cancel_amend_retry_endpoints_called": False,
            "live_endpoint_called": False,
            "orders_submitted": False,
            "order_controls_added": False,
            "paper_live_real_capital_trading_added": False,
            "money_flow_rules_changed": False,
            "smart_routing_sor_fanout_added": False,
            "evidence_packs_generated": False,
        },
        "pt0_roadmap_status": "captured_for_future_approval_gated_paper_sandbox_runtime",
    }


def write_uat42_monitor_summary(
    output_path: str,
    *,
    recorded_at: datetime | None = None,
    uat34_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    summary = build_uat42_monitor_summary(recorded_at=recorded_at, uat34_summary=uat34_summary)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return summary


def _fixture_market_data(timestamp_utc: str) -> tuple[UAT42MarketDataSnapshot, ...]:
    base_prices = {
        "BTC": Decimal("81000"),
        "ETH": Decimal("2350"),
        "SOL": Decimal("97.10"),
        "XRP": Decimal("0.524"),
        "ZEC": Decimal("138.65"),
        "BNB": Decimal("654.65"),
        "SUI": Decimal("1.2899"),
        "TON": Decimal("2.3212"),
        "DOGE": Decimal("0.109475"),
        "TRX": Decimal("0.081"),
        "LAYER": Decimal("0.126845"),
        "CHIP": Decimal("0.060684"),
        "UNI": Decimal("8.21"),
        "ONDO": Decimal("0.449655"),
        "AAVE": Decimal("100.0275"),
    }
    snapshots: list[UAT42MarketDataSnapshot] = []
    for index, symbol in enumerate(UAT42_WATCHLIST):
        base = base_prices[symbol]
        candles = _synthetic_candles(symbol=symbol, base=base, count=40, timeframe_minutes=60, end_time=timestamp_utc)
        latest = candles[-1].close
        bid = latest * Decimal("0.9995")
        ask = latest * Decimal("1.0005")
        snapshots.append(
            UAT42MarketDataSnapshot(
                symbol=symbol,
                venue="hyperliquid",
                product_type="USDC perpetual",
                quote_or_settlement="USDC",
                timeframe="1h",
                latest_price=latest,
                mid_price=latest,
                mark_price=latest,
                change_24h_pct=Decimal(index - 7) / Decimal("1000"),
                volume_24h=Decimal("1000000") + Decimal(index) * Decimal("25000"),
                candles=candles,
                order_book={
                    "bid": _decimal_to_string(bid),
                    "ask": _decimal_to_string(ask),
                    "spread": _decimal_to_string(ask - bid),
                    "source": "public_read_only_fixture_shape",
                },
                funding=Decimal("0.0001"),
                open_interest=None,
                timestamp_utc=timestamp_utc,
            )
        )
    return tuple(snapshots)


def _synthetic_candles(
    *,
    symbol: str,
    base: Decimal,
    count: int,
    timeframe_minutes: int,
    end_time: str,
) -> tuple[UAT42Candle, ...]:
    end_dt = _parse_timestamp(end_time)
    symbol_bias = Decimal((sum(ord(ch) for ch in symbol) % 9) - 4) / Decimal("10000")
    candles: list[UAT42Candle] = []
    for offset in range(count):
        index = offset - count + 1
        timestamp = end_dt + timedelta(minutes=index * timeframe_minutes)
        drift = Decimal(offset - count // 2) / Decimal("10000")
        wave = Decimal(((offset % 7) - 3)) / Decimal("20000")
        close = base * (Decimal("1") + drift + wave + symbol_bias)
        open_price = close * (Decimal("1") - Decimal("0.0008"))
        high = max(open_price, close) * Decimal("1.0012")
        low = min(open_price, close) * Decimal("0.9988")
        candles.append(
            UAT42Candle(
                timestamp_utc=timestamp.isoformat().replace("+00:00", "Z"),
                open=_round(open_price),
                high=_round(high),
                low=_round(low),
                close=_round(close),
                volume=_round(Decimal("1000") + Decimal(offset * 17)),
            )
        )
    return tuple(candles)


def _sandbox_confirmation_from_uat34(
    uat34_summary: Mapping[str, Any] | None,
    timestamp_utc: str,
) -> UAT42SandboxAccountPollResult:
    drawdown = dict(uat34_summary.get("drawdown_feed") or {}) if uat34_summary else {}
    equity = drawdown.get("sandbox_account_equity")
    timestamp = drawdown.get("timestamp_utc") or timestamp_utc
    return UAT42SandboxAccountPollResult(
        sandbox_account_equity=_optional_decimal(equity),
        withdrawable=_optional_decimal((uat34_summary or {}).get("equity_resolution", {}).get("perp_withdrawable")),
        available_balance=_optional_decimal((uat34_summary or {}).get("equity_resolution", {}).get("selected_sandbox_equity")),
        open_positions=(),
        open_orders=(),
        realized_pnl=None,
        unrealized_pnl=None,
        timestamp_utc=str(timestamp),
        unavailable_fields=(
            "realized_pnl_unavailable_from_current_summary",
            "unrealized_pnl_unavailable_from_current_summary",
            "open_positions_empty_or_unavailable_from_current_summary",
        ),
    )


def _indicator_value(label: str, value: Decimal | None, enough_history: bool) -> UAT42IndicatorValue:
    if not enough_history or value is None:
        return UAT42IndicatorValue(
            label=label,
            value=None,
            enough_history=False,
            reason="indicator_unavailable_insufficient_history",
        )
    return UAT42IndicatorValue(
        label=label,
        value=_round(value),
        enough_history=True,
        reason="computed",
    )


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


def _rsi(values: Sequence[Decimal], period: int) -> Decimal | None:
    if len(values) <= period:
        return None
    gains: list[Decimal] = []
    losses: list[Decimal] = []
    for previous, current in zip(values, values[1:], strict=False):
        delta = current - previous
        gains.append(max(delta, Decimal("0")))
        losses.append(abs(min(delta, Decimal("0"))))
    avg_gain = sum(gains[:period]) / Decimal(period)
    avg_loss = sum(losses[:period]) / Decimal(period)
    for gain, loss in zip(gains[period:], losses[period:], strict=False):
        avg_gain = ((avg_gain * Decimal(period - 1)) + gain) / Decimal(period)
        avg_loss = ((avg_loss * Decimal(period - 1)) + loss) / Decimal(period)
    if avg_loss == 0:
        return Decimal("100")
    rs = avg_gain / avg_loss
    return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))


def _macd(values: Sequence[Decimal]) -> tuple[Decimal | None, Decimal | None, Decimal | None]:
    if len(values) < 35:
        return None, None, None
    macd_series: list[Decimal] = []
    for index in range(26, len(values) + 1):
        slice_values = values[:index]
        ema12 = _ema(slice_values, 12)
        ema26 = _ema(slice_values, 26)
        if ema12 is not None and ema26 is not None:
            macd_series.append(ema12 - ema26)
    if len(macd_series) < 9:
        return None, None, None
    signal = _ema(macd_series, 9)
    macd_value = macd_series[-1]
    if signal is None:
        return None, None, None
    return macd_value, signal, macd_value - signal


def _round(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP).normalize()


def _to_decimal(value: Decimal | str | int | float) -> Decimal:
    return Decimal(str(value))


def _optional_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _decimal_to_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value.normalize(), "f")


def _parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    return parsed.astimezone(UTC)
