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


PT_RT1_MAINNET_INFO_URL = "https://api.hyperliquid.xyz/info"
PT_RT1_TESTNET_INFO_URL = "https://api.hyperliquid-testnet.xyz/info"
PT_RT1_EXACT_TESTNET_PROBE_APPROVAL = (
    "I APPROVE PT-RT1 TESTNET PLUMBING PROBES ONLY. HYPERLIQUID TESTNET ONLY. "
    "POST-ONLY UNDER 10 USDC DEFAULT NOTIONAL. CANCEL/RECONCILE REQUIRED. "
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
RUNTIME_STATE_PATHS = {
    "state": "reports/paper_runtime/pt_rt1_state.json",
    "decisions": "reports/paper_runtime/pt_rt1_decisions.jsonl",
    "trades": "reports/paper_runtime/pt_rt1_trades.jsonl",
    "equity_curves": "reports/paper_runtime/pt_rt1_equity_curves.json",
    "data_health": "reports/paper_runtime/pt_rt1_data_health.json",
    "testnet_probe_audit": "reports/paper_runtime/pt_rt1_testnet_probe_audit.jsonl",
}
SUPPORTED_CANONICAL_SYMBOLS = ("BTC", "ETH", "SOL", "XRP", "DOGE", "HYPE", "BNB", "SUI", "AVAX")
STABLECOIN_SYMBOLS = {"USDT", "USDC", "DAI", "FDUSD", "TUSD", "USDE", "USDS"}


class DataHealth(StrEnum):
    HEALTHY = "healthy"
    STALE = "stale"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class LaneRole(StrEnum):
    CONTROL = "control_lane"
    CANDIDATE = "evidence_only_candidate_lane"
    REFERENCE = "mf_orig_evidence_only_reference_lane"


@dataclass(frozen=True)
class StrategyLaneConfig:
    lane_id: str
    strategy_id: str
    role: LaneRole
    label: str
    initial_equity: Decimal = Decimal("10000")
    allocation_pct: Decimal = Decimal("1")
    fill_model: str = "next_candle_open"
    production_approved: bool = False
    paper_runtime_approved_as_production: bool = False
    live_trading_approved: bool = False
    reason_codes: tuple[str, ...] = ()


PT_RT1_STRATEGY_LANES: tuple[StrategyLaneConfig, ...] = (
    StrategyLaneConfig(
        lane_id="lane_control_money_flow_v1_2_baseline",
        strategy_id="money_flow_v1_2_baseline",
        role=LaneRole.CONTROL,
        label="Money Flow v1.2 baseline observation lane",
        reason_codes=("production_derived_rules_unchanged", "not_production_approval"),
    ),
    StrategyLaneConfig(
        lane_id="lane_candidate_avoid_low_rolling_range_50",
        strategy_id="avoid_low_rolling_range_50",
        role=LaneRole.CANDIDATE,
        label="avoid_low_rolling_range_50 evidence-only candidate lane",
        reason_codes=("evidence_only_candidate_lane", "not_production_approved"),
    ),
    StrategyLaneConfig(
        lane_id="lane_candidate_avoid_low_rolling_range_20",
        strategy_id="avoid_low_rolling_range_20",
        role=LaneRole.CANDIDATE,
        label="avoid_low_rolling_range_20 evidence-only candidate lane",
        reason_codes=("evidence_only_candidate_lane", "not_production_approved"),
    ),
    StrategyLaneConfig(
        lane_id="lane_reference_mf_orig_breakout_resistance_full_equity",
        strategy_id="mf_orig_1d_stage2_breakout_resistance_full_equity",
        role=LaneRole.REFERENCE,
        label="MF-ORIG evidence-only reference lane",
        reason_codes=("mf_orig_reference_lane", "mf_orig_reference_lane_1d_primary", "not_production_approved"),
    ),
)


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
    asset_id: int | None
    szDecimals: int | None
    precision_status: str
    supported_by_venue: bool
    data_health: DataHealth
    scanner_eligible: bool
    reason_codes: tuple[str, ...]


def resolve_top20_universe(
    requested_symbols: Sequence[str],
    *,
    hyperliquid_meta: Sequence[Mapping[str, Any]],
    mids: Mapping[str, Any] | None = None,
) -> tuple[ScannerUniverseRow, ...]:
    meta_by_symbol = {str(asset.get("name", "")).upper(): (index, asset) for index, asset in enumerate(hyperliquid_meta)}
    mids = {str(key).upper(): value for key, value in (mids or {}).items()}
    rows: list[ScannerUniverseRow] = []
    for requested in requested_symbols:
        symbol = requested.upper()
        reasons: list[str] = []
        if symbol in STABLECOIN_SYMBOLS:
            reasons.append("stablecoin_excluded")
        if symbol == "SHIB" or symbol == "KSHIB":
            venue_symbol = "kSHIB"
            reasons.append("venue_symbol_unit_semantics_deferred")
        else:
            venue_symbol = symbol
        asset_tuple = meta_by_symbol.get(str(venue_symbol).upper())
        asset_id: int | None = None
        sz_decimals: int | None = None
        if asset_tuple is None:
            reasons.append("unsupported_by_hyperliquid")
        else:
            asset_id, asset = asset_tuple
            try:
                sz_decimals = int(asset["szDecimals"])
            except (KeyError, TypeError, ValueError):
                reasons.append("precision_missing")
        mid_value = mids.get(str(venue_symbol).upper())
        if mid_value is None:
            reasons.append("market_data_unavailable")
        else:
            try:
                if _dec(mid_value, field_name="mid_price") <= 0:
                    reasons.append("market_data_unavailable")
            except ValueError:
                reasons.append("market_data_unavailable")
        if asset_tuple is not None and "unsupported_by_hyperliquid" not in reasons:
            reasons.append("supported_by_hyperliquid")
        eligible = (
            asset_tuple is not None
            and sz_decimals is not None
            and mid_value is not None
            and "stablecoin_excluded" not in reasons
            and "venue_symbol_unit_semantics_deferred" not in reasons
            and "market_data_unavailable" not in reasons
        )
        rows.append(
            ScannerUniverseRow(
                requested_symbol=symbol,
                resolved_venue_symbol=venue_symbol if asset_tuple is not None else None,
                asset_id=asset_id,
                szDecimals=sz_decimals,
                precision_status="precision_ready" if sz_decimals is not None else "precision_missing",
                supported_by_venue=asset_tuple is not None,
                data_health=DataHealth.HEALTHY if mid_value is not None and eligible else DataHealth.UNAVAILABLE,
                scanner_eligible=eligible,
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
    quantity: Decimal = Decimal("0.001")
    notional: Decimal = Decimal("1")
    scanner_signal_eligible: bool = True
    daily_probe_count: int = 0
    daily_cap: int = 1
    notional_cap: Decimal = Decimal("10")
    post_only: bool = True
    tif: str = "Alo"
    submit_lease_acquired: bool = True
    artifact_label: str = "pt_rt1_testnet_only"
    unknown_or_open_probe_state: bool = False


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
    notional_cap_default: Decimal = Decimal("10")
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
        if not candidate.scanner_signal_eligible:
            reasons.append("scanner_signal_not_eligible")
        if candidate.daily_probe_count >= candidate.daily_cap:
            reasons.append("testnet_daily_probe_cap_exceeded")
        if candidate.notional >= candidate.notional_cap:
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
                "cancel_reconcile_required": True,
                "testnet_fills_update_strategy_pnl": False,
                "strategy_pnl_updated": False,
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


def build_pt_rt1_summary() -> dict[str, Any]:
    lanes = [
        {
            **asdict(lane),
            "initial_equity": str(lane.initial_equity),
            "allocation_pct": str(lane.allocation_pct),
            "role": str(lane.role),
        }
        for lane in PT_RT1_STRATEGY_LANES
    ]
    return {
        "phase": "PT-RT1",
        "report": "pt_rt1_real_time_paper_observation_and_testnet_plumbing",
        "status": "implemented",
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
        "symbols": list(SUPPORTED_CANONICAL_SYMBOLS),
        "timeframes": list(TIMEFRAME_DURATIONS),
        "scanner_universe": [
            {
                "requested_symbol": symbol,
                "resolved_venue_symbol": symbol,
                "supported_by_venue": True,
                "data_health": "pending_runtime_refresh",
                "scanner_eligible": True,
                "reason_codes": ["supported_by_hyperliquid", "runtime_market_data_health_pending"],
            }
            for symbol in SUPPORTED_CANONICAL_SYMBOLS
        ]
        + [
            {
                "requested_symbol": "SHIB",
                "resolved_venue_symbol": "kSHIB",
                "supported_by_venue": False,
                "data_health": "unavailable",
                "scanner_eligible": False,
                "reason_codes": ["venue_symbol_unit_semantics_deferred"],
            }
        ],
        "market_data_health": [
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "source": "Hyperliquid public mainnet",
                "status": "pending_runtime_refresh",
                "fully_closed_candle_status": "pending_runtime_refresh",
                "last_update_utc": None,
                "reason_codes": ["runtime_not_started"],
            }
            for symbol in SUPPORTED_CANONICAL_SYMBOLS
            for timeframe in TIMEFRAME_DURATIONS
        ],
        "strategy_lanes": lanes,
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
        "testnet_probe_policy": {
            "PT_RT1_TESTNET_PROBES_ENABLED": False,
            "PT_RT1_TESTNET_DAILY_PROBE_CAP": 1,
            "PT_RT1_TESTNET_PROBE_NOTIONAL_CAP": "10",
            "PT_RT1_TESTNET_KILL_SWITCH": True,
            "default_blocks_probes": True,
            "order_type": "post_only_limit",
            "tif": "Alo",
        },
        "dashboard_status": {
            "view": "Paper Observation",
            "status": "implemented",
            "date_filters": "display-only filter; not canonical evidence; not backend replay",
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
        },
    }


def ensure_runtime_state_directory() -> Path:
    path = Path(RUNTIME_STATE_PATHS["state"]).parent
    path.mkdir(parents=True, exist_ok=True)
    return path
