"""SEL-EV1 — point-in-time cross-sectional breakout-selection evidence layer.

RESEARCH / EVIDENCE ONLY. This module tests the founder's selection hypothesis
(approach b): each period, rank the 23-symbol universe on breakout/relative
strength and hold only the strongest name(s), rotating as leadership changes.
It is routed under ``strategy_type == "cross_sectional_selection"`` by
``services.strategy_validation.strategy_types`` and must never be judged by the
per-symbol breadth/anti-concentration gate (and vice versa).

Honesty bar (the gate, not raw PnL):
  - beat a RANDOM-selection benchmark out-of-sample after conservative
    depth-aware friction (EXEC-EV1), across many seeds;
  - beat naive baselines (equal-weight buy-and-hold, naive past-return pick);
  - actually rotate (a strategy that is secretly always one name is a
    single-name bet, not selection — the reframed ZEC lesson);
  - survive chronological 70/30 and anchored walk-forward thirds OOS splits
    with parameters chosen on train only.

No-lookahead guarantee: the selection decision at a closed candle timestamp t
uses only candles with index <= the candle that closed at t. Fills happen at
the NEXT candle open (optionally +k candles late for the late-entry
sensitivity). ``verify_point_in_time_scores`` re-scores on truncated/tampered
history and is exercised by tests, including a deliberately leaky scorer that
must be caught.

Sizing is explicit and documented: a FIXED FRACTION of current equity per held
name (top-1 -> 50%, top-3 -> 30% each). Never full-equity-on-one-name, which is
what inflated the ZEC result in approach a.

Friction: every entry/exit/rotation fill is priced through the EXEC-EV1
depth-aware model (tier half-spread + square-root participation impact +
fill-probability chase, on top of SV2.3 fee/slippage/adverse-gap terms).
Concentrated breakout names are often thin exactly when chased, so impact
matters most here. Depth remains MODELED from candle volume, never real
order-book depth.

Pure and deterministic: Decimal arithmetic, no I/O, no network, no runtime
imports. Random benchmarks use seeded ``random.Random`` only.
"""

from __future__ import annotations

import importlib.util
import random
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Sequence

from services.execution_quality.exec_ev1 import (
    BPS,
    DepthAwareScenario,
    candle_dollar_volume,
    depth_aware_execution_price,
    entry_timing_cost_bps,
    fill_friction_bps,
)


def _load_sibling(filename: str, alias: str):
    """Load a sibling module by file path (repo idiom, see
    ``scripts/run_goal_strat1_discovery.py``) so research runners do not pull
    the heavy ``services.strategy_validation`` package ``__init__`` (DB/
    settings). Under pytest the package import works and is preferred so type
    identities stay unified."""
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


try:  # pragma: no cover - exercised implicitly by both import contexts
    from services.strategy_validation import goal_strat1 as _goal_strat1
    from services.strategy_validation import strategy_types as _strategy_types
except Exception:  # heavy package __init__ unavailable outside pytest
    _goal_strat1 = _load_sibling("goal_strat1.py", "sel_ev1_goal_strat1")
    _strategy_types = _load_sibling("strategy_types.py", "sel_ev1_strategy_types")

Candle = _goal_strat1.Candle
Dataset = _goal_strat1.Dataset
Metrics = _goal_strat1.Metrics
Trade = _goal_strat1.Trade
_atr = _goal_strat1._atr
_iso = _goal_strat1._iso
_json_ready = _goal_strat1._json_ready
_metrics = _goal_strat1._metrics
_metrics_to_dict = _goal_strat1._metrics_to_dict
_money = _goal_strat1._money
_parse_time = _goal_strat1._parse_time
_ratio = _goal_strat1._ratio
_trade_to_dict = _goal_strat1._trade_to_dict

SELECTION_GATE_ID = _strategy_types.SELECTION_GATE_ID
PER_SYMBOL_GATE_ID = _strategy_types.PER_SYMBOL_GATE_ID
STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION = (
    _strategy_types.STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION
)
STRATEGY_TYPE_PER_SYMBOL = _strategy_types.STRATEGY_TYPE_PER_SYMBOL
StrategyTypeRoutingError = _strategy_types.StrategyTypeRoutingError
ensure_gate_applies = _strategy_types.ensure_gate_applies
routing_policy = _strategy_types.routing_policy
strategy_type_for = _strategy_types.strategy_type_for

PHASE = "SEL-EV1"
STARTING_EQUITY = Decimal("10000")
ATR_PERIOD = 14

# Bounded signal set (Must 2). Small and documented; parameters are chosen on
# the train split only. No broad optimizer.
SIGNAL_DONCHIAN = "donchian_breakout_strength"
SIGNAL_VOL_MOMENTUM = "vol_adjusted_relative_momentum"
SIGNAL_NAIVE_PAST_RETURN = "naive_past_return"  # naive baseline only
SELECTION_SIGNALS = (SIGNAL_DONCHIAN, SIGNAL_VOL_MOMENTUM)
SELECTION_LOOKBACKS = (20, 40)
SELECTION_TOP_NS = (1, 3)
SELECTION_TIMEFRAMES = ("4h", "1d")
ATR_TRAIL_MULTIPLE = Decimal("2.8")
# Fixed fraction of current equity per held name. Documented sizing; never
# full-equity-on-one-name.
SLOT_FRACTION_BY_TOP_N = {1: Decimal("0.50"), 3: Decimal("0.30")}

LATE_ENTRY_LATENESS_STEPS = (0, 1, 2)

# Rotation/diversity thresholds (the reframed ZEC check). A selection strategy
# that is secretly one name almost all the time is flagged and failed.
MAX_SINGLE_SYMBOL_TIME_SHARE = Decimal("0.50")
MAX_SINGLE_SYMBOL_POSITIVE_PNL_SHARE = Decimal("0.60")
MIN_DISTINCT_SYMBOLS_HELD = 3
MIN_OOS_TRADES = 12


@dataclass(frozen=True, slots=True)
class SelectionConfig:
    config_id: str
    strategy_type: str
    signal: str
    lookback: int
    top_n: int
    timeframe: str
    slot_fraction: Decimal
    atr_trail_multiple: Decimal
    entry_delay_candles: int = 0


def generate_selection_configs() -> list[SelectionConfig]:
    """The full bounded grid: 2 signals x 2 lookbacks x top-1/top-3 x 4h/1d."""
    configs: list[SelectionConfig] = []
    for timeframe in SELECTION_TIMEFRAMES:
        for signal in SELECTION_SIGNALS:
            for lookback in SELECTION_LOOKBACKS:
                for top_n in SELECTION_TOP_NS:
                    configs.append(
                        SelectionConfig(
                            config_id=(
                                f"sel_ev1_{signal}_lb{lookback}_top{top_n}_{timeframe}"
                            ),
                            strategy_type=STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION,
                            signal=signal,
                            lookback=lookback,
                            top_n=top_n,
                            timeframe=timeframe,
                            slot_fraction=SLOT_FRACTION_BY_TOP_N[top_n],
                            atr_trail_multiple=ATR_TRAIL_MULTIPLE,
                        )
                    )
    return configs


def naive_past_return_config(timeframe: str, lookback: int = 20) -> SelectionConfig:
    """Naive baseline: pick the highest raw past return, same machinery."""
    return SelectionConfig(
        config_id=f"sel_ev1_naive_past_return_lb{lookback}_top1_{timeframe}",
        strategy_type=STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION,
        signal=SIGNAL_NAIVE_PAST_RETURN,
        lookback=lookback,
        top_n=1,
        timeframe=timeframe,
        slot_fraction=SLOT_FRACTION_BY_TOP_N[1],
        atr_trail_multiple=ATR_TRAIL_MULTIPLE,
    )


# ---------------------------------------------------------------------------
# Dataset adapter (SV2.2 raw candle payload -> goal_strat1 Dataset)
# ---------------------------------------------------------------------------


def dataset_from_sv22_payload(payload: dict[str, Any], *, source_path: str) -> Dataset:
    """Build a goal_strat1 ``Dataset`` from one SV2.2 raw candle artifact.

    ``Candle.timestamp`` is the candle CLOSE time — the moment the candle is
    fully closed and may be used for a selection decision.
    """
    symbol = str(payload.get("symbol") or "").upper()
    timeframe = str(payload.get("timeframe") or "").lower()
    candles: list[Candle] = []
    for row in payload.get("candles", []):
        candles.append(
            Candle(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=_parse_time(row["close_time"]),
                open=Decimal(str(row["open"])),
                high=Decimal(str(row["high"])),
                low=Decimal(str(row["low"])),
                close=Decimal(str(row["close"])),
                volume=Decimal(str(row.get("volume") or "0")),
                source_path=source_path,
            )
        )
    return Dataset(
        symbol=symbol,
        timeframe=timeframe,
        source_path=source_path,
        source_provenance="sv2_2_public_mainnet_refresh",
        canonical_evidence_status="sv2_2_research_refresh_not_canonical",
        candles=tuple(sorted(candles, key=lambda candle: candle.timestamp)),
    )


# ---------------------------------------------------------------------------
# Point-in-time selection scores (Must 2). Causal by construction: only
# candles[: idx + 1] are read.
# ---------------------------------------------------------------------------


def selection_score(
    candles: Sequence[Candle], idx: int, *, signal: str, lookback: int
) -> Decimal | None:
    """Score one symbol at one closed candle using only data up to that close.

    - donchian_breakout_strength: (close - prior N-period high) / ATR14 —
      ATR-normalized distance above the breakout level (cross-symbol
      comparable in volatility units). Positive only when actually above the
      prior high.
    - vol_adjusted_relative_momentum: lookback return / (ATR14 / close) —
      return per unit of volatility.
    - naive_past_return: raw lookback return (naive baseline).
    """
    if idx < lookback or idx >= len(candles):
        return None
    atr = _atr(
        [c.high for c in candles[: idx + 1]],
        [c.low for c in candles[: idx + 1]],
        [c.close for c in candles[: idx + 1]],
        idx,
        ATR_PERIOD,
    )
    if atr is None or atr <= 0:
        return None
    close = candles[idx].close
    if close <= 0:
        return None
    if signal == SIGNAL_DONCHIAN:
        prior_high = max(c.high for c in candles[idx - lookback : idx])
        return (close - prior_high) / atr
    past_close = candles[idx - lookback].close
    if past_close <= 0:
        return None
    lookback_return = (close - past_close) / past_close
    if signal == SIGNAL_VOL_MOMENTUM:
        atr_pct = atr / close
        if atr_pct <= 0:
            return None
        return lookback_return / atr_pct
    if signal == SIGNAL_NAIVE_PAST_RETURN:
        return lookback_return
    raise ValueError(f"unknown_selection_signal:{signal}")


def verify_point_in_time_scores(
    score_fn: Callable[[Sequence[Candle], int], Decimal | None],
    candles: Sequence[Candle],
    sample_indices: Sequence[int],
) -> bool:
    """True iff ``score_fn`` provably uses only data at or before each index.

    Two independent probes per sampled index:
      1. truncation — score on candles[: idx + 1] must equal the full-series
         score (a leaky scorer crashes or diverges);
      2. tampering — mutating every future candle's prices must not change
         the score.
    A synthetic leaky scorer must fail this check (tested in CI).
    """
    for idx in sample_indices:
        if idx < 0 or idx >= len(candles):
            continue
        full = score_fn(candles, idx)
        try:
            truncated = score_fn(candles[: idx + 1], idx)
        except IndexError:
            return False
        if truncated != full:
            return False
        if idx + 1 < len(candles):
            tampered = list(candles[: idx + 1]) + [
                replace(
                    c,
                    open=c.open * Decimal("7"),
                    high=c.high * Decimal("9"),
                    low=c.low * Decimal("3"),
                    close=c.close * Decimal("5"),
                )
                for c in candles[idx + 1 :]
            ]
            if score_fn(tampered, idx) != full:
                return False
    return True


# ---------------------------------------------------------------------------
# Universe: aligned point-in-time view over one timeframe (Must 1)
# ---------------------------------------------------------------------------


def _rolling_prior_high(highs: Sequence[Decimal], lookback: int) -> list[Decimal | None]:
    """O(n) monotonic-deque rolling max of ``highs[idx - lookback : idx]``.

    Exactly equals ``max(highs[idx - lookback : idx])`` (the form used by
    ``selection_score``); a consistency test enforces the equality.
    """
    output: list[Decimal | None] = []
    window: deque[int] = deque()
    for idx in range(len(highs)):
        if idx >= 1:
            j = idx - 1
            while window and highs[window[-1]] <= highs[j]:
                window.pop()
            window.append(j)
            while window and window[0] < idx - lookback:
                window.popleft()
        output.append(highs[window[0]] if idx >= lookback else None)
    return output


class SelectionUniverse:
    """Precomputed causal arrays for one timeframe across the universe.

    Score arrays are filled per (signal, lookback) on demand by calling the
    same ``selection_score`` used by the no-lookahead checker, so the
    simulator and the checker can never diverge.
    """

    def __init__(self, datasets: Sequence[Dataset]) -> None:
        timeframes = {dataset.timeframe for dataset in datasets}
        if len(timeframes) > 1:
            raise ValueError(f"mixed_timeframes_in_selection_universe:{sorted(timeframes)}")
        self.timeframe = next(iter(timeframes)) if timeframes else ""
        self.datasets: dict[str, Dataset] = {d.symbol: d for d in datasets}
        self.symbols: tuple[str, ...] = tuple(sorted(self.datasets))
        self.index_by_time: dict[str, dict[datetime, int]] = {
            symbol: {c.timestamp: i for i, c in enumerate(d.candles)}
            for symbol, d in self.datasets.items()
        }
        self.timeline: tuple[datetime, ...] = tuple(
            sorted({c.timestamp for d in datasets for c in d.candles})
        )
        self.candle_dicts: dict[str, list[dict[str, Any]]] = {
            symbol: [
                {
                    "open": str(c.open),
                    "high": str(c.high),
                    "low": str(c.low),
                    "close": str(c.close),
                    "volume": str(c.volume),
                }
                for c in d.candles
            ]
            for symbol, d in self.datasets.items()
        }
        self._atr_cache: dict[str, list[Decimal | None]] = {}
        self._score_cache: dict[tuple[str, str, int], list[Decimal | None]] = {}

    def atr_row(self, symbol: str) -> list[Decimal | None]:
        cached = self._atr_cache.get(symbol)
        if cached is None:
            candles = self.datasets[symbol].candles
            highs = [c.high for c in candles]
            lows = [c.low for c in candles]
            closes = [c.close for c in candles]
            cached = [_atr(highs, lows, closes, idx, ATR_PERIOD) for idx in range(len(candles))]
            self._atr_cache[symbol] = cached
        return cached

    def score_row(self, symbol: str, signal: str, lookback: int) -> list[Decimal | None]:
        key = (symbol, signal, lookback)
        cached = self._score_cache.get(key)
        if cached is None:
            candles = self.datasets[symbol].candles
            highs = [c.high for c in candles]
            closes = [c.close for c in candles]
            atr_row = self.atr_row(symbol)
            prior_highs = _rolling_prior_high(highs, lookback)
            cached = []
            for idx in range(len(candles)):
                atr = atr_row[idx]
                close = closes[idx]
                if idx < lookback or atr is None or atr <= 0 or close <= 0:
                    cached.append(None)
                    continue
                if signal == SIGNAL_DONCHIAN:
                    prior_high = prior_highs[idx]
                    if prior_high is None:
                        cached.append(None)
                        continue
                    cached.append((close - prior_high) / atr)
                    continue
                past_close = closes[idx - lookback]
                if past_close <= 0:
                    cached.append(None)
                    continue
                lookback_return = (close - past_close) / past_close
                if signal == SIGNAL_VOL_MOMENTUM:
                    cached.append(lookback_return / (atr / close))
                elif signal == SIGNAL_NAIVE_PAST_RETURN:
                    cached.append(lookback_return)
                else:
                    raise ValueError(f"unknown_selection_signal:{signal}")
            self._score_cache[key] = cached
        return cached


# ---------------------------------------------------------------------------
# Point-in-time cross-sectional portfolio simulator (Must 1)
# ---------------------------------------------------------------------------


def _adverse_gap_bps(signal_close: Decimal, fill_open: Decimal, side: str) -> Decimal:
    if signal_close <= 0:
        return Decimal("0")
    if side == "buy":
        return (fill_open - signal_close) / signal_close * BPS
    return (signal_close - fill_open) / signal_close * BPS


def simulate_selection_portfolio(
    universe: SelectionUniverse,
    config: SelectionConfig,
    scenario: DepthAwareScenario,
    *,
    score_provider: Callable[[str, int], Decimal | None] | None = None,
    rebalance_timestamps: frozenset[datetime] | None = None,
) -> dict[str, Any]:
    """Simulate the rotation portfolio with strict point-in-time selection.

    At each closed-candle timestamp t on the universe timeline:
      1. update ATR trailing stops for held names from the candle closed at t;
      2. (decision) rank every eligible symbol on its score computed from data
         up to and including the candle closed at t; the target book is the
         top-N names with score > 0 (cash for unfilled slots);
      3. rotate: names no longer in the target book exit at their NEXT candle
         open; new names enter at their NEXT candle open
         (+ ``entry_delay_candles`` for the late-entry sensitivity).

    Sizing: ``config.slot_fraction`` of CURRENT equity per entered name.
    Friction: every fill goes through EXEC-EV1 ``fill_friction_bps`` with the
    fill candle's dollar-volume as the liquidity proxy.

    ``score_provider`` overrides the config signal (used by the seeded random
    benchmark); ``rebalance_timestamps`` restricts decision moments (the
    matched-cadence random benchmark rotates exactly when the strategy did).
    """
    ensure_gate_applies(config.strategy_type, SELECTION_GATE_ID)
    score_rows: dict[str, list[Decimal | None]] = {}
    if score_provider is None:
        score_rows = {
            symbol: universe.score_row(symbol, config.signal, config.lookback)
            for symbol in universe.symbols
        }

    def score_at(symbol: str, idx: int) -> Decimal | None:
        if score_provider is not None:
            return score_provider(symbol, idx)
        return score_rows[symbol][idx]

    equity = STARTING_EQUITY
    positions: dict[str, dict[str, Any]] = {}
    trades: list[Trade] = []
    decision_timestamps: list[datetime] = []
    holding_candles: dict[str, int] = defaultdict(int)
    friction_bps_paid: list[Decimal] = []
    friction_quote_paid = Decimal("0")
    timing_costs: dict[int, list[Decimal]] = {step: [] for step in LATE_ENTRY_LATENESS_STEPS}

    def close_position(
        symbol: str, fill_idx: int | None, signal_idx: int, exit_reason: str
    ) -> None:
        nonlocal equity, friction_quote_paid
        position = positions.pop(symbol)
        dataset = universe.datasets[symbol]
        if fill_idx is None:
            raw_exit = dataset.candles[-1].close
            fill_candle = dataset.candles[-1]
            exit_time = fill_candle.timestamp
        else:
            raw_exit = dataset.candles[fill_idx].open
            fill_candle = dataset.candles[fill_idx]
            exit_time = fill_candle.timestamp
        quantity = position["quantity"]
        gap = _adverse_gap_bps(dataset.candles[signal_idx].close, raw_exit, "sell")
        friction = fill_friction_bps(
            scenario=scenario,
            symbol=symbol,
            notional=_money(raw_exit * quantity),
            liquidity_proxy=candle_dollar_volume(
                universe.candle_dicts[symbol][fill_idx if fill_idx is not None else -1]
            ),
            adverse_gap=gap,
        )
        exit_price = depth_aware_execution_price(
            raw_price=raw_exit, side="sell", friction_total_bps=friction.total_bps
        )
        friction_bps_paid.append(friction.total_bps)
        friction_quote_paid += _money((raw_exit - exit_price) * quantity)
        exit_fee = _money(exit_price * quantity * scenario.fee_bps / BPS)
        gross_pnl = _money((exit_price - position["entry_price"]) * quantity)
        net_pnl = _money(gross_pnl - exit_fee - position["entry_fee"])
        equity = _money(equity + net_pnl)
        trades.append(
            Trade(
                strategy_id=config.config_id,
                symbol=symbol,
                timeframe=config.timeframe,
                entry_time=position["entry_time"],
                exit_time=exit_time,
                entry_price=position["entry_price"],
                exit_price=exit_price,
                quantity=quantity,
                gross_pnl=gross_pnl,
                fees=_money(position["entry_fee"] + exit_fee),
                slippage=Decimal("0"),
                net_pnl=net_pnl,
                equity_after=equity,
                entry_reason=position["entry_reason"],
                exit_reason=exit_reason,
            )
        )

    def open_position(symbol: str, signal_idx: int, decision_time: datetime) -> None:
        nonlocal equity, friction_quote_paid
        dataset = universe.datasets[symbol]
        fill_idx = signal_idx + 1 + config.entry_delay_candles
        if fill_idx >= len(dataset.candles):
            return
        for step in LATE_ENTRY_LATENESS_STEPS:
            cost = entry_timing_cost_bps(
                universe.candle_dicts[symbol], signal_idx, step, "buy"
            )
            if cost is not None:
                timing_costs[step].append(cost)
        raw_entry = dataset.candles[fill_idx].open
        if raw_entry <= 0:
            return
        notional = _money(equity * config.slot_fraction)
        if notional <= 0:
            return
        gap = _adverse_gap_bps(dataset.candles[signal_idx].close, raw_entry, "buy")
        friction = fill_friction_bps(
            scenario=scenario,
            symbol=symbol,
            notional=notional,
            liquidity_proxy=candle_dollar_volume(universe.candle_dicts[symbol][fill_idx]),
            adverse_gap=gap,
        )
        entry_price = depth_aware_execution_price(
            raw_price=raw_entry, side="buy", friction_total_bps=friction.total_bps
        )
        quantity = notional / entry_price
        if quantity <= 0:
            return
        friction_bps_paid.append(friction.total_bps)
        friction_quote_paid += _money((entry_price - raw_entry) * quantity)
        entry_fee = _money(notional * scenario.fee_bps / BPS)
        atr_row = universe.atr_row(symbol)
        atr = atr_row[signal_idx]
        fill_candle = dataset.candles[fill_idx]
        positions[symbol] = {
            "entry_time": fill_candle.timestamp,
            "entry_price": entry_price,
            "quantity": quantity,
            "entry_fee": entry_fee,
            "entry_reason": config.signal,
            "highest_close": fill_candle.close,
            "stop": (entry_price - atr * config.atr_trail_multiple) if atr is not None else None,
        }
        decision_timestamps.append(decision_time)

    for t in universe.timeline:
        # 1) trailing-stop maintenance + end-of-data forced closes.
        stop_exits: list[str] = []
        for symbol in sorted(positions):
            idx = universe.index_by_time[symbol].get(t)
            if idx is None:
                last = universe.datasets[symbol].candles[-1]
                if t > last.timestamp:
                    close_position(
                        symbol, None, len(universe.datasets[symbol].candles) - 1,
                        "end_of_window_forced_close",
                    )
                continue
            holding_candles[symbol] += 1
            position = positions[symbol]
            candle = universe.datasets[symbol].candles[idx]
            position["highest_close"] = max(position["highest_close"], candle.close)
            atr = universe.atr_row(symbol)[idx]
            if atr is not None:
                trail = position["highest_close"] - atr * config.atr_trail_multiple
                position["stop"] = max(position["stop"] or trail, trail)
            if position["stop"] is not None and candle.close <= position["stop"]:
                stop_exits.append(symbol)

        # 2) decision: rank eligible symbols on point-in-time scores.
        is_decision_time = rebalance_timestamps is None or t in rebalance_timestamps
        if is_decision_time:
            scored: list[tuple[Decimal, str, int]] = []
            for symbol in universe.symbols:
                idx = universe.index_by_time[symbol].get(t)
                if idx is None or idx + 1 >= len(universe.datasets[symbol].candles):
                    continue
                score = score_at(symbol, idx)
                if score is not None and score > 0:
                    scored.append((score, symbol, idx))
            scored.sort(key=lambda row: (-row[0], row[1]))
            target_order = [(symbol, idx) for _, symbol, idx in scored[: config.top_n]]
            target = dict(target_order)
        else:
            target_order = [
                (symbol, universe.index_by_time[symbol][t])
                for symbol in positions
                if t in universe.index_by_time[symbol]
            ]
            target = dict(target_order)

        # 3) rotate: exits first (free slots + realize equity), then entries.
        for symbol in sorted(positions):
            idx = universe.index_by_time[symbol].get(t)
            if idx is None:
                continue
            stop_hit = symbol in stop_exits
            rotated_out = is_decision_time and symbol not in target
            if not (stop_hit or rotated_out):
                continue
            fill_idx = idx + 1 if idx + 1 < len(universe.datasets[symbol].candles) else None
            if fill_idx is None:
                # No next candle to fill the rotation/stop at: end-of-data close.
                exit_reason = "end_of_window_forced_close"
            else:
                exit_reason = "atr_trailing_stop_exit" if stop_hit else "rotated_out_of_top_n"
            close_position(symbol, fill_idx, idx, exit_reason)
        if is_decision_time:
            # Enter in score order so limited slots go to the strongest names.
            for symbol, signal_idx in target_order:
                if symbol in positions or len(positions) >= config.top_n:
                    continue
                open_position(symbol, signal_idx, t)

    for symbol in sorted(positions):
        close_position(
            symbol,
            None,
            len(universe.datasets[symbol].candles) - 1,
            "end_of_window_forced_close",
        )

    avg_friction = (
        sum(friction_bps_paid, Decimal("0")) / Decimal(len(friction_bps_paid))
        if friction_bps_paid
        else Decimal("0")
    )
    return {
        "config_id": config.config_id,
        "strategy_type": config.strategy_type,
        "scenario_id": scenario.scenario_id,
        "timeframe": config.timeframe,
        "trades": tuple(trades),
        "metrics": _metrics(trades),
        "decision_timestamps": tuple(decision_timestamps),
        "holding_candles_by_symbol": dict(sorted(holding_candles.items())),
        "avg_friction_bps": _money(avg_friction),
        "friction_paid_quote": _money(friction_quote_paid),
        "entry_timing_cost_bps_by_lateness": {
            step: (
                _money(sum(values, Decimal("0")) / Decimal(len(values))) if values else None
            )
            for step, values in timing_costs.items()
        },
    }


# ---------------------------------------------------------------------------
# Truth serums (Must 3)
# ---------------------------------------------------------------------------


def random_selection_benchmark(
    universe: SelectionUniverse,
    config: SelectionConfig,
    scenario: DepthAwareScenario,
    *,
    seeds: Sequence[int],
    rebalance_timestamps: frozenset[datetime],
) -> list[dict[str, Any]]:
    """Matched-cadence random benchmark — the headline comparison.

    Each seed replays the SAME portfolio machinery (same slots, sizing, ATR
    trail, friction) but replaces the selection score with a seeded uniform
    draw, and re-ranks ONLY at the timestamps where the strategy itself made
    an entry decision. Same trade cadence, random symbol choice: any edge left
    over random is selection skill, not timing/frequency artifacts.
    Deterministic and reproducible per seed.
    """
    results: list[dict[str, Any]] = []
    for seed in seeds:
        rng = random.Random(seed)
        draws: dict[tuple[str, int], Decimal] = {}

        def provider(symbol: str, idx: int) -> Decimal:
            key = (symbol, idx)
            if key not in draws:
                draws[key] = Decimal(str(rng.random()))
            return draws[key]

        random_config = replace(
            config, config_id=f"{config.config_id}_random_seed{seed}"
        )
        result = simulate_selection_portfolio(
            universe,
            random_config,
            scenario,
            score_provider=provider,
            rebalance_timestamps=rebalance_timestamps,
        )
        result["seed"] = seed
        results.append(result)
    return results


def equal_weight_buy_hold(
    universe: SelectionUniverse,
    scenario: DepthAwareScenario,
    *,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> dict[str, Any]:
    """Naive baseline: equal-weight buy-and-hold the whole universe.

    One friction-priced entry per symbol at the first candle open in the
    window, one friction-priced exit at the last candle close. 1/n of starting
    equity per symbol.
    """
    nets: dict[str, Decimal] = {}
    count = len(universe.symbols)
    if count == 0:
        return {"net_pnl": Decimal("0"), "per_symbol_net_pnl": {}}
    notional = _money(STARTING_EQUITY / Decimal(count))
    for symbol in universe.symbols:
        candles = universe.datasets[symbol].candles
        in_window = [
            (idx, c)
            for idx, c in enumerate(candles)
            if (start_time is None or c.timestamp >= start_time)
            and (end_time is None or c.timestamp <= end_time)
        ]
        if len(in_window) < 2:
            continue
        entry_idx, entry_candle = in_window[0]
        exit_idx, exit_candle = in_window[-1]
        entry_friction = fill_friction_bps(
            scenario=scenario,
            symbol=symbol,
            notional=notional,
            liquidity_proxy=candle_dollar_volume(universe.candle_dicts[symbol][entry_idx]),
            adverse_gap=Decimal("0"),
        )
        entry_price = depth_aware_execution_price(
            raw_price=entry_candle.open,
            side="buy",
            friction_total_bps=entry_friction.total_bps,
        )
        if entry_price <= 0:
            continue
        quantity = notional / entry_price
        exit_friction = fill_friction_bps(
            scenario=scenario,
            symbol=symbol,
            notional=_money(exit_candle.close * quantity),
            liquidity_proxy=candle_dollar_volume(universe.candle_dicts[symbol][exit_idx]),
            adverse_gap=Decimal("0"),
        )
        exit_price = depth_aware_execution_price(
            raw_price=exit_candle.close,
            side="sell",
            friction_total_bps=exit_friction.total_bps,
        )
        fees = _money((notional + exit_price * quantity) * scenario.fee_bps / BPS)
        nets[symbol] = _money((exit_price - entry_price) * quantity - fees)
    total = _money(sum(nets.values(), Decimal("0")))
    return {"net_pnl": total, "per_symbol_net_pnl": {k: nets[k] for k in sorted(nets)}}


def rotation_diversity_metrics(result: dict[str, Any]) -> dict[str, Any]:
    """The reframed ZEC check: is this selection, or a single-name bet?

    Measures distinct symbols held, rotation count, and the max single-symbol
    share of time-in-position and of positive PnL. Flags ``single_name_bet``
    when one symbol dominates either dimension.
    """
    holding = result["holding_candles_by_symbol"]
    trades: Sequence[Trade] = result["trades"]
    total_held = sum(holding.values())
    max_time_share = (
        max(_ratio(Decimal(v), Decimal(total_held)) for v in holding.values())
        if total_held > 0
        else Decimal("0")
    )
    positive_by_symbol: dict[str, Decimal] = defaultdict(Decimal)
    for trade in trades:
        if trade.net_pnl > 0:
            positive_by_symbol[trade.symbol] += trade.net_pnl
    positive_total = sum(positive_by_symbol.values(), Decimal("0"))
    max_pnl_share = (
        max(_ratio(v, positive_total) for v in positive_by_symbol.values())
        if positive_total > 0
        else Decimal("0")
    )
    distinct = len([s for s, v in holding.items() if v > 0])
    single_name_bet = (
        max_time_share > MAX_SINGLE_SYMBOL_TIME_SHARE
        or max_pnl_share > MAX_SINGLE_SYMBOL_POSITIVE_PNL_SHARE
        or (total_held > 0 and distinct < MIN_DISTINCT_SYMBOLS_HELD)
    )
    return {
        "distinct_symbols_held": distinct,
        "rotation_count": len(result["decision_timestamps"]),
        "trade_count": len(trades),
        "max_single_symbol_time_share": max_time_share,
        "max_single_symbol_positive_pnl_share": max_pnl_share,
        "max_time_share_threshold": MAX_SINGLE_SYMBOL_TIME_SHARE,
        "max_positive_pnl_share_threshold": MAX_SINGLE_SYMBOL_POSITIVE_PNL_SHARE,
        "min_distinct_symbols_required": MIN_DISTINCT_SYMBOLS_HELD,
        "single_name_bet": single_name_bet,
    }


def distribution_stats(values: Sequence[Decimal]) -> dict[str, Any]:
    if not values:
        return {"count": 0}
    ordered = sorted(values)
    n = len(ordered)

    def pct(q: Decimal) -> Decimal:
        # Nearest-rank percentile on the sorted sample.
        rank = max(1, min(n, int((q * n).to_integral_value(rounding="ROUND_CEILING"))))
        return ordered[rank - 1]

    return {
        "count": n,
        "min": ordered[0],
        "p05": pct(Decimal("0.05")),
        "p25": pct(Decimal("0.25")),
        "median": pct(Decimal("0.50")),
        "mean": _money(sum(ordered, Decimal("0")) / Decimal(n)),
        "p75": pct(Decimal("0.75")),
        "p95": pct(Decimal("0.95")),
        "max": ordered[-1],
    }


# ---------------------------------------------------------------------------
# OOS evaluation (Must 4)
# ---------------------------------------------------------------------------


def timeline_split_time(universe: SelectionUniverse, ratio: Decimal) -> datetime:
    timeline = universe.timeline
    if not timeline:
        raise ValueError("empty_universe_timeline")
    return timeline[min(len(timeline) - 1, int(len(timeline) * float(ratio)))]


def trades_net_pnl(trades: Sequence[Trade], *, after: datetime | None = None,
                   up_to: datetime | None = None) -> Decimal:
    total = Decimal("0")
    for trade in trades:
        if after is not None and trade.entry_time <= after:
            continue
        if up_to is not None and trade.entry_time > up_to:
            continue
        total += trade.net_pnl
    return _money(total)


def window_metrics(trades: Sequence[Trade], *, after: datetime | None = None,
                   up_to: datetime | None = None) -> Metrics:
    selected = [
        trade
        for trade in trades
        if (after is None or trade.entry_time > after)
        and (up_to is None or trade.entry_time <= up_to)
    ]
    return _metrics(selected)


def select_best_config_id(
    results_by_config: dict[str, dict[str, Any]], *, train_up_to: datetime
) -> str:
    """Train-only parameter choice: best train-window net PnL, ties by id."""
    ranked = sorted(
        results_by_config.items(),
        key=lambda item: (-trades_net_pnl(item[1]["trades"], up_to=train_up_to), item[0]),
    )
    return ranked[0][0]


# ---------------------------------------------------------------------------
# Selection gate (the verdict; never applied to per_symbol strategies)
# ---------------------------------------------------------------------------

VERDICT_BEATS_RANDOM = "beats_random_oos_post_friction"
VERDICT_NO_SKILL = "no_selection_skill_demonstrated"


def evaluate_selection_gate(
    *,
    strategy_type: str,
    oos_net_pnl: Decimal,
    oos_trade_count: int,
    walk_forward_oos_net_pnl: Decimal,
    random_oos_net_pnls: Sequence[Decimal],
    diversity: dict[str, Any],
    min_oos_trades: int = MIN_OOS_TRADES,
) -> dict[str, Any]:
    """Selection-strategy gate (Musts 3-4). Routing-guarded.

    Pass requires ALL of: positive chronological OOS net post-conservative
    friction; positive anchored walk-forward OOS net; OOS sample size; beats
    the random-selection distribution at its 95th percentile (empirical
    p <= ~0.05); and rotation diversity (not a single-name bet).
    """
    ensure_gate_applies(strategy_type, SELECTION_GATE_ID)
    reasons: list[str] = []
    if oos_net_pnl <= 0:
        reasons.append("oos_net_pnl_not_positive_post_friction")
    if walk_forward_oos_net_pnl <= 0:
        reasons.append("walk_forward_oos_net_pnl_not_positive")
    if oos_trade_count < min_oos_trades:
        reasons.append("rejected_low_oos_sample")
    random_stats = distribution_stats(list(random_oos_net_pnls))
    if random_stats.get("count", 0) > 0:
        beats = sum(1 for value in random_oos_net_pnls if oos_net_pnl > value)
        empirical_p = _ratio(
            Decimal(len(random_oos_net_pnls) - beats + 1),
            Decimal(len(random_oos_net_pnls) + 1),
        )
        if oos_net_pnl <= random_stats["p95"]:
            reasons.append("does_not_beat_random_selection_oos")
    else:
        beats = 0
        empirical_p = None
        reasons.append("random_benchmark_missing")
    if diversity.get("single_name_bet", True):
        reasons.append("single_name_bet_not_selection")
    status = VERDICT_BEATS_RANDOM if not reasons else VERDICT_NO_SKILL
    return {
        "gate_id": SELECTION_GATE_ID,
        "status": status,
        "passed": status == VERDICT_BEATS_RANDOM,
        "reason_codes": reasons or ["selection_gate_passed"],
        "oos_net_pnl": oos_net_pnl,
        "oos_trade_count": oos_trade_count,
        "walk_forward_oos_net_pnl": walk_forward_oos_net_pnl,
        "random_oos_distribution": random_stats,
        "random_seeds_beaten": beats,
        "empirical_p_value_vs_random": empirical_p,
        "random_p95_bar": random_stats.get("p95"),
        "diversity": diversity,
        "min_oos_trades_required": min_oos_trades,
    }


def boundary_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "changes_production_money_flow_rules": False,
        "changes_per_symbol_lane_behavior_or_results": False,
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
    }
