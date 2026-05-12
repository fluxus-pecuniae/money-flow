from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from core.domain.enums import StrategyValidationCapitalSizingMode, StrategyValidationFillTiming, Timeframe
from services.strategy_validation import MoneyFlowBacktestService, strategy_validation_report_to_dict
from services.strategy_validation.service import _request_payload
from services.strategy_validation.sor_ev2 import (
    ALL_VARIANTS,
    build_sor_ev2_report_sync,
    sor_ev2_report_to_markdown,
)
from tests.test_sv10_strategy_validation import (
    build_request_for_window,
    build_settings,
    build_test_session_factory,
    bullish_then_break_closes,
    seed_candles,
    seed_symbol,
)


def _seeded_canonical_pack(tmp_path: Path):
    settings = build_settings(
        MONEY_FLOW_15M_RSI_FLOOR=80.0,
        MONEY_FLOW_15M_RSI_CEILING=90.0,
        MONEY_FLOW_15M_OVERBOUGHT_RSI=95.0,
        MONEY_FLOW_15M_REQUIRE_MACD_CONFIRMATION=False,
    )
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    closes = bullish_then_break_closes()
    opens = [close - Decimal("0.4") for close in closes]
    highs = [max(open_, close) + Decimal("0.8") for open_, close in zip(opens, closes, strict=True)]
    lows = [min(open_, close) - Decimal("0.8") for open_, close in zip(opens, closes, strict=True)]
    lows[34] = Decimal("103.0")
    start, delta = seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=closes,
        opens=opens,
        highs=highs,
        lows=lows,
    )
    request = build_request_for_window(
        start=start,
        delta=delta,
        closes=closes,
        instrument_key=instrument_key,
        fill_timing=StrategyValidationFillTiming.NEXT_CANDLE_OPEN,
        fee_bps=Decimal("5"),
        slippage_bps=Decimal("3"),
    )
    request.assumptions.capital_sizing_mode = StrategyValidationCapitalSizingMode.DYNAMIC_EQUITY_PCT
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)
    report = asyncio.run(service.run_money_flow_backtest(request))
    payload = strategy_validation_report_to_dict(report)
    pack = tmp_path / "reports" / "strategy_validation" / "money_flow_sv2_0_2_hyperliquid_public_btc_15m_canonical_db_imported" / "20260512T064916Z" / "batch_report.json"
    pack.parent.mkdir(parents=True)
    import json
    pack.write_text(json.dumps({
        "batch_id": "test-sor-ev2",
        "batch_name": "test_sor_ev2",
        "run_reports": [
            {
                "run_id": "run-btc-15m-open",
                "run_index": 0,
                "request": _request_payload(request),
                "status": "completed",
                "report": payload,
                "report_id": payload["report_id"],
                "reason_codes": [],
            }
        ],
    }), encoding="utf-8")
    return settings, session_factory, service, pack


def test_sor_ev2_uses_canonical_sv202_paths_and_measures_baseline_parity(tmp_path: Path) -> None:
    _, _, service, pack = _seeded_canonical_pack(tmp_path)

    report = build_sor_ev2_report_sync([pack], backtest_service=service)

    assert report["phase"] == "SOR-EV2"
    assert report["baseline_evidence_references"] == [str(pack)]
    assert report["baseline_parity_summary"]["status_counts"] == {"baseline_parity_passed": 1}
    assert report["boundary_flags"]["uses_dashboard_date_filter_recalculation"] is False
    assert report["boundary_flags"]["uses_hyperliquid_testnet_prices"] is False


def test_sor_ev2_true_forward_variants_and_rejected_signal_truth(tmp_path: Path) -> None:
    _, _, service, pack = _seeded_canonical_pack(tmp_path)

    report = build_sor_ev2_report_sync([pack], backtest_service=service)
    variants = {row["variant_id"]: row for row in report["variant_summary"]}

    for variant_id in ALL_VARIANTS:
        assert variant_id in variants
        assert variants[variant_id]["methodology"] == "true_forward_replay"
        assert variants[variant_id]["production_approved"] is False
    assert variants["fixed_stop_loss_pct_2"]["stop_exits"] >= 0
    assert "rsi_not_constructive" in report["rejected_signal_replay_summary"]["required_categories"]
    assert report["large_loss_candle_context_summary"]["sample_count"] >= 1
    assert "control_pocket_impact" in report


def test_sor_ev2_report_avoids_proof_live_and_order_language(tmp_path: Path) -> None:
    _, _, service, pack = _seeded_canonical_pack(tmp_path)

    report = build_sor_ev2_report_sync([pack], backtest_service=service)
    markdown = sor_ev2_report_to_markdown(report).lower()

    assert "true-forward" in markdown
    assert "production money flow rules are unchanged" in markdown
    assert "no order endpoints are called" in markdown
    for forbidden in ("proven", "optimal", "approved for live", "guaranteed", "ready for real trading", "production-approved"):
        assert forbidden not in markdown


def test_sor_ev2_outputs_exist_after_generation() -> None:
    assert Path("docs/sor_ev2_true_forward_stop_and_rejected_signal_replay.md").exists()
    assert Path("docs/sor_ev2_true_forward_stop_and_rejected_signal_replay_summary.json").exists()


def test_sor_ev2_does_not_modify_production_money_flow_rules() -> None:
    source = Path("services/strategy/money_flow.py").read_text()
    assert "fixed_stop_loss_pct_1" not in source
    assert "large_bear_candle_exit" not in source
    assert "lower_rsi_trend_intact_entry" not in source
    assert "SOR-EV2" not in source
