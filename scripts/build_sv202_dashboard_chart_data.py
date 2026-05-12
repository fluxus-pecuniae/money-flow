from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any


DEFAULT_SUMMARY = Path("docs/sv2_0_historical_data_refresh_summary.json")
DEFAULT_RAW_DIR = Path("/tmp/money-flow-sv202-candles")
DEFAULT_OUTPUT_DIR = Path("reports/strategy_validation/sv2_0_2_dashboard_chart_data")


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
    fill_timing = run_report["request"].get("fill_timing") or metrics.get("fill_timing")
    return {
        "strategy_id": "money_flow_v1_2_canonical",
        "strategy_label": "SV2.0.2 canonical Money Flow v1.2",
        "strategy_description": "DB-imported canonical SV2.0.2 evidence replay for dashboard inspection.",
        "strategy_truth_lane": "hyperliquid_public_mainnet_canonical_db_imported",
        "research_only": True,
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
    written = 0
    for dataset in summary["datasets"]:
        symbol = dataset["symbol"]
        timeframe = dataset["timeframe"]
        if not dataset.get("canonical_evidence_ready") or symbol == "SHIB":
            continue
        raw_path = args.raw_dir / f"hyperliquid_public_{symbol.lower()}_{timeframe}_sv2_0_2.json"
        if not raw_path.exists():
            raise FileNotFoundError(f"Missing raw candle file: {raw_path}")
        pack_path = pack_by_key[(symbol, timeframe)]
        batch = json.loads(batch_report_path(pack_path).read_text(encoding="utf-8"))
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        candles = normalize_candles(raw["candles"])
        indicator_rows = indicators(raw["candles"])
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
        payload = {
            "report": "sv2_0_2_dashboard_historical_replay_chart_data",
            "generated_from": {
                "summary": args.summary.as_posix(),
                "raw_candles": raw_path.as_posix(),
                "evidence_pack": pack_path,
            },
            "symbol": symbol,
            "timeframe": timeframe,
            "dataset": dataset,
            "replays": replays,
        }
        out_path = output_root / f"hyperliquid_public_{symbol.lower()}_{timeframe}_chart.json"
        out_path.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
        written += 1
    print(json.dumps({"output_dir": output_root.as_posix(), "files_written": written}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
