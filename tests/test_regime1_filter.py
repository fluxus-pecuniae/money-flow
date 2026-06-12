"""REGIME1 — deterministic, offline tests (no network, no DB, no runtime).

Asserts the phase's documented guarantees:
  - the regime state computes exactly (breadth counting, threshold edge,
    both BTC rules, warm-up returns None — never a guessed state);
  - no-lookahead: truncation + future-tampering probes cannot change a
    state; the gated signal provider is causal through the simulator;
  - the filter's mechanism works on a synthetic crash fixture: gating
    reduces max drawdown vs always-long through the REAL simulator;
  - whipsaw cost is surfaced (flip counts, false vs true risk-off spells,
    return given up) — never hidden;
  - the importable gate works (state lookup at/before as_of; refuses times
    before its first state; resolvable through the strategy_types seam);
  - the risk-tool gate's semantics: every reason fires; a pass is only the
    drawdown-reduction verdict and ALWAYS carries the not-alpha qualifier;
  - honest framing: the disclaimer travels on every surface (state, gate
    output, CLI artifact, committed summary) and the committed verdict is
    the honest FAIL with the hindsight block labeled not-a-verdict;
  - the deployed default config is pinned to the committed train-only
    choice (re-tuning without new evidence fails CI).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from services.execution_quality.exec_ev1 import scenario_by_id
from services.strategy_validation import regime1 as rg
from services.strategy_validation import strategy_types
from services.strategy_validation import tsmom_ev1 as tsmom
from services.strategy_validation.goal_strat1 import Candle, Dataset
from services.strategy_validation.sel_ev1 import SelectionUniverse

REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = REPO_ROOT / "docs" / "regime1_market_regime_risk_off_filter_evidence_summary.json"
CONSERVATIVE = scenario_by_id("exec_ev1_conservative")
T0 = datetime(2025, 1, 1, tzinfo=UTC)


def make_dataset(symbol: str, prices: list[float]) -> Dataset:
    candles = []
    for i, price in enumerate(prices):
        p = Decimal(str(price))
        candles.append(
            Candle(
                symbol=symbol,
                timeframe="1d",
                timestamp=T0 + timedelta(days=i + 1),
                open=p,
                high=p * Decimal("1.001"),
                low=p * Decimal("0.999"),
                close=p,
                volume=Decimal("50000000"),
                source_path="synthetic",
            )
        )
    return Dataset(
        symbol=symbol,
        timeframe="1d",
        source_path="synthetic",
        source_provenance="synthetic",
        canonical_evidence_status="synthetic",
        candles=tuple(candles),
    )


def trend_prices(n: int, *, up: bool, start: float = 100.0, step: float = 0.5) -> list[float]:
    return [start + (step * i if up else -step * i * 0.5) for i in range(n)]


def crash_prices(n: int, crash_at: int) -> list[float]:
    # Steady uptrend, then a -50% grind: the synthetic crash fixture.
    prices = []
    level = 100.0
    for i in range(n):
        level = level * (1.01 if i < crash_at else 0.99)
        prices.append(level)
    return prices


def small_config(config_id: str = "regime1_lb5_br5_btc_vote_1d", *, btc_rule: str = "vote") -> rg.RegimeConfig:
    return rg.RegimeConfig(
        config_id=config_id, lookback_days=5, breadth_threshold=Decimal("0.5"), btc_rule=btc_rule
    )


# ---------------------------------------------------------------------------
# The regime state
# ---------------------------------------------------------------------------


def test_regime_state_breadth_threshold_and_btc_rules():
    closes = {
        "BTC": [Decimal(p) for p in (100, 101, 102, 103, 104, 105)],  # up
        "ETH": [Decimal(p) for p in (100, 99, 98, 97, 96, 95)],  # down
        "SOL": [Decimal(p) for p in (100, 101, 103, 104, 105, 106)],  # up
        "XRP": [Decimal(p) for p in (100, 99, 97, 96, 95, 94)],  # down
    }
    idx = {s: 5 for s in closes}
    state = rg.regime_state_at(closes, idx, small_config())
    assert state is not None
    assert state["breadth"] == Decimal("0.5") and state["breadth_up_count"] == 2
    assert state["risk_on"] and state["state"] == rg.STATE_RISK_ON  # 0.5 >= 0.5, vote rule
    assert state["btc_trend_up"] is True
    assert state["risk_score"] == state["breadth"]
    assert "not alpha" in state["disclaimer"].lower() or "NOT ALPHA" in state["disclaimer"]
    # required rule with BTC down flips the same breadth to risk_off.
    closes_btc_down = dict(closes)
    closes_btc_down["BTC"] = [Decimal(p) for p in (100, 99, 98, 97, 96, 95)]
    closes_btc_down["ETH"] = [Decimal(p) for p in (100, 101, 102, 103, 104, 105)]
    state_req = rg.regime_state_at(closes_btc_down, idx, small_config(btc_rule="required"))
    assert state_req is not None
    assert state_req["breadth"] == Decimal("0.5")
    assert not state_req["risk_on"]  # breadth met, BTC down, required rule
    state_vote = rg.regime_state_at(closes_btc_down, idx, small_config(btc_rule="vote"))
    assert state_vote is not None and state_vote["risk_on"]


def test_warm_up_returns_none_never_a_guessed_state():
    closes = {"BTC": [Decimal("100")] * 4, "ETH": [Decimal("100")] * 4}
    assert rg.regime_state_at(closes, {"BTC": 3, "ETH": 3}, small_config()) is None


def test_no_lookahead_truncation_and_tampering():
    datasets = [
        make_dataset("BTC", trend_prices(40, up=True)),
        make_dataset("ETH", trend_prices(40, up=False)),
        make_dataset("SOL", trend_prices(40, up=True)),
    ]
    universe = SelectionUniverse(datasets)
    times = [universe.timeline[i] for i in (10, 20, 30)]
    assert rg.verify_regime_point_in_time(universe, small_config(), times)


# ---------------------------------------------------------------------------
# The synthetic crash fixture: gating must reduce drawdown via the simulator
# ---------------------------------------------------------------------------


def _book_config(label: str):
    return tsmom.TsmomConfig(
        config_id=f"regime1_book_{label}",
        strategy_type=tsmom.STRATEGY_TYPE_TIME_SERIES_MOMENTUM,
        lookback_days=60,
        portfolio_vol_target=Decimal("0.20"),
        mode="long_only",
        vol_targeting=False,
        rebalance_interval_days=7,
    )


def test_gating_reduces_drawdown_on_synthetic_crash():
    n, crash_at = 160, 80
    datasets = [make_dataset(s, crash_prices(n, crash_at)) for s in ("BTC", "ETH", "SOL")]
    universe = SelectionUniverse(datasets)
    config = small_config()
    always = tsmom.simulate_tsmom_portfolio(
        universe, _book_config("always"), CONSERVATIVE, signal_provider=rg.always_long_provider
    )
    gated = tsmom.simulate_tsmom_portfolio(
        universe,
        _book_config("gated"),
        CONSERVATIVE,
        signal_provider=rg.gated_long_provider(universe, config),
    )
    always_dd = rg.curve_stats(always["equity_curve"])["max_drawdown_pct"]
    gated_dd = rg.curve_stats(gated["equity_curve"])["max_drawdown_pct"]
    assert always_dd > Decimal("20")  # the crash is real for the long book
    assert gated_dd < always_dd * Decimal("0.5")  # gating steps aside


# ---------------------------------------------------------------------------
# Whipsaw cost surfaced
# ---------------------------------------------------------------------------


def test_whipsaw_stats_count_flips_and_classify_spells():
    times = [T0 + timedelta(days=i) for i in range(10)]
    on = {"risk_on": True}
    off = {"risk_on": False}
    series = [
        (times[0], on), (times[1], off), (times[2], off), (times[3], on),
        (times[4], off), (times[5], on), (times[6], on), (times[7], off),
        (times[8], off), (times[9], on),
    ]
    # Always-long book: gains during the first risk-off spell (FALSE
    # risk-off), loses during the second (true), gains again in the third.
    curve = [
        (times[0], Decimal("100")), (times[1], Decimal("101")), (times[2], Decimal("103")),
        (times[3], Decimal("103")), (times[4], Decimal("99")), (times[5], Decimal("99")),
        (times[6], Decimal("100")), (times[7], Decimal("101")), (times[8], Decimal("102")),
        (times[9], Decimal("102")),
    ]
    stats = rg.whipsaw_stats(series, curve)
    assert stats["state_flips"] == 6
    assert stats["risk_off_spells"] == 3
    assert stats["risk_off_days"] == 5
    assert stats["false_risk_off_spells"] == 2  # spells 1 and 3 gained
    assert Decimal(str(stats["return_given_up_in_false_risk_off"])) == Decimal("5")
    assert Decimal(str(stats["drawdown_avoided_in_true_risk_off"])) == Decimal("-4")
    assert len(stats["spell_detail"]) == 3
    assert stats["spell_detail"][0]["false_risk_off"] is True


# ---------------------------------------------------------------------------
# The importable gate
# ---------------------------------------------------------------------------


def test_regime_gate_lookup_and_refusal_before_first_state():
    datasets = [
        make_dataset("BTC", trend_prices(30, up=True)),
        make_dataset("ETH", trend_prices(30, up=True)),
    ]
    gate = rg.build_regime_gate(datasets, small_config())
    assert gate.is_risk_on(gate.last_state_time)
    # As-of between two closes resolves to the latest state at or before.
    mid = gate.first_state_time + timedelta(hours=12)
    assert gate.is_risk_on(mid) == gate.is_risk_on(gate.first_state_time)
    with pytest.raises(rg.RegimeGateError, match="no_regime_state_at_or_before"):
        gate.is_risk_on(gate.first_state_time - timedelta(days=1))
    state = gate.state_at(gate.last_state_time)
    assert state["disclaimer"] == rg.DISCLAIMER
    with pytest.raises(rg.RegimeGateError):
        rg.RegimeGate([], small_config())


def test_strategy_types_seam_resolves_the_gate_builder():
    builder = strategy_types.resolve_regime_filter()
    assert builder is rg.build_regime_gate
    datasets = [
        make_dataset("BTC", trend_prices(40, up=False)),
        make_dataset("ETH", trend_prices(40, up=False)),
    ]
    gate = builder(datasets, small_config())
    assert not gate.is_risk_on(gate.last_state_time)  # broad downtrend => risk_off


def test_default_config_is_pinned_to_the_committed_train_choice():
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    assert rg.DEFAULT_CONFIG.config_id == summary["train_only_choice"]["chosen_config"]
    assert rg.DEFAULT_CONFIG.config_id == summary["reusable_gate"]["default_config_pinned"]


# ---------------------------------------------------------------------------
# The risk-tool gate semantics
# ---------------------------------------------------------------------------


def _healthy_gate_kwargs():
    return {
        "always_oos_stats": {
            "days": 300, "max_drawdown_pct": Decimal("60"),
            "sharpe_annual": Decimal("0.2"), "total_return_pct": Decimal("10"),
        },
        "gated_oos_stats": {
            "days": 300, "max_drawdown_pct": Decimal("30"),
            "sharpe_annual": Decimal("0.6"), "total_return_pct": Decimal("5"),
        },
        "fold_dd_reductions": [
            {"gated_max_drawdown_pct": Decimal("20"), "always_max_drawdown_pct": Decimal("40")},
            {"gated_max_drawdown_pct": Decimal("30"), "always_max_drawdown_pct": Decimal("60")},
        ],
        "no_lookahead_verified": True,
    }


def test_gate_pass_carries_not_alpha_qualifier_and_each_reason_fires():
    gate = rg.evaluate_regime_filter_gate(**_healthy_gate_kwargs())
    assert gate["passed"] and gate["status"] == rg.VERDICT_PASS
    assert "risk_tool_not_alpha_no_profit_claim" in gate["qualifiers"]
    assert "gives_up_return_vs_always_long_by_design" in gate["qualifiers"]
    assert gate["disclaimer"] == rg.DISCLAIMER

    cases = [
        ({"gated_oos_stats": {"days": 300, "max_drawdown_pct": Decimal("50"), "sharpe_annual": Decimal("0.6"), "total_return_pct": Decimal("5")}}, "oos_drawdown_not_materially_reduced"),
        ({"gated_oos_stats": {"days": 300, "max_drawdown_pct": Decimal("30"), "sharpe_annual": Decimal("0.1"), "total_return_pct": Decimal("5")}}, "oos_risk_adjusted_worse_than_always_long"),
        ({"fold_dd_reductions": [{"gated_max_drawdown_pct": Decimal("50"), "always_max_drawdown_pct": Decimal("40")}]}, "walk_forward_drawdown_not_reduced_in_every_fold"),
        ({"gated_oos_stats": {"days": 30, "max_drawdown_pct": Decimal("30"), "sharpe_annual": Decimal("0.6"), "total_return_pct": Decimal("5")}}, "rejected_low_oos_days"),
        ({"no_lookahead_verified": False}, "no_lookahead_unverified"),
    ]
    for override, reason in cases:
        kwargs = {**_healthy_gate_kwargs(), **override}
        gate = rg.evaluate_regime_filter_gate(**kwargs)
        assert not gate["passed"] and gate["status"] == rg.VERDICT_FAIL
        assert reason in gate["reason_codes"], reason


# ---------------------------------------------------------------------------
# CLI offline replay + disclaimer on every surface
# ---------------------------------------------------------------------------


def test_cli_offline_replay_writes_disclaimed_artifact(tmp_path):
    import importlib.util
    import sys

    candles = {
        s: [
            {
                "close_time": (T0 + timedelta(days=i + 1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": str(100 + i), "high": str(101 + i), "low": str(99 + i),
                "close": str(100 + i), "volume_base": "1000",
            }
            for i in range(40)
        ]
        for s in ("BTC", "ETH", "SOL")
    }
    input_path = tmp_path / "candles.json"
    input_path.write_text(json.dumps(candles), encoding="utf-8")
    output_path = tmp_path / "state.json"

    spec = importlib.util.spec_from_file_location(
        "regime1_cli_under_test", REPO_ROOT / "scripts" / "run_regime_filter.py"
    )
    cli = importlib.util.module_from_spec(spec)
    sys.modules["regime1_cli_under_test"] = cli
    spec.loader.exec_module(cli)
    assert cli.main(["--input-json", str(input_path), "--output", str(output_path)]) == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["disclaimer"] == rg.DISCLAIMER
    assert "not a validated control" in payload["committed_verdict_note"]
    assert payload["state"]["state"] in (rg.STATE_RISK_ON, rg.STATE_RISK_OFF)
    assert payload["boundaries"]["signal_only_no_orders"] is True
    assert payload["source"] == "offline_input_json_replay"


def test_committed_summary_is_honest_and_disclaimed():
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    assert summary["phase"] == rg.PHASE
    assert summary["verdict"] == rg.VERDICT_FAIL  # the committed honest fail
    assert summary["disclaimer"] == rg.DISCLAIMER
    gate = summary["regime_filter_gate"]
    assert gate["status"] == rg.VERDICT_FAIL
    assert "risk_tool_not_alpha_no_profit_claim" in gate["qualifiers"]
    assert summary["boundaries"]["risk_tool_not_alpha"] is True
    assert summary["boundaries"]["signal_only_no_orders"] is True
    assert "NOT A VERDICT" in summary["hindsight_texture_not_a_verdict"]["note"]
    # Whipsaw cost is surfaced with both sides (given up AND avoided).
    oos = summary["whipsaw_cost"]["oos_window"]
    assert oos["state_flips"] > 0 and oos["risk_off_spells"] > 0
    assert "return_given_up_in_false_risk_off" in oos
    assert "drawdown_avoided_in_true_risk_off" in oos
    # No-lookahead probe ran and verified on the committed run.
    assert summary["no_lookahead"]["verified"] is True
    # Research Log honesty: the authored outcome for this phase is fail.
    decision_log = (REPO_ROOT / "money-flow" / "03_Decision_Log.md").read_text(encoding="utf-8")
    block_start = decision_log.find("phase: REGIME1")
    assert block_start != -1, "REGIME1 research_log block must exist"
    assert "outcome: fail" in decision_log[block_start : block_start + 400]
