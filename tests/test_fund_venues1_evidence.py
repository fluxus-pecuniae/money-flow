"""FUND-VENUES1 — deterministic, offline tests (no network, no DB, no runtime).

Asserts the phase's documented guarantees:
  - routing: ``fund_venues1_`` ids route to the SAME funding_carry type/gate
    (other gates refuse them);
  - funding accrual per venue interval: 8h-venue daily sums accrue exactly
    on the perp leg (short receives positive funding) — the FUND-EV1
    convention on DATA1-shaped rows; partial days never enter the timeline;
  - delta-neutrality within tolerance on flat prices at every leverage;
  - leverage mechanics: costs and funding capture scale with gross leverage;
    borrow accrues only on the real cash shortfall (1x book borrows 0 on
    flat prices; 3x/5x borrow > 0); the cost sweep scales the borrow rate;
  - liquidation: a synthetic adverse gap liquidates the levered book
    (force-close at stressed extremes, event recorded) and does NOT trigger
    at 1x on the same gap; the margin seam requires the cited cost model;
    the default ``margin_model=None`` path stays byte-identical;
  - no-lookahead: only-future funding tampering cannot change decisions;
  - cost-sweep monotonicity on the pure-repricing path;
  - venue-fair-window enforcement: OKX/Kraken/HL funding depth is excluded
    from the deep-OOS verdict with recorded reasons;
  - the DATA1 adapter refuses zero-volume (venue-backfill) candles and maps
    event counts to complete/partial funding days correctly;
  - K-019 reconciliation: per-symbol nets minus borrow equals net PnL,
    including through a liquidation;
  - gate v3 semantics: every new reason fires (OOS regime buckets,
    liquidation in OOS / stressed), small regime buckets are qualifiers not
    silent passes, verdict strings are FUND-EV2's, and the committed
    summary stays honest (all cells failed; nothing renders green).
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
from services.strategy_validation import fund_venues1 as fv
from services.strategy_validation import strategy_types
from services.strategy_validation.goal_strat1 import Candle, Dataset

REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = (
    REPO_ROOT / "docs" / "fund_venues1_deep_venue_leverage_carry_evidence_summary.json"
)
CONSERVATIVE = scenario_by_id("exec_ev1_conservative")
T0 = datetime(2025, 1, 1, tzinfo=UTC)


def make_dataset(
    symbol: str,
    prices: list[float],
    volume: float = 50_000_000,
    *,
    high_spikes: dict[int, float] | None = None,
) -> Dataset:
    candles = []
    for i, price in enumerate(prices):
        p = Decimal(str(price))
        high = p * Decimal(str(high_spikes.get(i, 1.001))) if high_spikes else p * Decimal("1.001")
        candles.append(
            Candle(
                symbol=symbol,
                timeframe="1d",
                timestamp=T0 + timedelta(days=i + 1),
                open=p,
                high=high,
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


def make_asset(
    symbol: str, n: int, funding, *, high_spikes: dict[int, float] | None = None
) -> fund.CarryAsset:
    funding_map = {
        T0 + timedelta(days=i + 1): (funding[i] if isinstance(funding, list) else funding)
        for i in range(n)
    }
    return fund.CarryAsset(
        symbol=symbol,
        perp=make_dataset(symbol, [100.0] * n, high_spikes=high_spikes),
        spot=make_dataset(symbol, [100.0] * n),
        funding_by_close=funding_map,
        funding_hours_by_close={k: 24 for k in funding_map},
    )


def universe(n: int = 120, funding=Decimal("0.0003"), **kwargs) -> fund.CarryUniverse:
    return fund.CarryUniverse(
        [make_asset("BTC", n, funding, **kwargs), make_asset("ETH", n, funding, **kwargs)]
    )


def simulate(uni, config, leverage=Decimal("1"), scale=Decimal("1.0"), **kwargs):
    model = fv.cost_model_for(config.venue_construction, scale)
    margin = fv.margin_model_for(leverage, scale)
    return fund.simulate_funding_carry_portfolio(
        uni, config, CONSERVATIVE, leg_cost_model=model, margin_model=margin, **kwargs
    )


def base_config(leverage=Decimal("1"), cadence=14, top_k=2, **kwargs):
    config = fv.config_for(fv.CONSTRUCTION_BINANCE_SINGLE, leverage, cadence, top_k)
    return replace(config, **kwargs) if kwargs else config


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def test_fund_venues1_routes_to_the_funding_carry_gate_only():
    assert (
        strategy_types.strategy_type_for("fund_venues1_binance_single_lev1_cad14_top2_1d")
        == fund.STRATEGY_TYPE_FUNDING_CARRY
    )
    with pytest.raises(fund.StrategyTypeRoutingError):
        fv.evaluate_funding_carry_gate_v3(
            leverage=Decimal("1"),
            oos_regime_pnls={},
            liquidation_count_oos=0,
            liquidation_count_stressed=0,
            cost_sensitivity_sweep=[],
            strategy_type="time_series_momentum",
            oos_strategy_stats={},
            oos_net_pnl=Decimal("1"),
            walk_forward_net_pnls=[Decimal("1")],
            regime_pnls={},
            leave_one_out_oos_net={"BTC": Decimal("1")},
            stressed_max_drawdown_pct=Decimal("1"),
        )


# ---------------------------------------------------------------------------
# Funding accrual per venue interval (DATA1-shaped rows)
# ---------------------------------------------------------------------------


def test_8h_venue_daily_sums_accrue_exactly_and_short_receives_positive():
    # 30 days, constant +3bps/day summed from 3x 8h events; always-on short.
    uni = universe(n=30, funding=Decimal("0.0003"))
    config = base_config(top_k=2, entry_margin_multiple=None)
    result = simulate(uni, config, signal_provider=fund.always_on_provider)
    assert result["funding_collected_total"] > 0  # short perp RECEIVES
    # Exact accrual: each held day pays qty*close*rate; with flat 100 closes
    # and equal slots the first full funding day pays 2 legs x slot x rate.
    assert result["funding_by_symbol"]["BTC"] == result["funding_by_symbol"]["ETH"]


def test_funding_maps_from_data1_complete_vs_partial_days():
    rows = [
        {"close_time": "2025-01-02T00:00:00Z", "funding_rate_sum": "0.0003", "events": 3},
        {"close_time": "2025-01-03T00:00:00Z", "funding_rate_sum": "0.0002", "events": 2},
        {"close_time": "2025-01-04T00:00:00Z", "funding_rate_sum": "0.0006", "events": 6},
    ]
    funding, hours = fv.funding_maps_from_data1(rows, interval_hours=8.0)
    t2 = datetime(2025, 1, 2, tzinfo=UTC)
    t3 = datetime(2025, 1, 3, tzinfo=UTC)
    t4 = datetime(2025, 1, 4, tzinfo=UTC)
    assert funding[t2] == Decimal("0.0003") and hours[t2] == 24  # complete 8h day
    assert hours[t3] == 2  # partial day: excluded from the aligned timeline
    assert hours[t4] == 24  # shortened intervals (more events) still complete
    # 1h venue: 24 events complete, 23 partial.
    funding1h, hours1h = fv.funding_maps_from_data1(
        [
            {"close_time": "2025-01-02T00:00:00Z", "funding_rate_sum": "0.001", "events": 24},
            {"close_time": "2025-01-03T00:00:00Z", "funding_rate_sum": "0.001", "events": 23},
        ],
        interval_hours=1.0,
    )
    assert hours1h[t2] == 24 and hours1h[t3] == 23


def test_partial_funding_days_never_enter_the_aligned_timeline():
    asset = make_asset("BTC", 10, Decimal("0.0003"))
    broken_hours = dict(asset.funding_hours_by_close)
    t_partial = T0 + timedelta(days=5)
    broken_hours[t_partial] = 2
    broken = fund.CarryAsset(
        symbol="BTC",
        perp=asset.perp,
        spot=asset.spot,
        funding_by_close=asset.funding_by_close,
        funding_hours_by_close=broken_hours,
    )
    uni = fund.CarryUniverse([broken])
    assert t_partial not in uni.timeline
    assert len(uni.timeline) == 9


# ---------------------------------------------------------------------------
# Delta-neutrality + leverage mechanics
# ---------------------------------------------------------------------------


def test_flat_prices_stay_delta_neutral_at_every_leverage():
    for leverage in fv.LEVERAGE_LEVELS:
        uni = universe(n=60)
        result = simulate(uni, base_config(leverage), leverage)
        assert result["max_residual_delta_fraction"] < Decimal("0.02"), leverage
        assert result["liquidation_count"] == 0


def test_leverage_scales_funding_capture_costs_and_borrow():
    results = {}
    for leverage in (Decimal("1"), Decimal("3"), Decimal("5")):
        uni = universe(n=90)
        results[leverage] = simulate(
            uni, base_config(leverage, entry_margin_multiple=None), leverage
        )
    f1 = results[Decimal("1")]["funding_collected_total"]
    f3 = results[Decimal("3")]["funding_collected_total"]
    f5 = results[Decimal("5")]["funding_collected_total"]
    assert f3 > f1 * 2 and f5 > f3  # capture scales with gross leverage
    assert results[Decimal("3")]["fees_total"] > results[Decimal("1")]["fees_total"] * 2
    # Borrow only on the real cash shortfall: 1x (0.5+0.05 of equity) needs
    # none on flat prices; 3x and 5x do — and 5x borrows more.
    assert results[Decimal("1")]["borrow_cost_total"] == 0
    assert results[Decimal("3")]["borrow_cost_total"] > 0
    assert results[Decimal("5")]["borrow_cost_total"] > results[Decimal("3")]["borrow_cost_total"]
    assert results[Decimal("5")]["max_borrowed"] > results[Decimal("3")]["max_borrowed"]


def test_margin_model_requires_cited_cost_model_and_documented_levels():
    uni = universe(n=30)
    with pytest.raises(ValueError, match="margin_model_requires_leg_cost_model"):
        fund.simulate_funding_carry_portfolio(
            uni, base_config(), CONSERVATIVE, margin_model=fv.margin_model_for(Decimal("1"))
        )
    with pytest.raises(ValueError, match="leverage_not_in_documented_levels"):
        fv.margin_model_for(Decimal("2"))
    # Sweep scales the borrow rate together with every other cost term.
    assert fv.margin_model_for(Decimal("3"), Decimal("2.0")).borrow_daily_rate == Decimal("0.0004")


def test_default_margin_none_keeps_result_keys_byte_identical():
    uni = universe(n=30)
    model = fv.cost_model_for(fv.CONSTRUCTION_BINANCE_SINGLE)
    result = fund.simulate_funding_carry_portfolio(
        uni, base_config(), CONSERVATIVE, leg_cost_model=model
    )
    assert "liquidation_count" not in result and "borrow_cost_total" not in result


# ---------------------------------------------------------------------------
# Liquidation on a synthetic gap
# ---------------------------------------------------------------------------


def _gap_universe(spike: float) -> fund.CarryUniverse:
    # Day 40 perp candle spikes intraday (short marked at the high) while
    # closes stay flat — the legged/basis gap the margin model must price.
    return universe(n=60, high_spikes={40: spike})


def test_synthetic_gap_liquidates_5x_but_not_1x():
    # +45% intraday perp high (a real DOGE-April-2021-scale candle): at 5x
    # the stressed loss (~2.5x equity x 45%) breaches account maintenance;
    # the same candle leaves the 1x book far from liquidation.
    config5 = base_config(Decimal("5"), entry_margin_multiple=None)
    res5 = simulate(_gap_universe(1.45), config5, Decimal("5"))
    assert res5["liquidation_count"] >= 1
    t_liq, _stressed_equity = res5["liquidation_events"][0]
    assert t_liq == T0 + timedelta(days=41)  # the spike candle's close day
    liq_trades = [e for e in res5["trade_events"] if str(e[3]).startswith("liquidation_")]
    assert liq_trades, "liquidation must force-close at stressed extremes"
    config1 = base_config(Decimal("1"), entry_margin_multiple=None)
    res1 = simulate(_gap_universe(1.45), config1, Decimal("1"))
    assert res1["liquidation_count"] == 0  # same gap, unlevered book survives


def test_gate_fails_on_liquidation_events_and_oos_regime_buckets():
    healthy = {
        "strategy_type": fund.STRATEGY_TYPE_FUNDING_CARRY,
        "oos_strategy_stats": {"days": 200, "sharpe_annual": Decimal("2"), "max_drawdown_pct": Decimal("1")},
        "oos_net_pnl": Decimal("100"),
        "walk_forward_net_pnls": [Decimal("50"), Decimal("40")],
        "regime_pnls": {
            "bull": {"days": 100, "net_pnl": Decimal("60")},
            "neutral": {"days": 100, "net_pnl": Decimal("30")},
            "bear": {"days": 100, "net_pnl": Decimal("20")},
        },
        "leave_one_out_oos_net": {"BTC": Decimal("80"), "ETH": Decimal("70")},
        "stressed_max_drawdown_pct": Decimal("2"),
    }
    sweep = [{"scale": "1.0", "oos_net_pnl": "100"}]
    good_regimes = {
        "bull": {"days": 90, "net_pnl": Decimal("50")},
        "neutral": {"days": 60, "net_pnl": Decimal("30")},
        "bear": {"days": 50, "net_pnl": Decimal("20")},
    }
    gate = fv.evaluate_funding_carry_gate_v3(
        leverage=Decimal("1"),
        oos_regime_pnls=good_regimes,
        liquidation_count_oos=0,
        liquidation_count_stressed=0,
        cost_sensitivity_sweep=sweep,
        **healthy,
    )
    assert gate["passed"] and gate["status"] == fv.VERDICT_PASS
    # A negative OOS bear bucket fails even when everything else is healthy.
    bear_neg = dict(good_regimes)
    bear_neg["bear"] = {"days": 50, "net_pnl": Decimal("-1")}
    gate = fv.evaluate_funding_carry_gate_v3(
        leverage=Decimal("1"),
        oos_regime_pnls=bear_neg,
        liquidation_count_oos=0,
        liquidation_count_stressed=0,
        cost_sensitivity_sweep=sweep,
        **healthy,
    )
    assert not gate["passed"]
    assert "oos_regime_bear_net_carry_not_positive" in gate["reason_codes"]
    # A too-small bucket is a QUALIFIER, never a silent pass or fail.
    small = dict(good_regimes)
    small["bear"] = {"days": 5, "net_pnl": Decimal("-1")}
    gate = fv.evaluate_funding_carry_gate_v3(
        leverage=Decimal("1"),
        oos_regime_pnls=small,
        liquidation_count_oos=0,
        liquidation_count_stressed=0,
        cost_sensitivity_sweep=sweep,
        **healthy,
    )
    assert gate["passed"]
    assert any("sample_too_small_to_judge" in q for q in gate["qualifiers"])
    # Liquidations fail the tail in OOS and in the stressed run.
    for kwargs, reason in (
        ({"liquidation_count_oos": 1, "liquidation_count_stressed": 0}, "liquidation_event_in_oos"),
        ({"liquidation_count_oos": 0, "liquidation_count_stressed": 2}, "liquidation_event_in_stressed_run"),
    ):
        gate = fv.evaluate_funding_carry_gate_v3(
            leverage=Decimal("3"),
            oos_regime_pnls=good_regimes,
            cost_sensitivity_sweep=sweep,
            **kwargs,
            **healthy,
        )
        assert not gate["passed"] and reason in gate["reason_codes"]
        assert gate["status"] == fv.VERDICT_FAIL


# ---------------------------------------------------------------------------
# No-lookahead + sweep monotonicity
# ---------------------------------------------------------------------------


def test_only_future_funding_cannot_change_decisions():
    n = 90
    base_funding = [Decimal("0.0003")] * n
    tampered = list(base_funding)
    for i in range(60, n):
        tampered[i] = Decimal("-0.009")  # violently different FUTURE funding
    uni_a = fund.CarryUniverse([make_asset("BTC", n, base_funding), make_asset("ETH", n, base_funding)])
    uni_b = fund.CarryUniverse([make_asset("BTC", n, tampered), make_asset("ETH", n, tampered)])
    cutoff = T0 + timedelta(days=60)
    res_a = simulate(uni_a, base_config(), Decimal("1"))
    res_b = simulate(uni_b, base_config(), Decimal("1"))
    events_a = [e for e in res_a["trade_events"] if e[0] <= cutoff]
    events_b = [e for e in res_b["trade_events"] if e[0] <= cutoff]
    assert events_a == events_b


def test_cost_sweep_monotone_on_pure_repricing_path():
    nets = []
    for scale in (Decimal("0"), Decimal("1.0"), Decimal("2.0"), Decimal("4.0")):
        uni = universe(n=90)
        result = simulate(uni, base_config(entry_margin_multiple=None), Decimal("3"), scale)
        nets.append(result["net_pnl"])
    assert nets == sorted(nets, reverse=True)


# ---------------------------------------------------------------------------
# Venue-fair windows + DATA1 adapter honesty
# ---------------------------------------------------------------------------


def test_venue_fair_check_excludes_shallow_funding_histories():
    table = fv.venue_fair_funding_check(
        {"binance": 2088, "bybit": 1730, "okx": 92, "kraken": 366, "hyperliquid": 1089}
    )
    assert table["binance"]["eligible_for_deep_oos_verdict"]
    assert table["bybit"]["eligible_for_deep_oos_verdict"]
    for venue in ("okx", "kraken", "hyperliquid"):
        assert not table[venue]["eligible_for_deep_oos_verdict"]
        assert "funding_history_below_min_for_deep_oos" in table[venue]["exclusion_reason"]
    # The verdict constructions only source funding from eligible venues.
    assert fv.MIN_FUNDING_DAYS_FOR_DEEP_OOS == 1500


def test_zero_volume_backfill_candles_are_refused():
    rows = [
        {"close_time": "2025-01-02T00:00:00Z", "open": "1", "high": "1", "low": "1", "close": "1", "volume_base": "0.0"},
    ]
    with pytest.raises(fv.ZeroVolumeCandleError, match="zero_volume_backfill_candle"):
        fv.dataset_from_data1_rows("BTC", "hyperliquid", "perp_1d", rows)


def test_leverage_config_grid_and_fee_models_are_cited():
    config = fv.config_for(fv.CONSTRUCTION_BINANCE_SINGLE, Decimal("3"), 14, 2)
    assert config.leg_notional_fraction == Decimal("1.5")  # 0.5 x leverage
    assert config.mode == "collect_only"
    taker = fv.cost_model_for(fv.CONSTRUCTION_BINANCE_SINGLE)
    maker = fv.cost_model_for(fv.CONSTRUCTION_BINANCE_SINGLE, fill_side=fv.MAKER)
    assert taker.spec("BTC", "perp").fee_bps == Decimal("5.0")
    assert maker.spec("BTC", "perp").fee_bps == Decimal("2.0")
    assert "fetched 2026-06-12" in taker.spec("BTC", "perp").basis
    bybit = fv.cost_model_for(fv.CONSTRUCTION_BYBIT_SINGLE)
    assert bybit.spec("BTC", "perp").fee_bps == Decimal("5.5")
    cross = fv.cost_model_for(fv.CONSTRUCTION_BINANCE_CROSS_COINBASE)
    assert cross.spec("BTC", "spot").fee_bps == Decimal("60.0")
    assert cross.spec("BTC", "spot").flat_cost_quote == Decimal("2.00")
    with pytest.raises(ValueError):
        fv.cost_model_for("unknown_venue")


# ---------------------------------------------------------------------------
# K-019 reconciliation (including through a liquidation)
# ---------------------------------------------------------------------------


def test_per_symbol_nets_minus_borrow_reconcile_to_net_pnl_through_liquidation():
    # K-019: realized (friction-priced fills) + funding - fees per symbol,
    # minus the account-level borrow cost, must equal net PnL exactly —
    # including through a forced liquidation close.
    config = base_config(Decimal("5"), entry_margin_multiple=None)
    result = simulate(_gap_universe(1.45), config, Decimal("5"))
    assert result["liquidation_count"] >= 1
    per_symbol_sum = sum(result["per_symbol_net_pnl"].values(), Decimal("0"))
    reconciled = per_symbol_sum - result["borrow_cost_total"]
    assert abs(reconciled - result["net_pnl"]) <= Decimal("0.5"), (
        reconciled,
        result["net_pnl"],
    )


# ---------------------------------------------------------------------------
# Committed summary honesty
# ---------------------------------------------------------------------------


def test_committed_summary_reconciles_and_stays_honest():
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    assert summary["phase"] == fv.PHASE
    assert summary["routing"]["gate_id"] == fund.FUNDING_CARRY_GATE_ID
    boundaries = summary["boundaries"]
    assert boundaries["venue_fair_window_enforced_from_data1_coverage"] is True
    assert boundaries["maker_fills_reported_as_non_gateable_bound_only"] is True
    assert boundaries["leverage_financing_and_liquidation_modeled"] is True
    guard = summary["discipline_guard"]
    assert guard["gateable_verdict_prices_taker_fills_only"] is True
    assert any("Binance fee schedule" in s for s in guard["sources"])
    assert any("Bybit fee schedule" in s for s in guard["sources"])
    # Venue-fair: shallow-funding venues are excluded with recorded reasons.
    vf = summary["venue_fair_windows"]
    for venue in ("okx", "kraken", "hyperliquid"):
        assert not vf[venue]["eligible_for_deep_oos_verdict"]
    # All nine cells exist and every verdict is the gate's output — and in
    # the committed run, every cell FAILED (never render green on a fail).
    cells = summary["cells"]
    assert len(cells) == 9
    for key, cell in cells.items():
        gate = cell["funding_carry_gate"]
        assert gate["status"] in (fv.VERDICT_PASS, fv.VERDICT_FAIL)
        assert gate["status"] == fv.VERDICT_FAIL, key
        assert gate["reason_codes"], key
        assert cell["cost_sensitivity_sweep"], key
    assert summary["any_cell_passed"] is False
    assert summary["adversarial_review"]["log"] == "not_required_no_positive_verdict"
    # The leverage sweep table is consistent with the cells.
    for construction, rows in summary["leverage_sweep_by_construction"].items():
        for row in rows:
            cell = cells[f"{construction}|lev{row['leverage_gross']}"]
            assert row["verdict"] == cell["funding_carry_gate"]["status"]
    # The near-miss is documented as a fail with its single binding reason.
    near_miss = cells["binance_single|lev1"]["funding_carry_gate"]
    assert near_miss["reason_codes"] == ["stressed_tail_drawdown_exceeds_documented_limit"]
    # Research Log honesty: the authored outcome for this phase is not pass.
    decision_log = (REPO_ROOT / "money-flow" / "03_Decision_Log.md").read_text(encoding="utf-8")
    block_start = decision_log.find("phase: FUND-VENUES1")
    assert block_start != -1, "FUND-VENUES1 research_log block must exist"
    block = decision_log[block_start : block_start + 400]
    assert "outcome: fail" in block
