from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from core.domain.enums import StrategyValidationFillTiming, Timeframe
from core.domain.models import Candle
from services.strategy_validation.mf_orig_ev1 import (
    GAP_MATRIX,
    MF_ORIG_HYPOTHESES,
    PRIMARY_TIMEFRAME_POLICY,
    SOURCE_RULE_EXTRACTION,
    _OpenOriginalPosition,
    _accounting_event,
    _close_original_position,
    _control_pocket_impact,
    _drawdown_stats,
    _missing_original_indicator_reasons,
    _original_metrics,
    _resolve_original_fill,
    _structure_stop_price,
    _trim_original_position,
)


def _candle(index: int, *, close: str = "100") -> Candle:
    open_time = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=index)
    return Candle(
        instrument_key="perpetual:linear:BTC:USDC:USDC",
        instrument_ref_id="BTC",
        venue="hyperliquid",
        symbol="BTC",
        timeframe=Timeframe.D1,
        open_time=open_time,
        close_time=open_time + timedelta(days=1),
        open=Decimal(close),
        high=Decimal(close) + Decimal("2"),
        low=Decimal(close) - Decimal("2"),
        close=Decimal(close),
        volume=Decimal("100"),
        trade_count=10,
    )


def _sample_open_position(*, quantity: str = "1", entry_fee: str = "1") -> _OpenOriginalPosition:
    entry_time = datetime(2026, 1, 2, tzinfo=UTC)
    equity_before = Decimal("10000")
    fee = Decimal(entry_fee)
    quantity_dec = Decimal(quantity)
    return _OpenOriginalPosition(
        trade_id="test-trade",
        hypothesis_id="mf_orig_1d_stage2_5_20_crossover",
        symbol="BTC",
        timeframe="1d",
        fill_timing="next_candle_open",
        entry_signal_time=datetime(2026, 1, 1, tzinfo=UTC),
        entry_time=entry_time,
        entry_price=Decimal("100"),
        stop_price=Decimal("90"),
        quantity=quantity_dec,
        remaining_quantity=quantity_dec,
        equity_before=equity_before,
        entry_fee=fee,
        risk_budget=Decimal("100"),
        notional=Decimal("100") * quantity_dec,
        sizing_mode="source_1pct_risk",
        entry_reason_codes=("stage2_price_above_sma20",),
        stage_at_entry="stage_2_markup",
        min_equity_seen=equity_before - fee,
        accounting_events=[
            _accounting_event(
                event_type="entry_fee",
                timestamp=entry_time,
                quantity=quantity_dec,
                price=Decimal("100"),
                gross_pnl=Decimal("0"),
                fee=fee,
                net_amount=-fee,
                remaining_quantity_after_event=quantity_dec,
                realized_equity_after_event=equity_before - fee,
                mark_to_market_equity_after_event=equity_before - fee,
            )
        ],
    )


def test_mf_orig_ev1_source_spec_report_and_json_exist() -> None:
    spec = Path("docs/mf_orig_ev1_original_money_flow_spec_and_gap_matrix.md")
    report = Path("docs/mf_orig_ev1_original_money_flow_reconstruction.md")
    summary = Path("docs/mf_orig_ev1_original_money_flow_reconstruction_summary.json")

    assert spec.exists()
    assert report.exists()
    assert summary.exists()
    spec_text = spec.read_text(encoding="utf-8")
    report_text = report.read_text(encoding="utf-8").lower()
    payload = json.loads(summary.read_text(encoding="utf-8"))

    assert "The Money Flow Trading System" in spec_text
    assert "## Gap Matrix" in spec_text
    assert "Four Stages" in spec_text
    assert "Support / Resistance" in spec_text
    assert payload["phase"] == "MF-ORIG-EV1.1"
    assert payload["hotpatch"]["pre_hotpatch_pnl_drawdown_conclusions_quarantined"] is True
    assert payload["accounting_convention"]["model"] == "event_ledger_accounting"
    assert payload["source_document"]["source_basis"] == "prompt_provided_source_truth_summary"
    assert payload["boundary_flags"]["changes_production_money_flow_rules"] is False
    assert payload["boundary_flags"]["uses_dashboard_date_filter_recalculation"] is False
    assert payload["boundary_flags"]["uses_hyperliquid_testnet_prices"] is False
    for forbidden in ("proven", "optimal", "approved for live", "approved for paper", "ready for real trading", "production-approved"):
        assert forbidden not in report_text


def test_mf_orig_ev1_gap_matrix_and_hypotheses_reflect_source_hierarchy() -> None:
    sections = {row["section"] for row in SOURCE_RULE_EXTRACTION}
    original_rules = " ".join(row["original_pdf_rule"] for row in GAP_MATRIX)

    assert set(MF_ORIG_HYPOTHESES) == {
        "mf_orig_1d_stage2_5_20_crossover",
        "mf_orig_1d_stage2_breakout_resistance",
        "mf_orig_stage2_pullback_reclaim",
        "mf_orig_stage_filter_only",
    }
    assert {"Four Stages", "Moving Averages", "TSI / MACD", "RSI / Profit Taking"} <= sections
    assert {"Support / Resistance / Pivots / Stops", "Position Sizing", "Timeframe Adaptation"} <= sections
    assert "Stage/20SMA/5EMA trigger hierarchy" in original_rules
    assert "RSI > 70" in original_rules
    assert "support/resistance or pivots" in original_rules
    assert PRIMARY_TIMEFRAME_POLICY["1d"] == "primary_original_money_flow_timeframe"
    assert PRIMARY_TIMEFRAME_POLICY["4h"] == "secondary_context_comparative_run"
    assert PRIMARY_TIMEFRAME_POLICY["1h"] == "exploratory_timing_context_only"
    assert PRIMARY_TIMEFRAME_POLICY["15m"] == "not_source_primary_timeframe"


def test_mf_orig_ev1_is_separate_from_production_money_flow() -> None:
    production_source = Path("services/strategy/money_flow.py").read_text(encoding="utf-8")
    research_source = Path("services/strategy_validation/mf_orig_ev1.py").read_text(encoding="utf-8")

    assert "MF_ORIG_HYPOTHESES" not in production_source
    assert "mf_orig_1d_stage2_5_20_crossover" not in production_source
    assert "risk_budget = equity * Decimal(\"0.01\")" in research_source
    assert "SAME_CANDLE_CLOSE_RESEARCH_ONLY" in research_source
    assert "intrabar_stop_fill_at_stop_price" in research_source
    assert "TSI is deferred; MACD" in research_source


def test_mf_orig_ev1_missing_indicators_do_not_default_to_zero() -> None:
    missing_rsi = SimpleNamespace(
        ema_5=Decimal("101"),
        ema_10=Decimal("100"),
        sma_20=Decimal("99"),
        rsi_14=None,
        macd=Decimal("1"),
        macd_signal=Decimal("0.5"),
        macd_histogram=Decimal("0.5"),
    )
    missing_macd = SimpleNamespace(
        ema_5=Decimal("101"),
        ema_10=Decimal("100"),
        sma_20=Decimal("99"),
        rsi_14=Decimal("60"),
        macd=None,
        macd_signal=Decimal("0.5"),
        macd_histogram=Decimal("0.5"),
    )

    assert "missing_rsi" in _missing_original_indicator_reasons(missing_rsi)
    assert "missing_macd" in _missing_original_indicator_reasons(missing_macd)
    assert "missing_indicator_field" in _missing_original_indicator_reasons(missing_rsi)
    assert "0" not in _missing_original_indicator_reasons(missing_rsi)


def test_mf_orig_ev1_fill_models_exclude_same_candle_optimism() -> None:
    candles = [_candle(0, close="100"), _candle(1, close="105")]

    next_open = _resolve_original_fill(candles, 0, StrategyValidationFillTiming.NEXT_CANDLE_OPEN)
    next_close = _resolve_original_fill(candles, 0, StrategyValidationFillTiming.NEXT_CANDLE_CLOSE)
    same_close = _resolve_original_fill(candles, 0, StrategyValidationFillTiming.SAME_CANDLE_CLOSE_RESEARCH_ONLY)

    assert next_open == {"time": candles[1].open_time, "price": candles[1].open}
    assert next_close == {"time": candles[1].close_time, "price": candles[1].close}
    assert same_close is None


def test_mf_orig_ev1_structure_stop_uses_prior_candles_only() -> None:
    candles = [_candle(index, close=str(100 + index)) for index in range(12)]
    candles[7].low = Decimal("91")
    candles[11].low = Decimal("1")

    stop = _structure_stop_price(candles, 11)

    assert stop == Decimal("91")


def test_mf_orig_ev1_summary_uses_canonical_sv202_and_gate_labels() -> None:
    payload = json.loads(Path("docs/mf_orig_ev1_original_money_flow_reconstruction_summary.json").read_text(encoding="utf-8"))

    assert payload["data_sources"]["canonical_timestamp"] == "20260512T064916Z"
    assert payload["data_sources"]["uses_dashboard_date_filters_as_canonical_evidence"] is False
    assert payload["data_sources"]["uses_hyperliquid_testnet_prices"] is False
    assert payload["baseline_parity_summary"]["status_counts"].get("baseline_parity_passed", 0) >= 1
    assert any(row["reason_codes"] == ["not_source_primary_timeframe"] for row in payload["excluded_scenarios"])
    for row in payload["hypothesis_summary"]:
        assert row["methodology"] == "true_forward_replay"
        assert row["production_approved"] is False
        assert row["performance_label"] == "improved_pnl_drawdown_pre_gate"
        assert row["outcome_label"] == "source_faithful_but_underperformed"
        assert row["gate_blockers"] == ["control_pocket_not_preserved"]
    for row in payload["candidate_status"]:
        assert row["status"] == "source_faithful_but_underperformed"
        assert row["production_approved"] is False
        assert row["gate_blockers"] == ["control_pocket_not_preserved"]
    assert payload["accounting_invariant_summary"]["status"] == "passed"
    assert payload["accounting_invariant_summary"]["equity_delta_violations"] == 0
    assert payload["accounting_invariant_summary"]["fee_sum_violations"] == 0
    assert payload["accounting_invariant_summary"]["remaining_quantity_violations"] == 0


def test_mf_orig_ev1_no_order_or_live_language_in_outputs() -> None:
    report = Path("docs/mf_orig_ev1_original_money_flow_reconstruction.md").read_text(encoding="utf-8")
    summary = json.loads(Path("docs/mf_orig_ev1_original_money_flow_reconstruction_summary.json").read_text(encoding="utf-8"))

    assert "No orders were submitted" in report
    assert "Hyperliquid testnet prices are not used as strategy truth" in report
    assert summary["boundary_flags"]["submits_orders"] is False
    assert summary["boundary_flags"]["calls_private_signed_or_order_endpoints"] is False
    assert summary["boundary_flags"]["approves_live_trading"] is False


def test_mf_orig_ev11_no_trim_winning_trade_accounting_counts_fees_once() -> None:
    open_position = _sample_open_position()

    trade = _close_original_position(
        open_position=open_position,
        current_realized_equity=Decimal("9999"),
        exit_signal_time=datetime(2026, 1, 3, tzinfo=UTC),
        exit_time=datetime(2026, 1, 3, tzinfo=UTC),
        exit_price=Decimal("200"),
        exit_reason="price_close_below_sma20_exit",
        fee_bps=Decimal("50"),
        forced_exit=False,
        stop_fill_model="not_stop_exit",
    )

    assert Decimal(trade["entry_fee"]) == Decimal("1")
    assert Decimal(trade["final_close_gross_pnl"]) == Decimal("100")
    assert Decimal(trade["final_close_fee"]) == Decimal("1")
    assert Decimal(trade["net_pnl"]) == Decimal("98")
    assert Decimal(trade["equity_after_trade"]) == Decimal("10098")
    assert Decimal(trade["equity_after_trade"]) - Decimal(trade["equity_before_trade"]) == Decimal(trade["net_pnl"])
    assert [event["event_type"] for event in trade["accounting_events"]] == ["entry_fee", "final_close"]
    assert sum(Decimal(event["fee"]) for event in trade["accounting_events"]) == Decimal(trade["total_fees"])


def test_mf_orig_ev11_no_trim_losing_trade_accounting_counts_fees_once() -> None:
    open_position = _sample_open_position()

    trade = _close_original_position(
        open_position=open_position,
        current_realized_equity=Decimal("9999"),
        exit_signal_time=datetime(2026, 1, 3, tzinfo=UTC),
        exit_time=datetime(2026, 1, 3, tzinfo=UTC),
        exit_price=Decimal("0"),
        exit_reason="structure_stop_hit",
        fee_bps=Decimal("0"),
        forced_exit=False,
        stop_fill_model="intrabar_stop_fill_at_stop_price",
    )

    assert Decimal(trade["entry_fee"]) == Decimal("1")
    assert Decimal(trade["final_close_gross_pnl"]) == Decimal("-100")
    assert Decimal(trade["final_close_fee"]) == Decimal("0")
    assert Decimal(trade["net_pnl"]) == Decimal("-101")
    assert Decimal(trade["equity_after_trade"]) == Decimal("9899")
    assert Decimal(trade["equity_after_trade"]) - Decimal(trade["equity_before_trade"]) == Decimal(trade["net_pnl"])


def test_mf_orig_ev11_single_trim_is_not_readded_at_final_close() -> None:
    open_position = _sample_open_position(quantity="2")

    trim = _trim_original_position(
        open_position=open_position,
        current_realized_equity=Decimal("9999"),
        trim_signal_time=datetime(2026, 1, 3, tzinfo=UTC),
        trim_price=Decimal("150"),
        fee_bps=Decimal("0"),
        reason="rsi_profit_warning_macd_bearish_trim_25pct",
    )
    trade = _close_original_position(
        open_position=open_position,
        current_realized_equity=Decimal(trim["realized_equity_after_event"]),
        exit_signal_time=datetime(2026, 1, 4, tzinfo=UTC),
        exit_time=datetime(2026, 1, 4, tzinfo=UTC),
        exit_price=Decimal("200"),
        exit_reason="ema5_cross_below_sma20_exit",
        fee_bps=Decimal("0"),
        forced_exit=False,
        stop_fill_model="not_stop_exit",
    )

    assert Decimal(trim["gross_pnl"]) == Decimal("25")
    assert Decimal(trade["trim_net_pnl"]) == Decimal("25")
    assert Decimal(trade["final_close_gross_pnl"]) == Decimal("150")
    assert Decimal(trade["net_pnl"]) == Decimal("174")
    assert Decimal(trade["equity_after_trade"]) == Decimal("10174")
    assert Decimal(trade["remaining_quantity_final"]) == Decimal("0")
    assert Decimal(trade["equity_after_trade"]) - Decimal(trade["equity_before_trade"]) == Decimal(trade["net_pnl"])


def test_mf_orig_ev11_multiple_trim_events_are_each_counted_once() -> None:
    open_position = _sample_open_position(quantity="4")
    current_equity = Decimal("9999")

    first = _trim_original_position(
        open_position=open_position,
        current_realized_equity=current_equity,
        trim_signal_time=datetime(2026, 1, 3, tzinfo=UTC),
        trim_price=Decimal("120"),
        fee_bps=Decimal("0"),
        reason="first_trim",
    )
    second = _trim_original_position(
        open_position=open_position,
        current_realized_equity=Decimal(first["realized_equity_after_event"]),
        trim_signal_time=datetime(2026, 1, 4, tzinfo=UTC),
        trim_price=Decimal("140"),
        fee_bps=Decimal("0"),
        reason="second_trim",
    )
    trade = _close_original_position(
        open_position=open_position,
        current_realized_equity=Decimal(second["realized_equity_after_event"]),
        exit_signal_time=datetime(2026, 1, 5, tzinfo=UTC),
        exit_time=datetime(2026, 1, 5, tzinfo=UTC),
        exit_price=Decimal("160"),
        exit_reason="price_close_below_sma20_exit",
        fee_bps=Decimal("0"),
        forced_exit=False,
        stop_fill_model="not_stop_exit",
    )

    assert [event["event_type"] for event in trade["accounting_events"]] == [
        "entry_fee",
        "trim_close",
        "trim_close",
        "final_close",
    ]
    assert Decimal(trade["trim_net_pnl"]) == Decimal("50")
    assert Decimal(trade["final_close_gross_pnl"]) == Decimal("135")
    assert Decimal(trade["net_pnl"]) == Decimal("184")
    assert Decimal(trade["remaining_quantity_final"]) == Decimal("0")


def test_mf_orig_ev11_drawdown_is_peak_to_trough_not_initial_minus_min() -> None:
    stats = _drawdown_stats([Decimal("10000"), Decimal("12000"), Decimal("11000")])
    below_initial = _drawdown_stats([Decimal("10000"), Decimal("9800"), Decimal("9700"), Decimal("10500")])

    assert stats["max_drawdown"] == Decimal("1000")
    assert stats["max_drawdown_pct"] == Decimal("1000") / Decimal("12000")
    assert below_initial["max_drawdown"] == Decimal("300")

    metrics = _original_metrics(
        [],
        initial_equity=Decimal("10000"),
        ending_equity=Decimal("11000"),
        realized_equity_curve=[Decimal("10000"), Decimal("12000"), Decimal("11000")],
        mark_to_market_equity_curve=[Decimal("10000"), Decimal("12000"), Decimal("11000")],
    )
    assert metrics["drawdown_method"] == "peak_to_trough"
    assert metrics["mark_to_market_max_drawdown"] == Decimal("1000")


def test_mf_orig_ev11_positive_1d_pockets_filter_matches_label() -> None:
    rows = [
        {
            "hypothesis_id": "mf_orig_1d_stage2_5_20_crossover",
            "symbol": "BTC",
            "timeframe": "1d",
            "baseline_net_pnl": "10",
            "net_pnl_delta_vs_v1_2": "5",
            "drawdown_delta_vs_v1_2": "-1",
            "trade_count": 1,
        },
        {
            "hypothesis_id": "mf_orig_1d_stage2_5_20_crossover",
            "symbol": "ETH",
            "timeframe": "1d",
            "baseline_net_pnl": "-20",
            "net_pnl_delta_vs_v1_2": "-100",
            "drawdown_delta_vs_v1_2": "200",
            "trade_count": 1,
        },
    ]

    pockets = _control_pocket_impact(rows)
    positive = next(
        row
        for row in pockets
        if row["hypothesis_id"] == "mf_orig_1d_stage2_5_20_crossover"
        and row["control_pocket"] == "positive 1d pockets"
    )
    all_1d = next(
        row
        for row in pockets
        if row["hypothesis_id"] == "mf_orig_1d_stage2_5_20_crossover"
        and row["control_pocket"] == "all_1d_pockets"
    )

    assert positive["filter"] == "baseline_positive"
    assert positive["trade_count"] == 1
    assert positive["net_pnl_delta_sum"] == "5"
    assert positive["gating_control"] is True
    assert all_1d["filter"] == "all"
    assert all_1d["trade_count"] == 2
    assert all_1d["gating_control"] is False
