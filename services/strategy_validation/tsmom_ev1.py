"""TSMOM-EV1 — volatility-targeted time-series momentum evidence layer.

RESEARCH / EVIDENCE ONLY. Tests trend "done right" after the earlier trend
failures (full-equity sizing -> ZEC blowup, short windows, indicator-gate
noise, thin alts): per-asset time-series momentum with VOLATILITY TARGETING
and RISK PARITY on LIQUID MAJORS, judged against BUY-AND-HOLD on a
risk-adjusted basis (Sharpe + max drawdown) out-of-sample after EXEC-EV1
depth-aware friction. The honest question: does vol-targeted trend add
risk-adjusted value, or is it just (leveraged) beta? Either answer is
valuable; the gate never forces a positive.

Routed under ``strategy_type == "time_series_momentum"`` by
``services.strategy_validation.strategy_types`` with its OWN gate
(buy-and-hold risk-adjusted comparison). It must never be judged by the
per-symbol breadth gate or the selection random-benchmark gate, and vice
versa.

Design (Must 1):
  - Signal: sign of the trailing ``lookback``-day return per asset, computed
    at closed candles only. Exactly-zero trailing return means FLAT — chop
    with no drift must not accumulate exposure.
  - Volatility targeting (the core fix): each asset's weight is inversely
    proportional to its own realized volatility, so every asset contributes
    an EQUAL RISK BUDGET (portfolio_vol_target / N). This is the specific
    fix for the ZEC-class failure: the highest-vol name can no longer
    dominate the book.
  - Portfolio caps: per-asset |weight| <= MAX_SINGLE_ASSET_WEIGHT and gross
    leverage <= MAX_GROSS_LEVERAGE (1.5x, documented). If the equal-risk
    weights exceed the gross cap they are scaled down proportionally.
  - Cadence: weekly rebalance (every 7th aligned daily close), next-candle-
    open fills, a rebalance band (trades below MIN_TRADE_NOTIONAL_FRACTION
    of equity are skipped) -> low turnover.
  - Account: 10,000 USDC. Friction: every fill is priced through the
    EXEC-EV1 depth-aware model at the actual traded notional (modeled depth,
    never real order-book depth).

Assumption boundaries (documented, never hidden):
  - Perp FUNDING is NOT modeled (neither paid by shorts/longs nor earned).
    Long/short results are therefore optimistic for whichever side would
    have paid net funding; this is called out in the evidence report.
  - Depth/liquidity inputs are MODELED from candle volume (see exec_ev1).

Pure and deterministic: Decimal arithmetic, no I/O, no network. Random
baselines use seeded ``random.Random`` only.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Sequence

from services.execution_quality.exec_ev1 import (
    BPS,
    DepthAwareScenario,
    candle_dollar_volume,
    depth_aware_execution_price,
    entry_timing_cost_bps,
    fill_friction_bps,
)

try:  # pragma: no cover - exercised implicitly by both import contexts
    from services.strategy_validation import sel_ev1 as _sel_ev1
    from services.strategy_validation import strategy_types as _strategy_types
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

    _sel_ev1 = _load_sibling("sel_ev1.py", "tsmom_ev1_sel_ev1")
    _strategy_types = _load_sibling("strategy_types.py", "tsmom_ev1_strategy_types")

# Reused SEL-EV1 plumbing (universe alignment, SV2.2 adapter, stats).
SelectionUniverse = _sel_ev1.SelectionUniverse
dataset_from_sv22_payload = _sel_ev1.dataset_from_sv22_payload
distribution_stats = _sel_ev1.distribution_stats
verify_point_in_time_scores = _sel_ev1.verify_point_in_time_scores
_money = _sel_ev1._money

STRATEGY_TYPE_TIME_SERIES_MOMENTUM = _strategy_types.STRATEGY_TYPE_TIME_SERIES_MOMENTUM
TSMOM_GATE_ID = _strategy_types.TSMOM_GATE_ID
StrategyTypeRoutingError = _strategy_types.StrategyTypeRoutingError
ensure_gate_applies = _strategy_types.ensure_gate_applies

PHASE = "TSMOM-EV1"
STARTING_EQUITY = Decimal("10000")

# Liquid-majors subset of SUPPORTED_CANONICAL_SYMBOLS (documented; Must 0):
# all eight have full 889-candle 1d history (2024-01-02 -> 2026-06-08) and sit
# in the EXEC-EV1 major/large liquidity tiers, so modeled friction is benign
# at 10k sizing. HYPE is excluded: mid-alt tier AND only ~550 candles (listed
# 2024-12), which would distort the aligned universe and the buy-hold bar.
LIQUID_UNIVERSE = ("AVAX", "BNB", "BTC", "DOGE", "ETH", "SOL", "SUI", "XRP")
EXCLUDED_THIN_SYMBOLS = ("HYPE",)

# Bounded grid (Must 1): 3 lookbacks x 2 portfolio vol targets x 2 modes = 12.
TSMOM_LOOKBACKS = (30, 60, 90)
PORTFOLIO_VOL_TARGETS = (Decimal("0.20"), Decimal("0.40"))
TSMOM_MODES = ("long_only", "long_short")
TSMOM_TIMEFRAME = "1d"

VOL_WINDOW_DAYS = 30
ANNUALIZATION_DAYS = Decimal("365")
REBALANCE_INTERVAL_DAYS = 7
MAX_GROSS_LEVERAGE = Decimal("1.5")
MAX_SINGLE_ASSET_WEIGHT = Decimal("0.40")
MIN_TRADE_NOTIONAL_FRACTION = Decimal("0.005")
LATE_ENTRY_LATENESS_STEPS = (0, 1, 2)

MIN_OOS_DAYS = 120
MIN_OOS_TRADES = 12

VERDICT_BEATS_BUY_HOLD = "beats_buy_hold_risk_adjusted_oos"
VERDICT_NO_EDGE = "no_risk_adjusted_edge_vs_buy_hold"


@dataclass(frozen=True, slots=True)
class TsmomConfig:
    config_id: str
    strategy_type: str
    lookback_days: int
    portfolio_vol_target: Decimal  # annualized, e.g. 0.20
    mode: str  # long_only | long_short
    vol_targeting: bool = True
    timeframe: str = TSMOM_TIMEFRAME
    vol_window_days: int = VOL_WINDOW_DAYS
    rebalance_interval_days: int = REBALANCE_INTERVAL_DAYS
    entry_delay_candles: int = 0


def generate_tsmom_configs() -> list[TsmomConfig]:
    """The full bounded grid; parameters are chosen on the train split only."""
    configs: list[TsmomConfig] = []
    for mode in TSMOM_MODES:
        for lookback in TSMOM_LOOKBACKS:
            for vol_target in PORTFOLIO_VOL_TARGETS:
                vt = str(vol_target).replace("0.", "")
                configs.append(
                    TsmomConfig(
                        config_id=f"tsmom_ev1_lb{lookback}_vt{vt}_{mode}_1d",
                        strategy_type=STRATEGY_TYPE_TIME_SERIES_MOMENTUM,
                        lookback_days=lookback,
                        portfolio_vol_target=vol_target,
                        mode=mode,
                    )
                )
    return configs


# ---------------------------------------------------------------------------
# Causal signal + realized volatility (Must 1)
# ---------------------------------------------------------------------------


def tsmom_signal(closes: Sequence[Decimal], idx: int, lookback: int) -> int | None:
    """Sign of the trailing ``lookback`` return using closes[: idx + 1] only.

    +1 trend up, -1 trend down, 0 exactly-flat (chop with no drift stays
    FLAT), None when there is not enough history.
    """
    if idx < lookback or idx >= len(closes):
        return None
    past = closes[idx - lookback]
    if past <= 0:
        return None
    trailing = closes[idx] - past
    if trailing > 0:
        return 1
    if trailing < 0:
        return -1
    return 0


def realized_vol_annual(
    closes: Sequence[Decimal], idx: int, window: int
) -> Decimal | None:
    """Annualized realized volatility of simple daily returns over the
    ``window`` returns ending at ``idx`` (causal: closes[: idx + 1] only)."""
    if idx < window or idx >= len(closes):
        return None
    returns: list[Decimal] = []
    for j in range(idx - window + 1, idx + 1):
        prev = closes[j - 1]
        if prev <= 0:
            return None
        returns.append(closes[j] / prev - Decimal("1"))
    n = Decimal(len(returns))
    mean = sum(returns, Decimal("0")) / n
    variance = sum((r - mean) ** 2 for r in returns) / n
    if variance < 0:
        return None
    daily_vol = variance.sqrt()
    vol = daily_vol * ANNUALIZATION_DAYS.sqrt()
    return vol if vol > 0 else None


def target_weights(
    *,
    signals: dict[str, int],
    vols: dict[str, Decimal | None],
    config: TsmomConfig,
) -> dict[str, Decimal]:
    """Equal-risk-budget (risk parity) weights with explicit caps.

    Each asset receives risk budget ``portfolio_vol_target / N``; its weight
    is ``signal * min(budget / realized_vol, MAX_SINGLE_ASSET_WEIGHT)``. With
    vol-targeting OFF (benchmarks), weight is ``signal / N``. If gross
    exposure exceeds MAX_GROSS_LEVERAGE everything scales down
    proportionally (the documented leverage cap).
    """
    n = Decimal(len(signals)) if signals else Decimal("1")
    weights: dict[str, Decimal] = {}
    for symbol, signal in signals.items():
        if signal is None or signal == 0:
            weights[symbol] = Decimal("0")
            continue
        if config.mode == "long_only" and signal < 0:
            weights[symbol] = Decimal("0")
            continue
        if config.vol_targeting:
            vol = vols.get(symbol)
            if vol is None or vol <= 0:
                weights[symbol] = Decimal("0")
                continue
            budget = config.portfolio_vol_target / n
            magnitude = min(budget / vol, MAX_SINGLE_ASSET_WEIGHT)
        else:
            magnitude = Decimal("1") / n
        weights[symbol] = magnitude if signal > 0 else -magnitude
    gross = sum(abs(w) for w in weights.values())
    if gross > MAX_GROSS_LEVERAGE:
        scale = MAX_GROSS_LEVERAGE / gross
        weights = {s: w * scale for s, w in weights.items()}
    return weights


# ---------------------------------------------------------------------------
# Mark-to-market portfolio simulator (Must 1)
# ---------------------------------------------------------------------------


@dataclass
class _Position:
    qty: Decimal = Decimal("0")  # signed; negative = short (perp-style)
    entry: Decimal = Decimal("0")


def _apply_fill(
    position: _Position, fill_price: Decimal, delta_qty: Decimal
) -> tuple[_Position, Decimal]:
    """Apply a signed fill to a signed position; return (position, realized).

    Perp-style accounting: realized PnL is recognized on the closed portion
    against the average entry; adds re-average the entry; a flip opens the
    remainder at the fill price.
    """
    q, e = position.qty, position.entry
    if q != 0 and (q > 0) != (delta_qty > 0):
        closing = min(abs(delta_qty), abs(q)) * (Decimal("1") if q > 0 else Decimal("-1"))
        realized = (fill_price - e) * closing
        q_new = q - closing
        delta_rem = delta_qty + closing
        if delta_rem != 0:
            return _Position(qty=delta_rem, entry=fill_price), realized
        return _Position(qty=q_new, entry=e if q_new != 0 else Decimal("0")), realized
    new_q = q + delta_qty
    new_e = (
        (e * q + fill_price * delta_qty) / new_q if new_q != 0 else Decimal("0")
    )
    return _Position(qty=new_q, entry=new_e), Decimal("0")


def simulate_tsmom_portfolio(
    universe: "SelectionUniverse",
    config: TsmomConfig,
    scenario: DepthAwareScenario,
    *,
    signal_provider: Callable[[str, int], int | None] | None = None,
    rebalance_timestamps: frozenset[datetime] | None = None,
) -> dict[str, Any]:
    """Simulate the vol-targeted TSMOM book with strict point-in-time rules.

    At each aligned closed daily candle t (all symbols present, next candle
    exists), mark the book to market. On rebalance days (every
    ``rebalance_interval_days``-th aligned close, or exactly the provided
    ``rebalance_timestamps``):
      1. (decision) compute each asset's trailing-return sign and realized
         vol from data up to and including the candle closed at t;
      2. derive equal-risk-budget weights (caps applied);
      3. trade toward target at the NEXT candle open
         (+``entry_delay_candles`` for the late-entry sensitivity), pricing
         every fill through EXEC-EV1 friction at the traded notional, and
         skipping dust trades under the rebalance band.

    ``signal_provider`` overrides the trailing-return signal (always-long and
    seeded random baselines reuse the exact machinery).
    """
    ensure_gate_applies(config.strategy_type, TSMOM_GATE_ID)
    symbols = universe.symbols
    closes: dict[str, list[Decimal]] = {
        s: [c.close for c in universe.datasets[s].candles] for s in symbols
    }

    # Aligned decision timeline: timestamps where EVERY symbol has a candle
    # and a next candle to fill at.
    aligned: list[tuple[datetime, dict[str, int]]] = []
    for t in universe.timeline:
        index_map: dict[str, int] = {}
        ok = True
        for s in symbols:
            idx = universe.index_by_time[s].get(t)
            if idx is None:
                ok = False
                break
            index_map[s] = idx
        if ok:
            aligned.append((t, index_map))

    cash = STARTING_EQUITY
    positions: dict[str, _Position] = {s: _Position() for s in symbols}
    equity_curve: list[tuple[datetime, Decimal]] = []
    realized_by_symbol: dict[str, Decimal] = defaultdict(Decimal)
    fees_by_symbol: dict[str, Decimal] = defaultdict(Decimal)
    friction_bps_paid: list[Decimal] = []
    friction_quote_paid = Decimal("0")
    traded_notional_total = Decimal("0")
    trade_count = 0
    rebalance_count = 0
    trade_events: list[tuple[datetime, str, str, Decimal]] = []
    decision_timestamps: list[datetime] = []
    timing_costs: dict[int, list[Decimal]] = {k: [] for k in LATE_ENTRY_LATENESS_STEPS}
    gross_exposures: list[Decimal] = []
    net_exposures: list[Decimal] = []

    def mtm_equity(index_map: dict[str, int]) -> Decimal:
        unrealized = Decimal("0")
        for s, pos in positions.items():
            if pos.qty != 0:
                unrealized += (closes[s][index_map[s]] - pos.entry) * pos.qty
        return cash + unrealized

    def execute(symbol: str, signal_idx: int, delta_qty: Decimal) -> None:
        nonlocal cash, friction_quote_paid, traded_notional_total, trade_count
        dataset = universe.datasets[symbol]
        fill_idx = signal_idx + 1 + config.entry_delay_candles
        if fill_idx >= len(dataset.candles) or delta_qty == 0:
            return
        raw_fill = dataset.candles[fill_idx].open
        if raw_fill <= 0:
            return
        side = "buy" if delta_qty > 0 else "sell"
        for step in LATE_ENTRY_LATENESS_STEPS:
            cost = entry_timing_cost_bps(
                universe.candle_dicts[symbol], signal_idx, step, side
            )
            if cost is not None:
                timing_costs[step].append(cost)
        notional = abs(delta_qty) * raw_fill
        signal_close = dataset.candles[signal_idx].close
        gap = (
            (raw_fill - signal_close) / signal_close * BPS
            if side == "buy"
            else (signal_close - raw_fill) / signal_close * BPS
        ) if signal_close > 0 else Decimal("0")
        friction = fill_friction_bps(
            scenario=scenario,
            symbol=symbol,
            notional=_money(notional),
            liquidity_proxy=candle_dollar_volume(universe.candle_dicts[symbol][fill_idx]),
            adverse_gap=gap,
        )
        fill_price = depth_aware_execution_price(
            raw_price=raw_fill, side=side, friction_total_bps=friction.total_bps
        )
        friction_bps_paid.append(friction.total_bps)
        friction_quote_paid += _money(abs(fill_price - raw_fill) * abs(delta_qty))
        fee = _money(notional * scenario.fee_bps / BPS)
        positions[symbol], realized = _apply_fill(positions[symbol], fill_price, delta_qty)
        cash = _money(cash + realized - fee)
        realized_by_symbol[symbol] += _money(realized)
        fees_by_symbol[symbol] += fee
        traded_notional_total += _money(notional)
        trade_count += 1
        trade_events.append(
            (dataset.candles[fill_idx].timestamp, symbol, side, _money(notional))
        )

    for k, (t, index_map) in enumerate(aligned):
        is_rebalance = (
            t in rebalance_timestamps
            if rebalance_timestamps is not None
            else k % config.rebalance_interval_days == 0
        )
        # Skip the final aligned candle as a decision point guard: execute()
        # already refuses fills past the end of data.
        if is_rebalance:
            signals: dict[str, int] = {}
            vols: dict[str, Decimal | None] = {}
            for s in symbols:
                idx = index_map[s]
                if signal_provider is not None:
                    sig = signal_provider(s, idx)
                else:
                    sig = tsmom_signal(closes[s], idx, config.lookback_days)
                if sig is None:
                    sig = 0
                signals[s] = sig
                vols[s] = realized_vol_annual(closes[s], idx, config.vol_window_days)
            weights = target_weights(signals=signals, vols=vols, config=config)
            equity_now = mtm_equity(index_map)
            if equity_now > 0:
                rebalance_count += 1
                decision_timestamps.append(t)
                for s in sorted(symbols):
                    idx = index_map[s]
                    close = closes[s][idx]
                    if close <= 0:
                        continue
                    target_qty = weights[s] * equity_now / close
                    delta = target_qty - positions[s].qty
                    if abs(delta) * close < equity_now * MIN_TRADE_NOTIONAL_FRACTION:
                        continue
                    execute(s, idx, delta)
        equity_t = mtm_equity(index_map)
        equity_curve.append((t, equity_t))
        gross = sum(
            abs(positions[s].qty) * closes[s][index_map[s]] for s in symbols
        )
        net = sum(positions[s].qty * closes[s][index_map[s]] for s in symbols)
        if equity_t > 0:
            gross_exposures.append(gross / equity_t)
            net_exposures.append(net / equity_t)

    # Forced close of every open position at the last aligned close so the
    # final equity is fully realized (friction-priced at the last close).
    if aligned:
        last_t, last_map = aligned[-1]
        for s in sorted(symbols):
            pos = positions[s]
            if pos.qty == 0:
                continue
            close = closes[s][last_map[s]]
            side = "sell" if pos.qty > 0 else "buy"
            notional = abs(pos.qty) * close
            friction = fill_friction_bps(
                scenario=scenario,
                symbol=s,
                notional=_money(notional),
                liquidity_proxy=candle_dollar_volume(
                    universe.candle_dicts[s][last_map[s]]
                ),
                adverse_gap=Decimal("0"),
            )
            fill_price = depth_aware_execution_price(
                raw_price=close, side=side, friction_total_bps=friction.total_bps
            )
            friction_bps_paid.append(friction.total_bps)
            friction_quote_paid += _money(abs(fill_price - close) * abs(pos.qty))
            fee = _money(notional * scenario.fee_bps / BPS)
            positions[s], realized = _apply_fill(positions[s], fill_price, -pos.qty)
            cash = _money(cash + realized - fee)
            realized_by_symbol[s] += _money(realized)
            fees_by_symbol[s] += fee
            trade_count += 1
            trade_events.append((last_t, s, side, _money(notional)))
        if equity_curve:
            equity_curve[-1] = (last_t, cash)

    avg_friction = (
        sum(friction_bps_paid, Decimal("0")) / Decimal(len(friction_bps_paid))
        if friction_bps_paid
        else Decimal("0")
    )
    days = Decimal(max(1, len(equity_curve)))
    years = days / ANNUALIZATION_DAYS
    avg_equity = (
        sum(v for _, v in equity_curve) / Decimal(len(equity_curve))
        if equity_curve
        else STARTING_EQUITY
    )
    per_symbol_net = {
        s: _money(realized_by_symbol[s] - fees_by_symbol[s]) for s in sorted(symbols)
    }
    return {
        "config_id": config.config_id,
        "strategy_type": config.strategy_type,
        "scenario_id": scenario.scenario_id,
        "timeframe": config.timeframe,
        "equity_curve": tuple(equity_curve),
        "ending_equity": equity_curve[-1][1] if equity_curve else STARTING_EQUITY,
        "net_pnl": _money((equity_curve[-1][1] if equity_curve else STARTING_EQUITY) - STARTING_EQUITY),
        "trade_count": trade_count,
        "trade_events": tuple(trade_events),
        "rebalance_count": rebalance_count,
        "decision_timestamps": tuple(decision_timestamps),
        "per_symbol_net_pnl": per_symbol_net,
        "avg_friction_bps": _money(avg_friction),
        "friction_paid_quote": _money(friction_quote_paid),
        "turnover_annual": _money(
            traded_notional_total / avg_equity / years if avg_equity > 0 and years > 0 else Decimal("0")
        ),
        "avg_gross_exposure": _money(
            sum(gross_exposures, Decimal("0")) / Decimal(len(gross_exposures))
            if gross_exposures
            else Decimal("0")
        ),
        "avg_net_exposure": _money(
            sum(net_exposures, Decimal("0")) / Decimal(len(net_exposures))
            if net_exposures
            else Decimal("0")
        ),
        "entry_timing_cost_bps_by_lateness": {
            step: (
                _money(sum(values, Decimal("0")) / Decimal(len(values)))
                if values
                else None
            )
            for step, values in timing_costs.items()
        },
    }


# ---------------------------------------------------------------------------
# Equity-curve statistics (the risk-adjusted vocabulary of the gate)
# ---------------------------------------------------------------------------


def curve_stats(
    curve: Sequence[tuple[datetime, Decimal]],
    *,
    after: datetime | None = None,
    up_to: datetime | None = None,
) -> dict[str, Any]:
    """Sharpe (annualized, rf=0), annualized vol, max drawdown %, total
    return % over the (after, up_to] window of a mark-to-market curve."""
    window = [
        (t, v)
        for t, v in curve
        if (after is None or t > after) and (up_to is None or t <= up_to)
    ]
    if len(window) < 2:
        return {"days": len(window), "sharpe_annual": None, "vol_annual": None,
                "max_drawdown_pct": None, "total_return_pct": None}
    returns: list[Decimal] = []
    for i in range(1, len(window)):
        prev = window[i - 1][1]
        if prev <= 0:
            return {"days": len(window), "sharpe_annual": None, "vol_annual": None,
                    "max_drawdown_pct": None, "total_return_pct": None}
        returns.append(window[i][1] / prev - Decimal("1"))
    n = Decimal(len(returns))
    mean = sum(returns, Decimal("0")) / n
    variance = sum((r - mean) ** 2 for r in returns) / n
    std = variance.sqrt() if variance > 0 else Decimal("0")
    sharpe = (
        _money(mean / std * ANNUALIZATION_DAYS.sqrt()) if std > 0 else None
    )
    peak = window[0][1]
    max_dd = Decimal("0")
    for _, value in window:
        peak = max(peak, value)
        if peak > 0:
            max_dd = max(max_dd, (peak - value) / peak)
    start, end = window[0][1], window[-1][1]
    return {
        "days": len(window),
        "sharpe_annual": sharpe,
        "vol_annual": _money(std * ANNUALIZATION_DAYS.sqrt()),
        "max_drawdown_pct": _money(max_dd * Decimal("100")),
        "total_return_pct": _money((end / start - Decimal("1")) * Decimal("100")),
    }


def risk_contributions(
    result: dict[str, Any], universe: "SelectionUniverse"
) -> dict[str, Any]:
    """Per-symbol share of total absolute net PnL — the concentration view."""
    per_symbol = result["per_symbol_net_pnl"]
    total_abs = sum(abs(v) for v in per_symbol.values())
    shares = {
        s: (_money(abs(v) / total_abs) if total_abs > 0 else Decimal("0"))
        for s, v in per_symbol.items()
    }
    top_symbol = max(per_symbol, key=lambda s: per_symbol[s]) if per_symbol else None
    return {
        "per_symbol_net_pnl": per_symbol,
        "abs_share_by_symbol": shares,
        "top_contributor": top_symbol,
    }


# ---------------------------------------------------------------------------
# Benchmarks (Must 2) — same machinery, same friction, same window
# ---------------------------------------------------------------------------


def always_long_provider(_symbol: str, _idx: int) -> int:
    return 1


def buy_hold_benchmark(
    universe: "SelectionUniverse",
    scenario: DepthAwareScenario,
    *,
    reference: TsmomConfig,
) -> dict[str, Any]:
    """Equal-weight buy-and-hold (the headline bar): one rebalance at the
    first aligned close, then hold; vol-targeting OFF."""
    config = replace(
        reference,
        config_id="tsmom_ev1_benchmark_buy_hold_equal_weight",
        mode="long_only",
        vol_targeting=False,
        entry_delay_candles=0,
    )
    first = _first_aligned_timestamp(universe)
    return simulate_tsmom_portfolio(
        universe,
        config,
        scenario,
        signal_provider=always_long_provider,
        rebalance_timestamps=frozenset({first} if first else set()),
    )


def always_long_no_vol_target_benchmark(
    universe: "SelectionUniverse",
    scenario: DepthAwareScenario,
    *,
    reference: TsmomConfig,
) -> dict[str, Any]:
    """Always-long, weekly equal-weight rebalance, NO vol target — isolates
    the combined value of trend timing + vol targeting."""
    config = replace(
        reference,
        config_id="tsmom_ev1_benchmark_always_long_no_vol_target",
        mode="long_only",
        vol_targeting=False,
        entry_delay_candles=0,
    )
    return simulate_tsmom_portfolio(
        universe, config, scenario, signal_provider=always_long_provider
    )


def always_long_vol_target_benchmark(
    universe: "SelectionUniverse",
    scenario: DepthAwareScenario,
    *,
    reference: TsmomConfig,
) -> dict[str, Any]:
    """Always-long WITH vol target ("vol-targeted beta") — isolates whether
    any edge comes from the trend signal or purely from vol targeting. This
    is the direct probe of the honest question (just leveraged/levered
    beta?)."""
    config = replace(
        reference,
        config_id="tsmom_ev1_benchmark_always_long_vol_target",
        mode="long_only",
        vol_targeting=True,
        entry_delay_candles=0,
    )
    return simulate_tsmom_portfolio(
        universe, config, scenario, signal_provider=always_long_provider
    )


def random_long_flat_benchmark(
    universe: "SelectionUniverse",
    scenario: DepthAwareScenario,
    *,
    reference: TsmomConfig,
    seeds: Sequence[int],
) -> list[dict[str, Any]]:
    """Seeded random long/flat baseline (sanity): the same vol-targeted
    machinery with a coin-flip signal per (symbol, decision candle)."""
    results: list[dict[str, Any]] = []
    for seed in seeds:
        rng = random.Random(seed)
        draws: dict[tuple[str, int], int] = {}

        def provider(symbol: str, idx: int) -> int:
            key = (symbol, idx)
            if key not in draws:
                draws[key] = 1 if rng.random() < Decimal("0.5") else 0
            return draws[key]

        config = replace(
            reference,
            config_id=f"{reference.config_id}_random_seed{seed}",
            mode="long_only",
        )
        result = simulate_tsmom_portfolio(
            universe, config, scenario, signal_provider=provider
        )
        result["seed"] = seed
        results.append(result)
    return results


def _first_aligned_timestamp(universe: "SelectionUniverse") -> datetime | None:
    for t in universe.timeline:
        if all(t in universe.index_by_time[s] for s in universe.symbols):
            return t
    return None


# ---------------------------------------------------------------------------
# OOS helpers (Must 3): train-only choice on RISK-ADJUSTED return
# ---------------------------------------------------------------------------


def timeline_split_time(universe: "SelectionUniverse", ratio: Decimal) -> datetime:
    return _sel_ev1.timeline_split_time(universe, ratio)


def select_best_config_id(
    results_by_config: dict[str, dict[str, Any]], *, train_up_to: datetime
) -> str:
    """Train-only parameter choice on train-window SHARPE (risk-adjusted, the
    phase's vocabulary), ties broken by config id."""

    def train_sharpe(result: dict[str, Any]) -> Decimal:
        stats = curve_stats(result["equity_curve"], up_to=train_up_to)
        sharpe = stats["sharpe_annual"]
        return sharpe if sharpe is not None else Decimal("-999")

    ranked = sorted(
        results_by_config.items(),
        key=lambda item: (-train_sharpe(item[1]), item[0]),
    )
    return ranked[0][0]


# ---------------------------------------------------------------------------
# The TSMOM gate (Must 3) — its own; routing-guarded
# ---------------------------------------------------------------------------


def evaluate_tsmom_gate(
    *,
    strategy_type: str,
    oos_strategy_stats: dict[str, Any],
    oos_buy_hold_stats: dict[str, Any],
    walk_forward_sharpe_edges: Sequence[Decimal | None],
    leave_one_out_edges: dict[str, Decimal | None],
    oos_trade_count: int,
    min_oos_days: int = MIN_OOS_DAYS,
    min_oos_trades: int = MIN_OOS_TRADES,
) -> dict[str, Any]:
    """TSMOM's verdict: risk-adjusted vs buy-and-hold, OOS, post-friction.

    Pass requires ALL of:
      - OOS Sharpe strictly above buy-and-hold's (post-conservative-friction);
      - OOS max drawdown NOT WORSE than buy-and-hold's (trend's claimed value
        is drawdown reduction — it must show up);
      - the anchored walk-forward Sharpe edge vs buy-and-hold positive in
        EVERY fold (params chosen on train only);
      - leave-one-out: dropping ANY single asset keeps the OOS Sharpe edge
        positive (the "not one name" bar, adapted for a liquid book);
      - enough OOS sample (days and trades).
    Never applied to per_symbol / cross_sectional_selection strategies.
    """
    ensure_gate_applies(strategy_type, TSMOM_GATE_ID)
    reasons: list[str] = []
    s_sharpe = oos_strategy_stats.get("sharpe_annual")
    b_sharpe = oos_buy_hold_stats.get("sharpe_annual")
    s_dd = oos_strategy_stats.get("max_drawdown_pct")
    b_dd = oos_buy_hold_stats.get("max_drawdown_pct")
    if s_sharpe is None or b_sharpe is None or s_sharpe <= b_sharpe:
        reasons.append("oos_sharpe_does_not_beat_buy_hold")
    if s_dd is None or b_dd is None or s_dd > b_dd:
        reasons.append("oos_drawdown_worse_than_buy_hold")
    if not walk_forward_sharpe_edges or any(
        edge is None or edge <= 0 for edge in walk_forward_sharpe_edges
    ):
        reasons.append("walk_forward_sharpe_edge_not_positive_in_every_fold")
    if not leave_one_out_edges or any(
        edge is None or edge <= 0 for edge in leave_one_out_edges.values()
    ):
        reasons.append("leave_one_out_breaks_risk_adjusted_edge")
    if (oos_strategy_stats.get("days") or 0) < min_oos_days:
        reasons.append("rejected_low_oos_days")
    if oos_trade_count < min_oos_trades:
        reasons.append("rejected_low_oos_trade_count")
    status = VERDICT_BEATS_BUY_HOLD if not reasons else VERDICT_NO_EDGE
    # Non-failing honesty qualifiers: the gate is a RELATIVE comparison vs
    # buy-and-hold, so a pass in a falling market can coexist with the
    # strategy itself losing money. Qualifiers make that impossible to miss —
    # a relative pass with negative absolute OOS Sharpe is defensive value
    # (drawdown reduction), NOT a deployable positive edge.
    qualifiers: list[str] = []
    if s_sharpe is not None and s_sharpe <= 0:
        qualifiers.append("oos_absolute_sharpe_not_positive_relative_edge_only")
    s_ret = oos_strategy_stats.get("total_return_pct")
    if s_ret is not None and s_ret <= 0:
        qualifiers.append("oos_absolute_return_negative_defensive_value_only")
    return {
        "gate_id": TSMOM_GATE_ID,
        "status": status,
        "passed": status == VERDICT_BEATS_BUY_HOLD,
        "qualifiers": qualifiers,
        "reason_codes": reasons or ["tsmom_gate_passed"],
        "oos_strategy": oos_strategy_stats,
        "oos_buy_hold": oos_buy_hold_stats,
        "oos_sharpe_edge_vs_buy_hold": (
            _money(s_sharpe - b_sharpe)
            if s_sharpe is not None and b_sharpe is not None
            else None
        ),
        "oos_drawdown_delta_vs_buy_hold_pct": (
            _money(s_dd - b_dd) if s_dd is not None and b_dd is not None else None
        ),
        "walk_forward_sharpe_edges": list(walk_forward_sharpe_edges),
        "leave_one_out_sharpe_edges": dict(sorted(leave_one_out_edges.items())),
        "oos_trade_count": oos_trade_count,
        "min_oos_days_required": min_oos_days,
        "min_oos_trades_required": min_oos_trades,
    }


def boundary_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "changes_production_money_flow_rules": False,
        "changes_per_symbol_lane_behavior_or_results": False,
        "changes_selection_lane_behavior_or_results": False,
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
        "perp_funding_not_modeled": True,
    }
