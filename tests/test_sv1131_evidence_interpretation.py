from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from core.domain.enums import Environment, StrategyFamily, StrategyValidationFillTiming
from core.domain.models import (
    StrategyValidationAssumptions,
    StrategyValidationBatchReport,
    StrategyValidationBatchRunReport,
    StrategyValidationMetrics,
    StrategyValidationReport,
    StrategyValidationRequest,
)
from services.strategy_validation.service import strategy_validation_batch_report_to_markdown


def _metrics(net_pnl: str) -> StrategyValidationMetrics:
    return StrategyValidationMetrics(
        number_of_trades=3,
        winning_trades=2,
        losing_trades=1,
        win_rate=Decimal("0.66666667"),
        loss_rate=Decimal("0.33333333"),
        average_win=Decimal("10"),
        average_loss=Decimal("-5"),
        profit_factor=Decimal("2.0"),
        gross_pnl=Decimal(net_pnl) + Decimal("3"),
        net_pnl=Decimal(net_pnl),
        total_fees=Decimal("2"),
        total_slippage_cost=Decimal("1"),
        max_drawdown=Decimal("4"),
        max_drawdown_pct=Decimal("0.0004"),
        closed_trade_max_drawdown=Decimal("4"),
        closed_trade_max_drawdown_pct=Decimal("0.0004"),
        mark_to_market_max_drawdown=Decimal("6"),
        mark_to_market_max_drawdown_pct=Decimal("0.0006"),
        drawdown_methodology="closed_trade_and_mark_to_market",
        average_trade_duration_seconds=Decimal("3600"),
        best_trade_id="best",
        best_trade_net_pnl=Decimal("11"),
        worst_trade_id="worst",
        worst_trade_net_pnl=Decimal("-5"),
        return_on_initial_capital=Decimal(net_pnl) / Decimal("10000"),
        trades_by_component_timeframe={"sleeve_1h:1h": 3},
        no_trade_reason_counts={"bearish_alignment": 1},
        invalid_reason_counts={"insufficient_history": 1},
    )


def _run_report(*, run_id: str, symbol: str, fill_timing: StrategyValidationFillTiming, net_pnl: str) -> StrategyValidationBatchRunReport:
    start_at = datetime(2026, 1, 1, tzinfo=UTC)
    end_at = datetime(2026, 1, 2, tzinfo=UTC)
    assumptions = StrategyValidationAssumptions(
        initial_capital=Decimal("10000"),
        fee_bps=Decimal("2"),
        slippage_bps=Decimal("1"),
        position_notional_pct=Decimal("1"),
        fill_timing=fill_timing,
    )
    request = StrategyValidationRequest(
        strategy_family=StrategyFamily.MONEY_FLOW,
        environment=Environment.TESTNET,
        venue="hyperliquid",
        symbol=symbol,
        start_at=start_at,
        end_at=end_at,
        assumptions=assumptions,
        component_keys=("sleeve_1h",),
    )
    report = StrategyValidationReport(
        report_id=f"{run_id}-report",
        strategy_family=StrategyFamily.MONEY_FLOW,
        environment=Environment.TESTNET,
        venue="hyperliquid",
        symbol=symbol,
        instrument_key=f"perpetual:linear:{symbol}:USDC:USDC",
        instrument_ref_id=None,
        start_at=start_at,
        end_at=end_at,
        assumptions=assumptions,
        component_reports=[],
        aggregate_metrics=_metrics(net_pnl),
        data_coverage_summary={
            "minimum_coverage_percent": Decimal("100"),
            "total_actual_candle_count": 24,
            "total_expected_candle_count": 24,
            "warning_reason_codes": [],
        },
        regime_comparison={"rows": []},
    )
    return StrategyValidationBatchRunReport(
        run_id=run_id,
        run_index=0,
        request=request,
        status="completed",
        report=report,
        report_id=report.report_id,
    )


def test_batch_markdown_clarifies_grouped_aggregate_semantics() -> None:
    runs = [
        _run_report(
            run_id="btc-open",
            symbol="BTC",
            fill_timing=StrategyValidationFillTiming.NEXT_CANDLE_OPEN,
            net_pnl="10",
        ),
        _run_report(
            run_id="eth-close",
            symbol="ETH",
            fill_timing=StrategyValidationFillTiming.NEXT_CANDLE_CLOSE,
            net_pnl="20",
        ),
    ]
    comparison_summary = {
        "run_summaries": [
            {
                "run_id": run.run_id,
                "status": run.status,
                "component_keys": list(run.request.component_keys),
                "fill_timing": run.request.assumptions.fill_timing.value,
                "venue": run.request.venue,
                "symbol": run.request.symbol,
                "start_at": run.request.start_at.isoformat(),
                "end_at": run.request.end_at.isoformat(),
                "metrics": {
                    "number_of_trades": run.report.aggregate_metrics.number_of_trades,
                    "net_pnl": run.report.aggregate_metrics.net_pnl,
                    "win_rate": run.report.aggregate_metrics.win_rate,
                    "profit_factor": run.report.aggregate_metrics.profit_factor,
                    "mark_to_market_max_drawdown": run.report.aggregate_metrics.mark_to_market_max_drawdown,
                    "total_fees": run.report.aggregate_metrics.total_fees,
                    "total_slippage_cost": run.report.aggregate_metrics.total_slippage_cost,
                },
                "limitations": [],
                "error_message": None,
            }
            for run in runs
        ],
        "data_coverage_comparison": [
            {
                "run_id": run.run_id,
                "component_keys": list(run.request.component_keys),
                "symbol": run.request.symbol,
                "date_window": f"{run.request.start_at.isoformat()}->{run.request.end_at.isoformat()}",
                "total_actual_candle_count": 24,
                "total_expected_candle_count": 24,
                "minimum_coverage_percent": Decimal("100"),
                "warning_reason_codes": [],
            }
            for run in runs
        ],
        "regime_comparison": [],
        "fill_timing_comparison": [
            {
                "fill_timing": "next_candle_open",
                "scenario_count": 1,
                "run_count": 1,
                "completed_run_count": 1,
                "blocked_run_count": 0,
                "blocked_reason_counts": {},
                "sum_trades_across_research_runs": 3,
                "total_trades": 3,
                "sum_net_pnl_across_research_runs": Decimal("10"),
                "total_net_pnl": Decimal("10"),
                "average_net_pnl_per_completed_run": Decimal("10"),
                "average_net_pnl": Decimal("10"),
                "largest_mark_to_market_drawdown": Decimal("6"),
            }
        ],
        "component_comparison": [],
        "symbol_comparison": [],
        "date_window_comparison": [],
        "highest_observed_net_pnl_run": None,
        "lowest_observed_net_pnl_run": None,
        "highest_observed_win_rate_run": None,
        "largest_observed_mark_to_market_drawdown_run": None,
        "most_trades_run": None,
        "least_trades_run": None,
        "methodology": "reporting_only",
    }
    report = StrategyValidationBatchReport(
        batch_id="sv1131-test",
        batch_name="sv1131 test",
        strategy_family=StrategyFamily.MONEY_FLOW,
        run_reports=runs,
        assumptions_matrix={
            "symbols": ["BTC", "ETH"],
            "components": ["sleeve_1h"],
            "fill_timings": ["next_candle_open", "next_candle_close"],
            "date_windows": ["2026-01-01T00:00:00Z->2026-01-02T00:00:00Z"],
        },
        comparison_summary=comparison_summary,
    )

    markdown = strategy_validation_batch_report_to_markdown(report)

    assert "Grouped Aggregate Semantics" in markdown
    assert "sum_net_pnl_across_research_runs" in markdown
    assert "sum trades across research runs" in markdown
    assert "not one tradable account result" in markdown
    assert "single-scenario strategy PnL" in markdown


def test_sv1131_founder_report_contains_required_interpretation_sections() -> None:
    report = Path("docs/strategy_validation_sv1_13_1_hyperliquid_evidence_interpretation.md")

    assert report.exists()
    contents = report.read_text()

    for required in [
        "Grouped Aggregate Semantics",
        "Scenario-Level Results",
        "ETH Concentration Analysis",
        "Drawdown Interpretation",
        "Regime Dependence",
        "Cost Sensitivity",
        "Fill Timing Interpretation",
        "Hyperliquid USDC perpetual",
        "ready_for_founder_review",
    ]:
        assert required in contents

    for required in [
        "`sleeve_1h` | `ETH` | `next_candle_open`",
        "`sleeve_1h` | `ETH` | `next_candle_close`",
        "`5/3`",
        "Paper-trading design remains deferred",
    ]:
        assert required in contents


def test_sv1131_founder_report_avoids_forbidden_claim_language() -> None:
    contents = Path(
        "docs/strategy_validation_sv1_13_1_hyperliquid_evidence_interpretation.md"
    ).read_text().lower()

    forbidden_phrases = [
        "proven",
        "profitable",
        "profitability",
        "approved",
        "recommended strategy",
        "best strategy",
        "optimal",
        "ready for paper trading",
        "ready for live trading",
    ]

    for phrase in forbidden_phrases:
        assert phrase not in contents


def test_sv1131_report_preserves_hyperliquid_only_scope() -> None:
    contents = Path(
        "docs/strategy_validation_sv1_13_1_hyperliquid_evidence_interpretation.md"
    ).read_text()

    assert "Aster, Binance, OKX, Coinbase, and Kraken remain deferred comparative work" in contents
    assert "cross-venue comparison remains deferred" in contents
    assert "StrategyDecision" not in contents
    assert "OrderIntent" not in contents
    assert "Evidence packs analyzed" in contents
