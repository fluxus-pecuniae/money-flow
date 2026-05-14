from __future__ import annotations

import argparse
import asyncio
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
from typing import Any

from core.domain.enums import StrategyValidationFillTiming, Timeframe
from core.domain.models import Candle
from scripts.build_mf_orig_ev2_multitimeframe_evidence import (
    _normalize_mf_orig_trade,
    _replay_from_row as mf_orig_replay_from_row,
)
from scripts.build_sv202_dashboard_chart_data import (
    indicator_lookup,
    indicators,
    markers_for_trades,
    normalize_candles,
    normalize_strategy_validation_trades,
    replay_from_run,
    safe_replay_path_segment,
    variant_equity_curve,
    variant_reason_counts,
    variant_summary,
)
from services.strategy_validation.mf_orig_ev1 import (
    _build_original_context,
    _coerce_utc as mf_orig_coerce_utc,
    _run_original_hypothesis,
)
from services.strategy_validation.service import MoneyFlowBacktestService
from services.strategy_validation.sor_ev2 import _request_from_payload
from services.strategy_validation.sor_ev3 import _feature_rows, _run_variant_replay


DEFAULT_SUMMARY = Path("docs/sv2_1_broad_hyperliquid_1d_period_evidence_summary.json")
DEFAULT_REPORT = Path("docs/sv2_1_broad_hyperliquid_1d_period_evidence.md")
DEFAULT_CHART_ROOT = Path("reports/strategy_validation/sv2_1_broad_1d_dashboard_chart_data")
DEFAULT_PACK_ROOT = Path("reports/strategy_validation")
DEFAULT_RUN_TIMESTAMP = "20260514T220500Z"

SV21_BASELINE_STRATEGY_ID = "money_flow_v1_2_canonical"
SV21_CANDIDATE_STRATEGY_IDS = (
    "avoid_low_rolling_range_50",
    "avoid_low_rolling_range_20",
    "mf_orig_1d_stage2_breakout_resistance_full_equity",
)
SV21_PERIODS = ("2024", "2025", "YTD", "ALL")
SV21_PACK_RE = re.compile(
    r"money_flow_sv2_1_hyperliquid_broad_1d_(?P<period>2024|2025|ytd|all)_(?P<symbol>.+?)_canonical_db_imported$"
)


def _dec(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    if value is None or value == "":
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return default


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {str(key): _json_ready(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    enum_value = getattr(value, "value", None)
    if enum_value is not None:
        return enum_value
    return value


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _period_and_symbol(pack_path: str) -> tuple[str, str]:
    campaign_name = Path(pack_path).parent.name if Path(pack_path).name.startswith("20") else Path(pack_path).name
    match = SV21_PACK_RE.match(campaign_name)
    if not match:
        raise ValueError(f"unsupported_sv21_pack_path: {pack_path}")
    return match.group("period").upper(), match.group("symbol").upper()


def _candle_from_raw(row: dict[str, Any]) -> Candle:
    return Candle(
        instrument_key=row.get("instrument_key"),
        instrument_ref_id=None,
        venue="hyperliquid",
        symbol=str(row["symbol"]),
        timeframe=Timeframe("1d"),
        open_time=_parse_utc(str(row["open_time"])),
        close_time=_parse_utc(str(row["close_time"])),
        open=Decimal(str(row["open"])),
        high=Decimal(str(row["high"])),
        low=Decimal(str(row["low"])),
        close=Decimal(str(row["close"])),
        volume=Decimal(str(row.get("volume", "0"))),
        trade_count=int(row["trade_count"]) if row.get("trade_count") is not None else None,
    )


def _scenario_from_run(pack_path: str, run: dict[str, Any]) -> dict[str, Any]:
    report = run["report"]
    component = (report.get("component_reports") or [{}])[0]
    metrics = component.get("metrics") or report.get("aggregate_metrics") or {}
    request = run.get("request") or {}
    symbol = str(report.get("symbol") or request.get("symbol"))
    timeframe = str(component.get("timeframe") or report.get("timeframe") or "1d").lower()
    fill_timing = str((request.get("assumptions") or {}).get("fill_timing") or run.get("fill_timing"))
    return {
        "scenario_key": f"{symbol}:{timeframe}:{fill_timing}:{run.get('run_id')}",
        "batch_report_path": str(Path(pack_path) / "batch_report.json"),
        "run_id": str(run.get("run_id")),
        "symbol": symbol,
        "timeframe": timeframe,
        "component_key": str(component.get("component_key") or "sleeve_1d"),
        "fill_timing": fill_timing,
        "request": request,
        "metrics": metrics,
        "canonical_trade_count": len(component.get("trades", [])),
        "canonical_trades": component.get("trades", []),
    }


def _candidate_pack_slug(strategy_id: str, period: str, symbol: str) -> str:
    return (
        "money_flow_sv2_1_hyperliquid_broad_1d_"
        f"{safe_replay_path_segment(strategy_id)}_{period.lower()}_{symbol.lower()}_"
        "evidence_only"
    )


def _selected_chart_path(root: Path, period: str, symbol: str, strategy_id: str, fill: str) -> Path:
    return root / "selected" / (
        f"hyperliquid_public_{safe_replay_path_segment(symbol)}_1d_{period.lower()}_"
        f"{safe_replay_path_segment(strategy_id)}_{safe_replay_path_segment(fill)}_sv21_replay.json"
    )


def _candidate_pack_manifest(
    *,
    strategy_id: str,
    period: str,
    symbol: str,
    run_timestamp: str,
    run_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "phase": "SV2.1",
        "artifact": "broad_1d_candidate_evidence_pack",
        "run_timestamp": run_timestamp,
        "strategy_id": strategy_id,
        "period": period,
        "symbol": symbol,
        "timeframe": "1d",
        "fill_assumptions": [row["fill_timing"] for row in run_reports],
        "methodology": "true_forward_replay",
        "baseline": "money_flow_v1_2_canonical",
        "evidence_only": True,
        "production_approved": False,
        "submits_orders": False,
        "uses_private_signed_or_order_endpoints": False,
        "uses_testnet_prices_as_strategy_truth": False,
    }


def _write_candidate_pack(
    *,
    pack_root: Path,
    run_timestamp: str,
    strategy_id: str,
    period: str,
    symbol: str,
    run_reports: list[dict[str, Any]],
) -> str:
    pack_dir = pack_root / _candidate_pack_slug(strategy_id, period, symbol) / run_timestamp
    pack_dir.mkdir(parents=True, exist_ok=True)
    manifest = _candidate_pack_manifest(
        strategy_id=strategy_id,
        period=period,
        symbol=symbol,
        run_timestamp=run_timestamp,
        run_reports=run_reports,
    )
    payload = {
        "phase": "SV2.1",
        "manifest": manifest,
        "assumptions_matrix": {
            "symbols": [symbol],
            "components": ["sleeve_1d"],
            "fill_timings": [row["fill_timing"] for row in run_reports],
            "strategy_ids": [strategy_id],
            "periods": [period],
            "initial_capital_values": ["10000"],
            "capital_sizing_modes": ["dynamic_equity_pct"],
        },
        "run_reports": run_reports,
        "boundary_flags": {
            "evidence_only": True,
            "production_approved": False,
            "orders_submitted": False,
            "private_signed_or_order_endpoints_called": False,
            "testnet_prices_used_as_strategy_truth": False,
        },
    }
    (pack_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (pack_dir / "batch_report.json").write_text(json.dumps(_json_ready(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (pack_dir / "README.md").write_text(
        "# SV2.1 Broad 1D Candidate Evidence Pack\n\n"
        "Evidence-only research replay. Production Money Flow rules are unchanged. "
        "No orders were submitted and no private/signed/order endpoints were called.\n",
        encoding="utf-8",
    )
    return pack_dir.as_posix()


def _candidate_run_report(
    *,
    strategy_id: str,
    period: str,
    symbol: str,
    fill_timing: str,
    scenario: dict[str, Any],
    replay: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": "completed",
        "phase": "SV2.1",
        "strategy_id": strategy_id,
        "period": period,
        "symbol": symbol,
        "timeframe": "1d",
        "fill_timing": fill_timing,
        "run_id": f"sv21-{safe_replay_path_segment(strategy_id)}-{period.lower()}-{symbol.lower()}-{safe_replay_path_segment(fill_timing)}",
        "request": scenario["request"],
        "report": {
            "strategy_id": strategy_id,
            "period": period,
            "symbol": symbol,
            "timeframe": "1d",
            "aggregate_metrics": replay.get("summary", {}),
            "component_reports": [
                {
                    "component_key": "sleeve_1d",
                    "timeframe": "1d",
                    "metrics": replay.get("summary", {}),
                    "trades": replay.get("trades", []),
                }
            ],
            "trades": replay.get("trades", []),
            "reason_counts": replay.get("reason_counts", {}),
            "boundary_flags": replay.get("boundary_flags", {}),
        },
    }


async def _sor_ev3_replay(
    *,
    service: MoneyFlowBacktestService,
    scenario: dict[str, Any],
    strategy_id: str,
    candles: list[Candle],
    snapshots: list[Any],
    feature_rows: list[dict[str, Any]],
    indicator_rows: list[dict[str, Any]],
    first_candle_time: str | None,
) -> dict[str, Any]:
    request = _request_from_payload(scenario["request"])
    result = await _run_variant_replay(
        service=service,
        request=request,
        scenario=scenario,
        variant_id=strategy_id,
        preloaded_candles=candles,
        preloaded_snapshots=snapshots,
        precomputed_features=feature_rows,
        include_replay_payload=True,
    )
    trades = normalize_strategy_validation_trades(
        result["trades"],
        variant_id=strategy_id,
        indicator_rows=indicator_rows,
    )
    return {
        "strategy_id": strategy_id,
        "strategy_label": f"SOR-EV3 {strategy_id}",
        "strategy_description": "SV2.1 broad 1D true-forward rolling-range filter replay. Evidence-only and not approved.",
        "strategy_truth_lane": "hyperliquid_public_mainnet_sv2_1_broad_1d",
        "research_only": True,
        "changes_production_rules": False,
        "production_approved": False,
        "testnet_prices_used_as_strategy_truth": False,
        "symbol": scenario["symbol"],
        "timeframe": "1d",
        "component": "sleeve_1d",
        "period": scenario["period"],
        "fill_assumption": scenario["fill_timing"],
        "data_source": "SV2.1 Hyperliquid public-mainnet broad 1D candles",
        "evidence_pack_path": "",
        "candles": [],
        "indicators": [],
        "trades": trades,
        "markers": markers_for_trades(trades),
        "equity_curve": variant_equity_curve(trades, first_candle_time),
        "summary": variant_summary(result["metrics"], trades),
        "reason_counts": variant_reason_counts(result, trades),
        "variant_metadata": {
            "phase": "SV2.1",
            "source_phase": "SOR-EV3",
            "variant_id": strategy_id,
            "methodology": "true_forward_replay",
            "evidence_only": True,
        },
        "boundary_flags": {
            "evidence_only": True,
            "no_orders": True,
            "no_private_signed_or_order_endpoints": True,
            "testnet_prices_used_as_strategy_truth": False,
            "production_rule_change": False,
        },
    }


def _mf_orig_replay(
    *,
    scenario: dict[str, Any],
    candles: list[Candle],
    context: list[dict[str, Any]],
    indicator_rows_by_time: dict[str, dict[str, Any]],
    chart_candles: list[dict[str, Any]],
    indicator_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    request = _request_from_payload(scenario["request"])
    result = _run_original_hypothesis(
        scenario=scenario,
        hypothesis_id="mf_orig_1d_stage2_breakout_resistance_full_equity",
        base_hypothesis_id="mf_orig_1d_stage2_breakout_resistance",
        sizing_mode="full_equity_notional",
        candles=candles,
        context=context,
        start_at=mf_orig_coerce_utc(request.start_at),
        end_at=mf_orig_coerce_utc(request.end_at),
        fill_timing=StrategyValidationFillTiming(scenario["fill_timing"]),
        fee_bps=request.assumptions.fee_bps,
        slippage_bps=request.assumptions.slippage_bps,
        initial_equity=request.assumptions.initial_capital,
        baseline_metrics=scenario["metrics"],
    )
    row = result["row"]
    row["timeframe"] = "1d"
    trades = [
        _normalize_mf_orig_trade(trade, indicator_rows_by_time=indicator_rows_by_time)
        for trade in result["trades"]
    ]
    replay = mf_orig_replay_from_row(
        row,
        trades=trades,
        candles=chart_candles,
        indicator_rows=indicator_rows,
        evidence_pack_path="",
    )
    replay.update(
        {
            "period": scenario["period"],
            "strategy_truth_lane": "hyperliquid_public_mainnet_sv2_1_broad_1d",
            "data_source": "SV2.1 Hyperliquid public-mainnet broad 1D candles",
        }
    )
    replay["boundary_flags"] = {
        "evidence_only": True,
        "no_orders": True,
        "no_private_signed_or_order_endpoints": True,
        "testnet_prices_used_as_strategy_truth": False,
        "production_rule_change": False,
    }
    return replay


async def build_sv21_broad_historical_replay(args: argparse.Namespace) -> dict[str, Any]:
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    dataset_by_symbol = {row["symbol"]: row for row in summary.get("datasets", [])}
    output_root = args.chart_root / args.run_timestamp
    selected_root = output_root / "selected"
    selected_root.mkdir(parents=True, exist_ok=True)

    service = MoneyFlowBacktestService()
    raw_cache: dict[str, dict[str, Any]] = {}
    candidate_runs: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    selected_paths: list[str] = []
    mf_orig_skipped: dict[str, str] = {}

    pack_paths = list(summary.get("evidence_pack_paths", []))
    if args.max_packs:
        pack_paths = pack_paths[: args.max_packs]

    for index, pack_path in enumerate(pack_paths, start=1):
        period, symbol = _period_and_symbol(pack_path)
        dataset = dataset_by_symbol.get(symbol)
        if not dataset or not dataset.get("raw_path"):
            continue
        if symbol not in raw_cache:
            raw = json.loads(Path(dataset["raw_path"]).read_text(encoding="utf-8"))
            raw_candles = raw["candles"]
            domain_candles = [_candle_from_raw(row) for row in raw_candles]
            chart_candles = normalize_candles(raw_candles)
            indicator_rows = indicators(raw_candles)
            snapshots = service._indicator_service._compute_snapshots(domain_candles)
            mf_orig_context = None
            mf_orig_context_error = None
            try:
                mf_orig_context = _build_original_context(domain_candles, snapshots)
            except Exception as exc:  # noqa: BLE001 - evidence builder records per-symbol data gaps.
                mf_orig_context_error = f"{type(exc).__name__}: {exc}"
                mf_orig_skipped[symbol] = mf_orig_context_error
            raw_cache[symbol] = {
                "raw": raw,
                "domain_candles": domain_candles,
                "chart_candles": chart_candles,
                "indicator_rows": indicator_rows,
                "indicator_rows_by_time": indicator_lookup(indicator_rows),
                "snapshots": snapshots,
                "features": _feature_rows(domain_candles, snapshots),
                "mf_orig_context": mf_orig_context,
                "mf_orig_context_error": mf_orig_context_error,
            }
        cached = raw_cache[symbol]
        batch = json.loads((Path(pack_path) / "batch_report.json").read_text(encoding="utf-8"))
        for run in batch.get("run_reports", []):
            if run.get("status") != "completed" or not run.get("report"):
                continue
            scenario = _scenario_from_run(pack_path, run)
            scenario["period"] = period
            baseline = replay_from_run(
                dataset={
                    "symbol": symbol,
                    "timeframe": "1d",
                    "component": "sleeve_1d",
                    "source": "SV2.1 Hyperliquid public-mainnet broad 1D evidence pack",
                },
                candles=cached["chart_candles"],
                indicator_rows=cached["indicator_rows"],
                pack_path=pack_path,
                run_report=run,
            )
            baseline.update(
                {
                    "strategy_id": SV21_BASELINE_STRATEGY_ID,
                    "strategy_label": "Money Flow v1.2",
                    "period": period,
                    "strategy_truth_lane": "hyperliquid_public_mainnet_sv2_1_broad_1d",
                    "data_source": "SV2.1 Hyperliquid public-mainnet broad 1D evidence pack",
                    "production_approved": False,
                }
            )
            replays = [baseline]
            for strategy_id in ("avoid_low_rolling_range_50", "avoid_low_rolling_range_20"):
                replays.append(
                    await _sor_ev3_replay(
                        service=service,
                        scenario=scenario,
                        strategy_id=strategy_id,
                        candles=cached["domain_candles"],
                        snapshots=cached["snapshots"],
                        feature_rows=cached["features"],
                        indicator_rows=cached["indicator_rows"],
                        first_candle_time=cached["chart_candles"][0]["timestamp_utc"] if cached["chart_candles"] else None,
                    )
                )
            if cached["mf_orig_context"] is not None:
                replays.append(
                    _mf_orig_replay(
                        scenario=scenario,
                        candles=cached["domain_candles"],
                        context=cached["mf_orig_context"],
                        indicator_rows_by_time=cached["indicator_rows_by_time"],
                        chart_candles=cached["chart_candles"],
                        indicator_rows=cached["indicator_rows"],
                    )
                )
            else:
                scenario.setdefault("reason_codes", []).append("mf_orig_candidate_skipped_missing_indicator_context")

            for replay in replays:
                replay["candles"] = cached["chart_candles"]
                replay["indicators"] = cached["indicator_rows"]
                selected_payload = {
                    "report": "sv2_1_broad_1d_dashboard_chart_data",
                    "phase": "SV2.1",
                    "generated_from": {
                        "summary": args.summary.as_posix(),
                        "raw_candles": str(dataset["raw_path"]),
                        "evidence_pack": pack_path,
                    },
                    "symbol": symbol,
                    "timeframe": "1d",
                    "period": period,
                    "dataset": {
                        "symbol": symbol,
                        "timeframe": "1d",
                        "period": period,
                        "source": "SV2.1 Hyperliquid public-mainnet broad 1D candles",
                        "canonical_evidence_ready": True,
                        "sv21_broad_replay_ready": True,
                    },
                    "selected_replay": {
                        "strategy_id": replay.get("strategy_id"),
                        "fill_assumption": replay.get("fill_assumption"),
                        "period": period,
                    },
                    "replays": [replay],
                }
                selected_path = _selected_chart_path(
                    output_root,
                    period,
                    symbol,
                    replay.get("strategy_id", "unknown"),
                    replay.get("fill_assumption", "unknown"),
                )
                selected_path.write_text(
                    json.dumps(_json_ready(selected_payload), separators=(",", ":"), sort_keys=True),
                    encoding="utf-8",
                )
                selected_paths.append(selected_path.as_posix())
                strategy_id = replay.get("strategy_id")
                if strategy_id in SV21_CANDIDATE_STRATEGY_IDS:
                    candidate_runs[(strategy_id, period, symbol)].append(
                        _candidate_run_report(
                            strategy_id=strategy_id,
                            period=period,
                            symbol=symbol,
                            fill_timing=replay.get("fill_assumption", "unknown"),
                            scenario=scenario,
                            replay=replay,
                        )
                    )
        if args.progress_every and index % args.progress_every == 0:
            print(json.dumps({"processed_packs": index, "selected_chart_files": len(selected_paths)}, sort_keys=True))

    candidate_pack_paths: list[str] = []
    for (strategy_id, period, symbol), run_reports in sorted(candidate_runs.items()):
        candidate_pack_paths.append(
            _write_candidate_pack(
                pack_root=args.pack_root,
                run_timestamp=args.run_timestamp,
                strategy_id=strategy_id,
                period=period,
                symbol=symbol,
                run_reports=run_reports,
            )
        )

    parsed_pack_symbols = {
        _period_and_symbol(path)[1]
        for path in summary.get("evidence_pack_paths", [])
        if "money_flow_sv2_1_hyperliquid_broad_1d_" in path
    }
    manifest = {
        "phase": "SV2.1",
        "report": "sv2_1_broad_1d_historical_replay_chart_data",
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "run_timestamp": args.run_timestamp,
        "baseline_strategy_id": SV21_BASELINE_STRATEGY_ID,
        "candidate_strategy_ids": list(SV21_CANDIDATE_STRATEGY_IDS),
        "periods": list(SV21_PERIODS),
        "symbol_count": len(parsed_pack_symbols),
        "baseline_evidence_pack_count": len(summary.get("evidence_pack_paths", [])),
        "candidate_evidence_pack_count": len(candidate_pack_paths),
        "selected_chart_data_count": len(selected_paths),
        "chart_data_root": output_root.as_posix(),
        "candidate_evidence_pack_paths": candidate_pack_paths,
        "selected_chart_data_paths": selected_paths,
        "mf_orig_candidate_skipped_symbols": mf_orig_skipped,
        "boundary_flags": {
            "evidence_only": True,
            "orders_submitted": False,
            "private_signed_or_order_endpoints_called": False,
            "testnet_prices_used_as_strategy_truth": False,
            "production_rules_changed": False,
            "paper_or_live_approved": False,
        },
    }
    (output_root / "manifest.json").write_text(json.dumps(_json_ready(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def update_sv21_summary(summary_path: Path, report_path: Path, manifest: dict[str, Any]) -> None:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["historical_replay_status"] = {
        "status": "generated",
        "chart_data_root": manifest["chart_data_root"],
        "selected_chart_data_count": manifest["selected_chart_data_count"],
        "period_filter_required": True,
        "periods": manifest["periods"],
        "baseline_strategy_id": manifest["baseline_strategy_id"],
        "candidate_strategy_ids": manifest["candidate_strategy_ids"],
    }
    summary["candidate_evidence_status"] = {
        "status": "generated",
        "candidate_strategy_ids": manifest["candidate_strategy_ids"],
        "evidence_pack_count": manifest["candidate_evidence_pack_count"],
        "evidence_pack_paths": manifest["candidate_evidence_pack_paths"],
        "evidence_only": True,
        "production_approved": False,
    }
    summary_path.write_text(json.dumps(_json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if report_path.exists():
        report = report_path.read_text(encoding="utf-8")
        marker = "\n## Historical Replay Addendum\n"
        addendum = (
            marker
            + "\n"
            + f"- Chart-data root: `{manifest['chart_data_root']}`\n"
            + f"- Selected chart-data files: `{manifest['selected_chart_data_count']}`\n"
            + f"- Candidate evidence packs: `{manifest['candidate_evidence_pack_count']}`\n"
            + f"- Candidate strategies: `{', '.join(manifest['candidate_strategy_ids'])}`\n"
            + "- Status: evidence-only; no production rule change, no paper/live approval, no orders.\n"
        )
        report = report.split(marker)[0].rstrip() + "\n" + addendum
        report_path.write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build SV2.1 broad 1D Historical Replay chart data and conservative candidate packs.")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--chart-root", type=Path, default=DEFAULT_CHART_ROOT)
    parser.add_argument("--pack-root", type=Path, default=DEFAULT_PACK_ROOT)
    parser.add_argument("--run-timestamp", default=DEFAULT_RUN_TIMESTAMP)
    parser.add_argument("--max-packs", type=int, default=0)
    parser.add_argument("--progress-every", type=int, default=100)
    parser.add_argument("--no-summary-update", action="store_true")
    args = parser.parse_args()
    manifest = asyncio.run(build_sv21_broad_historical_replay(args))
    if not args.no_summary_update:
        update_sv21_summary(args.summary, args.report, manifest)
    print(json.dumps(_json_ready({
        "chart_data_root": manifest["chart_data_root"],
        "candidate_evidence_pack_count": manifest["candidate_evidence_pack_count"],
        "selected_chart_data_count": manifest["selected_chart_data_count"],
    }), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
