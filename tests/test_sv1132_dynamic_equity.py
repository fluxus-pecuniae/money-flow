from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import func, select

from core.domain.enums import StrategyValidationCapitalSizingMode, Timeframe
from db.models import (
    ExecutionReadinessEvaluationModel,
    MandateDesiredTradeModel,
    OrderIntentModel,
    SubmittedOrderModel,
)
from services.strategy_validation import (
    MoneyFlowBacktestService,
    build_money_flow_research_campaign_batch_request,
    money_flow_research_campaign_config_from_dict,
    strategy_validation_report_to_dict,
    strategy_validation_report_to_markdown,
)
from tests.test_sv10_strategy_validation import (
    build_request_for_window,
    build_settings,
    build_test_session_factory,
    bullish_then_break_closes,
    seed_candles,
    seed_symbol,
)


def _run_report(
    *,
    capital_sizing_mode: StrategyValidationCapitalSizingMode,
    fee_bps: Decimal = Decimal("0"),
):
    settings = build_settings()
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    closes = bullish_then_break_closes()
    start, delta = seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=closes,
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)
    request = build_request_for_window(
        start=start,
        delta=delta,
        closes=closes,
        instrument_key=instrument_key,
        fee_bps=fee_bps,
    )
    request.assumptions.capital_sizing_mode = capital_sizing_mode
    report = asyncio.run(service.run_money_flow_backtest(request))
    return report, session_factory


def test_constant_capital_sizing_mode_keeps_entry_notional_unchanged() -> None:
    report, _ = _run_report(
        capital_sizing_mode=(
            StrategyValidationCapitalSizingMode.CONSTANT_INITIAL_CAPITAL_NOTIONAL_PER_TRADE
        )
    )
    trades = report.component_reports[0].trades

    assert len(trades) >= 2
    assert trades[0].entry_notional == Decimal("10000.00000000")
    assert trades[1].entry_notional == Decimal("10000.00000000")
    assert trades[0].capital_sizing_mode == (
        StrategyValidationCapitalSizingMode.CONSTANT_INITIAL_CAPITAL_NOTIONAL_PER_TRADE
    )


def test_dynamic_equity_mode_increases_next_notional_after_win() -> None:
    report, _ = _run_report(
        capital_sizing_mode=StrategyValidationCapitalSizingMode.DYNAMIC_EQUITY_PCT
    )
    trades = report.component_reports[0].trades

    assert len(trades) >= 2
    assert trades[0].net_pnl > 0
    assert trades[1].entry_notional == trades[0].equity_after_exit
    assert trades[1].entry_notional > trades[0].entry_notional
    assert report.aggregate_metrics.ending_equity == trades[-1].equity_after_exit


def test_dynamic_equity_mode_decreases_next_notional_after_loss() -> None:
    report, _ = _run_report(
        capital_sizing_mode=StrategyValidationCapitalSizingMode.DYNAMIC_EQUITY_PCT,
        fee_bps=Decimal("100"),
    )
    trades = report.component_reports[0].trades

    assert len(trades) >= 2
    assert trades[0].net_pnl < 0
    assert trades[1].entry_notional == trades[0].equity_after_exit
    assert trades[1].entry_notional < trades[0].entry_notional


def test_dynamic_equity_final_equity_equals_sequential_net_pnl() -> None:
    report, _ = _run_report(
        capital_sizing_mode=StrategyValidationCapitalSizingMode.DYNAMIC_EQUITY_PCT
    )
    net_pnl = sum(
        (trade.net_pnl for trade in report.component_reports[0].trades),
        Decimal("0"),
    )

    assert report.aggregate_metrics.starting_equity == Decimal("10000.00000000")
    assert report.aggregate_metrics.ending_equity == Decimal("9982.08295638")
    assert report.aggregate_metrics.net_account_pnl == Decimal("-17.91704362")
    assert report.aggregate_metrics.ending_equity == Decimal("10000") + net_pnl


def test_dynamic_equity_depletion_skips_new_entries() -> None:
    report, _ = _run_report(
        capital_sizing_mode=StrategyValidationCapitalSizingMode.DYNAMIC_EQUITY_PCT,
        fee_bps=Decimal("10000"),
    )

    assert report.aggregate_metrics.ending_equity <= 0
    assert report.aggregate_metrics.trades_skipped_due_to_insufficient_equity > 0
    assert (
        report.aggregate_metrics.invalid_reason_counts["dynamic_equity_depleted"]
        == report.aggregate_metrics.trades_skipped_due_to_insufficient_equity
    )
    assert "dynamic_equity_depleted_no_new_trades_opened" in report.limitations


def test_dynamic_report_output_exposes_account_equity_fields_without_live_artifacts() -> None:
    report, session_factory = _run_report(
        capital_sizing_mode=StrategyValidationCapitalSizingMode.DYNAMIC_EQUITY_PCT
    )

    payload = strategy_validation_report_to_dict(report)
    markdown = strategy_validation_report_to_markdown(report)
    assert payload["assumptions"]["capital_sizing_mode"] == "dynamic_equity_pct"
    assert payload["assumptions"]["entry_notional_formula"] == (
        "current_realized_equity * position_notional_pct"
    )
    assert payload["aggregate_metrics"]["starting_equity"] == "10000.00000000"
    assert "Ending equity" in markdown
    assert "dynamic_equity_pct" in markdown
    assert "constant_initial_capital_notional_per_trade" not in markdown
    for forbidden in ("proven profitable", "paper trading approved", "ready for live trading"):
        assert forbidden not in markdown.lower()

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(MandateDesiredTradeModel)) == 0
        assert session.scalar(select(func.count()).select_from(OrderIntentModel)) == 0
        assert session.scalar(select(func.count()).select_from(ExecutionReadinessEvaluationModel)) == 0
        assert session.scalar(select(func.count()).select_from(SubmittedOrderModel)) == 0


def test_campaign_config_can_expand_dynamic_equity_mode() -> None:
    config = money_flow_research_campaign_config_from_dict(
        {
            "campaign_name": "sv1132_dynamic_fixture",
            "description": "fixture",
            "environment": "testnet",
            "venue": "hyperliquid",
            "symbols": [{"symbol": "BTC", "instrument_key": "perpetual:linear:BTC:USDC:USDC"}],
            "components": ["sleeve_15m"],
            "fill_timings": ["next_candle_open"],
            "windows": [
                {
                    "label": "fixture",
                    "start": "2026-01-01T00:00:00Z",
                    "end": "2026-01-02T00:00:00Z",
                }
            ],
            "fee_bps_values": ["0"],
            "slippage_bps_values": ["0"],
            "initial_capital": "10000",
            "position_notional_pct": "1.0",
            "capital_sizing_modes": [
                "constant_initial_capital_notional_per_trade",
                "dynamic_equity_pct",
            ],
            "output_dir": "reports/strategy_validation",
        }
    )
    batch_request = build_money_flow_research_campaign_batch_request(config)

    assert [run.assumptions.capital_sizing_mode for run in batch_request.runs] == [
        StrategyValidationCapitalSizingMode.CONSTANT_INITIAL_CAPITAL_NOTIONAL_PER_TRADE,
        StrategyValidationCapitalSizingMode.DYNAMIC_EQUITY_PCT,
    ]
