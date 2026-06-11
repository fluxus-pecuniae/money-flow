"""FUND-EV1 — delta-neutral perpetual funding-carry evidence layer.

RESEARCH / EVIDENCE ONLY. Tests the STRUCTURAL, NON-PREDICTIVE edge: harvest
Hyperliquid perp funding while hedged delta-neutral on the SAME venue (short
HL perp + long HL spot in equal notional), so the funding stream is earned
regardless of price direction. The honest question: does net funding AFTER
ALL COSTS stay positive out-of-sample and through the tail (crash days,
funding inversions, basis dislocations) — or is it pennies in front of a
steamroller? Either answer is valuable; the gate never forces a positive.

Routed under ``strategy_type == "funding_carry"`` by
``services.strategy_validation.strategy_types`` with its OWN gate (net carry
positive OOS post-cost, non-bull-regime robust, leave-one-out robust, tail
drawdown inside a documented limit). It must never be judged by the
per-symbol breadth gate, the selection random-benchmark gate, or the TSMOM
buy-hold gate, and vice versa.

Construction (Must 1):
  - Single-venue Hyperliquid book per asset: SHORT the perp and LONG the
    spot pair in equal notional (positive-funding side). ``flip_sides`` mode
    also takes the mirrored book (LONG perp + SHORT spot) when trailing
    funding is negative — that variant ASSUMES SPOT BORROW IS AVAILABLE,
    which HL spot does not natively provide; borrow cost is NOT modeled, so
    flip-side rows are upper bounds (documented).
  - Selection/tilt: at each rebalance, rank assets by trailing
    ``funding_lookback_days``-day mean funding (causal: slots <= t only) and
    hold up to ``top_k`` names on the collectable side, equal notional
    slots = ``leg_notional_fraction`` * equity / top_k per leg.
  - Funding accrual: Hyperliquid funding is hourly; the committed snapshot
    aggregates hourly rates into daily candle slots. Daily accrual is
    ``-perp_qty * perp_close * daily_rate_sum`` (positive rate: longs pay
    shorts, so the short perp RECEIVES). Applying the day's summed rate at
    the daily close mark is a documented approximation of hour-by-hour marks.
  - Costs (modeled honestly): EXEC-EV1 depth-aware friction on EVERY fill of
    BOTH legs (perp leg at its liquidity tier; the HL spot leg always at the
    widest mid-alt tier — spot books are thinner), scenario fee_bps on both
    legs, rebalance trades to stay neutral as prices move, and the
    spot/perp basis drift is marked to market (both legs at their own
    venue's closes).

Tail risk (Must 2): the classic failure is a "neutral" book that is not
neutral during a gap. The evidence run stresses: residual-delta tracking
(discrete rebalances leave drift), a spot-leg-lag run (the hedge leg fills
one candle late around every rebalance — legged execution in fast markets),
stress-scenario friction, worst-day PnL, and the funding-inversion regime.

Pure and deterministic: Decimal arithmetic, no I/O, no network.
"""

from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Sequence

from services.execution_quality.exec_ev1 import (
    BPS,
    DepthAwareScenario,
    candle_dollar_volume,
    depth_aware_execution_price,
    fill_friction_bps,
)

try:  # pragma: no cover - exercised implicitly by both import contexts
    from services.strategy_validation import strategy_types as _strategy_types
    from services.strategy_validation import tsmom_ev1 as _tsmom_ev1
except Exception:  # heavy package __init__ unavailable outside pytest
    import importlib.util
    import sys
    from pathlib import Path

    def _load_sibling(filename: str, alias: str):
        if alias in sys.modules:
            return sys.modules[alias]
        module_path = Path(__file__).resolve().with_name(filename)
        spec = importlib.util.spec_from_file_location(alias, module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"unable_to_load_module:{module_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[alias] = module
        spec.loader.exec_module(module)
        return module

    _strategy_types = _load_sibling("strategy_types.py", "fund_ev1_strategy_types")
    _tsmom_ev1 = _load_sibling("tsmom_ev1.py", "fund_ev1_tsmom_ev1")

# Reused TSMOM-EV1 plumbing: signed perp-style position fills, curve stats,
# the SV2.2 dataset adapter (via sel_ev1), and Decimal money rounding.
_Position = _tsmom_ev1._Position
_apply_fill = _tsmom_ev1._apply_fill
curve_stats = _tsmom_ev1.curve_stats
dataset_from_sv22_payload = _tsmom_ev1.dataset_from_sv22_payload
_money = _tsmom_ev1._money
ANNUALIZATION_DAYS = _tsmom_ev1.ANNUALIZATION_DAYS

STRATEGY_TYPE_FUNDING_CARRY = _strategy_types.STRATEGY_TYPE_FUNDING_CARRY
FUNDING_CARRY_GATE_ID = _strategy_types.FUNDING_CARRY_GATE_ID
StrategyTypeRoutingError = _strategy_types.StrategyTypeRoutingError
ensure_gate_applies = _strategy_types.ensure_gate_applies

PHASE = "FUND-EV1"
STARTING_EQUITY = Decimal("10000")

# Carry universe (documented): the three liquid majors with HL spot via Unit
# plus HYPE (HL-native spot, the most liquid HL spot pair). The aligned
# window is limited by the YOUNGEST spot listing (USOL 2025-05-10); next HL
# spot names (UFART/UPUMP/...) are excluded as thin meme-tier liquidity.
CARRY_UNIVERSE = ("BTC", "ETH", "HYPE", "SOL")
SPOT_PAIR_BY_SYMBOL = {
    "BTC": "UBTC/USDC",
    "ETH": "UETH/USDC",
    "SOL": "USOL/USDC",
    "HYPE": "HYPE/USDC",
}

# Bounded grid (Must 1): 2 modes x 2 cadences x 2 universe sizes = 8.
CARRY_MODES = ("collect_only", "flip_sides")
REBALANCE_CADENCES_DAYS = (7, 14)
TOP_K_CHOICES = (2, 4)
FUNDING_LOOKBACK_DAYS = 7
CARRY_TIMEFRAME = "1d"

# Sizing: half the 10k account per leg side, split across top_k slots. The
# other half is unencumbered (perp margin at ~1x effective leverage — far
# from liquidation; liquidation mechanics are NOT modeled, documented).
LEG_NOTIONAL_FRACTION = Decimal("0.5")
MIN_TRADE_NOTIONAL_FRACTION = Decimal("0.005")

# The spot legs are always priced at the WIDEST EXEC-EV1 liquidity tier
# (mid-alt, 5 bps half-spread) regardless of the perp tier: HL spot books
# are far thinner than the matching perp books. Achieved by suffixing the
# friction symbol so the tier lookup falls through to the conservative
# default.
SPOT_FRICTION_SUFFIX = "_SPOT"

# Tail limits (Must 2/3, documented): a carry book earning single-digit
# annual funding cannot justify deep drawdowns. OOS max drawdown must stay
# inside MAX_OOS_DRAWDOWN_PCT under the conservative gate scenario, and the
# stressed run (stress friction + spot leg lagging one candle) must stay
# inside MAX_STRESSED_DRAWDOWN_PCT over the full window.
MAX_OOS_DRAWDOWN_PCT = Decimal("5")
MAX_STRESSED_DRAWDOWN_PCT = Decimal("8")

# Regime classification for the not-bull-only check: BTC trailing 90d perp
# return at each decision close (point-in-time), bear < -10%, bull > +10%.
REGIME_TRAILING_DAYS = 90
REGIME_BAND = Decimal("0.10")

MIN_OOS_DAYS = 90

VERDICT_PASS = "carry_survives_costs_and_tail_oos"
VERDICT_FAIL = "carry_does_not_survive_costs_and_tail_oos"


@dataclass(frozen=True, slots=True)
class FundingCarryConfig:
    config_id: str
    strategy_type: str
    mode: str  # collect_only | flip_sides
    rebalance_interval_days: int
    top_k: int
    funding_lookback_days: int = FUNDING_LOOKBACK_DAYS
    leg_notional_fraction: Decimal = LEG_NOTIONAL_FRACTION
    spot_leg_lag_days: int = 0  # tail stress: hedge leg fills one candle late
    timeframe: str = CARRY_TIMEFRAME


def generate_funding_carry_configs() -> list[FundingCarryConfig]:
    """The full bounded grid; parameters are chosen on the train split only."""
    configs: list[FundingCarryConfig] = []
    for mode in CARRY_MODES:
        for cadence in REBALANCE_CADENCES_DAYS:
            for top_k in TOP_K_CHOICES:
                configs.append(
                    FundingCarryConfig(
                        config_id=f"fund_ev1_{mode}_cad{cadence}_top{top_k}_1d",
                        strategy_type=STRATEGY_TYPE_FUNDING_CARRY,
                        mode=mode,
                        rebalance_interval_days=cadence,
                        top_k=top_k,
                    )
                )
    return configs


# ---------------------------------------------------------------------------
# Universe: aligned perp + spot + funding view (Must 1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CarryAsset:
    """One asset's three aligned inputs (all keyed by daily candle CLOSE)."""

    symbol: str
    perp: Any  # goal_strat1 Dataset (SV2.2 perp candles)
    spot: Any  # goal_strat1 Dataset (HL spot candles)
    funding_by_close: dict[datetime, Decimal]  # daily funding-rate sums
    funding_hours_by_close: dict[datetime, int]


class CarryUniverse:
    """Aligned timeline where EVERY asset has a perp candle, a spot candle,
    and a full 24-hour funding slot at the same daily close."""

    def __init__(self, assets: Sequence[CarryAsset]) -> None:
        self.assets: dict[str, CarryAsset] = {a.symbol: a for a in assets}
        self.symbols: tuple[str, ...] = tuple(sorted(self.assets))
        self.perp_index: dict[str, dict[datetime, int]] = {}
        self.spot_index: dict[str, dict[datetime, int]] = {}
        self.perp_candle_dicts: dict[str, list[dict[str, Any]]] = {}
        self.spot_candle_dicts: dict[str, list[dict[str, Any]]] = {}
        for symbol, asset in self.assets.items():
            self.perp_index[symbol] = {
                c.timestamp: i for i, c in enumerate(asset.perp.candles)
            }
            self.spot_index[symbol] = {
                c.timestamp: i for i, c in enumerate(asset.spot.candles)
            }
            self.perp_candle_dicts[symbol] = [
                {"open": str(c.open), "high": str(c.high), "low": str(c.low),
                 "close": str(c.close), "volume": str(c.volume)}
                for c in asset.perp.candles
            ]
            self.spot_candle_dicts[symbol] = [
                {"open": str(c.open), "high": str(c.high), "low": str(c.low),
                 "close": str(c.close), "volume": str(c.volume)}
                for c in asset.spot.candles
            ]
        all_times = sorted(
            {c.timestamp for a in assets for c in a.perp.candles}
        )
        self.timeline: tuple[datetime, ...] = tuple(
            t
            for t in all_times
            if all(
                t in self.perp_index[s]
                and t in self.spot_index[s]
                and self.assets[s].funding_hours_by_close.get(t) == 24
                for s in self.symbols
            )
        )
        # Sorted funding-slot times per symbol for causal trailing lookups.
        self.funding_times: dict[str, list[datetime]] = {
            s: sorted(self.assets[s].funding_by_close) for s in self.symbols
        }


def funding_maps_from_snapshot(
    funding_block: dict[str, Any],
) -> tuple[dict[datetime, Decimal], dict[datetime, int]]:
    """Parse one coin's ``daily_funding_rate_sums`` rows from the committed
    FUND-EV1 snapshot summary into (funding_by_close, hours_by_close)."""
    from datetime import UTC

    funding_by_close: dict[datetime, Decimal] = {}
    hours_by_close: dict[datetime, int] = {}
    for row in funding_block["daily_funding_rate_sums"]:
        t = datetime.strptime(str(row["close_time"]), "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=UTC
        )
        funding_by_close[t] = Decimal(str(row["funding_rate_sum"]))
        hours_by_close[t] = int(row["hours"])
    return funding_by_close, hours_by_close


def timeline_split_time(universe: CarryUniverse, ratio: Decimal) -> datetime:
    timeline = universe.timeline
    split_index = max(0, min(len(timeline) - 1, int(len(timeline) * float(ratio)) - 1))
    return timeline[split_index]


# ---------------------------------------------------------------------------
# Causal trailing-funding signal (Must 1) — slots <= t only
# ---------------------------------------------------------------------------


def trailing_funding_mean(
    funding_times: Sequence[datetime],
    funding_by_close: dict[datetime, Decimal],
    t: datetime,
    lookback_days: int,
) -> Decimal | None:
    """Mean of the last ``lookback_days`` daily funding-rate sums at or
    before ``t``. None when fewer than ``lookback_days`` slots exist."""
    end = bisect_right(funding_times, t)
    if end < lookback_days:
        return None
    window = funding_times[end - lookback_days : end]
    total = sum((funding_by_close[ts] for ts in window), Decimal("0"))
    return total / Decimal(lookback_days)


def verify_funding_signal_point_in_time(
    funding_times: Sequence[datetime],
    funding_by_close: dict[datetime, Decimal],
    sample_times: Sequence[datetime],
    lookback_days: int,
) -> bool:
    """True iff the trailing-funding signal provably ignores future slots:
    tampering with every funding entry AFTER t must not change the signal,
    and truncating the series at t must reproduce it."""
    for t in sample_times:
        full = trailing_funding_mean(funding_times, funding_by_close, t, lookback_days)
        truncated_times = [ts for ts in funding_times if ts <= t]
        truncated_map = {ts: funding_by_close[ts] for ts in truncated_times}
        if trailing_funding_mean(truncated_times, truncated_map, t, lookback_days) != full:
            return False
        tampered = dict(funding_by_close)
        for ts in funding_times:
            if ts > t:
                tampered[ts] = funding_by_close[ts] * Decimal("-7") + Decimal("1")
        if trailing_funding_mean(funding_times, tampered, t, lookback_days) != full:
            return False
    return True


# ---------------------------------------------------------------------------
# The two-leg delta-neutral simulator (Must 1)
# ---------------------------------------------------------------------------


def simulate_funding_carry_portfolio(
    universe: CarryUniverse,
    config: FundingCarryConfig,
    scenario: DepthAwareScenario,
    *,
    signal_provider: Callable[[str, datetime], int] | None = None,
) -> dict[str, Any]:
    """Simulate the delta-neutral carry book with strict point-in-time rules.

    At each aligned daily close t: pending fills whose fill candle closed by
    t execute first (priced at that candle's OPEN through EXEC-EV1
    friction), then the day's funding accrues on the perp leg held through
    that candle, then the book is marked to market (each leg at its own
    venue's close — basis drift is real PnL). The book state never includes
    a fill before its fill candle: a lagged hedge leg therefore leaves REAL
    one-leg exposure through the interim closes (visible in the
    residual-delta series and the equity curve, not assumed away).
    On rebalance closes (every ``rebalance_interval_days``-th aligned close):
      1. (decision) trailing funding mean per asset from slots <= t only;
      2. side per asset: collect (+1: short perp / long spot) when trailing
         funding > 0; ``flip_sides`` also takes -1 (long perp / short spot,
         spot borrow ASSUMED, borrow cost NOT modeled) when < 0; exactly-zero
         or insufficient history = flat;
      3. rank by |trailing funding|, keep up to ``top_k`` names, target
         equal leg notional = leg_notional_fraction * equity / top_k;
      4. queue BOTH legs toward target for the next candle open, every fill
         priced through EXEC-EV1 friction at the traded notional (perp leg
         at its tier, spot leg at the conservative mid-alt tier), fees on
         both legs, dust trades under the rebalance band skipped; pending
         not-yet-filled deltas count toward targets so a slow leg is never
         double-ordered.
    ``spot_leg_lag_days`` delays ONLY the spot-leg fills (legged execution
    stress: the book carries REAL one-leg exposure around every rebalance).

    ``signal_provider(symbol, t) -> {-1, 0, +1}`` overrides the funding side
    for benchmarks (always-on uses +1 for every asset).
    """
    ensure_gate_applies(config.strategy_type, FUNDING_CARRY_GATE_ID)
    symbols = universe.symbols
    timeline = universe.timeline

    cash = STARTING_EQUITY
    perp_pos: dict[str, Any] = {s: _Position() for s in symbols}
    spot_pos: dict[str, Any] = {s: _Position() for s in symbols}
    equity_curve: list[tuple[datetime, Decimal]] = []
    funding_by_symbol: dict[str, Decimal] = defaultdict(Decimal)
    funding_collected_total = Decimal("0")
    funding_on_negative_days: dict[str, Decimal] = defaultdict(Decimal)
    negative_day_exposure_days: dict[str, int] = defaultdict(int)
    realized_by_symbol: dict[str, Decimal] = defaultdict(Decimal)
    fees_by_symbol: dict[str, Decimal] = defaultdict(Decimal)
    fees_by_leg: dict[str, Decimal] = {"perp": Decimal("0"), "spot": Decimal("0")}
    friction_quote_by_leg: dict[str, Decimal] = {"perp": Decimal("0"), "spot": Decimal("0")}
    friction_bps_paid: list[Decimal] = []
    traded_notional_total = Decimal("0")
    trade_count = 0
    trade_events: list[tuple[datetime, str, str, str, Decimal]] = []
    rebalance_count = 0
    decision_timestamps: list[datetime] = []
    residual_delta_fractions: list[Decimal] = []
    daily_pnl: list[tuple[datetime, Decimal]] = []

    def perp_close(symbol: str, t: datetime) -> Decimal:
        asset = universe.assets[symbol]
        return asset.perp.candles[universe.perp_index[symbol][t]].close

    def spot_close(symbol: str, t: datetime) -> Decimal:
        asset = universe.assets[symbol]
        return asset.spot.candles[universe.spot_index[symbol][t]].close

    def mtm_equity(t: datetime) -> Decimal:
        unrealized = Decimal("0")
        for s in symbols:
            if perp_pos[s].qty != 0:
                unrealized += (perp_close(s, t) - perp_pos[s].entry) * perp_pos[s].qty
            if spot_pos[s].qty != 0:
                unrealized += (spot_close(s, t) - spot_pos[s].entry) * spot_pos[s].qty
        return cash + unrealized

    # Pending-fill queue: a fill decided at close t executes when its fill
    # candle has CLOSED (fills price at that candle's open). Until then the
    # book state does NOT include it — so a lagged hedge leg leaves real
    # one-leg exposure through the interim closes (the legged-execution
    # tail risk this phase must measure, not assume away).
    pending_fills: list[tuple[str, str, int, Decimal, int]] = []

    def execute_leg(
        symbol: str, leg: str, signal_idx: int, fill_idx: int, delta_qty: Decimal
    ) -> None:
        nonlocal cash, traded_notional_total, trade_count
        if delta_qty == 0:
            return
        asset = universe.assets[symbol]
        dataset = asset.perp if leg == "perp" else asset.spot
        candle_dicts = (
            universe.perp_candle_dicts if leg == "perp" else universe.spot_candle_dicts
        )
        if fill_idx >= len(dataset.candles):
            return
        raw_fill = dataset.candles[fill_idx].open
        if raw_fill <= 0:
            return
        side = "buy" if delta_qty > 0 else "sell"
        notional = abs(delta_qty) * raw_fill
        signal_close = dataset.candles[signal_idx].close
        gap = (
            (raw_fill - signal_close) / signal_close * BPS
            if side == "buy"
            else (signal_close - raw_fill) / signal_close * BPS
        ) if signal_close > 0 else Decimal("0")
        friction_symbol = symbol if leg == "perp" else f"{symbol}{SPOT_FRICTION_SUFFIX}"
        friction = fill_friction_bps(
            scenario=scenario,
            symbol=friction_symbol,
            notional=_money(notional),
            liquidity_proxy=candle_dollar_volume(candle_dicts[symbol][fill_idx]),
            adverse_gap=gap,
        )
        fill_price = depth_aware_execution_price(
            raw_price=raw_fill, side=side, friction_total_bps=friction.total_bps
        )
        friction_bps_paid.append(friction.total_bps)
        friction_quote_by_leg[leg] += _money(abs(fill_price - raw_fill) * abs(delta_qty))
        fee = _money(notional * scenario.fee_bps / BPS)
        book = perp_pos if leg == "perp" else spot_pos
        book[symbol], realized = _apply_fill(book[symbol], fill_price, delta_qty)
        cash = _money(cash + realized - fee)
        realized_by_symbol[symbol] += _money(realized)
        fees_by_symbol[symbol] += fee
        fees_by_leg[leg] += fee
        traded_notional_total += _money(notional)
        trade_count += 1
        trade_events.append(
            (dataset.candles[fill_idx].timestamp, symbol, leg, side, _money(notional))
        )

    prev_equity: Decimal | None = None
    for k, t in enumerate(timeline):
        # 0) Execute pending fills whose fill candle has closed by t (fills
        #    price at that candle's open, so they are part of the book for
        #    the whole candle — including its funding accrual below).
        if pending_fills:
            still_pending: list[tuple[str, str, int, Decimal, int]] = []
            for symbol, leg, signal_idx, delta_qty, fill_idx in pending_fills:
                dataset = (
                    universe.assets[symbol].perp
                    if leg == "perp"
                    else universe.assets[symbol].spot
                )
                if fill_idx < len(dataset.candles) and dataset.candles[
                    fill_idx
                ].timestamp <= t:
                    execute_leg(symbol, leg, signal_idx, fill_idx, delta_qty)
                else:
                    still_pending.append((symbol, leg, signal_idx, delta_qty, fill_idx))
            pending_fills = still_pending

        # 1) Funding accrual for the candle that closed at t, on the perp leg
        #    held through that candle (fills happen at candle opens, so the
        #    current position held the whole slot). Daily-close mark
        #    approximation, documented.
        for s in symbols:
            qty = perp_pos[s].qty
            if qty == 0:
                continue
            rate = universe.assets[s].funding_by_close.get(t)
            if rate is None:
                continue
            payment = _money(-qty * perp_close(s, t) * rate)
            cash = _money(cash + payment)
            funding_by_symbol[s] += payment
            funding_collected_total += payment
            if rate < 0:
                funding_on_negative_days[s] += payment
                negative_day_exposure_days[s] += 1

        # 2) Rebalance decision at this close; fills at next candle open.
        if k % config.rebalance_interval_days == 0:
            equity_now = mtm_equity(t)
            if equity_now > 0:
                rebalance_count += 1
                decision_timestamps.append(t)
                sides: dict[str, int] = {}
                strengths: dict[str, Decimal] = {}
                for s in symbols:
                    if signal_provider is not None:
                        side_s = signal_provider(s, t)
                        strength = Decimal("1")
                    else:
                        signal = trailing_funding_mean(
                            universe.funding_times[s],
                            universe.assets[s].funding_by_close,
                            t,
                            config.funding_lookback_days,
                        )
                        if signal is None or signal == 0:
                            side_s, strength = 0, Decimal("0")
                        elif signal > 0:
                            side_s, strength = 1, signal
                        else:
                            side_s = -1 if config.mode == "flip_sides" else 0
                            strength = -signal
                    sides[s] = side_s
                    strengths[s] = strength
                active = [s for s in symbols if sides[s] != 0]
                top_k = min(config.top_k, len(symbols))
                selected = sorted(active, key=lambda s: (-strengths[s], s))[:top_k]
                slot_notional = equity_now * config.leg_notional_fraction / Decimal(top_k)
                for s in sorted(symbols):
                    side_s = sides[s] if s in selected else 0
                    p_close = perp_close(s, t)
                    s_close = spot_close(s, t)
                    if p_close <= 0 or s_close <= 0:
                        continue
                    # Delta-neutral targets: equal notional, opposite signs.
                    # Pending (not-yet-filled) deltas are counted so a slow
                    # leg is not re-ordered twice across rebalances.
                    pend_perp = sum(
                        d for sym, leg, _, d, _ in pending_fills
                        if sym == s and leg == "perp"
                    )
                    pend_spot = sum(
                        d for sym, leg, _, d, _ in pending_fills
                        if sym == s and leg == "spot"
                    )
                    target_perp_qty = -Decimal(side_s) * slot_notional / p_close
                    target_spot_qty = Decimal(side_s) * slot_notional / s_close
                    perp_delta = target_perp_qty - (perp_pos[s].qty + pend_perp)
                    spot_delta = target_spot_qty - (spot_pos[s].qty + pend_spot)
                    band = equity_now * MIN_TRADE_NOTIONAL_FRACTION
                    perp_signal_idx = universe.perp_index[s][t]
                    spot_signal_idx = universe.spot_index[s][t]
                    if abs(perp_delta) * p_close >= band:
                        pending_fills.append(
                            (s, "perp", perp_signal_idx, perp_delta, perp_signal_idx + 1)
                        )
                    if abs(spot_delta) * s_close >= band:
                        pending_fills.append(
                            (
                                s,
                                "spot",
                                spot_signal_idx,
                                spot_delta,
                                spot_signal_idx + 1 + config.spot_leg_lag_days,
                            )
                        )

        # 3) Mark to market + residual-delta tracking.
        equity_t = mtm_equity(t)
        equity_curve.append((t, equity_t))
        if equity_t > 0:
            residual = sum(
                abs(
                    perp_pos[s].qty * perp_close(s, t)
                    + spot_pos[s].qty * spot_close(s, t)
                )
                for s in symbols
            )
            residual_delta_fractions.append(residual / equity_t)
        if prev_equity is not None:
            daily_pnl.append((t, _money(equity_t - prev_equity)))
        prev_equity = equity_t

    # Forced close of both legs at the last aligned close (friction-priced)
    # so the final equity is fully realized.
    if timeline:
        last_t = timeline[-1]
        for s in sorted(symbols):
            for leg, book, price in (
                ("perp", perp_pos, perp_close(s, last_t)),
                ("spot", spot_pos, spot_close(s, last_t)),
            ):
                pos = book[s]
                if pos.qty == 0 or price <= 0:
                    continue
                side = "sell" if pos.qty > 0 else "buy"
                notional = abs(pos.qty) * price
                friction_symbol = s if leg == "perp" else f"{s}{SPOT_FRICTION_SUFFIX}"
                candle_dicts = (
                    universe.perp_candle_dicts if leg == "perp" else universe.spot_candle_dicts
                )
                index_map = universe.perp_index if leg == "perp" else universe.spot_index
                friction = fill_friction_bps(
                    scenario=scenario,
                    symbol=friction_symbol,
                    notional=_money(notional),
                    liquidity_proxy=candle_dollar_volume(
                        candle_dicts[s][index_map[s][last_t]]
                    ),
                    adverse_gap=Decimal("0"),
                )
                fill_price = depth_aware_execution_price(
                    raw_price=price, side=side, friction_total_bps=friction.total_bps
                )
                friction_bps_paid.append(friction.total_bps)
                friction_quote_by_leg[leg] += _money(abs(fill_price - price) * abs(pos.qty))
                fee = _money(notional * scenario.fee_bps / BPS)
                book[s], realized = _apply_fill(book[s], fill_price, -pos.qty)
                cash = _money(cash + realized - fee)
                realized_by_symbol[s] += _money(realized)
                fees_by_symbol[s] += fee
                fees_by_leg[leg] += fee
                trade_count += 1
                trade_events.append((last_t, s, leg, side, _money(notional)))
        if equity_curve:
            equity_curve[-1] = (last_t, cash)

    avg_friction = (
        sum(friction_bps_paid, Decimal("0")) / Decimal(len(friction_bps_paid))
        if friction_bps_paid
        else Decimal("0")
    )
    per_symbol_net = {
        s: _money(realized_by_symbol[s] + funding_by_symbol[s] - fees_by_symbol[s])
        for s in sorted(symbols)
    }
    ending_equity = equity_curve[-1][1] if equity_curve else STARTING_EQUITY
    worst_days = sorted(daily_pnl, key=lambda row: row[1])[:5]
    return {
        "config_id": config.config_id,
        "strategy_type": config.strategy_type,
        "scenario_id": scenario.scenario_id,
        "timeframe": config.timeframe,
        "equity_curve": tuple(equity_curve),
        "ending_equity": ending_equity,
        "net_pnl": _money(ending_equity - STARTING_EQUITY),
        "funding_collected_total": _money(funding_collected_total),
        "funding_by_symbol": {s: _money(v) for s, v in sorted(funding_by_symbol.items())},
        "funding_paid_on_negative_days_by_symbol": {
            s: _money(v) for s, v in sorted(funding_on_negative_days.items())
        },
        "negative_funding_exposure_days_by_symbol": dict(
            sorted(negative_day_exposure_days.items())
        ),
        "fees_total": _money(fees_by_leg["perp"] + fees_by_leg["spot"]),
        "fees_by_leg": {leg: _money(v) for leg, v in fees_by_leg.items()},
        "friction_quote_by_leg": {leg: _money(v) for leg, v in friction_quote_by_leg.items()},
        "avg_friction_bps": _money(avg_friction),
        "trade_count": trade_count,
        "trade_events": tuple(trade_events),
        "rebalance_count": rebalance_count,
        "decision_timestamps": tuple(decision_timestamps),
        "per_symbol_net_pnl": per_symbol_net,
        "traded_notional_total": _money(traded_notional_total),
        "max_residual_delta_fraction": (
            _money(max(residual_delta_fractions)) if residual_delta_fractions else Decimal("0")
        ),
        "avg_residual_delta_fraction": (
            _money(
                sum(residual_delta_fractions, Decimal("0"))
                / Decimal(len(residual_delta_fractions))
            )
            if residual_delta_fractions
            else Decimal("0")
        ),
        "worst_days": tuple(worst_days),
    }


# ---------------------------------------------------------------------------
# Benchmarks (Must 3): gross funding (how much costs eat) + cash + always-on
# ---------------------------------------------------------------------------


def always_on_provider(_symbol: str, _t: datetime) -> int:
    return 1


def zero_cost_scenario(parent: DepthAwareScenario) -> DepthAwareScenario:
    """The same scenario with every cost term zeroed — the gross-carry bound."""
    from dataclasses import replace as _replace

    return _replace(
        parent,
        scenario_id=f"{parent.scenario_id}_zero_cost",
        fee_bps=Decimal("0"),
        slippage_bps=Decimal("0"),
        adverse_gap_penalty_bps=Decimal("0"),
        spread_tier_multiplier=Decimal("0"),
        impact_coefficient_bps=Decimal("0"),
        fill_probability=Decimal("1"),
        chase_penalty_bps=Decimal("0"),
    )


# ---------------------------------------------------------------------------
# Regime classification (Must 2/3): not bull-only
# ---------------------------------------------------------------------------


def classify_regimes(
    universe: CarryUniverse,
    *,
    reference_symbol: str = "BTC",
    trailing_days: int = REGIME_TRAILING_DAYS,
    band: Decimal = REGIME_BAND,
) -> dict[datetime, str]:
    """Point-in-time regime per aligned close from the reference perp's
    trailing return: bear < -band, bull > +band, else neutral. Uses only
    closes <= t (the full perp history may extend before the aligned
    window, which is fine — it is still point-in-time)."""
    asset = universe.assets[reference_symbol]
    closes = [c.close for c in asset.perp.candles]
    index = universe.perp_index[reference_symbol]
    regimes: dict[datetime, str] = {}
    for t in universe.timeline:
        idx = index[t]
        if idx < trailing_days or closes[idx - trailing_days] <= 0:
            regimes[t] = "neutral"
            continue
        trailing = closes[idx] / closes[idx - trailing_days] - Decimal("1")
        if trailing < -band:
            regimes[t] = "bear"
        elif trailing > band:
            regimes[t] = "bull"
        else:
            regimes[t] = "neutral"
    return regimes


def pnl_by_regime(
    equity_curve: Sequence[tuple[datetime, Decimal]],
    regimes: dict[datetime, str],
) -> dict[str, dict[str, Any]]:
    """Daily equity-change attribution per regime label."""
    out: dict[str, dict[str, Any]] = {
        label: {"days": 0, "net_pnl": Decimal("0")} for label in ("bull", "neutral", "bear")
    }
    for i in range(1, len(equity_curve)):
        t, value = equity_curve[i]
        label = regimes.get(t, "neutral")
        out[label]["days"] += 1
        out[label]["net_pnl"] += value - equity_curve[i - 1][1]
    for label in out:
        out[label]["net_pnl"] = _money(out[label]["net_pnl"])
    return out


# ---------------------------------------------------------------------------
# OOS helpers (Must 3): train-only choice on train-window Sharpe
# ---------------------------------------------------------------------------


def select_best_config_id(
    results_by_config: dict[str, dict[str, Any]], *, train_up_to: datetime
) -> str:
    """Train-only parameter choice on train-window SHARPE (risk-adjusted —
    carry is judged on Sharpe + drawdown, not gross funding), ties broken by
    config id."""

    def train_sharpe(result: dict[str, Any]) -> Decimal:
        stats = curve_stats(result["equity_curve"], up_to=train_up_to)
        sharpe = stats["sharpe_annual"]
        return sharpe if sharpe is not None else Decimal("-999")

    ranked = sorted(
        results_by_config.items(),
        key=lambda item: (-train_sharpe(item[1]), item[0]),
    )
    return ranked[0][0]


def window_net_pnl(
    curve: Sequence[tuple[datetime, Decimal]],
    *,
    after: datetime | None = None,
    up_to: datetime | None = None,
) -> Decimal | None:
    window = [
        v for t, v in curve
        if (after is None or t > after) and (up_to is None or t <= up_to)
    ]
    if len(window) < 2:
        return None
    return _money(window[-1] - window[0])


# ---------------------------------------------------------------------------
# The funding_carry gate (Must 3) — its own; routing-guarded
# ---------------------------------------------------------------------------


def evaluate_funding_carry_gate(
    *,
    strategy_type: str,
    oos_strategy_stats: dict[str, Any],
    oos_net_pnl: Decimal | None,
    walk_forward_net_pnls: Sequence[Decimal | None],
    regime_pnls: dict[str, dict[str, Any]],
    leave_one_out_oos_net: dict[str, Decimal | None],
    stressed_max_drawdown_pct: Decimal | None,
    max_oos_drawdown_pct: Decimal = MAX_OOS_DRAWDOWN_PCT,
    max_stressed_drawdown_pct: Decimal = MAX_STRESSED_DRAWDOWN_PCT,
    min_oos_days: int = MIN_OOS_DAYS,
) -> dict[str, Any]:
    """The carry verdict: net funding survives costs AND the tail, OOS.

    Pass requires ALL of:
      - OOS net carry (after all costs, conservative friction) > 0;
      - anchored walk-forward: net carry positive in EVERY fold (params
        chosen on train only);
      - NOT bull-only: combined non-bull (bear + neutral) net carry > 0
        over the full window — funding that only exists in bulls is beta
        rent, not a structural edge;
      - leave-one-out: dropping ANY single asset keeps OOS net carry > 0
        (not a single-name artifact);
      - tail: OOS max drawdown <= ``max_oos_drawdown_pct`` AND the stressed
        run (stress friction + spot leg lagging a candle) keeps full-window
        max drawdown <= ``max_stressed_drawdown_pct``;
      - enough OOS sample (days).
    Never applied to per_symbol / selection / time_series_momentum
    strategies. Judged on Sharpe + max drawdown, not gross funding
    collected; the verdict is never forced positive.
    """
    ensure_gate_applies(strategy_type, FUNDING_CARRY_GATE_ID)
    reasons: list[str] = []
    if oos_net_pnl is None or oos_net_pnl <= 0:
        reasons.append("oos_net_carry_not_positive_after_costs")
    if not walk_forward_net_pnls or any(
        net is None or net <= 0 for net in walk_forward_net_pnls
    ):
        reasons.append("walk_forward_net_carry_not_positive_in_every_fold")
    non_bull = (
        regime_pnls.get("bear", {}).get("net_pnl", Decimal("0"))
        + regime_pnls.get("neutral", {}).get("net_pnl", Decimal("0"))
    )
    if non_bull <= 0:
        reasons.append("non_bull_regime_net_carry_not_positive")
    if not leave_one_out_oos_net or any(
        net is None or net <= 0 for net in leave_one_out_oos_net.values()
    ):
        reasons.append("leave_one_out_breaks_oos_net_carry")
    oos_dd = oos_strategy_stats.get("max_drawdown_pct")
    if oos_dd is None or oos_dd > max_oos_drawdown_pct:
        reasons.append("oos_drawdown_exceeds_documented_limit")
    if stressed_max_drawdown_pct is None or (
        stressed_max_drawdown_pct > max_stressed_drawdown_pct
    ):
        reasons.append("stressed_tail_drawdown_exceeds_documented_limit")
    if (oos_strategy_stats.get("days") or 0) < min_oos_days:
        reasons.append("rejected_low_oos_days")
    status = VERDICT_PASS if not reasons else VERDICT_FAIL
    # Honesty qualifiers (non-failing): a pass that leans on the flip-side
    # book is an upper bound (spot borrow unmodeled), and a thin absolute
    # Sharpe must not be over-read.
    qualifiers: list[str] = []
    sharpe = oos_strategy_stats.get("sharpe_annual")
    if status == VERDICT_PASS and sharpe is not None and sharpe < Decimal("1"):
        qualifiers.append("oos_sharpe_below_one_thin_edge")
    return {
        "gate_id": FUNDING_CARRY_GATE_ID,
        "status": status,
        "passed": status == VERDICT_PASS,
        "qualifiers": qualifiers,
        "reason_codes": reasons or ["funding_carry_gate_passed"],
        "oos_strategy": oos_strategy_stats,
        "oos_net_pnl": oos_net_pnl,
        "walk_forward_net_pnls": list(walk_forward_net_pnls),
        "non_bull_net_pnl": _money(non_bull),
        "regime_pnls": regime_pnls,
        "leave_one_out_oos_net": dict(sorted(leave_one_out_oos_net.items())),
        "stressed_max_drawdown_pct": stressed_max_drawdown_pct,
        "max_oos_drawdown_pct_limit": max_oos_drawdown_pct,
        "max_stressed_drawdown_pct_limit": max_stressed_drawdown_pct,
        "min_oos_days_required": min_oos_days,
    }


def boundary_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "changes_production_money_flow_rules": False,
        "changes_per_symbol_lane_behavior_or_results": False,
        "changes_selection_lane_behavior_or_results": False,
        "changes_tsmom_lane_behavior_or_results": False,
        "mutates_active_pt_rt_runtime": False,
        "mutates_runtime_artifacts": False,
        "creates_order_intent": False,
        "creates_prepared_venue_order": False,
        "creates_submitted_order": False,
        "submits_live_orders": False,
        "submits_testnet_orders": False,
        "calls_private_signed_or_order_endpoints": False,
        "uses_testnet_data_as_strategy_truth": False,
        "approves_live_trading": False,
        "approves_production_strategy": False,
        "modeled_depth_not_real": True,
        "funding_modeled_from_public_history": True,
        "daily_funding_accrual_approximation": True,
        "spot_borrow_not_modeled_flip_rows_upper_bound": True,
        "liquidation_mechanics_not_modeled": True,
    }
