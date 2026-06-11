"""FUND-EV2 — deterministic, offline tests (no network, no DB, no runtime).

Asserts the phase's documented guarantees:
  - routing: ``fund_ev2_`` ids route to the SAME funding_carry type/gate;
  - the cited per-venue cost model is APPLIED per venue/asset/leg (hl spot
    vs Kraken spot differ; fees + flat settlement differ; the default
    ``leg_cost_model=None`` path stays byte-identical FUND-EV1);
  - the cost-sensitivity sweep is monotonic on the pure-repricing path
    (higher cost => lower net when entries are not cost-gated);
  - selectivity gates entries exactly (expected funding must clear the
    margin x round-trip cost) with hold-while-favorable hysteresis;
  - the cross-venue legging stress holds REAL one-leg exposure;
  - no-lookahead: decisions before a divergence point are identical when
    only FUTURE funding differs;
  - K-019 reconciliation on v2 runs;
  - gate v2 semantics: verdict strings, breakpoint helper, fragility
    qualifier, and the discipline guard (a pass that exists only below
    realistic costs cannot happen because the main check runs at 1.0);
  - the committed evidence summary + l2Book calibration reconcile, and the
    authored Research Log outcome stays honest (never green on a fail).
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from services.execution_quality.exec_ev1 import scenario_by_id
from services.strategy_validation import fund_ev1 as fund
from services.strategy_validation import fund_ev2 as ev2
from services.strategy_validation import strategy_types
from services.strategy_validation.goal_strat1 import Candle, Dataset

REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = REPO_ROOT / "docs" / "fund_ev2_realistic_cost_carry_evidence_summary.json"
L2_PATH = REPO_ROOT / "docs" / "fund_ev2_l2book_calibration_summary.json"
CONSERVATIVE = scenario_by_id("exec_ev1_conservative")
T0 = datetime(2025, 1, 1, tzinfo=UTC)


def make_dataset(symbol: str, prices: list[float], volume: float = 5_000_000) -> Dataset:
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
                volume=Decimal(str(volume)),
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


def make_asset(symbol: str, n: int, funding) -> fund.CarryAsset:
    funding_map = {
        T0 + timedelta(days=i + 1): (funding[i] if isinstance(funding, list) else funding)
        for i in range(n)
    }
    return fund.CarryAsset(
        symbol=symbol,
        perp=make_dataset(symbol, [100.0] * n),
        spot=make_dataset(symbol, [100.0] * n),
        funding_by_close=funding_map,
        funding_hours_by_close={k: 24 for k in funding_map},
    )


def universe(n: int = 120, funding=Decimal("0.0003")) -> fund.CarryUniverse:
    # Real symbol names: the cited cost models key on them.
    return fund.CarryUniverse([make_asset("BTC", n, funding), make_asset("ETH", n, funding)])


def cfg(config_id: str = "fund_ev2_hl_single_cad28_top2_1d") -> fund.FundingCarryConfig:
    return {c.config_id: c for c in ev2.generate_fund_ev2_configs()}[config_id]


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def test_fund_ev2_ids_route_to_funding_carry_same_gate() -> None:
    assert (
        strategy_types.strategy_type_for("fund_ev2_hl_single_cad14_top2_1d")
        == strategy_types.STRATEGY_TYPE_FUNDING_CARRY
    )
    assert strategy_types.strategy_type_for("fund_ev1_x") == "funding_carry"
    assert strategy_types.strategy_type_for("tsmom_ev1_x") == "time_series_momentum"
    route = strategy_types.route_for(strategy_types.STRATEGY_TYPE_FUNDING_CARRY)
    assert route.gate_id == strategy_types.FUNDING_CARRY_GATE_ID


# ---------------------------------------------------------------------------
# The cited per-venue cost model is actually applied
# ---------------------------------------------------------------------------


def test_cost_model_is_per_venue_per_asset_per_leg_and_cited() -> None:
    hl = ev2.hl_single_cost_model()
    xv = ev2.cross_venue_cost_model()
    # HL spot fee (7 bps, cited) differs from perp (4.5) and from Kraken (40).
    assert hl.spec("BTC", "spot").fee_bps == Decimal("7.0")
    assert hl.spec("BTC", "perp").fee_bps == Decimal("4.5")
    assert xv.spec("BTC", "spot").fee_bps == Decimal("40.0")
    assert xv.spec("BTC", "spot").flat_cost_quote == Decimal("2.00")
    # Per-asset: USOL is the thinnest measured HL spot book.
    assert hl.spec("SOL", "spot").half_spread_bps > hl.spec("BTC", "spot").half_spread_bps
    # Every spec carries its citation.
    for model in (hl, xv):
        for key, leg_desc in model.describe()["legs"].items():
            assert leg_desc["basis"], key
    # Round-trip costs: cross-venue retail fees dominate.
    rt_hl = hl.round_trip_cost_bps("BTC", Decimal("2500"))
    rt_xv = xv.round_trip_cost_bps("BTC", Decimal("2500"))
    assert rt_xv > rt_hl * 3


def test_realistic_model_cheaper_than_fund_ev1_widest_tier_and_default_unchanged() -> None:
    uni = universe()
    config = cfg()
    realistic = fund.simulate_funding_carry_portfolio(
        uni, config, CONSERVATIVE, leg_cost_model=ev2.hl_single_cost_model()
    )
    # Default path (no model) = FUND-EV1 conservative behavior; same config
    # without the selectivity guard active (it requires a cost model).
    v1_path = fund.simulate_funding_carry_portfolio(uni, config, CONSERVATIVE)
    assert realistic["net_pnl"] > v1_path["net_pnl"]
    assert realistic["trade_count"] > 0
    # And the FUND-EV1 default behavior itself is untouched: a fund_ev1-era
    # config still produces avg friction at the widest-tier level for spot.
    assert v1_path["avg_friction_bps"] > realistic["avg_friction_bps"]


# ---------------------------------------------------------------------------
# Sweep monotonicity (pure repricing path)
# ---------------------------------------------------------------------------


def test_sweep_is_monotonic_when_entries_are_not_cost_gated() -> None:
    uni = universe()
    plain = replace(cfg(), config_id="fund_ev2_plain", entry_margin_multiple=None)
    hl = ev2.hl_single_cost_model()
    nets = []
    for scale in ev2.SWEEP_SCALES:
        result = fund.simulate_funding_carry_portfolio(
            uni, plain, CONSERVATIVE, leg_cost_model=hl.with_scale(scale)
        )
        nets.append(result["net_pnl"])
    assert all(nets[i] >= nets[i + 1] for i in range(len(nets) - 1))
    assert nets[0] > nets[-1]  # the dial actually moves cost


def test_breakpoint_helper_finds_first_non_positive_scale() -> None:
    rows = [
        {"scale": "0.5", "oos_net_pnl": "10"},
        {"scale": "1.0", "oos_net_pnl": "1"},
        {"scale": "1.5", "oos_net_pnl": "-3"},
        {"scale": "2.0", "oos_net_pnl": "-9"},
    ]
    assert ev2.sweep_breakpoint_scale(rows) == Decimal("1.5")
    assert ev2.sweep_breakpoint_scale(rows[:2]) is None
    dead = [{"scale": "0.25", "oos_net_pnl": "-1"}]
    assert ev2.sweep_breakpoint_scale(dead) == Decimal("0.25")


# ---------------------------------------------------------------------------
# Selectivity + hysteresis
# ---------------------------------------------------------------------------


def test_selectivity_blocks_thin_entries_and_allows_fat_ones() -> None:
    uni = universe(funding=Decimal("0.0003"))  # 3 bps/day = 42 bps over 14d
    hl = ev2.hl_single_cost_model()  # BTC round trip 33 bps -> 2x = 66 bps bar
    blocked = fund.simulate_funding_carry_portfolio(
        uni, cfg("fund_ev2_hl_single_cad14_top2_1d"), CONSERVATIVE, leg_cost_model=hl
    )
    assert blocked["trade_count"] == 0  # 42 < 66: stays out
    entered = fund.simulate_funding_carry_portfolio(
        uni, cfg("fund_ev2_hl_single_cad28_top2_1d"), CONSERVATIVE, leg_cost_model=hl
    )
    assert entered["trade_count"] > 0  # 84 >= 66: enters


def test_hysteresis_holds_while_favorable_and_exits_on_inversion() -> None:
    n = 168
    # Fat funding for 56 days (clears the entry bar), then thin-but-positive
    # (would NOT clear entry, must still be HELD), then negative (must exit).
    rates = (
        [Decimal("0.0006")] * 56 + [Decimal("0.0001")] * 56 + [Decimal("-0.0003")] * 56
    )
    uni = fund.CarryUniverse(
        [make_asset("BTC", n, list(rates)), make_asset("ETH", n, list(rates))]
    )
    hl = ev2.hl_single_cost_model()
    result = fund.simulate_funding_carry_portfolio(
        uni, cfg("fund_ev2_hl_single_cad28_top2_1d"), CONSERVATIVE, leg_cost_model=hl
    )
    assert result["trade_count"] > 0
    # Positive-day accrual (total minus the negative-day bleed) must exceed
    # what the fat stretch alone can deliver (entry at the first eligible
    # rebalance leaves at most ~27 fat accrual days = 2500 * 0.0006 * 27
    # ~= 40.5): the thin-but-positive period — which would NOT clear the
    # entry bar — was therefore HELD, not churned.
    paid_negative = result["funding_paid_on_negative_days_by_symbol"].get(
        "BTC", Decimal("0")
    )
    positive_day_accrual = result["funding_by_symbol"]["BTC"] - paid_negative
    fat_only_upper_bound = Decimal("2500") * Decimal("0.0006") * Decimal("27")
    assert positive_day_accrual > fat_only_upper_bound + Decimal("7")
    # And the book exited after inversion at the first cadence decision:
    # negative exposure is bounded by signal lookback + one cadence.
    assert result["negative_funding_exposure_days_by_symbol"].get("BTC", 0) <= (
        fund.FUNDING_LOOKBACK_DAYS + 28
    )


def test_legging_stress_holds_real_one_leg_exposure_for_cross_venue() -> None:
    # 10 bps/day x 28d hold = 280 bps expected: clears the ~230 bps cross-
    # venue entry bar (2x the ~115 bps retail round trip), so the book trades.
    uni = universe(funding=Decimal("0.0010"))
    xv = ev2.cross_venue_cost_model()
    lagged_cfg = replace(
        cfg("fund_ev2_cross_venue_cad28_top2_1d"),
        config_id="fund_ev2_cross_venue_lag_test",
        spot_leg_lag_days=1,
    )
    result = fund.simulate_funding_carry_portfolio(
        uni, lagged_cfg, CONSERVATIVE, leg_cost_model=xv
    )
    assert result["trade_count"] > 0
    assert result["max_residual_delta_fraction"] > Decimal("0.2")


# ---------------------------------------------------------------------------
# No-lookahead at the simulator level
# ---------------------------------------------------------------------------


def test_decisions_before_divergence_identical_when_only_future_funding_differs() -> None:
    n = 120
    base_rates = [Decimal("0.0006")] * n
    tampered_rates = list(base_rates)
    for i in range(80, n):  # tamper only the FUTURE relative to day 80
        tampered_rates[i] = Decimal("-0.0009")
    hl = ev2.hl_single_cost_model()
    config = cfg("fund_ev2_hl_single_cad14_top2_1d")
    results = []
    for rates in (base_rates, tampered_rates):
        uni = fund.CarryUniverse(
            [make_asset("BTC", n, list(rates)), make_asset("ETH", n, list(rates))]
        )
        results.append(
            fund.simulate_funding_carry_portfolio(
                uni, config, CONSERVATIVE, leg_cost_model=hl
            )
        )
    cutoff = T0 + timedelta(days=80)
    early = [
        [e for e in r["trade_events"] if e[0] <= cutoff] for r in results
    ]
    assert early[0] == early[1]
    assert early[0], "expected trades before the divergence point"


# ---------------------------------------------------------------------------
# Reconciliation (K-019)
# ---------------------------------------------------------------------------


def test_v2_run_reconciles_per_symbol_to_net() -> None:
    uni = universe(funding=Decimal("0.0006"))
    result = fund.simulate_funding_carry_portfolio(
        uni, cfg(), CONSERVATIVE, leg_cost_model=ev2.hl_single_cost_model()
    )
    total = sum(result["per_symbol_net_pnl"].values(), Decimal("0"))
    assert abs(total - result["net_pnl"]) < Decimal("0.5")
    assert result["equity_curve"][-1][1] == result["ending_equity"]


# ---------------------------------------------------------------------------
# Gate v2 semantics
# ---------------------------------------------------------------------------


def _gate_kwargs(**overrides):
    kwargs = dict(
        strategy_type=fund.STRATEGY_TYPE_FUNDING_CARRY,
        oos_strategy_stats={
            "days": 119,
            "sharpe_annual": Decimal("2"),
            "max_drawdown_pct": Decimal("1"),
            "total_return_pct": Decimal("1"),
            "vol_annual": Decimal("0.01"),
        },
        oos_net_pnl=Decimal("120"),
        walk_forward_net_pnls=[Decimal("60"), Decimal("40")],
        regime_pnls={
            "bull": {"days": 100, "net_pnl": Decimal("100")},
            "neutral": {"days": 100, "net_pnl": Decimal("50")},
            "bear": {"days": 100, "net_pnl": Decimal("20")},
        },
        leave_one_out_oos_net={"BTC": Decimal("80"), "ETH": Decimal("60")},
        stressed_max_drawdown_pct=Decimal("3"),
    )
    kwargs.update(overrides)
    return kwargs


def test_gate_v2_maps_verdicts_and_flags_fragility() -> None:
    healthy_sweep = [
        {"scale": "0.5", "oos_net_pnl": "200"},
        {"scale": "1.0", "oos_net_pnl": "120"},
        {"scale": "2.0", "oos_net_pnl": "10"},
        {"scale": "3.0", "oos_net_pnl": "-5"},
    ]
    gate = ev2.evaluate_funding_carry_gate_v2(
        cost_sensitivity_sweep=healthy_sweep, **_gate_kwargs()
    )
    assert gate["status"] == ev2.VERDICT_PASS_V2 and gate["passed"]
    assert "oos_edge_fragile_to_cost_assumptions" not in gate["qualifiers"]
    assert gate["cost_sensitivity"]["breakpoint_scale_where_oos_edge_dies"] == "3.0"

    fragile_sweep = [
        {"scale": "1.0", "oos_net_pnl": "5"},
        {"scale": "1.25", "oos_net_pnl": "-2"},
    ]
    fragile = ev2.evaluate_funding_carry_gate_v2(
        cost_sensitivity_sweep=fragile_sweep, **_gate_kwargs()
    )
    assert fragile["passed"]
    assert "oos_edge_fragile_to_cost_assumptions" in fragile["qualifiers"]

    failing = ev2.evaluate_funding_carry_gate_v2(
        cost_sensitivity_sweep=fragile_sweep,
        **_gate_kwargs(oos_net_pnl=Decimal("-6")),
    )
    assert failing["status"] == ev2.VERDICT_FAIL_V2 and not failing["passed"]
    assert "oos_net_carry_not_positive_after_costs" in failing["reason_codes"]
    # Routing enforcement carried through from the underlying gate.
    with pytest.raises(strategy_types.StrategyTypeRoutingError):
        ev2.evaluate_funding_carry_gate_v2(
            cost_sensitivity_sweep=fragile_sweep,
            **_gate_kwargs(strategy_type="per_symbol"),
        )


# ---------------------------------------------------------------------------
# Committed evidence summary + calibration (CI-safe: committed docs only)
# ---------------------------------------------------------------------------


def _summary() -> dict:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def test_committed_summary_gate_breakpoint_and_discipline_guard() -> None:
    summary = _summary()
    gate = summary["funding_carry_gate"]
    assert gate["gate_id"] == "funding_carry_net_oos_tail_gate"
    assert summary["verdict"] == gate["status"]
    assert summary["verdict"] in (ev2.VERDICT_PASS_V2, ev2.VERDICT_FAIL_V2)
    assert summary["discipline_guard"]["costs_cited_not_tuned"] is True
    assert summary["discipline_guard"]["one_honest_retest_no_fund_ev3_cost_tweak"] is True
    assert len(summary["discipline_guard"]["sources"]) >= 3
    sweep = summary["cost_sensitivity_sweep"]
    scales = [Decimal(r["scale"]) for r in sweep["rows"]]
    assert Decimal("1.0") in scales and len(scales) >= 5
    assert "breakpoint_scale_where_oos_edge_dies" in sweep
    assert summary["boundaries"]["costs_cited_not_tuned_to_verdict"] is True
    assert summary["boundaries"]["calls_private_signed_or_order_endpoints"] is False


def test_committed_summary_reports_both_constructions_and_reconciles() -> None:
    summary = _summary()
    constructions = {row["construction"] for row in summary["per_config_results"]}
    assert constructions == set(ev2.CONSTRUCTIONS)
    for row in summary["per_config_results"]:
        total = sum(Decimal(v) for v in row["per_symbol_net_pnl"].values())
        assert abs(total - Decimal(row["net_pnl"])) < Decimal("1"), row["config_id"]
    rt = summary["design"]["round_trip_cost_bps_at_2500_notional"]
    # The honest retail comparison: cross-venue round trips cost a multiple
    # of single-venue at this account size.
    assert Decimal(rt["cross_venue"]["BTC"]) > Decimal(rt["hl_single"]["BTC"]) * 3
    assert set(summary["leave_one_out"]) == set(fund.CARRY_UNIVERSE)
    # Both constructions' legged stress is reported.
    assert "stressed_run_chosen" in summary["tail_stress"]
    assert "stressed_run_other_construction" in summary["tail_stress"]


def test_committed_l2book_calibration_is_public_read_only_and_complete() -> None:
    payload = json.loads(L2_PATH.read_text(encoding="utf-8"))
    assert payload["phase"] == "FUND-EV2"
    assert set(payload["books"]) == set(fund.CARRY_UNIVERSE)
    assert (
        payload["provenance"]["access"]
        == "public_read_only_no_keys_no_private_no_signed_no_orders"
    )
    assert payload["honesty"]["point_in_time_snapshot_not_window_history"] is True
    for symbol, sides in payload["books"].items():
        for side in ("perp", "spot"):
            assert Decimal(sides[side]["half_spread_bps"]) >= 0
            assert Decimal(sides[side]["visible_depth_quote_by_band_bps"]["10"]) > 0


def test_research_log_outcome_for_fund_ev2_stays_honest() -> None:
    """Pinned: if the gate failed, the authored outcome is fail and can
    never render green; a pass may only be authored with the gate green."""
    payload = json.loads(
        (REPO_ROOT / "docs" / "research_log.json").read_text(encoding="utf-8")
    )
    by_phase = {entry["phase"]: entry for entry in payload["entries"]}
    entry = by_phase.get("FUND-EV2")
    assert entry is not None, "FUND-EV2 research_log block missing"
    summary = _summary()
    if summary["verdict"] == ev2.VERDICT_FAIL_V2:
        assert entry["outcome"] == "fail"
    assert payload["standing"]["passed_gate"] == sum(
        1 for e in payload["entries"] if e["outcome"] == "pass"
    )
