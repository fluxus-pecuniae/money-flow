"""TREND-SUITE1 — the canonical trend-following suite (research/evidence only).

TSMOM-EV1 tested ONE trend form (return-sign time-series momentum,
vol-targeted) and found it defensive-but-not-profitable (relative gate pass,
absolute OOS loss). That is one signal out of a documented family, and the
vol-targeting may have capped the upside: volatility targeting is known to
diminish returns in outlier trends, because strong trends run WITH high
volatility, so vol-targeting cuts exposure exactly in the big move.

TREND-SUITE1 tests the real suite — the canonical systems never tried here:

  - DONCHIAN CHANNEL BREAKOUT (the Turtle system): long on an N-day-high
    breakout, exit on the opposite (half-period) channel or an ATR/chandelier
    trailing stop. Canonical periods 20-day (S1, exit 10) and 55-day (S2,
    exit 20). A genuinely different signal than return-sign momentum.
  - MOVING-AVERAGE CROSSOVER (dual SMA): long while SMA_short > SMA_long;
    short MA in {10, 20, 30} x long MA in {50, 100, 200}.
  - MULTI-TIMEFRAME CONFIRMATION: the daily momentum signal only counts when
    the weekly (frozen at completed 7-day blocks) trailing-return sign
    agrees.
  - TSMOM BASELINE: the exact EV1 signal carried over, apples-to-apples.
  - ENSEMBLE: majority vote and average (fractional strength) of one
    canonical config per family above.

The key lever (Must 2): every signal runs under BOTH sizings —
  (a) vol-targeted (EV1 style: equal risk budget portfolio_vol_target / N,
      per-asset weight cap 0.40, gross cap 1.5x), and
  (b) non-vol-targeted equal-dollar (signal-strength-scaled 1/N, same gross
      leverage cap 1.5x, documented)
— so the report can say whether removing the vol cap converted defensive
into profitable, or just added drawdown.

Everything is judged by the SAME buy-and-hold risk-adjusted gate as
TSMOM-EV1 (``tsmom_ev1.evaluate_tsmom_gate``: OOS Sharpe AND max drawdown vs
equal-weight buy-and-hold, walk-forward folds, leave-one-out, sample
minimums, non-failing absolute-loss honesty qualifiers). Routed under
``strategy_type == "trend_suite"`` (prefix ``trend_suite1_``) by
``services.strategy_validation.strategy_types``; the route deliberately
shares ``TSMOM_GATE_ID`` — same headline question, new signals/sizing/exits.

Simulation reuses ``tsmom_ev1.simulate_tsmom_portfolio`` verbatim (closed-
candle decisions, next-open fills, EXEC-EV1 depth-aware friction at traded
notional, rebalance band, forced final close) through its ``signal_provider``
and ``rebalance_timestamps`` seams. Suite signals are long-only ({0, 1}
states; the TSMOM carry-over keeps its ±1 signal under ``mode=long_only``,
matching the EV1 train-chosen mode); EV1's own grid already covered
long_short and found no edge there.

Assumption boundaries (documented, never hidden): perp FUNDING is NOT
modeled (long-only books would typically PAY funding in bull regimes, so
absolute profits here are optimistic); depth/liquidity is MODELED from
candle volume (EXEC-EV1), never real order-book depth.

Pure and deterministic: Decimal arithmetic, no I/O, no network. Random
baselines use seeded ``random.Random`` only.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Sequence

from services.execution_quality.exec_ev1 import DepthAwareScenario

try:  # pragma: no cover - exercised implicitly by both import contexts
    from services.strategy_validation import sel_ev1 as _sel_ev1
    from services.strategy_validation import strategy_types as _strategy_types
    from services.strategy_validation import tsmom_ev1 as _tsmom
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

    _tsmom = _load_sibling("tsmom_ev1.py", "trend_suite1_tsmom_ev1")
    _sel_ev1 = sys.modules.get("tsmom_ev1_sel_ev1") or _load_sibling(
        "sel_ev1.py", "tsmom_ev1_sel_ev1"
    )
    _strategy_types = sys.modules.get("tsmom_ev1_strategy_types") or _load_sibling(
        "strategy_types.py", "tsmom_ev1_strategy_types"
    )

# Reused TSMOM-EV1 machinery (simulator, stats, gate, universe plumbing).
SelectionUniverse = _tsmom.SelectionUniverse
dataset_from_sv22_payload = _tsmom.dataset_from_sv22_payload
distribution_stats = _tsmom.distribution_stats
verify_point_in_time_scores = _tsmom.verify_point_in_time_scores
simulate_tsmom_portfolio = _tsmom.simulate_tsmom_portfolio
curve_stats = _tsmom.curve_stats
evaluate_tsmom_gate = _tsmom.evaluate_tsmom_gate
tsmom_signal = _tsmom.tsmom_signal
timeline_split_time = _tsmom.timeline_split_time
always_long_provider = _tsmom.always_long_provider
_first_aligned_timestamp = _tsmom._first_aligned_timestamp
_money = _tsmom._money
_atr = _sel_ev1._atr

STRATEGY_TYPE_TREND_SUITE = _strategy_types.STRATEGY_TYPE_TREND_SUITE
TREND_SUITE_ID_PREFIX = _strategy_types.TREND_SUITE_ID_PREFIX
TSMOM_GATE_ID = _strategy_types.TSMOM_GATE_ID
StrategyTypeRoutingError = _strategy_types.StrategyTypeRoutingError
ensure_gate_applies = _strategy_types.ensure_gate_applies

PHASE = "TREND-SUITE1"
STARTING_EQUITY = _tsmom.STARTING_EQUITY
LIQUID_UNIVERSE = _tsmom.LIQUID_UNIVERSE
EXCLUDED_THIN_SYMBOLS = _tsmom.EXCLUDED_THIN_SYMBOLS
TIMEFRAME = "1d"

# Signal families.
FAMILY_DONCHIAN = "donchian"
FAMILY_MA_CROSS = "ma_cross"
FAMILY_MTF = "mtf"
FAMILY_TSMOM = "tsmom"
FAMILY_ENSEMBLE = "ensemble"
FAMILIES = (FAMILY_DONCHIAN, FAMILY_MA_CROSS, FAMILY_MTF, FAMILY_TSMOM, FAMILY_ENSEMBLE)

# Bounded grid parameters (Must 1; documented, train-only choice).
DONCHIAN_PERIODS = ((20, 10), (55, 20))  # (entry-channel, exit-channel) Turtle S1/S2
MA_SHORT_PERIODS = (10, 20, 30)
MA_LONG_PERIODS = (50, 100, 200)
MA_CANONICAL = (20, 100)  # the mid-grid cell that also gets the ATR-trail exit
MTF_DAILY_LOOKBACKS = (30, 60, 90)
MTF_CANONICAL_LOOKBACK = 60  # the cell that also gets the ATR-trail exit
MTF_WEEKLY_LOOKBACK_WEEKS = 8
MTF_WEEK_DAYS = 7
TSMOM_LOOKBACKS = (30, 60, 90)  # the EV1 grid, carried over apples-to-apples
ENSEMBLE_KINDS = ("majority", "average")
ENSEMBLE_MAJORITY_THRESHOLD = 3  # of the 5 canonical members

# ATR/chandelier trailing stop (repo idiom: SEL-EV1 / GOAL-STRAT2 use
# ATR(14) and a 2.8x trail from the highest close since entry).
ATR_PERIOD = 14
ATR_TRAIL_MULTIPLE = Decimal("2.8")

# Exit styles.
EXIT_CHANNEL = "channel"  # Donchian opposite-channel exit (the Turtle exit)
EXIT_SIGNAL = "signal"  # hold while the signal is on; exit when it turns off
EXIT_ATR_TRAIL = "atr_trail"  # chandelier stop; re-entry needs a fresh signal

# Sizing variants (the key lever, Must 2).
SIZING_VOL_TARGETED = "vol_targeted"
SIZING_EQUAL_DOLLAR = "equal_dollar"
SIZINGS = (SIZING_VOL_TARGETED, SIZING_EQUAL_DOLLAR)
PORTFOLIO_VOL_TARGET = Decimal("0.20")  # EV1's train-chosen level
MAX_GROSS_LEVERAGE = _tsmom.MAX_GROSS_LEVERAGE  # 1.5x, shared documented cap

# Decision cadence: stop/cross exits are checked DAILY (a weekly cadence
# would let a hit stop ride for up to 6 more days); the TSMOM carry-over
# keeps EV1's weekly cadence apples-to-apples. The simulator's rebalance
# band (0.5% of equity) suppresses dust re-sizing between signal changes.
DAILY_CADENCE = 1
WEEKLY_CADENCE = _tsmom.REBALANCE_INTERVAL_DAYS

# Ensemble members: ONE canonical config per family (fixed and documented,
# never train-chosen): Turtle S1, Turtle S2, mid-grid MA cross, canonical
# MTF, and the EV1 train-chosen TSMOM lookback (30d — chosen on EV1's train
# split, not on this phase's data).
ENSEMBLE_MEMBERS = (
    (FAMILY_DONCHIAN, (20, 10), EXIT_CHANNEL),
    (FAMILY_DONCHIAN, (55, 20), EXIT_CHANNEL),
    (FAMILY_MA_CROSS, MA_CANONICAL, EXIT_SIGNAL),
    (FAMILY_MTF, (MTF_CANONICAL_LOOKBACK, MTF_WEEKLY_LOOKBACK_WEEKS), EXIT_SIGNAL),
    (FAMILY_TSMOM, (30,), EXIT_SIGNAL),
)

VERDICT_BEATS_BUY_HOLD = _tsmom.VERDICT_BEATS_BUY_HOLD
VERDICT_NO_EDGE = _tsmom.VERDICT_NO_EDGE
MIN_OOS_DAYS = _tsmom.MIN_OOS_DAYS
MIN_OOS_TRADES = _tsmom.MIN_OOS_TRADES


@dataclass(frozen=True, slots=True)
class TrendSuiteConfig:
    """A routed suite config. Field names deliberately match what
    ``simulate_tsmom_portfolio`` reads, so the EV1 simulator is reused
    verbatim through its provider/timestamps seams."""

    config_id: str
    strategy_type: str
    family: str
    family_params: tuple[int, ...]
    sizing: str
    exit_style: str
    decision_cadence_days: int
    portfolio_vol_target: Decimal = PORTFOLIO_VOL_TARGET
    mode: str = "long_only"
    vol_targeting: bool = True
    timeframe: str = TIMEFRAME
    vol_window_days: int = _tsmom.VOL_WINDOW_DAYS
    rebalance_interval_days: int = WEEKLY_CADENCE
    lookback_days: int = 0  # unused (signals always come from the provider)
    entry_delay_candles: int = 0


def _sizing_fields(sizing: str) -> dict[str, Any]:
    if sizing == SIZING_VOL_TARGETED:
        return {"sizing": sizing, "vol_targeting": True}
    if sizing == SIZING_EQUAL_DOLLAR:
        return {"sizing": sizing, "vol_targeting": False}
    raise ValueError(f"unknown_sizing:{sizing}")


def generate_trend_suite_configs() -> list[TrendSuiteConfig]:
    """The full bounded grid (46 configs); parameters are chosen on the
    train split only. Every signal cell exists in BOTH sizings so the
    vol-targeted vs non-vol-targeted comparison is always pairwise."""
    sizing_tag = {SIZING_VOL_TARGETED: "vt", SIZING_EQUAL_DOLLAR: "eq"}
    configs: list[TrendSuiteConfig] = []

    def add(config_id: str, **kwargs: Any) -> None:
        configs.append(
            TrendSuiteConfig(
                config_id=config_id,
                strategy_type=STRATEGY_TYPE_TREND_SUITE,
                **kwargs,
            )
        )

    for entry, exit_period in DONCHIAN_PERIODS:
        for exit_style in (EXIT_CHANNEL, EXIT_ATR_TRAIL):
            for sizing in SIZINGS:
                tag = "channel" if exit_style == EXIT_CHANNEL else "atr"
                add(
                    f"{TREND_SUITE_ID_PREFIX}donchian{entry}x{exit_period}_{tag}_{sizing_tag[sizing]}_1d",
                    family=FAMILY_DONCHIAN,
                    family_params=(entry, exit_period),
                    exit_style=exit_style,
                    decision_cadence_days=DAILY_CADENCE,
                    **_sizing_fields(sizing),
                )
    for short in MA_SHORT_PERIODS:
        for long in MA_LONG_PERIODS:
            for sizing in SIZINGS:
                add(
                    f"{TREND_SUITE_ID_PREFIX}ma{short}x{long}_signal_{sizing_tag[sizing]}_1d",
                    family=FAMILY_MA_CROSS,
                    family_params=(short, long),
                    exit_style=EXIT_SIGNAL,
                    decision_cadence_days=DAILY_CADENCE,
                    **_sizing_fields(sizing),
                )
    for sizing in SIZINGS:  # ATR-trail exit variant on the canonical MA cell
        short, long = MA_CANONICAL
        add(
            f"{TREND_SUITE_ID_PREFIX}ma{short}x{long}_atr_{sizing_tag[sizing]}_1d",
            family=FAMILY_MA_CROSS,
            family_params=(short, long),
            exit_style=EXIT_ATR_TRAIL,
            decision_cadence_days=DAILY_CADENCE,
            **_sizing_fields(sizing),
        )
    for lookback in MTF_DAILY_LOOKBACKS:
        for sizing in SIZINGS:
            add(
                f"{TREND_SUITE_ID_PREFIX}mtf{lookback}w{MTF_WEEKLY_LOOKBACK_WEEKS}_signal_{sizing_tag[sizing]}_1d",
                family=FAMILY_MTF,
                family_params=(lookback, MTF_WEEKLY_LOOKBACK_WEEKS),
                exit_style=EXIT_SIGNAL,
                decision_cadence_days=DAILY_CADENCE,
                **_sizing_fields(sizing),
            )
    for sizing in SIZINGS:  # ATR-trail exit variant on the canonical MTF cell
        add(
            f"{TREND_SUITE_ID_PREFIX}mtf{MTF_CANONICAL_LOOKBACK}w{MTF_WEEKLY_LOOKBACK_WEEKS}_atr_{sizing_tag[sizing]}_1d",
            family=FAMILY_MTF,
            family_params=(MTF_CANONICAL_LOOKBACK, MTF_WEEKLY_LOOKBACK_WEEKS),
            exit_style=EXIT_ATR_TRAIL,
            decision_cadence_days=DAILY_CADENCE,
            **_sizing_fields(sizing),
        )
    for lookback in TSMOM_LOOKBACKS:
        for sizing in SIZINGS:
            add(
                f"{TREND_SUITE_ID_PREFIX}tsmom{lookback}_signal_{sizing_tag[sizing]}_1d",
                family=FAMILY_TSMOM,
                family_params=(lookback,),
                exit_style=EXIT_SIGNAL,
                decision_cadence_days=WEEKLY_CADENCE,
                **_sizing_fields(sizing),
            )
    for kind_index, kind in enumerate(ENSEMBLE_KINDS):
        for sizing in SIZINGS:
            add(
                f"{TREND_SUITE_ID_PREFIX}ens_{kind}_{sizing_tag[sizing]}_1d",
                family=FAMILY_ENSEMBLE,
                family_params=(kind_index,),
                exit_style=EXIT_SIGNAL,
                decision_cadence_days=DAILY_CADENCE,
                **_sizing_fields(sizing),
            )
    return configs


# ---------------------------------------------------------------------------
# Causal signal state machines (Must 1). Every series is built by a single
# forward pass that reads only data at or before each index, so a value at
# idx is identical whether computed on the full series or on a truncation —
# the property ``verify_point_in_time_scores`` probes per family.
# ---------------------------------------------------------------------------


def donchian_state_series(
    highs: Sequence[Decimal],
    lows: Sequence[Decimal],
    closes: Sequence[Decimal],
    *,
    entry_period: int,
    exit_period: int,
    exit_style: str = EXIT_CHANNEL,
    atr_period: int = ATR_PERIOD,
    atr_multiple: Decimal = ATR_TRAIL_MULTIPLE,
) -> list[int]:
    """Turtle long-only state: enter when the close breaks the PRIOR
    ``entry_period``-day high; exit on the prior ``exit_period``-day low
    (channel) or on the chandelier trail (highest close since entry minus
    ``atr_multiple`` * ATR)."""
    n = len(closes)
    states = [0] * n
    in_position = False
    highest_close: Decimal | None = None
    for idx in range(n):
        if idx < entry_period:
            continue
        if not in_position:
            prior_high = max(highs[idx - entry_period : idx])
            if closes[idx] > prior_high:
                in_position = True
                highest_close = closes[idx]
        else:
            assert highest_close is not None
            highest_close = max(highest_close, closes[idx])
            if exit_style == EXIT_CHANNEL:
                prior_low = min(lows[idx - exit_period : idx])
                exit_hit = closes[idx] < prior_low
            else:
                atr = _atr(highs, lows, closes, idx, atr_period)
                exit_hit = atr is not None and closes[idx] < highest_close - atr * atr_multiple
            if exit_hit:
                in_position = False
                highest_close = None
        states[idx] = 1 if in_position else 0
    return states


def _sma_series(closes: Sequence[Decimal], period: int) -> list[Decimal | None]:
    prefix = [Decimal("0")]
    for close in closes:
        prefix.append(prefix[-1] + close)
    return [
        (prefix[idx + 1] - prefix[idx + 1 - period]) / Decimal(period)
        if idx + 1 >= period
        else None
        for idx in range(len(closes))
    ]


def ma_cross_state_series(
    closes: Sequence[Decimal], *, short_period: int, long_period: int
) -> list[int]:
    """Dual-SMA crossover, long-only: 1 while SMA_short > SMA_long."""
    short_sma = _sma_series(closes, short_period)
    long_sma = _sma_series(closes, long_period)
    return [
        1 if s is not None and l is not None and s > l else 0
        for s, l in zip(short_sma, long_sma)
    ]


def mtf_state_series(
    closes: Sequence[Decimal],
    *,
    daily_lookback: int,
    weekly_lookback_weeks: int = MTF_WEEKLY_LOOKBACK_WEEKS,
    week_days: int = MTF_WEEK_DAYS,
) -> list[int]:
    """Daily trailing-return sign gated by the weekly sign. The weekly
    signal is evaluated only at completed ``week_days``-day blocks (index
    (idx + 1) % 7 == 0) and FROZEN until the next block completes — a true
    lower-frequency confirmation, not just a longer lookback."""
    n = len(closes)
    states = [0] * n
    weekly_sig = 0
    weekly_lookback_days = weekly_lookback_weeks * week_days
    for idx in range(n):
        if (idx + 1) % week_days == 0:
            sig = tsmom_signal(closes, idx, weekly_lookback_days)
            weekly_sig = sig if sig is not None else 0
        daily_sig = tsmom_signal(closes, idx, daily_lookback)
        daily_sig = daily_sig if daily_sig is not None else 0
        states[idx] = 1 if (daily_sig == 1 and weekly_sig == 1) else 0
    return states


def tsmom_state_series(closes: Sequence[Decimal], *, lookback: int) -> list[int]:
    """The EV1 signal carried over verbatim: sign of the trailing return
    (±1; 0 for exact-flat or missing history). ``mode=long_only`` in the
    simulator zeroes the short side, matching the EV1 train-chosen mode."""
    return [
        (lambda sig: sig if sig is not None else 0)(tsmom_signal(closes, idx, lookback))
        for idx in range(len(closes))
    ]


def stop_overlaid_state_series(
    raw_states: Sequence[int],
    highs: Sequence[Decimal],
    lows: Sequence[Decimal],
    closes: Sequence[Decimal],
    *,
    atr_period: int = ATR_PERIOD,
    atr_multiple: Decimal = ATR_TRAIL_MULTIPLE,
) -> list[int]:
    """Chandelier trailing stop over a raw long-only signal: long while the
    raw signal is on, but a trail hit forces flat and DISARMS re-entry until
    the raw signal turns off and on again (a fresh signal)."""
    n = len(closes)
    states = [0] * n
    in_position = False
    armed = True
    highest_close: Decimal | None = None
    for idx in range(n):
        if raw_states[idx] <= 0:
            in_position = False
            armed = True
            highest_close = None
        elif in_position:
            assert highest_close is not None
            highest_close = max(highest_close, closes[idx])
            atr = _atr(highs, lows, closes, idx, atr_period)
            if atr is not None and closes[idx] < highest_close - atr * atr_multiple:
                in_position = False
                armed = False
                highest_close = None
        elif armed:
            in_position = True
            highest_close = closes[idx]
        states[idx] = 1 if in_position else 0
    return states


def ensemble_member_series(
    highs: Sequence[Decimal], lows: Sequence[Decimal], closes: Sequence[Decimal]
) -> list[list[int]]:
    """The five fixed canonical members, each mapped to a {0,1} long state
    (the TSMOM member's short side maps to 0 — the suite is long-only)."""
    members: list[list[int]] = []
    for family, params, exit_style in ENSEMBLE_MEMBERS:
        if family == FAMILY_DONCHIAN:
            entry, exit_period = params
            members.append(
                donchian_state_series(
                    highs, lows, closes,
                    entry_period=entry, exit_period=exit_period, exit_style=exit_style,
                )
            )
        elif family == FAMILY_MA_CROSS:
            short, long = params
            members.append(
                ma_cross_state_series(closes, short_period=short, long_period=long)
            )
        elif family == FAMILY_MTF:
            lookback, weeks = params
            members.append(
                mtf_state_series(closes, daily_lookback=lookback, weekly_lookback_weeks=weeks)
            )
        else:  # FAMILY_TSMOM
            (lookback,) = params
            members.append(
                [1 if s == 1 else 0 for s in tsmom_state_series(closes, lookback=lookback)]
            )
    return members


def ensemble_state_series(
    members: Sequence[Sequence[int]], *, kind: str
) -> list[int] | list[Decimal]:
    """Majority vote (>= 3 of 5 long -> 1) or average (fractional strength
    in {0, 0.2, ..., 1.0} — the trend-strength-scaled sizing probe)."""
    n = len(members[0])
    if kind == "majority":
        return [
            1 if sum(member[idx] for member in members) >= ENSEMBLE_MAJORITY_THRESHOLD else 0
            for idx in range(n)
        ]
    if kind == "average":
        count = Decimal(len(members))
        return [
            Decimal(sum(member[idx] for member in members)) / count for idx in range(n)
        ]
    raise ValueError(f"unknown_ensemble_kind:{kind}")


def build_strength_series(
    highs: Sequence[Decimal],
    lows: Sequence[Decimal],
    closes: Sequence[Decimal],
    config: TrendSuiteConfig,
) -> Sequence[int] | Sequence[Decimal]:
    """One symbol's causal strength series for a suite config."""
    if config.family == FAMILY_DONCHIAN:
        entry, exit_period = config.family_params
        return donchian_state_series(
            highs, lows, closes,
            entry_period=entry, exit_period=exit_period, exit_style=config.exit_style,
        )
    if config.family == FAMILY_MA_CROSS:
        short, long = config.family_params
        raw = ma_cross_state_series(closes, short_period=short, long_period=long)
        if config.exit_style == EXIT_ATR_TRAIL:
            return stop_overlaid_state_series(raw, highs, lows, closes)
        return raw
    if config.family == FAMILY_MTF:
        lookback, weeks = config.family_params
        raw = mtf_state_series(closes, daily_lookback=lookback, weekly_lookback_weeks=weeks)
        if config.exit_style == EXIT_ATR_TRAIL:
            return stop_overlaid_state_series(raw, highs, lows, closes)
        return raw
    if config.family == FAMILY_TSMOM:
        (lookback,) = config.family_params
        return tsmom_state_series(closes, lookback=lookback)
    if config.family == FAMILY_ENSEMBLE:
        (kind_index,) = config.family_params
        members = ensemble_member_series(highs, lows, closes)
        return ensemble_state_series(members, kind=ENSEMBLE_KINDS[kind_index])
    raise ValueError(f"unknown_family:{config.family}")


def strength_at(candles: Sequence[Any], idx: int, config: TrendSuiteConfig):
    """Point-wise scorer for ``verify_point_in_time_scores``: builds the
    series over EXACTLY the candles given (full, truncated, or future-
    tampered) and reads the value at idx. A causality break anywhere in a
    state machine makes the full-series value diverge from the truncated/
    tampered one, which the verifier flags."""
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    closes = [c.close for c in candles]
    return build_strength_series(highs, lows, closes, config)[idx]


# ---------------------------------------------------------------------------
# Simulation (reuses the EV1 simulator verbatim through its seams)
# ---------------------------------------------------------------------------


def aligned_timestamps(universe: "SelectionUniverse") -> list[datetime]:
    return [
        t
        for t in universe.timeline
        if all(t in universe.index_by_time[s] for s in universe.symbols)
    ]


def decision_timestamps(
    universe: "SelectionUniverse", cadence_days: int
) -> frozenset[datetime]:
    """Every ``cadence_days``-th aligned close — for cadence 7 these are
    exactly the timestamps the EV1 simulator's ``k % 7 == 0`` default picks."""
    return frozenset(aligned_timestamps(universe)[::cadence_days])


def simulate_trend_suite_portfolio(
    universe: "SelectionUniverse",
    config: TrendSuiteConfig,
    scenario: DepthAwareScenario,
) -> dict[str, Any]:
    """Run a suite config through the EV1 portfolio simulator: causal
    strength series per symbol -> ``signal_provider`` lookups, decision
    cadence -> explicit ``rebalance_timestamps``."""
    ensure_gate_applies(config.strategy_type, TSMOM_GATE_ID)
    series: dict[str, Sequence[int] | Sequence[Decimal]] = {}
    for symbol in universe.symbols:
        candles = universe.datasets[symbol].candles
        series[symbol] = build_strength_series(
            [c.high for c in candles],
            [c.low for c in candles],
            [c.close for c in candles],
            config,
        )

    def provider(symbol: str, idx: int):
        return series[symbol][idx]

    return simulate_tsmom_portfolio(
        universe,
        config,
        scenario,
        signal_provider=provider,
        rebalance_timestamps=decision_timestamps(universe, config.decision_cadence_days),
    )


# ---------------------------------------------------------------------------
# Benchmarks (same machinery, same friction, same window)
# ---------------------------------------------------------------------------


def buy_hold_benchmark(
    universe: "SelectionUniverse",
    scenario: DepthAwareScenario,
    *,
    reference: TrendSuiteConfig,
) -> dict[str, Any]:
    """Equal-weight buy-and-hold — the headline bar (identical in
    construction to the EV1 benchmark: one rebalance at the first aligned
    close, vol-targeting OFF, then hold)."""
    config = replace(
        reference,
        config_id=f"{TREND_SUITE_ID_PREFIX}benchmark_buy_hold_equal_weight",
        family=FAMILY_TSMOM,
        mode="long_only",
        vol_targeting=False,
        sizing=SIZING_EQUAL_DOLLAR,
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


def random_long_flat_benchmark(
    universe: "SelectionUniverse",
    scenario: DepthAwareScenario,
    *,
    reference: TrendSuiteConfig,
    seeds: Sequence[int],
) -> list[dict[str, Any]]:
    """Seeded random long/flat baseline through the same machinery (weekly
    cadence, the reference config's sizing)."""
    import random

    results: list[dict[str, Any]] = []
    weekly = decision_timestamps(universe, WEEKLY_CADENCE)
    for seed in seeds:
        rng = random.Random(seed)
        draws: dict[tuple[str, int], int] = {}

        def provider(symbol: str, idx: int) -> int:
            key = (symbol, idx)
            if key not in draws:
                draws[key] = 1 if rng.random() < 0.5 else 0
            return draws[key]

        config = replace(
            reference,
            config_id=f"{reference.config_id}_random_seed{seed}",
            mode="long_only",
        )
        result = simulate_tsmom_portfolio(
            universe, config, scenario, signal_provider=provider, rebalance_timestamps=weekly
        )
        result["seed"] = seed
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# Per-config OOS screen + the full gate (Must 2)
# ---------------------------------------------------------------------------


def per_config_screen(
    *,
    oos_strategy_stats: dict[str, Any],
    oos_buy_hold_stats: dict[str, Any],
    oos_trade_count: int,
) -> dict[str, Any]:
    """The OOS-comparison subset of the TSMOM gate, applied to EVERY config
    (Sharpe edge, drawdown-not-worse, sample minimums, absolute-loss honesty
    qualifiers). The FULL gate — adding walk-forward folds and leave-one-out
    — runs for the train-chosen config and each family champion; this screen
    deliberately reuses the gate's verdict vocabulary and never forces a
    positive."""
    reasons: list[str] = []
    s_sharpe = oos_strategy_stats.get("sharpe_annual")
    b_sharpe = oos_buy_hold_stats.get("sharpe_annual")
    s_dd = oos_strategy_stats.get("max_drawdown_pct")
    b_dd = oos_buy_hold_stats.get("max_drawdown_pct")
    if s_sharpe is None or b_sharpe is None or s_sharpe <= b_sharpe:
        reasons.append("oos_sharpe_does_not_beat_buy_hold")
    if s_dd is None or b_dd is None or s_dd > b_dd:
        reasons.append("oos_drawdown_worse_than_buy_hold")
    if (oos_strategy_stats.get("days") or 0) < MIN_OOS_DAYS:
        reasons.append("rejected_low_oos_days")
    if oos_trade_count < MIN_OOS_TRADES:
        reasons.append("rejected_low_oos_trade_count")
    qualifiers: list[str] = []
    if s_sharpe is not None and s_sharpe <= 0:
        qualifiers.append("oos_absolute_sharpe_not_positive_relative_edge_only")
    s_ret = oos_strategy_stats.get("total_return_pct")
    if s_ret is not None and s_ret <= 0:
        qualifiers.append("oos_absolute_return_negative_defensive_value_only")
    status = VERDICT_BEATS_BUY_HOLD if not reasons else VERDICT_NO_EDGE
    return {
        "screen_id": "trend_suite1_oos_screen",
        "full_gate": False,
        "status": status,
        "passed": status == VERDICT_BEATS_BUY_HOLD,
        "qualifiers": qualifiers,
        "reason_codes": reasons or ["oos_screen_passed"],
        "oos_sharpe_edge_vs_buy_hold": (
            _money(s_sharpe - b_sharpe)
            if s_sharpe is not None and b_sharpe is not None
            else None
        ),
        "oos_drawdown_delta_vs_buy_hold_pct": (
            _money(s_dd - b_dd) if s_dd is not None and b_dd is not None else None
        ),
        "oos_trade_count": oos_trade_count,
    }


# ---------------------------------------------------------------------------
# The vol-targeting comparison (the key lever, Must 2)
# ---------------------------------------------------------------------------

VT_VERDICT_CONVERTED = "removing_vol_target_converted_loss_to_profit_oos"
VT_VERDICT_IMPROVED_BOTH = "removing_vol_target_improved_return_and_drawdown_oos"
VT_VERDICT_RETURN_FOR_DD = "removing_vol_target_raised_return_and_drawdown_oos"
VT_VERDICT_JUST_RISK = "removing_vol_target_added_drawdown_without_more_return_oos"
VT_VERDICT_NO_CHANGE = "removing_vol_target_changed_little_oos"


def classify_vol_targeting_effect(
    vt_oos: dict[str, Any], eq_oos: dict[str, Any]
) -> str:
    """Deterministic, exhaustive classification of what removing the vol cap
    did OOS. 'Material' = return moves by more than 1 percentage point or
    drawdown by more than 2."""
    vt_ret, eq_ret = vt_oos.get("total_return_pct"), eq_oos.get("total_return_pct")
    vt_dd, eq_dd = vt_oos.get("max_drawdown_pct"), eq_oos.get("max_drawdown_pct")
    if None in (vt_ret, eq_ret, vt_dd, eq_dd):
        return VT_VERDICT_NO_CHANGE
    return_gain = eq_ret - vt_ret
    drawdown_gain = eq_dd - vt_dd  # positive = equal-dollar drew down MORE
    material_return = abs(return_gain) > Decimal("1")
    material_dd = abs(drawdown_gain) > Decimal("2")
    if vt_ret <= 0 and eq_ret > 0:
        return VT_VERDICT_CONVERTED
    if not material_return and not material_dd:
        return VT_VERDICT_NO_CHANGE
    if return_gain > 0 and drawdown_gain <= 0:
        return VT_VERDICT_IMPROVED_BOTH
    if return_gain > 0:
        return VT_VERDICT_RETURN_FOR_DD
    return VT_VERDICT_JUST_RISK


def boundary_flags() -> dict[str, bool]:
    flags = dict(_tsmom.boundary_flags())
    flags["signals_long_only_funding_would_be_paid_by_longs"] = True
    return flags
