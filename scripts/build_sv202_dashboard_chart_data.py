from __future__ import annotations

import asyncio
import argparse
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any

from services.strategy_validation.service import MoneyFlowBacktestService
from services.strategy_validation.sor_ev2 import (
    _assert_canonical_paths,
    _load_canonical_scenarios,
    _request_from_payload,
)
from services.strategy_validation.sor_ev3 import (
    _feature_rows,
    _run_variant_replay,
)


DEFAULT_SUMMARY = Path("docs/sv2_0_historical_data_refresh_summary.json")
DEFAULT_RAW_DIR = Path("/tmp/money-flow-sv202-candles")
DEFAULT_OUTPUT_DIR = Path("reports/strategy_validation/sv2_0_2_dashboard_chart_data")
SOR_EV3_HISTORICAL_REPLAY_VARIANTS = (
    "avoid_low_rolling_range_20",
    "avoid_low_rolling_range_50",
)
SOR_EV3_HISTORICAL_REPLAY_LABELS = {
    "avoid_low_rolling_range_20": "SOR-EV3 avoid low rolling range 20",
    "avoid_low_rolling_range_50": "SOR-EV3 avoid low rolling range 50",
}


def safe_replay_path_segment(value: Any) -> str:
    return "".join(
        char.lower() if char.isalnum() else "_" for char in str(value)
    ).strip("_")


def decimal_or_none(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def float_or_none(value: Any) -> float | None:
    parsed = decimal_or_none(value)
    return float(parsed) if parsed is not None else None


def ema(values: list[float | None], period: int) -> list[float | None]:
    alpha = 2 / (period + 1)
    result: list[float | None] = []
    current: float | None = None
    for value in values:
        if value is None:
            result.append(None)
            continue
        current = value if current is None else (value * alpha) + (current * (1 - alpha))
        result.append(current)
    return result


def sma(values: list[float | None], period: int) -> list[float | None]:
    result: list[float | None] = []
    window: list[float] = []
    for value in values:
        if value is not None:
            window.append(value)
        if len(window) > period:
            window.pop(0)
        result.append(sum(window) / period if len(window) == period else None)
    return result


def rsi(values: list[float | None], period: int = 14) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    gains: list[float] = []
    losses: list[float] = []
    previous: float | None = None
    average_gain: float | None = None
    average_loss: float | None = None
    for index, value in enumerate(values):
        if value is None or previous is None:
            previous = value
            continue
        change = value - previous
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
        if len(gains) < period:
            previous = value
            continue
        if len(gains) == period:
            average_gain = sum(gains) / period
            average_loss = sum(losses) / period
        elif average_gain is not None and average_loss is not None:
            average_gain = ((average_gain * (period - 1)) + gains[-1]) / period
            average_loss = ((average_loss * (period - 1)) + losses[-1]) / period
        if average_gain is not None and average_loss is not None:
            result[index] = 100.0 if average_loss == 0 else 100 - (100 / (1 + (average_gain / average_loss)))
        previous = value
    return result


def indicators(candles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    closes = [float_or_none(row.get("close")) for row in candles]
    ema5 = ema(closes, 5)
    ema10 = ema(closes, 10)
    sma20 = sma(closes, 20)
    rsi14 = rsi(closes, 14)
    macd_fast = ema(closes, 12)
    macd_slow = ema(closes, 26)
    macd_line: list[float | None] = []
    for fast, slow in zip(macd_fast, macd_slow, strict=True):
        macd_line.append(None if fast is None or slow is None else fast - slow)
    macd_signal = ema(macd_line, 9)
    rows: list[dict[str, Any]] = []
    for index, candle in enumerate(candles):
        macd_value = macd_line[index]
        signal_value = macd_signal[index]
        rows.append(
            {
                "timestamp_utc": candle["close_time"],
                "EMA5": ema5[index],
                "EMA10": ema10[index],
                "SMA20": sma20[index],
                "RSI": rsi14[index],
                "MACD": macd_value,
                "MACD_signal": signal_value,
                "MACD_histogram": None
                if macd_value is None or signal_value is None
                else macd_value - signal_value,
            }
        )
    return rows


def normalize_candles(candles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "timestamp_utc": row["close_time"],
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": row.get("volume", "0"),
        }
        for row in candles
    ]


def normalize_trade(trade: dict[str, Any]) -> dict[str, Any]:
    exit_reason = trade.get("exit_reason")
    entry_reason = trade.get("entry_reason")
    return {
        **trade,
        "entry_fill_time": trade.get("entry_time") or trade.get("entry_signal_time"),
        "exit_fill_time": trade.get("exit_time") or trade.get("exit_signal_time"),
        "equity_before_trade": trade.get("equity_before_entry"),
        "equity_after_trade": trade.get("equity_after_exit"),
        "entry_reason_codes": [entry_reason] if entry_reason else ["money_flow_entry"],
        "exit_reason_codes": [exit_reason] if exit_reason else [],
        "drawdown_after_trade": trade.get("max_adverse_excursion"),
        "entry_indicators": {},
        "exit_indicators": {},
    }


def iso_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    return str(value).replace("+00:00", "Z")


def scalar(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return iso_value(value)
    enum_value = getattr(value, "value", None)
    if enum_value is not None:
        return enum_value
    return value


def indicator_lookup(indicator_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row["timestamp_utc"]).replace("+00:00", "Z"): row
        for row in indicator_rows
        if row.get("timestamp_utc")
    }


def trade_indicator_snapshot(
    trade: Any,
    indicators_by_time: dict[str, dict[str, Any]],
    prefix: str,
) -> dict[str, Any]:
    timestamp = iso_value(getattr(trade, f"{prefix}_signal_time", None) or getattr(trade, f"{prefix}_time", None))
    row = indicators_by_time.get(timestamp or "") or {}
    return {
        "time": timestamp,
        "RSI": row.get("RSI"),
        "EMA5": row.get("EMA5"),
        "EMA10": row.get("EMA10"),
        "SMA20": row.get("SMA20"),
        "MACD": row.get("MACD"),
        "MACD_signal": row.get("MACD_signal"),
        "MACD_histogram": row.get("MACD_histogram"),
        "market_regime": getattr(trade, f"{prefix}_market_regime", None),
        "volatility_regime": getattr(trade, f"{prefix}_volatility_regime", None),
    }


def normalize_strategy_validation_trade(
    trade: Any,
    *,
    variant_id: str,
    indicators_by_time: dict[str, dict[str, Any]],
    max_equity_before: Decimal,
) -> dict[str, Any]:
    equity_after = Decimal(str(trade.equity_after_exit or trade.equity_before_entry or "0"))
    peak = max(max_equity_before, equity_after)
    entry_reason = trade.entry_reason or "baseline_entry_allowed"
    exit_reason = trade.exit_reason or "exit_without_reason"
    return {
        "trade_id": trade.trade_id,
        "strategy_family": scalar(trade.strategy_family),
        "component_key": trade.component_key,
        "component": trade.component_key,
        "timeframe": scalar(trade.timeframe),
        "symbol": trade.symbol,
        "side": scalar(trade.side),
        "entry_time": iso_value(trade.entry_time),
        "exit_time": iso_value(trade.exit_time),
        "entry_signal_time": iso_value(trade.entry_signal_time),
        "exit_signal_time": iso_value(trade.exit_signal_time),
        "entry_fill_time": iso_value(trade.entry_time),
        "exit_fill_time": iso_value(trade.exit_time),
        "raw_entry_price": scalar(trade.raw_entry_price),
        "raw_exit_price": scalar(trade.raw_exit_price),
        "entry_price": scalar(trade.entry_price),
        "exit_price": scalar(trade.exit_price),
        "size": scalar(trade.size),
        "entry_notional": scalar(trade.entry_notional),
        "notional_used": scalar(trade.entry_notional),
        "exit_notional": scalar(trade.exit_notional),
        "fees": scalar(trade.fees),
        "slippage_cost": scalar(trade.slippage_cost),
        "gross_pnl": scalar(trade.gross_pnl),
        "net_pnl": scalar(trade.net_pnl),
        "return_pct": scalar(trade.return_pct),
        "max_adverse_excursion": scalar(trade.max_adverse_excursion),
        "max_favorable_excursion": scalar(trade.max_favorable_excursion),
        "entry_reason": entry_reason,
        "exit_reason": exit_reason,
        "entry_reason_codes": [entry_reason],
        "exit_reason_codes": [exit_reason],
        "entry_indicators": trade_indicator_snapshot(trade, indicators_by_time, "entry"),
        "exit_indicators": trade_indicator_snapshot(trade, indicators_by_time, "exit"),
        "entry_evaluation_key": trade.entry_evaluation_key,
        "exit_evaluation_key": trade.exit_evaluation_key,
        "duration_seconds": trade.duration_seconds,
        "fill_timing": scalar(trade.fill_timing),
        "fill_assumption": scalar(trade.fill_timing),
        "entry_fill_source": trade.entry_fill_source,
        "exit_fill_source": trade.exit_fill_source,
        "forced_exit": trade.forced_exit,
        "entry_market_regime": trade.entry_market_regime,
        "entry_volatility_regime": trade.entry_volatility_regime,
        "exit_market_regime": trade.exit_market_regime,
        "exit_volatility_regime": trade.exit_volatility_regime,
        "market_regime": trade.entry_market_regime,
        "equity_before_entry": scalar(trade.equity_before_entry),
        "equity_after_exit": scalar(trade.equity_after_exit),
        "equity_before_trade": scalar(trade.equity_before_entry),
        "equity_after_trade": scalar(trade.equity_after_exit),
        "drawdown_after_trade": str((peak - equity_after).quantize(Decimal("0.00000001"))),
        "capital_sizing_mode": scalar(trade.capital_sizing_mode),
        "position_notional_pct": scalar(trade.position_notional_pct),
        "source": "historical_replay",
        "strategy_id": variant_id,
        "labels": {
            "historical_paper_replay": True,
            "not_live": True,
            "not_testnet_order": True,
            "not_real_capital": True,
            "research_variant": variant_id,
            "sor_ev3_variant": True,
        },
    }


def normalize_strategy_validation_trades(
    trades: list[Any],
    *,
    variant_id: str,
    indicator_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    indicators_by_time = indicator_lookup(indicator_rows)
    max_equity = Decimal("10000")
    normalized: list[dict[str, Any]] = []
    for trade in trades:
        row = normalize_strategy_validation_trade(
            trade,
            variant_id=variant_id,
            indicators_by_time=indicators_by_time,
            max_equity_before=max_equity,
        )
        try:
            max_equity = max(max_equity, Decimal(str(row["equity_after_trade"])))
        except (InvalidOperation, ValueError, TypeError):
            pass
        normalized.append(row)
    return normalized


def variant_summary(metrics: Any, trades: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "starting_equity": scalar(metrics.starting_equity),
        "ending_equity": scalar(metrics.ending_equity),
        "net_pnl": scalar(metrics.net_account_pnl),
        "realized_pnl": scalar(metrics.net_account_pnl),
        "unrealized_pnl": "0",
        "max_equity": scalar(metrics.maximum_realized_equity),
        "min_equity": scalar(metrics.minimum_realized_equity),
        "max_drawdown": scalar(metrics.mark_to_market_max_drawdown or metrics.max_drawdown),
        "max_drawdown_pct": scalar(metrics.mark_to_market_max_drawdown_pct or metrics.max_drawdown_pct),
        "trade_count": metrics.number_of_trades,
        "win_rate": scalar(metrics.win_rate),
        "profit_factor": scalar(metrics.profit_factor),
        "best_trade": scalar(metrics.best_trade_net_pnl),
        "worst_trade": scalar(metrics.worst_trade_net_pnl),
        "total_fees": scalar(metrics.total_fees),
        "total_slippage_cost": scalar(metrics.total_slippage_cost),
        "open_position_handling": "force_close_at_dataset_end",
        "forced_close_count": sum(1 for trade in trades if trade.get("forced_exit")),
    }


def variant_equity_curve(trades: list[dict[str, Any]], first_candle_time: str | None) -> list[dict[str, Any]]:
    curve = [
        {
            "time": first_candle_time,
            "equity": "10000",
            "realized_pnl": "0",
            "unrealized_pnl": "0",
            "source": "historical_replay_initial_equity",
        }
    ]
    for trade in trades:
        equity = trade.get("equity_after_trade")
        try:
            realized = str((Decimal(str(equity)) - Decimal("10000")).quantize(Decimal("0.00000001")))
        except (InvalidOperation, TypeError, ValueError):
            realized = "0"
        curve.append(
            {
                "time": trade.get("exit_fill_time"),
                "equity": equity,
                "realized_pnl": realized,
                "unrealized_pnl": "0",
                "trade_id": trade.get("trade_id"),
                "source": "historical_replay_closed_trade_equity",
            }
        )
    return curve


def variant_reason_counts(result: dict[str, Any], trades: list[dict[str, Any]]) -> dict[str, Any]:
    entry_reasons: Counter[str] = Counter()
    exit_reasons: Counter[str] = Counter()
    for trade in trades:
        entry_reasons.update(str(reason) for reason in trade.get("entry_reason_codes", []))
        exit_reasons.update(str(reason) for reason in trade.get("exit_reason_codes", []))
    return {
        "entry_reason_counts": dict(sorted(entry_reasons.items())),
        "exit_reason_counts": dict(sorted(exit_reasons.items())),
        "no_trade_reason_counts": result.get("no_trade_reason_counts") or {},
        "invalid_reason_counts": result.get("invalid_reason_counts") or {},
    }


async def build_sor_ev3_variant_replays(
    *,
    pack_paths: list[str],
    indicator_rows_by_key: dict[tuple[str, str], list[dict[str, Any]]],
    variant_ids: tuple[str, ...] = SOR_EV3_HISTORICAL_REPLAY_VARIANTS,
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    paths = [
        path / "batch_report.json" if (path := Path(raw_path)).is_dir() else path
        for raw_path in pack_paths
    ]
    _assert_canonical_paths(paths)
    scenarios = _load_canonical_scenarios(paths)
    service = MoneyFlowBacktestService()
    output: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for scenario in scenarios:
        request = _request_from_payload(scenario["request"])
        sleeve = service._requested_sleeves(request.component_keys)[0]
        candles = service._load_candles(request=request, timeframe=sleeve.timeframe, end_at=request.end_at)
        snapshots = service._indicator_service._compute_snapshots(candles)
        features = _feature_rows(candles, snapshots)
        key = (scenario["symbol"], scenario["timeframe"])
        indicator_rows = indicator_rows_by_key.get(key, [])
        first_candle_time = indicator_rows[0]["timestamp_utc"] if indicator_rows else None
        for variant_id in variant_ids:
            replay_result = await _run_variant_replay(
                service=service,
                request=request,
                scenario=scenario,
                variant_id=variant_id,
                preloaded_candles=candles,
                preloaded_snapshots=snapshots,
                precomputed_features=features,
                include_replay_payload=True,
            )
            trades = normalize_strategy_validation_trades(
                replay_result["trades"],
                variant_id=variant_id,
                indicator_rows=indicator_rows,
            )
            metrics = replay_result["metrics"]
            output.setdefault(key, []).append(
                {
                    "strategy_id": variant_id,
                    "strategy_label": SOR_EV3_HISTORICAL_REPLAY_LABELS[variant_id],
                    "strategy_description": (
                        "SOR-EV3 true-forward historical replay variant for founder drilldown. "
                        "Blocks baseline long entries when the rolling high-low range condition is met; "
                        "evidence-only and not a production Money Flow rule."
                    ),
                    "strategy_truth_lane": "hyperliquid_public_mainnet_canonical_db_imported",
                    "research_only": True,
                    "changes_production_rules": False,
                    "production_approved": False,
                    "testnet_prices_used_as_strategy_truth": False,
                    "symbol": scenario["symbol"],
                    "timeframe": scenario["timeframe"],
                    "component": scenario["component_key"],
                    "fill_assumption": scenario["fill_timing"],
                    "data_source": "hyperliquid_public_mainnet_canonical_db_imported",
                    "evidence_pack_path": str(scenario.get("batch_report_path", "")),
                    "candles": [],
                    "indicators": [],
                    "trades": trades,
                    "markers": markers_for_trades(trades),
                    "equity_curve": variant_equity_curve(trades, first_candle_time),
                    "summary": variant_summary(metrics, trades),
                    "reason_counts": variant_reason_counts(replay_result, trades),
                    "variant_metadata": {
                        "phase": "SOR-EV3",
                        "variant_id": variant_id,
                        "methodology": "true_forward_replay",
                        "source": "canonical_sv2_0_2_db_imported_pack_paths",
                        "historical_replay_full_grid": True,
                        "symbols": "BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX",
                        "timeframes": "15m/1h/4h/1d",
                        "fill_assumptions": "next_candle_open,next_candle_close",
                    },
                    "boundary_flags": {
                        "evidence_only": True,
                        "no_orders": True,
                        "no_private_signed_or_order_endpoints": True,
                        "testnet_prices_used_as_strategy_truth": False,
                        "production_rule_change": False,
                    },
                }
            )
    return output


def markers_for_trades(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []
    for trade in trades:
        trade_id = trade.get("trade_id")
        if trade.get("entry_fill_time"):
            markers.append(
                {
                    "time": trade["entry_fill_time"],
                    "trade_id": trade_id,
                    "marker_type": "entry_fill",
                    "color_role": "green",
                    "reason_codes": trade.get("entry_reason_codes", []),
                    "net_pnl": trade.get("net_pnl"),
                }
            )
        if trade.get("exit_fill_time"):
            markers.append(
                {
                    "time": trade["exit_fill_time"],
                    "trade_id": trade_id,
                    "marker_type": "exit_fill",
                    "color_role": "red" if not trade.get("forced_exit") else "yellow",
                    "reason_codes": trade.get("exit_reason_codes", []),
                    "net_pnl": trade.get("net_pnl"),
                }
            )
    return markers


def batch_report_path(pack_path: str) -> Path:
    return Path(pack_path) / "batch_report.json"


def replay_from_run(
    *,
    dataset: dict[str, Any],
    candles: list[dict[str, Any]],
    indicator_rows: list[dict[str, Any]],
    pack_path: str,
    run_report: dict[str, Any],
) -> dict[str, Any]:
    report = run_report["report"]
    component_report = report["component_reports"][0]
    metrics = component_report["metrics"]
    trades = [normalize_trade(row) for row in component_report.get("trades", [])]
    fill_timing = (
        run_report["request"].get("fill_timing")
        or (run_report["request"].get("assumptions") or {}).get("fill_timing")
        or metrics.get("fill_timing")
    )
    return {
        "strategy_id": "money_flow_v1_2_canonical",
        "strategy_label": "SV2.0.2 canonical Money Flow v1.2",
        "strategy_description": "DB-imported canonical SV2.0.2 evidence replay for dashboard inspection.",
        "strategy_truth_lane": "hyperliquid_public_mainnet_canonical_db_imported",
        "research_only": True,
        "changes_production_rules": False,
        "production_approved": False,
        "testnet_prices_used_as_strategy_truth": False,
        "symbol": dataset["symbol"],
        "timeframe": dataset["timeframe"],
        "component": dataset["component"],
        "fill_assumption": fill_timing,
        "data_source": dataset["source"],
        "evidence_pack_path": pack_path,
        "candles": candles,
        "indicators": indicator_rows,
        "trades": trades,
        "markers": markers_for_trades(trades),
        "equity_curve": metrics.get("closed_trade_equity_curve", []),
        "summary": {
            "starting_equity": metrics.get("starting_equity"),
            "ending_equity": metrics.get("ending_equity"),
            "net_pnl": metrics.get("net_pnl"),
            "max_drawdown": metrics.get("mark_to_market_max_drawdown") or metrics.get("max_drawdown"),
            "max_drawdown_pct": metrics.get("mark_to_market_max_drawdown_pct")
            or metrics.get("max_drawdown_pct"),
            "trade_count": metrics.get("number_of_trades"),
            "win_rate": metrics.get("win_rate"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build ignored SV2.0.2 dashboard chart data from existing candles/packs.")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-timestamp", default="20260512T064916Z")
    args = parser.parse_args()

    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    pack_paths = summary["canonical_evidence_status"]["evidence_pack_paths"]
    pack_by_key: dict[tuple[str, str], str] = {}
    for pack_path in pack_paths:
        name = Path(pack_path).parts[-2]
        parts = name.split("_")
        public_index = parts.index("public")
        symbol = parts[public_index + 1].upper()
        timeframe = parts[public_index + 2]
        pack_by_key[(symbol, timeframe)] = pack_path

    output_root = args.output_dir / args.run_timestamp
    output_root.mkdir(parents=True, exist_ok=True)
    selected_output_root = output_root / "selected"
    selected_output_root.mkdir(parents=True, exist_ok=True)

    candle_payloads_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    indicator_rows_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for dataset in summary["datasets"]:
        symbol = dataset["symbol"]
        timeframe = dataset["timeframe"]
        if not dataset.get("canonical_evidence_ready") or symbol == "SHIB":
            continue
        raw_path = args.raw_dir / f"hyperliquid_public_{symbol.lower()}_{timeframe}_sv2_0_2.json"
        if not raw_path.exists():
            raise FileNotFoundError(f"Missing raw candle file: {raw_path}")
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        key = (symbol, timeframe)
        candle_payloads_by_key[key] = {
            "raw_path": raw_path,
            "raw": raw,
            "candles": normalize_candles(raw["candles"]),
        }
        indicator_rows_by_key[key] = indicators(raw["candles"])

    sor_ev3_replays_by_key = asyncio.run(
        build_sor_ev3_variant_replays(
            pack_paths=pack_paths,
            indicator_rows_by_key=indicator_rows_by_key,
        )
    )

    written = 0
    selected_written = 0
    for dataset in summary["datasets"]:
        symbol = dataset["symbol"]
        timeframe = dataset["timeframe"]
        if not dataset.get("canonical_evidence_ready") or symbol == "SHIB":
            continue
        key = (symbol, timeframe)
        cached = candle_payloads_by_key[key]
        raw_path = cached["raw_path"]
        pack_path = pack_by_key[(symbol, timeframe)]
        batch = json.loads(batch_report_path(pack_path).read_text(encoding="utf-8"))
        candles = cached["candles"]
        indicator_rows = indicator_rows_by_key[key]
        replays = [
            replay_from_run(
                dataset=dataset,
                candles=candles,
                indicator_rows=indicator_rows,
                pack_path=pack_path,
                run_report=run_report,
            )
            for run_report in batch["run_reports"]
            if run_report.get("status") == "completed"
        ]
        replays.extend(
            {
                **replay,
                "candles": candles,
                "indicators": indicator_rows,
            }
            for replay in sor_ev3_replays_by_key.get(key, [])
        )
        payload = {
            "report": "sv2_0_2_dashboard_historical_replay_chart_data",
            "generated_from": {
                "summary": args.summary.as_posix(),
                "raw_candles": raw_path.as_posix(),
                "evidence_pack": pack_path,
                "sor_ev3_historical_replay_variants": list(SOR_EV3_HISTORICAL_REPLAY_VARIANTS),
            },
            "symbol": symbol,
            "timeframe": timeframe,
            "dataset": dataset,
            "replays": replays,
        }
        out_path = output_root / f"hyperliquid_public_{symbol.lower()}_{timeframe}_chart.json"
        out_path.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
        written += 1
        for replay in replays:
            selected_payload = {
                **payload,
                "replays": [replay],
                "selected_replay": {
                    "strategy_id": replay.get("strategy_id"),
                    "fill_assumption": replay.get("fill_assumption"),
                },
            }
            selected_path = selected_output_root / (
                f"hyperliquid_public_{symbol.lower()}_{timeframe}_"
                f"{safe_replay_path_segment(replay.get('strategy_id'))}_"
                f"{safe_replay_path_segment(replay.get('fill_assumption'))}_sv202_replay.json"
            )
            selected_path.write_text(
                json.dumps(selected_payload, separators=(",", ":"), sort_keys=True),
                encoding="utf-8",
            )
            selected_written += 1
    print(
        json.dumps(
            {
                "output_dir": output_root.as_posix(),
                "files_written": written,
                "selected_files_written": selected_written,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
