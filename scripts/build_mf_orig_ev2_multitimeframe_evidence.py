from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from services.strategy_validation.mf_orig_ev1 import (
    MF_ORIG_EV2_DISPLAY_LABELS,
    build_mf_orig_ev2_report_sync,
    write_mf_orig_ev2_outputs,
)
from scripts.build_sv202_dashboard_chart_data import (
    indicator_lookup,
    indicators,
    markers_for_trades,
    normalize_candles,
)


DEFAULT_MARKDOWN_OUTPUT = Path("docs/mf_orig_ev2_multitimeframe_evidence_packs.md")
DEFAULT_JSON_OUTPUT = Path("docs/mf_orig_ev2_multitimeframe_evidence_summary.json")
DEFAULT_RAW_DIR = Path("/tmp/money-flow-sv202-candles")
DEFAULT_PACK_ROOT = Path("reports/strategy_validation")
DEFAULT_CHART_ROOT = Path("reports/strategy_validation/mf_orig_ev2_dashboard_chart_data")
DEFAULT_RUN_TIMESTAMP = "20260513T002746Z"


def _dec(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    if value is None or value == "":
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return default


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    return str(value).replace("+00:00", "Z")


def _money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.00000001")).normalize())


def _strategy_label(hypothesis_id: str) -> str:
    display = MF_ORIG_EV2_DISPLAY_LABELS.get(hypothesis_id, hypothesis_id)
    return f"MF-ORIG-EV2 {display}"


def _pack_slug(hypothesis_id: str, symbol: str, timeframe: str) -> str:
    display = MF_ORIG_EV2_DISPLAY_LABELS.get(hypothesis_id, hypothesis_id)
    return f"mf_orig_ev2_{display}_{symbol.lower()}_{timeframe}_canonical_sv202"


def _safe_replay_path_segment(value: Any) -> str:
    return "".join(
        char.lower() if char.isalnum() else "_" for char in str(value)
    ).strip("_")


def _indicator_snapshot(
    indicator_rows_by_time: dict[str, dict[str, Any]],
    timestamp: Any,
) -> dict[str, Any]:
    row = indicator_rows_by_time.get(_iso(timestamp) or "") or {}
    return {
        "time": _iso(timestamp),
        "RSI": row.get("RSI"),
        "EMA5": row.get("EMA5"),
        "EMA10": row.get("EMA10"),
        "SMA20": row.get("SMA20"),
        "MACD": row.get("MACD"),
        "MACD_signal": row.get("MACD_signal"),
        "MACD_histogram": row.get("MACD_histogram"),
    }


def _normalize_mf_orig_trade(
    trade: dict[str, Any],
    *,
    indicator_rows_by_time: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    exit_reason = trade.get("exit_reason") or "exit_without_reason"
    forced_exit = bool(trade.get("forced_exit"))
    return {
        **trade,
        "strategy_id": trade.get("hypothesis_id"),
        "strategy_label": _strategy_label(str(trade.get("hypothesis_id"))),
        "sizing_mode": trade.get("sizing_mode", "source_1pct_risk"),
        "entry_fill_time": _iso(trade.get("entry_time") or trade.get("entry_signal_time")),
        "exit_fill_time": _iso(trade.get("exit_time") or trade.get("exit_signal_time")),
        "entry_time": _iso(trade.get("entry_time")),
        "exit_time": _iso(trade.get("exit_time")),
        "entry_signal_time": _iso(trade.get("entry_signal_time")),
        "exit_signal_time": _iso(trade.get("exit_signal_time")),
        "entry_reason_codes": trade.get("entry_reason_codes") or ["mf_orig_entry"],
        "exit_reason_codes": [exit_reason],
        "forced_exit": forced_exit,
        "stop_exit": exit_reason == "structure_stop_hit",
        "fill_assumption": trade.get("fill_timing"),
        "entry_indicators": _indicator_snapshot(indicator_rows_by_time, trade.get("entry_signal_time")),
        "exit_indicators": _indicator_snapshot(indicator_rows_by_time, trade.get("exit_signal_time")),
        "source": "historical_replay",
        "labels": {
            "historical_paper_replay": True,
            "not_live": True,
            "not_testnet_order": True,
            "not_real_capital": True,
            "mf_orig_ev2": True,
            "evidence_only": True,
        },
    }


def _trade_markers(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    markers = markers_for_trades(trades)
    for trade in trades:
        for event in trade.get("accounting_events", []):
            if event.get("event_type") == "trim_close":
                markers.append(
                    {
                        "time": _iso(event.get("timestamp")),
                        "trade_id": trade.get("trade_id"),
                        "marker_type": "trim",
                        "color_role": "yellow",
                        "reason_codes": ["rsi_macd_profit_warning_trim"],
                        "net_pnl": event.get("net_amount"),
                    }
                )
        if trade.get("stop_exit") and trade.get("exit_fill_time"):
            markers.append(
                {
                    "time": trade.get("exit_fill_time"),
                    "trade_id": trade.get("trade_id"),
                    "marker_type": "stop_exit",
                    "color_role": "orange",
                    "reason_codes": trade.get("exit_reason_codes", []),
                    "net_pnl": trade.get("net_pnl"),
                }
            )
    return sorted([marker for marker in markers if marker.get("time")], key=lambda row: row["time"])


def _equity_curve(trades: list[dict[str, Any]], first_candle_time: str | None) -> list[dict[str, Any]]:
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
        curve.append(
            {
                "time": trade.get("exit_fill_time"),
                "equity": equity,
                "realized_pnl": _money(_dec(equity) - Decimal("10000")),
                "unrealized_pnl": "0",
                "trade_id": trade.get("trade_id"),
                "source": "mf_orig_ev2_event_ledger_closed_trade_equity",
            }
        )
    return curve


def _reason_counts(row: dict[str, Any], trades: list[dict[str, Any]]) -> dict[str, Any]:
    entry_counts: dict[str, int] = defaultdict(int)
    exit_counts: dict[str, int] = defaultdict(int)
    for trade in trades:
        for reason in trade.get("entry_reason_codes", []):
            entry_counts[str(reason)] += 1
        for reason in trade.get("exit_reason_codes", []):
            exit_counts[str(reason)] += 1
    return {
        "entry_reason_counts": dict(sorted(entry_counts.items())),
        "exit_reason_counts": dict(sorted(exit_counts.items())),
        "no_trade_reason_counts": row.get("no_trade_reason_counts") or {},
        "invalid_reason_counts": row.get("invalid_reason_counts") or {},
    }


def _replay_from_row(
    row: dict[str, Any],
    *,
    trades: list[dict[str, Any]],
    candles: list[dict[str, Any]],
    indicator_rows: list[dict[str, Any]],
    evidence_pack_path: str,
) -> dict[str, Any]:
    first_candle_time = candles[0]["timestamp_utc"] if candles else None
    return {
        "strategy_id": row["hypothesis_id"],
        "strategy_label": _strategy_label(row["hypothesis_id"]),
        "strategy_description": (
            "MF-ORIG-EV2 Original Money Flow reconstruction. "
            "Evidence-only, not a production Money Flow rule change."
        ),
        "sizing_mode": row.get("sizing_mode", "source_1pct_risk"),
        "strategy_truth_lane": "hyperliquid_public_mainnet_canonical_db_imported",
        "research_only": True,
        "changes_production_rules": False,
        "production_approved": False,
        "testnet_prices_used_as_strategy_truth": False,
        "symbol": row["symbol"],
        "timeframe": row["timeframe"],
        "component": f"mf_orig_{row['timeframe']}",
        "fill_assumption": row["fill_timing"],
        "data_source": "SV2.0.2 DB-imported Hyperliquid public-mainnet candles",
        "evidence_pack_path": evidence_pack_path,
        "candles": candles,
        "indicators": indicator_rows,
        "trades": trades,
        "markers": _trade_markers(trades),
        "equity_curve": _equity_curve(trades, first_candle_time),
        "summary": {
            "starting_equity": row.get("initial_equity"),
            "ending_equity": row.get("ending_equity"),
            "net_pnl": row.get("net_pnl"),
            "realized_pnl": row.get("net_pnl"),
            "unrealized_pnl": "0",
            "max_drawdown": row.get("max_drawdown"),
            "max_drawdown_pct": row.get("mark_to_market_max_drawdown_pct"),
            "trade_count": row.get("trade_count"),
            "win_rate": row.get("win_rate"),
            "profit_factor": row.get("profit_factor"),
            "largest_loss": row.get("largest_loss"),
            "largest_win": row.get("largest_win"),
            "forced_close_count": row.get("forced_close_count"),
            "stop_exits": row.get("stop_exits"),
            "trim_events": row.get("trim_events"),
            "drawdown_method": row.get("drawdown_method"),
            "sizing_mode": row.get("sizing_mode", "source_1pct_risk"),
        },
        "reason_counts": _reason_counts(row, trades),
        "variant_metadata": {
            "phase": "MF-ORIG-EV2",
            "hypothesis_id": row["hypothesis_id"],
            "display_hypothesis_id": row.get("display_hypothesis_id"),
            "base_hypothesis_id": row.get("base_hypothesis_id"),
            "sizing_mode": row.get("sizing_mode", "source_1pct_risk"),
            "methodology": "true_forward_replay",
            "timeframe_role": row.get("timeframe_role"),
            "source": "canonical_sv2_0_2_db_imported_pack_paths",
        },
        "boundary_flags": {
            "evidence_only": True,
            "no_orders": True,
            "no_private_signed_or_order_endpoints": True,
            "testnet_prices_used_as_strategy_truth": False,
            "production_rule_change": False,
        },
    }


def _write_evidence_packs(
    report: dict[str, Any],
    *,
    pack_root: Path,
    run_timestamp: str,
) -> list[str]:
    rows_by_key = {
        (row["hypothesis_id"], row["symbol"], row["timeframe"], row["fill_timing"]): row
        for row in report["replay_results"]
    }
    trades_by_key: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for trade in report.get("trade_results", []):
        trades_by_key[(trade["hypothesis_id"], trade["symbol"], trade["timeframe"], trade["fill_timing"])].append(trade)

    pack_paths: list[str] = []
    for hypothesis_id in sorted({row["hypothesis_id"] for row in report["replay_results"]}):
        for symbol in sorted({row["symbol"] for row in report["replay_results"]}):
            for timeframe in ["15m", "1h", "4h", "1d"]:
                selected_rows = [
                    rows_by_key[(hypothesis_id, symbol, timeframe, fill)]
                    for fill in ("next_candle_open", "next_candle_close")
                    if (hypothesis_id, symbol, timeframe, fill) in rows_by_key
                ]
                if not selected_rows:
                    continue
                pack_dir = pack_root / _pack_slug(hypothesis_id, symbol, timeframe) / run_timestamp
                pack_dir.mkdir(parents=True, exist_ok=True)
                run_reports = []
                for row in selected_rows:
                    key = (hypothesis_id, symbol, timeframe, row["fill_timing"])
                    run_reports.append(
                        {
                            "status": "completed",
                            "phase": "MF-ORIG-EV2",
                            "hypothesis_id": hypothesis_id,
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "fill_timing": row["fill_timing"],
                            "request": {
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "fill_timing": row["fill_timing"],
                                "initial_equity": "10000",
                                "capital_sizing_mode": "dynamic_equity_pct",
                                "mf_orig_sizing_mode": row.get("sizing_mode", "source_1pct_risk"),
                            },
                            "report": {
                                "metrics": row,
                                "trades": trades_by_key.get(key, []),
                            },
                        }
                    )
                manifest = {
                    "phase": "MF-ORIG-EV2",
                    "generated_at": report["generated_at"],
                    "run_timestamp": run_timestamp,
                    "money_flow_baseline": "money_flow_v1_2",
                    "canonical_baseline_timestamp": "20260512T064916Z",
                    "hypothesis_id": hypothesis_id,
                    "display_hypothesis_id": MF_ORIG_EV2_DISPLAY_LABELS.get(hypothesis_id, hypothesis_id),
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "fill_assumptions": [row["fill_timing"] for row in selected_rows],
                    "sizing_mode": selected_rows[0].get("sizing_mode", "source_1pct_risk"),
                    "methodology": "true_forward_replay",
                    "accounting": "event_ledger_accounting",
                    "drawdown_method": "peak_to_trough",
                    "production_approved": False,
                    "submits_orders": False,
                    "uses_hyperliquid_testnet_prices": False,
                }
                (pack_dir / "manifest.json").write_text(
                    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                (pack_dir / "batch_report.json").write_text(
                    json.dumps(
                        {
                            "phase": "MF-ORIG-EV2",
                            "manifest": manifest,
                            "run_reports": run_reports,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                (pack_dir / "README.md").write_text(
                    "# MF-ORIG-EV2 Evidence Pack\n\n"
                    "Evidence-only Original Money Flow reconstruction. Production Money Flow v1.2 is unchanged. "
                    "No orders were submitted and no private/signed/order endpoints were called.\n",
                    encoding="utf-8",
                )
                pack_paths.append(pack_dir.as_posix())
    return pack_paths


def _write_chart_data(
    report: dict[str, Any],
    *,
    raw_dir: Path,
    chart_root: Path,
    run_timestamp: str,
    pack_paths: list[str],
) -> list[str]:
    pack_by_key: dict[tuple[str, str, str], str] = {}
    for pack_path in pack_paths:
        parts = Path(pack_path).parts[-2].split("_")
        # mf_orig_ev2_<display...>_<symbol>_<timeframe>_canonical_sv202
        symbol = parts[-4].upper()
        timeframe = parts[-3]
        display = "_".join(parts[3:-4])
        hypothesis = next(
            key for key, value in MF_ORIG_EV2_DISPLAY_LABELS.items() if value == display
        )
        pack_by_key[(hypothesis, symbol, timeframe)] = pack_path

    rows_by_dataset: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in report["replay_results"]:
        rows_by_dataset[(row["symbol"], row["timeframe"])].append(row)
    trades_by_key: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for trade in report.get("trade_results", []):
        trades_by_key[(trade["hypothesis_id"], trade["symbol"], trade["timeframe"], trade["fill_timing"])].append(trade)

    output_root = chart_root / run_timestamp
    output_root.mkdir(parents=True, exist_ok=True)
    selected_output_root = output_root / "selected"
    selected_output_root.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for (symbol, timeframe), rows in sorted(rows_by_dataset.items()):
        raw_path = raw_dir / f"hyperliquid_public_{symbol.lower()}_{timeframe}_sv2_0_2.json"
        if not raw_path.exists():
            raise FileNotFoundError(f"Missing raw candle file: {raw_path}")
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        candles = normalize_candles(raw["candles"])
        indicator_rows = indicators(raw["candles"])
        indicator_rows_by_time = indicator_lookup(indicator_rows)
        replays = []
        for row in sorted(rows, key=lambda item: (item["hypothesis_id"], item["fill_timing"])):
            key = (row["hypothesis_id"], symbol, timeframe, row["fill_timing"])
            trades = [
                _normalize_mf_orig_trade(trade, indicator_rows_by_time=indicator_rows_by_time)
                for trade in trades_by_key.get(key, [])
            ]
            evidence_pack_path = pack_by_key.get((row["hypothesis_id"], symbol, timeframe), "")
            replays.append(
                _replay_from_row(
                    row,
                    trades=trades,
                    candles=candles,
                    indicator_rows=indicator_rows,
                    evidence_pack_path=evidence_pack_path,
                )
            )
        payload = {
            "report": "mf_orig_ev2_dashboard_chart_data",
            "phase": "MF-ORIG-EV2",
            "generated_from": {
                "raw_candles": raw_path.as_posix(),
                "summary": DEFAULT_JSON_OUTPUT.as_posix(),
                "source": "canonical_sv2_0_2_db_imported_candle_truth",
            },
            "symbol": symbol,
            "timeframe": timeframe,
            "dataset": {
                "symbol": symbol,
                "timeframe": timeframe,
                "source": "SV2.0.2 DB-imported Hyperliquid public-mainnet candles",
                "canonical_evidence_ready": True,
                "mf_orig_ev2_ready": True,
            },
            "replays": replays,
        }
        out_path = output_root / f"hyperliquid_public_{symbol.lower()}_{timeframe}_mf_orig_ev2_chart.json"
        out_path.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
        written.append(out_path.as_posix())
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
                f"{_safe_replay_path_segment(replay.get('strategy_id'))}_"
                f"{_safe_replay_path_segment(replay.get('fill_assumption'))}_mf_orig_ev2_replay.json"
            )
            selected_path.write_text(
                json.dumps(selected_payload, separators=(",", ":"), sort_keys=True),
                encoding="utf-8",
            )
            written.append(selected_path.as_posix())
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Build MF-ORIG-EV2 evidence packs and dashboard chart data.")
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--pack-root", type=Path, default=DEFAULT_PACK_ROOT)
    parser.add_argument("--chart-root", type=Path, default=DEFAULT_CHART_ROOT)
    parser.add_argument("--run-timestamp", default=DEFAULT_RUN_TIMESTAMP)
    args = parser.parse_args()

    generated_at = datetime.now(UTC).replace(microsecond=0)
    report = build_mf_orig_ev2_report_sync(generated_at=generated_at)
    pack_paths = _write_evidence_packs(report, pack_root=args.pack_root, run_timestamp=args.run_timestamp)
    chart_files = _write_chart_data(
        report,
        raw_dir=args.raw_dir,
        chart_root=args.chart_root,
        run_timestamp=args.run_timestamp,
        pack_paths=pack_paths,
    )
    report["evidence_pack_status"] = {
        "status": "generated",
        "evidence_pack_paths": pack_paths,
        "pack_count": len(pack_paths),
        "generated_packs_are_review_artifacts": True,
        "large_pack_directories_committed": False,
    }
    report["dashboard_integration_status"] = {
        "historical_replay": "implemented",
        "evidence_ui": "implemented",
        "date_filter_warning": "display_filtered_not_canonical_pack_regeneration",
        "chart_data_report": "mf_orig_ev2_dashboard_chart_data",
        "chart_data_files": chart_files,
    }
    write_mf_orig_ev2_outputs(report, args.markdown_output, args.json_output)
    print(
        json.dumps(
            {
                "phase": "MF-ORIG-EV2",
                "evidence_pack_count": len(pack_paths),
                "chart_file_count": len(chart_files),
                "markdown": args.markdown_output.as_posix(),
                "summary": args.json_output.as_posix(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
