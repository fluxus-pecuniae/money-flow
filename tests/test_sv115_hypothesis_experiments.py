from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from services.strategy_validation.hypothesis_experiments import (
    build_money_flow_hypothesis_experiments,
    money_flow_hypothesis_experiments_to_markdown,
)
from services.strategy_validation.trade_anatomy import LoadedCandle


def _candles(symbol: str, timeframe: str) -> list[LoadedCandle]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    delta = timedelta(hours=1 if timeframe == "1h" else 4 if timeframe == "4h" else 0.25)
    rows: list[LoadedCandle] = []
    price = 100.0
    for index in range(90):
        open_time = start + (delta * index)
        close_time = open_time + delta
        price += 0.30 if index % 5 else -0.10
        rows.append(
            LoadedCandle(
                symbol=symbol,
                timeframe=timeframe,
                open_time=open_time,
                close_time=close_time,
                open=price,
                high=price + 1.0,
                low=price - 0.8,
                close=price + 0.25,
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
    regime: str = "uptrend",
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
        "entry_price": "112",
        "exit_price": "114",
        "entry_notional": "10000",
        "return_pct": str(float(net_pnl) / 10000),
        "duration_seconds": str(int(delta.total_seconds())),
        "entry_reason": None,
        "exit_reason": exit_reason,
        "entry_market_regime": regime,
        "net_pnl": net_pnl,
        "max_adverse_excursion": "-30",
        "max_favorable_excursion": "80",
        "fill_timing": "next_candle_close",
        "fee_bps": "2",
        "slippage_bps": "1",
        "capital_sizing_mode": "dynamic_equity_pct",
    }


def _batch_report(
    path: Path,
    *,
    component: str = "sleeve_1h",
    timeframe: str = "1h",
    symbol: str = "ETH",
    winner: str = "150",
    loser: str = "-80",
) -> Path:
    net = float(winner) + float(loser)
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
                        "initial_capital": "10000",
                        "position_notional_pct": "1.0",
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
                                    net_pnl=winner,
                                    exit_reason="trim_on_overbought_rsi",
                                ),
                                _trade(
                                    trade_id=f"{symbol}-loser",
                                    symbol=symbol,
                                    component=component,
                                    timeframe=timeframe,
                                    close_index=52,
                                    net_pnl=loser,
                                    exit_reason="ma_alignment_break",
                                    regime="sideways",
                                ),
                            ],
                            "metrics": {
                                "number_of_trades": "2",
                                "starting_equity": "10000",
                                "ending_equity": str(10000 + net),
                                "net_account_pnl": str(net),
                                "net_pnl": str(net),
                                "win_rate": "0.5",
                                "profit_factor": "1.5",
                                "closed_trade_max_drawdown": "80",
                                "mark_to_market_max_drawdown": "100",
                                "capital_sizing_mode": "dynamic_equity_pct",
                                "no_trade_reason_counts": {"rsi_not_constructive": 3},
                                "invalid_reason_counts": {"insufficient_history": 1},
                            },
                            "no_trade_reason_counts": {"rsi_not_constructive": 3},
                            "invalid_reason_counts": {"insufficient_history": 1},
                        }
                    ],
                },
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_hypothesis_experiment_report_has_baseline_and_research_only_variants(tmp_path: Path) -> None:
    batch = _batch_report(tmp_path / "batch_report.json")
    report = build_money_flow_hypothesis_experiments(
        [batch],
        candles_by_symbol_timeframe={("ETH", "1h"): _candles("ETH", "1h")},
    )
    markdown = money_flow_hypothesis_experiments_to_markdown(report)

    assert "Baseline is current Money Flow rules with `dynamic_equity_pct` sizing." in markdown
    assert "resistance_proximity_0_25pct" in markdown
    assert "research_only=true, changes_rules=false" in markdown
    assert report["boundary_flags"]["changes_production_money_flow_rules"] is False
    assert report["boundary_flags"]["uses_dynamic_equity_in_main_report"] is True


def test_baseline_comparison_is_present_for_each_filter_variant(tmp_path: Path) -> None:
    batch = _batch_report(tmp_path / "batch_report.json")
    report = build_money_flow_hypothesis_experiments(
        [batch],
        candles_by_symbol_timeframe={("ETH", "1h"): _candles("ETH", "1h")},
    )

    assert report["variant_results"]
    for row in report["variant_results"]:
        assert "baseline_net_account_pnl" in row
        assert "net_account_pnl_delta" in row
        assert "methodology" in row
        assert row["capital_sizing_mode"] == "dynamic_equity_pct"


def test_every_variant_has_methodology_classification(tmp_path: Path) -> None:
    batch = _batch_report(tmp_path / "batch_report.json")
    report = build_money_flow_hypothesis_experiments(
        [batch],
        candles_by_symbol_timeframe={("ETH", "1h"): _candles("ETH", "1h")},
    )
    methodologies = {row["variant_id"]: row["methodology"] for row in report["variant_definitions"]}

    assert methodologies["resistance_proximity_0_25pct"] == "completed_trade_overlay_estimate"
    assert methodologies["higher_low_confirmation_20c"] == "completed_trade_overlay_estimate"
    assert methodologies["sideways_regime_avoidance_15m"] == "completed_trade_overlay_estimate"
    assert methodologies["extension_limit_4h_1_5pct"] == "completed_trade_overlay_estimate"
    assert methodologies["recent_low_invalidation_proxy_20c"] == "lookahead_diagnostic_proxy"
    assert methodologies["lower_half_rsi_attribution"] == "reporting_only_attribution"
    assert methodologies["pullback_vs_continuation_attribution"] == "reporting_only_attribution"
    assert methodologies["lower_rsi_floor_expansion_replay_required"] == "deferred_requires_rejected_signal_replay"


def test_lower_rsi_and_pullback_sections_are_visible_without_rule_changes(tmp_path: Path) -> None:
    batch = _batch_report(tmp_path / "batch_report.json")
    markdown = money_flow_hypothesis_experiments_to_markdown(
        build_money_flow_hypothesis_experiments(
            [batch],
            candles_by_symbol_timeframe={("ETH", "1h"): _candles("ETH", "1h")},
        )
    )

    assert "Lower-Half RSI Attribution Inside Current Band" in markdown
    assert "Lower RSI Floor Expansion / Pullback Variants" in markdown
    assert "deferred_requires_rejected_signal_replay" in markdown
    assert "falling-knife risk" in markdown
    assert "Current production Money Flow does not enter below the RSI sleeve floor" in markdown
    assert "Pullback vs Continuation Attribution" in markdown


def test_recent_low_proxy_is_downgraded_and_excluded_from_normal_improvement_bucket(tmp_path: Path) -> None:
    batch = _batch_report(tmp_path / "batch_report.json")
    report = build_money_flow_hypothesis_experiments(
        [batch],
        candles_by_symbol_timeframe={("ETH", "1h"): _candles("ETH", "1h")},
    )
    status = report["hypothesis_status"]
    definitions = {row["variant_id"]: row for row in report["variant_definitions"]}
    markdown = money_flow_hypothesis_experiments_to_markdown(report)

    assert definitions["recent_low_invalidation_proxy_20c"]["methodology"] == "lookahead_diagnostic_proxy"
    assert "recent_low_invalidation_proxy_20c" in status["lookahead_proxy_upper_bound_not_candidate"]
    assert "recent_low_invalidation_proxy_20c" not in status["diagnostic_overlay_improved_needs_true_replay"]
    assert "lookahead diagnostic upper bound" in markdown
    assert "not a candidate rule result" in markdown


def test_report_explains_completed_trade_overlay_limitations(tmp_path: Path) -> None:
    batch = _batch_report(tmp_path / "batch_report.json")
    markdown = money_flow_hypothesis_experiments_to_markdown(
        build_money_flow_hypothesis_experiments(
            [batch],
            candles_by_symbol_timeframe={("ETH", "1h"): _candles("ETH", "1h")},
        )
    )

    assert "completed-trade overlay diagnostics" in markdown
    assert "not true candle-by-candle strategy replays" in markdown
    assert "do not admit new alternative trades" in markdown
    assert "do not fully model changed position occupancy" in markdown
    assert "do not fully model exact earlier exit fills" in markdown


def test_15m_sideways_and_4h_extension_variants_are_research_only(tmp_path: Path) -> None:
    batch15 = _batch_report(
        tmp_path / "batch15.json",
        component="sleeve_15m",
        timeframe="15m",
        symbol="BTC",
        winner="-20",
        loser="-50",
    )
    batch4h = _batch_report(
        tmp_path / "batch4h.json",
        component="sleeve_4h",
        timeframe="4h",
        symbol="SOL",
        winner="-30",
        loser="-90",
    )
    report = build_money_flow_hypothesis_experiments(
        [batch15, batch4h],
        candles_by_symbol_timeframe={
            ("BTC", "15m"): _candles("BTC", "15m"),
            ("SOL", "4h"): _candles("SOL", "4h"),
        },
    )
    ids = {row["variant_id"] for row in report["variant_results"]}
    definitions = {row["variant_id"]: row for row in report["variant_definitions"]}

    assert "sideways_regime_avoidance_15m" in ids
    assert "extension_limit_4h_2_0pct" in ids
    assert definitions["sideways_regime_avoidance_15m"]["changes_production_rules"] is False
    assert definitions["extension_limit_4h_2_0pct"]["research_only"] is True


def test_forbidden_language_and_live_artifacts_are_absent(tmp_path: Path) -> None:
    batch = _batch_report(tmp_path / "batch_report.json")
    report = build_money_flow_hypothesis_experiments(
        [batch],
        candles_by_symbol_timeframe={("ETH", "1h"): _candles("ETH", "1h")},
    )
    markdown = money_flow_hypothesis_experiments_to_markdown(report).lower()

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
    assert report["boundary_flags"]["creates_live_artifacts"] is False
    assert report["boundary_flags"]["creates_routing_artifacts"] is False
    assert report["boundary_flags"]["calls_exchange_order_endpoints"] is False


def test_production_money_flow_rules_are_not_modified_by_experiment_layer() -> None:
    source = Path("services/strategy/money_flow.py").read_text(encoding="utf-8")

    assert "MoneyFlowResearchVariant" not in source
    assert "lower_rsi_floor_expansion" not in source
    assert "resistance_proximity" not in source
    assert "higher_low_confirmation" not in source
