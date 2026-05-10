from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from core.domain.enums import Timeframe
from services.uat.public_read_only import PublicHTTPResult
from services.uat.shadow import UATShadowSignalStatus, UATShadowTimingAssumption, UATShadowTimingStatus
from services.uat.shadow_run import (
    UAT2ShadowMode,
    fetch_public_candles,
    render_uat2_report,
    require_uat2_shadow_mode,
    run_uat2_shadow_strategy,
)


def _safe_mode() -> UAT2ShadowMode:
    return UAT2ShadowMode(
        runtime_mode="uat",
        uat2_shadow_run=True,
        shadow_only=True,
        public_read_only=True,
        allow_public_read_only_network=True,
        private_endpoints_allowed=False,
        signed_endpoints_allowed=False,
        order_endpoints_allowed=False,
        api_keys_used=False,
        order_submission_enabled=False,
        paper_trading_enabled=False,
        live_trading_enabled=False,
    )


def _fixture_candle_payload(symbol: str, interval: str, count: int = 90) -> list[dict[str, Any]]:
    del symbol
    step = {"15m": 15, "1h": 60, "4h": 240}[interval]
    start = datetime(2026, 5, 1, tzinfo=UTC)
    rows: list[dict[str, Any]] = []
    price = Decimal("100")
    for index in range(count):
        open_time = start + timedelta(minutes=step * index)
        close_time = open_time + timedelta(minutes=step)
        # Oscillate mildly so RSI/MACD have complete but not one-way-extreme values.
        price += Decimal("0.30") if index % 4 in {0, 1} else Decimal("-0.10")
        open_price = price
        close_price = price + (Decimal("0.08") if index % 3 else Decimal("-0.04"))
        high = max(open_price, close_price) + Decimal("0.25")
        low = min(open_price, close_price) - Decimal("0.25")
        rows.append(
            {
                "t": int(open_time.timestamp() * 1000),
                "T": int(close_time.timestamp() * 1000),
                "o": str(open_price),
                "h": str(high),
                "l": str(low),
                "c": str(close_price),
                "v": "12345.678",
                "n": 10 + index,
            }
        )
    return rows


def _fixture_transport(method: str, url: str, payload: dict[str, Any] | None) -> PublicHTTPResult:
    assert method == "POST"
    assert url == "https://api.hyperliquid.xyz/info"
    assert payload is not None
    assert payload["type"] == "candleSnapshot"
    req = payload["req"]
    return PublicHTTPResult(
        url=url,
        method=method,
        status_code=200,
        payload=_fixture_candle_payload(req["coin"], req["interval"]),
        response_headers={},
        success=True,
    )


def test_uat2_shadow_mode_must_be_explicit_and_safe() -> None:
    with pytest.raises(ValueError, match="UAT2 shadow run requires explicit"):
        require_uat2_shadow_mode(UAT2ShadowMode())

    unsafe = _safe_mode().__class__(**{**_safe_mode().__dict__, "private_endpoints_allowed": True})
    with pytest.raises(ValueError, match="UAT2 shadow run requires explicit"):
        require_uat2_shadow_mode(unsafe)

    live_mode = _safe_mode().__class__(**{**_safe_mode().__dict__, "runtime_mode": "live"})
    with pytest.raises(ValueError, match="UAT2 shadow run requires explicit"):
        require_uat2_shadow_mode(live_mode)

    require_uat2_shadow_mode(_safe_mode())


def test_public_candle_fetch_uses_public_read_only_and_no_api_key() -> None:
    result, candles = fetch_public_candles(
        symbol="ETH",
        component="sleeve_1h",
        timeframe=Timeframe.H1,
        mode=_safe_mode(),
        lookback_candles=80,
        now=datetime(2026, 5, 10, 8, tzinfo=UTC),
        transport=_fixture_transport,
    )

    assert result.success is True
    assert result.attempted is True
    assert result.candle_count == 90
    assert candles
    assert _safe_mode().api_keys_used is False


def test_uat2_shadow_run_loads_universe_snapshot_and_emits_shadow_audits_only() -> None:
    result = run_uat2_shadow_strategy(
        mode=_safe_mode(),
        symbols=("ETH",),
        components=("sleeve_1h",),
        now=datetime(2026, 5, 10, 8, tzinfo=UTC),
        transport=_fixture_transport,
        run_id="uat2-shadow-fixture",
    )

    assert result.symbols_evaluated == ("ETH",)
    assert result.components_evaluated == ("sleeve_1h",)
    assert result.source_provider == "coingecko_public_markets"
    assert len(result.audit_records) == 1
    record = result.audit_records[0]
    assert record.top20_universe_member is True
    assert record.signal_status in {UATShadowSignalStatus.NO_TRADE, UATShadowSignalStatus.WOULD_OPEN}
    assert UATShadowTimingAssumption.NEXT_CANDLE_OPEN in record.timing_assumptions_evaluated
    assert UATShadowTimingAssumption.NEXT_CANDLE_CLOSE in record.timing_assumptions_evaluated
    assert UATShadowTimingAssumption.SAME_CANDLE_CLOSE_RESEARCH_ONLY not in record.timing_assumptions_evaluated
    assert record.same_candle_close_research_only is True
    assert record.timing_status_by_assumption["next_candle_open"] == UATShadowTimingStatus.AVAILABLE
    assert record.timing_status_by_assumption["next_candle_close"] == UATShadowTimingStatus.AVAILABLE
    assert record.no_live_artifacts_created is True
    assert result.boundary_flags["strategy_decisions_created"] is False
    assert result.boundary_flags["signal_events_created"] is False
    assert result.boundary_flags["order_intents_created"] is False
    assert result.boundary_flags["submitted_orders_created"] is False
    assert result.boundary_flags["routing_artifacts_created"] is False
    assert result.boundary_flags["approvals_created"] is False


def test_uat2_reason_summaries_and_shadow_drawdown_are_visible_not_live_account() -> None:
    result = run_uat2_shadow_strategy(
        mode=_safe_mode(),
        symbols=("ETH",),
        components=("sleeve_15m", "sleeve_1h", "sleeve_4h"),
        now=datetime(2026, 5, 10, 8, tzinfo=UTC),
        transport=_fixture_transport,
        run_id="uat2-shadow-fixture",
    )

    assert len(result.summaries) == 3
    assert sum(summary.no_trade_count + summary.would_open_count + summary.invalid_count for summary in result.summaries) == 3
    assert result.shadow_drawdown_state.not_live_account_drawdown is True
    assert result.shadow_drawdown_state.shadow_simulated_drawdown is True
    assert result.shadow_drawdown_state.current_shadow_equity == Decimal("10000")
    assert result.uat3_readiness_decision == "UAT3 is blocked"
    assert result.remaining_blockers


def test_uat2_report_records_boundaries_and_forbidden_approval_language_absent() -> None:
    result = run_uat2_shadow_strategy(
        mode=_safe_mode(),
        symbols=("ETH",),
        components=("sleeve_1h",),
        now=datetime(2026, 5, 10, 8, tzinfo=UTC),
        transport=_fixture_transport,
        run_id="uat2-shadow-fixture",
    )
    report = render_uat2_report(result)

    assert "UAT2 Shadow Strategy Top-20 Observation" in report
    assert "next_candle_open" in report
    assert "next_candle_close" in report
    assert "same_candle_close_research_only" in report
    assert "not_live_account_drawdown" in report
    assert "`strategy_decisions_created`: `false`" in report
    assert "`order_intents_created`: `false`" in report
    assert "`submitted_orders_created`: `false`" in report
    assert "UAT3 is blocked" in report
    for phrase in (
        "approved for paper trading",
        "ready for live trading",
        "proven profitable",
        "recommended strategy",
    ):
        assert phrase not in report.lower()


def test_committed_uat2_report_if_present() -> None:
    report_path = Path("docs/uat2_shadow_strategy_top20_observation.md")
    if report_path.exists():
        report = report_path.read_text()
        assert "UAT2 Shadow Strategy Top-20 Observation" in report
        assert "Paper trading is not approved" in report
        assert "Live trading is not approved" in report
        assert "Exchange order submission is not approved" in report
        assert "UAT3 is blocked" in report or "UAT3 approval-gated sandbox order design may be scoped" in report
