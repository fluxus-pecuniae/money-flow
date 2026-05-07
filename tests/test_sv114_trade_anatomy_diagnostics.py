from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from services.strategy_validation.trade_anatomy import (
    LoadedCandle,
    build_money_flow_trade_anatomy_diagnostics,
    money_flow_trade_anatomy_to_markdown,
)


def _candles(symbol: str, timeframe: str) -> list[LoadedCandle]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    delta = timedelta(hours=1 if timeframe == "1h" else 4 if timeframe == "4h" else 0.25)
    rows: list[LoadedCandle] = []
    price = 100.0
    for index in range(80):
        open_time = start + (delta * index)
        close_time = open_time + delta
        price += 0.25 if index % 3 else -0.05
        rows.append(
            LoadedCandle(
                symbol=symbol,
                timeframe=timeframe,
                open_time=open_time,
                close_time=close_time,
                open=price,
                high=price + 1.5,
                low=price - 1.0,
                close=price + 0.2,
                volume=1000,
            )
        )
    return rows


def _trade(
    *,
    trade_id: str,
    symbol: str,
    component: str,
    timeframe: str,
    close_index: int,
    net_pnl: str,
    exit_reason: str,
) -> dict[str, object]:
    delta = timedelta(hours=1 if timeframe == "1h" else 4 if timeframe == "4h" else 0.25)
    entry_signal_time = datetime(2026, 1, 1, tzinfo=UTC) + (delta * close_index)
    exit_time = entry_signal_time + delta
    return {
        "trade_id": trade_id,
        "symbol": symbol,
        "component_key": component,
        "timeframe": timeframe,
        "entry_signal_time": entry_signal_time.isoformat().replace("+00:00", "Z"),
        "entry_time": entry_signal_time.isoformat().replace("+00:00", "Z"),
        "exit_time": exit_time.isoformat().replace("+00:00", "Z"),
        "entry_price": "105",
        "exit_price": "107",
        "duration_seconds": str(int(delta.total_seconds())),
        "entry_reason": None,
        "exit_reason": exit_reason,
        "entry_market_regime": "uptrend",
        "net_pnl": net_pnl,
        "max_adverse_excursion": "-12.5",
        "max_favorable_excursion": "28.5",
        "fill_timing": "next_candle_close",
        "fee_bps": "2",
        "slippage_bps": "1",
    }


def _batch_report(path: Path, *, component: str, timeframe: str, symbol: str, net_pnl: str) -> Path:
    payload = {
        "batch_name": f"fixture_{component}",
        "run_reports": [
            {
                "status": "completed",
                "run_id": f"run-{component}-{symbol}",
                "request": {
                    "environment": "testnet",
                    "venue": "hyperliquid",
                    "symbol": symbol,
                    "instrument_key": f"perpetual:linear:{symbol}:USDC:USDC",
                    "component_keys": [component],
                    "assumptions": {
                        "fill_timing": "next_candle_close",
                        "fee_bps": "2",
                        "slippage_bps": "1",
                        "capital_sizing_mode": "dynamic_equity_pct",
                    },
                },
                "report": {
                    "symbol": symbol,
                    "component_reports": [
                        {
                            "component_key": component,
                            "timeframe": timeframe,
                            "trades": [
                                _trade(
                                    trade_id=f"{symbol}-winner",
                                    symbol=symbol,
                                    component=component,
                                    timeframe=timeframe,
                                    close_index=45,
                                    net_pnl=net_pnl,
                                    exit_reason="trim_on_overbought_rsi",
                                ),
                                _trade(
                                    trade_id=f"{symbol}-loser",
                                    symbol=symbol,
                                    component=component,
                                    timeframe=timeframe,
                                    close_index=52,
                                    net_pnl="-80",
                                    exit_reason="ma_alignment_break",
                                ),
                            ],
                            "metrics": {
                                "number_of_trades": "2",
                                "ending_equity": str(10000 + float(net_pnl) - 80),
                                "net_account_pnl": str(float(net_pnl) - 80),
                                "net_pnl": str(float(net_pnl) - 80),
                                "win_rate": "0.5",
                                "profit_factor": "1.5",
                                "mark_to_market_max_drawdown": "120",
                                "total_fees": "8",
                                "total_slippage_cost": "4",
                                "no_trade_reason_counts": {"bearish_alignment": 3},
                                "invalid_reason_counts": {"insufficient_history": 1},
                            },
                            "no_trade_reason_counts": {"bearish_alignment": 3},
                            "invalid_reason_counts": {"insufficient_history": 1},
                        }
                    ],
                },
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_trade_anatomy_report_generation_and_strategy_logic(tmp_path: Path) -> None:
    batch = _batch_report(
        tmp_path / "batch_report.json",
        component="sleeve_1h",
        timeframe="1h",
        symbol="ETH",
        net_pnl="150",
    )
    report = build_money_flow_trade_anatomy_diagnostics(
        [batch],
        candles_by_symbol_timeframe={("ETH", "1h"): _candles("ETH", "1h")},
    )
    markdown = money_flow_trade_anatomy_to_markdown(report)

    assert "Current Money Flow Rule Logic" in markdown
    assert "does not enter long when RSI is below the sleeve floor" in markdown
    assert "not a buy-deep-oversold-weakness system" in markdown
    assert "Market-structure diagnostics in this report are descriptive only" in markdown
    assert report["boundary_flags"]["changes_money_flow_rules"] is False
    assert report["market_structure_diagnostics"]["used_as_entry_filter"] is False


def test_eth_concentration_and_scenario_rows_are_visible(tmp_path: Path) -> None:
    batch = _batch_report(
        tmp_path / "batch_report.json",
        component="sleeve_1h",
        timeframe="1h",
        symbol="ETH",
        net_pnl="200",
    )
    report = build_money_flow_trade_anatomy_diagnostics(
        [batch],
        candles_by_symbol_timeframe={("ETH", "1h"): _candles("ETH", "1h")},
    )
    markdown = money_flow_trade_anatomy_to_markdown(report)

    assert "ETH 1h Winning Anatomy" in markdown
    assert "| `next_candle_close` | 2 | 1 |" in markdown
    assert "fee/slippage" in markdown
    assert "dynamic-equity evidence" in markdown


def test_report_avoids_forbidden_recommendation_or_approval_language(tmp_path: Path) -> None:
    batch = _batch_report(
        tmp_path / "batch_report.json",
        component="sleeve_15m",
        timeframe="15m",
        symbol="BTC",
        net_pnl="-20",
    )
    markdown = money_flow_trade_anatomy_to_markdown(
        build_money_flow_trade_anatomy_diagnostics(
            [batch],
            candles_by_symbol_timeframe={("BTC", "15m"): _candles("BTC", "15m")},
        )
    ).lower()

    for forbidden in (
        "proven",
        "profitable",
        "approved",
        "recommended strategy",
        "optimal",
        "ready for paper trading",
        "ready for live trading",
    ):
        assert forbidden not in markdown


def test_no_live_or_routing_artifact_flags_are_created(tmp_path: Path) -> None:
    batch = _batch_report(
        tmp_path / "batch_report.json",
        component="sleeve_4h",
        timeframe="4h",
        symbol="SOL",
        net_pnl="-50",
    )
    report = build_money_flow_trade_anatomy_diagnostics(
        [batch],
        candles_by_symbol_timeframe={("SOL", "4h"): _candles("SOL", "4h")},
    )

    assert report["boundary_flags"]["creates_live_artifacts"] is False
    assert report["boundary_flags"]["creates_routing_artifacts"] is False
    assert report["boundary_flags"]["calls_exchange_order_endpoints"] is False


def test_dashboard_labels_keep_grouped_sums_and_strategy_boundary_clear() -> None:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    script = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")

    assert "Sums across research runs, not one combined account." in html
    assert "dynamic equity is per scenario and not one combined account" in html
    assert "Entries below the RSI floor are not allowed." in html
    assert "Market-structure diagnostics are not entry filters." in html
    assert "Sum Net" in script
    assert "Scenario Net PnL" in script


def test_strategy_module_does_not_include_market_structure_filters() -> None:
    source = Path("services/strategy/money_flow.py").read_text(encoding="utf-8")

    assert "recent_swing" not in source
    assert "nearby_resistance" not in source
    assert "market_structure" not in source

