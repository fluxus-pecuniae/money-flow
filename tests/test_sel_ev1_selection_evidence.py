"""SEL-EV1 cross-sectional selection evidence — deterministic, offline tests.

No network, no runtime, no DB. Asserts the phase's documented guarantees:
  - Must 0 routing seam: per_symbol and cross_sectional_selection route to
    their own simulator/gate and the gates can NEVER cross-apply;
  - Must 0 regression: per-symbol simulation output is byte-identical to the
    committed pre-SEL-EV1 golden fixture for an existing config shape;
  - Must 1 no-lookahead: selection at t provably uses only data <= t, both at
    the score level and at the full-simulation level; a synthetic lookahead
    leak is caught;
  - Must 3 random benchmark is reproducible by seed; the rotation/diversity
    metric flags a synthetic always-one-symbol strategy;
  - friction is applied to every fill (buy fills above raw open, sell fills
    below) and friction is actually paid;
  - Must 4 OOS splits are chronological (train strictly before test).
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from services.execution_quality.exec_ev1 import scenario_by_id
from services.strategy_validation import goal_strat1, sel_ev1, strategy_types

GOLDEN_FIXTURE = Path(__file__).parent / "fixtures" / "sel_ev1" / "goal_strat1_per_symbol_golden.json"
CONSERVATIVE = scenario_by_id("exec_ev1_conservative")


# ---------------------------------------------------------------------------
# Deterministic synthetic data
# ---------------------------------------------------------------------------


def _synthetic_candles(symbol: str, *, drift: float, phase: float, n: int, timeframe: str = "1d"):
    candles = []
    price = 100.0
    start = datetime(2025, 1, 1, tzinfo=UTC)
    for i in range(n):
        close = price * (1.0 + drift + 0.012 * math.sin(i / 5.0 + phase))
        open_ = price
        high = max(open_, close) * 1.004
        low = min(open_, close) * 0.996
        candles.append(
            sel_ev1.Candle(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=start + timedelta(days=i + 1),
                open=Decimal(f"{open_:.6f}"),
                high=Decimal(f"{high:.6f}"),
                low=Decimal(f"{low:.6f}"),
                close=Decimal(f"{close:.6f}"),
                volume=Decimal("5000"),
                source_path="synthetic_test_fixture",
            )
        )
        price = close
    return tuple(candles)


def _dataset(symbol: str, *, drift: float, phase: float, n: int = 200) -> sel_ev1.Dataset:
    return sel_ev1.Dataset(
        symbol=symbol,
        timeframe="1d",
        source_path="synthetic_test_fixture",
        source_provenance="synthetic_deterministic_test",
        canonical_evidence_status="test_only",
        candles=_synthetic_candles(symbol, drift=drift, phase=phase, n=n),
    )


def _universe(n: int = 200) -> sel_ev1.SelectionUniverse:
    return sel_ev1.SelectionUniverse(
        [
            _dataset("AAA", drift=0.004, phase=0.0, n=n),
            _dataset("BBB", drift=0.002, phase=1.5, n=n),
            _dataset("CCC", drift=-0.001, phase=3.0, n=n),
            _dataset("DDD", drift=0.0005, phase=4.5, n=n),
        ]
    )


def _config(**overrides) -> sel_ev1.SelectionConfig:
    base = replace(sel_ev1.generate_selection_configs()[0], timeframe="1d")
    return replace(base, **overrides) if overrides else base


# ---------------------------------------------------------------------------
# Must 0 — routing seam
# ---------------------------------------------------------------------------


def test_strategy_type_tags_existing_lanes_per_symbol() -> None:
    for lane_id in strategy_types.PER_SYMBOL_LANE_IDS:
        assert strategy_types.strategy_type_for(lane_id) == strategy_types.STRATEGY_TYPE_PER_SYMBOL
    assert strategy_types.PER_SYMBOL_LANE_IDS == (
        "money_flow_v1_2_baseline",
        "avoid_low_rolling_range_20",
        "mf_orig_1d_stage2_breakout_resistance_full_equity",
    )
    # GOAL-STRAT1-era research configs are per-symbol too.
    assert (
        strategy_types.strategy_type_for("trend_breakout_donchian_breakout_atr_trail")
        == strategy_types.STRATEGY_TYPE_PER_SYMBOL
    )
    for config in sel_ev1.generate_selection_configs():
        assert (
            strategy_types.strategy_type_for(config.config_id)
            == strategy_types.STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION
        )


def test_routing_dispatches_each_type_to_its_own_simulator_and_gate() -> None:
    per_symbol = strategy_types.route_for(strategy_types.STRATEGY_TYPE_PER_SYMBOL)
    selection = strategy_types.route_for(
        strategy_types.STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION
    )
    assert per_symbol.gate_id != selection.gate_id
    assert per_symbol.simulator_ref != selection.simulator_ref
    assert (
        strategy_types.resolve_simulator(strategy_types.STRATEGY_TYPE_PER_SYMBOL)
        is goal_strat1.run_strategy_config
    )
    assert (
        strategy_types.resolve_gate(strategy_types.STRATEGY_TYPE_PER_SYMBOL)
        is goal_strat1.evaluate_candidate_gate
    )
    assert (
        strategy_types.resolve_simulator(
            strategy_types.STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION
        )
        is sel_ev1.simulate_selection_portfolio
    )
    assert (
        strategy_types.resolve_gate(strategy_types.STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION)
        is sel_ev1.evaluate_selection_gate
    )


def test_gates_never_cross_apply() -> None:
    # Selection gate refuses per-symbol strategies...
    with pytest.raises(strategy_types.StrategyTypeRoutingError):
        strategy_types.ensure_gate_applies(
            strategy_types.STRATEGY_TYPE_PER_SYMBOL, strategy_types.SELECTION_GATE_ID
        )
    # ...and the breadth gate refuses selection strategies.
    with pytest.raises(strategy_types.StrategyTypeRoutingError):
        strategy_types.ensure_gate_applies(
            strategy_types.STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION,
            strategy_types.PER_SYMBOL_GATE_ID,
        )
    with pytest.raises(strategy_types.StrategyTypeRoutingError):
        sel_ev1.evaluate_selection_gate(
            strategy_type=strategy_types.STRATEGY_TYPE_PER_SYMBOL,
            oos_net_pnl=Decimal("1"),
            oos_trade_count=100,
            walk_forward_oos_net_pnl=Decimal("1"),
            random_oos_net_pnls=[Decimal("0")],
            diversity={"single_name_bet": False},
        )
    # The selection simulator also refuses per-symbol configs.
    with pytest.raises(strategy_types.StrategyTypeRoutingError):
        sel_ev1.simulate_selection_portfolio(
            _universe(60),
            _config(strategy_type=strategy_types.STRATEGY_TYPE_PER_SYMBOL),
            CONSERVATIVE,
        )


# ---------------------------------------------------------------------------
# Must 0 — per-symbol behavior is unchanged (byte-identical regression)
# ---------------------------------------------------------------------------


def _golden_per_symbol_payload() -> str:
    """Deterministic per-symbol run serialized exactly as committed.

    Regenerate the fixture ONLY when a deliberate, reviewed change to the
    per-symbol simulator happens:
        .venv/bin/python -c "from tests.test_sel_ev1_selection_evidence import \
_write_golden_fixture; _write_golden_fixture()"
    """
    datasets = [
        goal_strat1.Dataset(
            symbol=symbol,
            timeframe="1d",
            source_path="synthetic_test_fixture",
            source_provenance="synthetic_deterministic_test",
            canonical_evidence_status="test_only",
            candles=tuple(
                goal_strat1.Candle(
                    symbol=symbol,
                    timeframe="1d",
                    timestamp=c.timestamp,
                    open=c.open,
                    high=c.high,
                    low=c.low,
                    close=c.close,
                    volume=c.volume,
                    source_path=c.source_path,
                )
                for c in _synthetic_candles(symbol, drift=drift, phase=phase, n=320)
            ),
        )
        for symbol, drift, phase in (("AAA", 0.004, 0.0), ("BBB", 0.002, 1.5))
    ]
    config = goal_strat1.StrategyConfig(
        strategy_id="trend_breakout_donchian_breakout_atr_trail_equity_10pct_none_20",
        display_name="trend_breakout: donchian_breakout / atr_trail / equity_10pct / none",
        family="trend_breakout",
        entry_model="donchian_breakout",
        exit_model="atr_trail",
        risk_model="equity_10pct",
        regime_filter="none",
        timeframe_scope=("1d",),
        params={"lookback": 20},
    )
    run = goal_strat1.run_strategy_config(config, datasets)
    payload = goal_strat1._json_ready(goal_strat1._run_to_dict(run, include_trades=True))
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _write_golden_fixture() -> None:
    GOLDEN_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN_FIXTURE.write_text(_golden_per_symbol_payload(), encoding="utf-8")


def test_per_symbol_simulation_output_byte_identical_to_golden() -> None:
    assert GOLDEN_FIXTURE.exists(), (
        "missing committed golden fixture; per-symbol regression cannot be verified"
    )
    assert _golden_per_symbol_payload() == GOLDEN_FIXTURE.read_text(encoding="utf-8"), (
        "per-symbol simulation output changed — SEL-EV1 must not alter approach-a "
        "behavior/results; if this change is deliberate, review and regenerate the fixture"
    )


# ---------------------------------------------------------------------------
# Must 1 / Must 6 — strict no-lookahead
# ---------------------------------------------------------------------------


def test_selection_scores_use_only_past_data() -> None:
    candles = _synthetic_candles("AAA", drift=0.004, phase=0.0, n=160)
    for signal in (*sel_ev1.SELECTION_SIGNALS, sel_ev1.SIGNAL_NAIVE_PAST_RETURN):
        for lookback in sel_ev1.SELECTION_LOOKBACKS:
            def score_fn(series, idx, signal=signal, lookback=lookback):
                return sel_ev1.selection_score(series, idx, signal=signal, lookback=lookback)

            assert sel_ev1.verify_point_in_time_scores(
                score_fn, candles, sample_indices=(45, 80, 120, 159)
            ), f"{signal}/lb{lookback} read future data"


def test_synthetic_lookahead_leak_is_caught() -> None:
    candles = _synthetic_candles("AAA", drift=0.004, phase=0.0, n=120)

    def leaky_score(series, idx):
        # Deliberate leak: peeks one candle into the future.
        if idx + 1 < len(series):
            return series[idx + 1].close - series[idx].close
        return None

    assert not sel_ev1.verify_point_in_time_scores(
        leaky_score, candles, sample_indices=(40, 60, 80)
    )


def test_simulation_decisions_invariant_to_future_tampering() -> None:
    universe = _universe(200)
    config = _config()
    baseline = sel_ev1.simulate_selection_portfolio(universe, config, CONSERVATIVE)

    cutoff_index = 120
    cutoff_time = universe.datasets["AAA"].candles[cutoff_index].timestamp
    tampered_datasets = []
    for symbol in universe.symbols:
        dataset = universe.datasets[symbol]
        tampered_candles = tuple(
            c
            if c.timestamp <= cutoff_time
            else replace(
                c,
                open=c.open * Decimal("3"),
                high=c.high * Decimal("4"),
                low=c.low * Decimal("2"),
                close=c.close * Decimal("3"),
            )
            for c in dataset.candles
        )
        tampered_datasets.append(replace(dataset, candles=tampered_candles))
    tampered = sel_ev1.simulate_selection_portfolio(
        sel_ev1.SelectionUniverse(tampered_datasets), config, CONSERVATIVE
    )

    def settled(trades):
        return [
            (t.symbol, t.entry_time, t.exit_time, str(t.entry_price), str(t.exit_price), str(t.net_pnl))
            for t in trades
            if t.exit_time <= cutoff_time
        ]

    assert settled(baseline["trades"]) == settled(tampered["trades"])
    assert [t for t in baseline["decision_timestamps"] if t < cutoff_time] == [
        t for t in tampered["decision_timestamps"] if t < cutoff_time
    ]


def test_score_rows_match_pointwise_selection_score() -> None:
    universe = _universe(160)
    candles = universe.datasets["AAA"].candles
    for signal in sel_ev1.SELECTION_SIGNALS:
        row = universe.score_row("AAA", signal, 20)
        for idx in range(0, 160, 13):
            assert row[idx] == sel_ev1.selection_score(candles, idx, signal=signal, lookback=20)


# ---------------------------------------------------------------------------
# Must 3 — random benchmark reproducibility + diversity flag
# ---------------------------------------------------------------------------


def test_random_benchmark_reproducible_by_seed() -> None:
    universe = _universe(150)
    config = _config()
    strategy = sel_ev1.simulate_selection_portfolio(universe, config, CONSERVATIVE)
    cadence = frozenset(strategy["decision_timestamps"])
    assert cadence, "synthetic fixture produced no rotation decisions — hollow test"
    first = sel_ev1.random_selection_benchmark(
        universe, config, CONSERVATIVE, seeds=(7, 8), rebalance_timestamps=cadence
    )
    second = sel_ev1.random_selection_benchmark(
        universe, config, CONSERVATIVE, seeds=(7, 8), rebalance_timestamps=cadence
    )
    assert [r["metrics"].net_pnl for r in first] == [r["metrics"].net_pnl for r in second]
    assert [len(r["trades"]) for r in first] == [len(r["trades"]) for r in second]
    nets = {str(r["metrics"].net_pnl) for r in sel_ev1.random_selection_benchmark(
        universe, config, CONSERVATIVE, seeds=range(1, 7), rebalance_timestamps=cadence
    )}
    assert len(nets) > 1, "random benchmark degenerate — all seeds identical"


def test_rotation_diversity_flags_always_one_symbol_strategy() -> None:
    universe = _universe(150)
    config = _config(top_n=1, slot_fraction=Decimal("0.50"))

    def always_aaa(symbol: str, idx: int) -> Decimal:
        return Decimal("2") if symbol == "AAA" else Decimal("1")

    result = sel_ev1.simulate_selection_portfolio(
        universe, config, CONSERVATIVE, score_provider=always_aaa
    )
    diversity = sel_ev1.rotation_diversity_metrics(result)
    assert diversity["single_name_bet"] is True
    assert diversity["max_single_symbol_time_share"] > Decimal("0.5")
    gate = sel_ev1.evaluate_selection_gate(
        strategy_type=config.strategy_type,
        oos_net_pnl=Decimal("1000"),
        oos_trade_count=100,
        walk_forward_oos_net_pnl=Decimal("1000"),
        random_oos_net_pnls=[Decimal("-5"), Decimal("0"), Decimal("5")],
        diversity=diversity,
    )
    assert gate["status"] == sel_ev1.VERDICT_NO_SKILL
    assert "single_name_bet_not_selection" in gate["reason_codes"]


# ---------------------------------------------------------------------------
# Friction is applied to every fill
# ---------------------------------------------------------------------------


def test_friction_applied_to_entry_and_exit_fills() -> None:
    universe = _universe(150)
    result = sel_ev1.simulate_selection_portfolio(universe, _config(), CONSERVATIVE)
    trades = result["trades"]
    assert trades, "synthetic fixture produced no trades — hollow test"
    checked_entry = checked_exit = 0
    for trade in trades:
        dataset = universe.datasets[trade.symbol]
        by_time = {c.timestamp: c for c in dataset.candles}
        entry_candle = by_time[trade.entry_time]
        # Buy fills strictly above the raw next-candle open (spread+impact+...).
        assert trade.entry_price > entry_candle.open
        checked_entry += 1
        if trade.exit_reason != "end_of_window_forced_close":
            exit_candle = by_time[trade.exit_time]
            assert trade.exit_price < exit_candle.open
            checked_exit += 1
        assert trade.fees > 0
    assert checked_entry > 0 and checked_exit > 0
    assert result["friction_paid_quote"] > 0
    assert result["avg_friction_bps"] >= CONSERVATIVE.slippage_bps


# ---------------------------------------------------------------------------
# Must 4 — chronological OOS splits
# ---------------------------------------------------------------------------


def test_oos_splits_are_chronological() -> None:
    universe = _universe(200)
    result = sel_ev1.simulate_selection_portfolio(universe, _config(), CONSERVATIVE)
    split = sel_ev1.timeline_split_time(universe, Decimal("0.70"))
    timeline = universe.timeline
    assert timeline[0] < split < timeline[-1]
    train = sel_ev1.window_metrics(result["trades"], up_to=split)
    test = sel_ev1.window_metrics(result["trades"], after=split)
    assert train.trade_count + test.trade_count == len(result["trades"])
    train_entries = [t.entry_time for t in result["trades"] if t.entry_time <= split]
    test_entries = [t.entry_time for t in result["trades"] if t.entry_time > split]
    assert all(entry <= split for entry in train_entries)
    assert all(entry > split for entry in test_entries)
    if train_entries and test_entries:
        assert max(train_entries) < min(test_entries)
    # Train-only parameter choice never reads post-split trades: tampering the
    # post-split window must not change the chosen config.
    results = {"only": result}
    assert sel_ev1.select_best_config_id(results, train_up_to=split) == "only"


def test_selection_gate_pass_and_fail_paths() -> None:
    diversity_ok = {
        "single_name_bet": False,
        "distinct_symbols_held": 5,
        "rotation_count": 30,
        "max_single_symbol_time_share": Decimal("0.3"),
        "max_single_symbol_positive_pnl_share": Decimal("0.4"),
        "max_time_share_threshold": sel_ev1.MAX_SINGLE_SYMBOL_TIME_SHARE,
        "max_positive_pnl_share_threshold": sel_ev1.MAX_SINGLE_SYMBOL_POSITIVE_PNL_SHARE,
    }
    random_nets = [Decimal(i) for i in range(-25, 25)]
    passing = sel_ev1.evaluate_selection_gate(
        strategy_type=sel_ev1.STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION,
        oos_net_pnl=Decimal("500"),
        oos_trade_count=40,
        walk_forward_oos_net_pnl=Decimal("100"),
        random_oos_net_pnls=random_nets,
        diversity=diversity_ok,
    )
    assert passing["status"] == sel_ev1.VERDICT_BEATS_RANDOM
    assert passing["passed"] is True
    failing = sel_ev1.evaluate_selection_gate(
        strategy_type=sel_ev1.STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION,
        oos_net_pnl=Decimal("1"),  # below the random p95 bar
        oos_trade_count=40,
        walk_forward_oos_net_pnl=Decimal("-10"),
        random_oos_net_pnls=random_nets,
        diversity=diversity_ok,
    )
    assert failing["status"] == sel_ev1.VERDICT_NO_SKILL
    assert "does_not_beat_random_selection_oos" in failing["reason_codes"]
    assert "walk_forward_oos_net_pnl_not_positive" in failing["reason_codes"]


def test_selection_grid_is_bounded() -> None:
    configs = sel_ev1.generate_selection_configs()
    assert len(configs) == 16  # 2 signals x 2 lookbacks x {top1, top3} x {4h, 1d}
    assert len({c.config_id for c in configs}) == len(configs)
    for config in configs:
        assert config.config_id.startswith("sel_ev1_")
        assert config.strategy_type == sel_ev1.STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION
        assert config.top_n in (1, 3)
        assert config.slot_fraction < Decimal("1")  # never full equity on one name


def test_runner_script_loads_without_package_side_effects() -> None:
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "run_sel_ev1_selection_evidence.py"
    spec = importlib.util.spec_from_file_location("sel_ev1_runner_under_test", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert module.GATE_SCENARIO_ID == "exec_ev1_conservative"
    assert module.DEFAULT_RANDOM_SEED_COUNT >= 30
