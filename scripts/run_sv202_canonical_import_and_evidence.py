#!/usr/bin/env python3
"""Run SV2.0.2 canonical candle import and evidence-pack generation.

This script is Strategy Validation research tooling only. It uses Hyperliquid
mainnet public `info` data, writes normalized candle files to a local work
directory, imports those rows through the hardened candle importer, and then
runs the existing canonical evidence-pack machinery. It never uses API keys,
private/signed/order endpoints, Hyperliquid testnet strategy truth, or live
execution artifacts.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Sequence

from core.config.settings import get_settings
from core.domain.enums import Environment, Timeframe
from services.strategy_validation import (
    MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY,
    MoneyFlowBacktestService,
    import_strategy_validation_candles_from_path,
    inspect_strategy_validation_database_status,
    money_flow_evidence_review_to_dict,
    review_money_flow_evidence,
    seed_strategy_validation_market_identity_from_manifest,
    strategy_validation_candle_import_result_to_dict,
    strategy_validation_market_identity_seed_result_to_dict,
)
from services.strategy_validation.evidence_review import (
    MoneyFlowEvidenceReviewDatabaseStatus,
    MoneyFlowEvidenceReviewSummary,
)
from services.strategy_validation.market_identity import (
    canonical_market_identity_instrument_key,
)
from services.strategy_validation.sv2 import (
    HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
    SV20_COMPONENT_BY_TIMEFRAME,
    SV20_MONEY_FLOW_VERSION,
    SV20_PUBLIC_CANDLE_LIMIT,
    SV20_REQUESTED_SYMBOLS,
    SV20_TARGET_START_AT,
    SV20_TIMEFRAME_SECONDS,
    SV20_TIMEFRAMES,
    SV20CandleDataset,
    SV20MarketIdentity,
    build_sv20_readiness_rows,
    build_sv20_summary,
    canonical_sv20_timeframe,
    display_sv20_timeframe,
    extract_hyperliquid_universe,
    fetch_hyperliquid_public_info,
    hyperliquid_candle_snapshot_payload,
    hyperliquid_meta_payload,
    iso_utc,
    normalize_hyperliquid_candle_snapshot,
    parse_utc,
    resolve_hyperliquid_market_identities,
    target_start_is_covered,
)

DEFAULT_SUMMARY_OUTPUT = Path("docs/sv2_0_historical_data_refresh_summary.json")
DEFAULT_REPORT_OUTPUT = Path("docs/sv2_0_2_canonical_sv2_evidence_packs.md")
DEFAULT_CONFIG_DIR = Path("configs/strategy_validation/campaigns/sv2_0_2")
DEFAULT_WORK_DIR = Path("/tmp/money-flow-sv202-candles")

_WINDOW_CONVENTION = (
    "(start_at, end_at] candle closes; closes exactly at start are excluded "
    "and closes on or before end are included."
)
_SOURCE_LABEL = "hyperliquid_public_mainnet_candleSnapshot"
_NO_ORDER_FLAGS = {
    "submits_orders": False,
    "calls_order_endpoints": False,
    "calls_private_or_signed_endpoints": False,
    "uses_api_keys": False,
    "uses_testnet_prices_as_strategy_truth": False,
    "enables_live_trading": False,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--campaign-config-dir", type=Path, default=DEFAULT_CONFIG_DIR)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    parser.add_argument("--fetch-public-data", action="store_true")
    parser.add_argument("--generate-evidence-packs", action="store_true")
    parser.add_argument("--end-at", default=None)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument(
        "--collision-policy",
        choices=("unique_suffix", "fail_if_exists"),
        default=MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY,
    )
    parser.add_argument(
        "--run-timestamp",
        default=None,
        help="Optional evidence-pack timestamp, e.g. 2026-05-11T23:55:00Z.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    generated_at = datetime.now(UTC).replace(microsecond=0)
    end_at = parse_utc(args.end_at) if args.end_at else generated_at
    run_timestamp = parse_utc(args.run_timestamp) if args.run_timestamp else generated_at
    service = MoneyFlowBacktestService(get_settings())
    db_status = inspect_strategy_validation_database_status(service)
    db_blockers = db_status_blocking_reason_codes(db_status)

    meta: Any = {"universe": []}
    identities: list[SV20MarketIdentity] = []
    datasets: list[SV20CandleDataset] = []
    import_results: list[dict[str, Any]] = []
    market_identity_seed_result: dict[str, Any] | None = None
    campaign_config_paths: list[Path] = []
    evidence_review: MoneyFlowEvidenceReviewSummary | None = None
    evidence_pack_paths: list[str] = []
    open_position_summary = empty_open_position_summary()
    source_reason_codes: list[str] = []

    if not args.fetch_public_data:
        source_reason_codes.append("historical_fetch_not_requested")
    else:
        try:
            meta = fetch_hyperliquid_public_info(
                hyperliquid_meta_payload(),
                url=HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
                timeout_seconds=args.timeout_seconds,
            )
            source_reason_codes.append("hyperliquid_public_mainnet_meta_fetch_succeeded")
        except Exception as exc:  # pragma: no cover - depends on network/API availability.
            source_reason_codes.append(f"hyperliquid_public_mainnet_meta_fetch_failed:{type(exc).__name__}")
            meta = {"universe": []}

    identities = sv202_canonical_evidence_identities(
        resolve_hyperliquid_market_identities(meta)
    )

    if db_blockers:
        datasets = blocked_datasets_for_identities(
            identities,
            import_reason_codes=tuple(db_blockers),
            fetch_reason_codes=tuple(source_reason_codes),
        )
    elif not args.fetch_public_data:
        datasets = blocked_datasets_for_identities(
            identities,
            import_reason_codes=(
                "historical_import_not_attempted",
                "db_import_not_attempted",
                "canonical_hardened_import_not_run",
            ),
            fetch_reason_codes=tuple(source_reason_codes),
        )
    else:
        market_identity_manifest_path = args.work_dir / "sv2_0_2_market_identity_manifest.json"
        market_identity_manifest = build_market_identity_manifest(
            identities=identities,
            meta_payload=meta,
            generated_at=generated_at,
        )
        args.work_dir.mkdir(parents=True, exist_ok=True)
        market_identity_manifest_path.write_text(
            json.dumps(market_identity_manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        seed_result = seed_strategy_validation_market_identity_from_manifest(
            market_identity_manifest_path,
            operator_verified=True,
            verified_by="SV2.0.2 canonical evidence import",
        )
        market_identity_seed_result = strategy_validation_market_identity_seed_result_to_dict(
            seed_result
        )
        if market_identity_seed_result.get("conflicts"):
            datasets = blocked_datasets_for_identities(
                identities,
                import_reason_codes=("market_identity_conflict_blocks_import",),
                fetch_reason_codes=tuple(source_reason_codes),
            )
        else:
            datasets, import_results = fetch_normalize_and_import_datasets(
                identities=identities,
                start_at=parse_utc(SV20_TARGET_START_AT),
                end_at=end_at,
                work_dir=args.work_dir,
                timeout_seconds=args.timeout_seconds,
            )

    if not db_blockers and args.generate_evidence_packs and any(row.db_imported for row in datasets):
        campaign_config_paths = write_sv202_campaign_configs(
            datasets=datasets,
            identities=identities,
            output_dir=args.campaign_config_dir,
        )
        if campaign_config_paths:
            evidence_review = review_money_flow_evidence(
                campaign_config_paths,
                service=service,
                output_dir="reports/strategy_validation",
                generate_evidence_packs=True,
                run_timestamp=run_timestamp,
                generated_at=generated_at,
                evidence_pack_collision_policy=args.collision_policy,
            )
            evidence_review_payload = money_flow_evidence_review_to_dict(evidence_review)
            evidence_pack_paths = list(evidence_review_payload["generated_evidence_pack_paths"])
            open_position_summary = summarize_open_position_handling(evidence_pack_paths)

    generated_timeframes = generated_timeframes_from_review(evidence_review)
    canonical_ready_datasets = mark_canonical_ready_datasets(
        datasets=datasets,
        generated_timeframes=generated_timeframes,
    )
    readiness_rows = build_sv20_readiness_rows(identities, canonical_ready_datasets)
    canonical_evidence_rows = canonical_evidence_rows_from_packs(evidence_pack_paths)
    summary = build_sv20_summary(
        identities=identities,
        readiness_rows=readiness_rows,
        evidence_rows=canonical_evidence_rows,
        evidence_pack_paths=evidence_pack_paths,
        generated_at_utc=iso_utc(generated_at),
    )
    summary["sv2_0_2"] = {
        "status": "canonical_evidence_generated" if evidence_pack_paths else "blocked",
        "db_status": database_status_to_summary(db_status),
        "db_blocking_reason_codes": db_blockers,
        "market_identity_seed_result": market_identity_seed_result,
        "import_results": import_results,
        "campaign_config_paths": [str(path) for path in campaign_config_paths],
        "evidence_review": (
            money_flow_evidence_review_to_dict(evidence_review)
            if evidence_review is not None
            else None
        ),
        "open_position_handling": open_position_summary,
        "sor_ev1_readiness_decision": sor_ev1_readiness_decision(
            db_blockers=db_blockers,
            evidence_pack_paths=evidence_pack_paths,
            readiness_rows=readiness_rows,
        ),
        "boundary_flags": dict(_NO_ORDER_FLAGS),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(summary, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(render_sv202_report(summary), encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"Wrote {args.report_output}")
    if campaign_config_paths:
        print("\n".join(str(path) for path in campaign_config_paths))
    if evidence_pack_paths:
        print("\n".join(evidence_pack_paths))
    return 0 if evidence_pack_paths else 2


def db_status_blocking_reason_codes(
    status: MoneyFlowEvidenceReviewDatabaseStatus,
) -> list[str]:
    reasons: list[str] = []
    if not status.reachable:
        reasons.append("strategy_validation_db_unreachable")
    if not status.intended_strategy_validation_database or not status.database_target_ready_for_evidence_generation:
        reasons.append("strategy_validation_db_target_ambiguous")
    if not status.schema_ready_for_evidence_generation:
        reasons.append("strategy_validation_schema_not_current")
    if status.required_schema_tables_missing:
        reasons.append("strategy_validation_required_table_missing")
    if not status.candles_table_exists:
        reasons.append("strategy_validation_required_table_missing")
    return sorted(set(reasons))


def database_status_to_summary(status: MoneyFlowEvidenceReviewDatabaseStatus) -> dict[str, Any]:
    return {
        "configured_database_url": status.configured_database_url,
        "database_host": status.database_host,
        "database_port": status.database_port,
        "database_name": status.database_name,
        "database_username": status.database_username,
        "intended_strategy_validation_database": status.intended_strategy_validation_database,
        "reachable": status.reachable,
        "schema_ready_for_evidence_generation": status.schema_ready_for_evidence_generation,
        "schema_status": status.schema_status,
        "migrations_current": status.migrations_current,
        "required_schema_tables_present": list(status.required_schema_tables_present),
        "required_schema_tables_missing": list(status.required_schema_tables_missing),
        "persisted_candle_count": status.persisted_candle_count,
        "blocking_error_type": status.blocking_error_type,
        "blocking_error_message": status.blocking_error_message,
    }


def sv202_canonical_evidence_identities(
    identities: Iterable[SV20MarketIdentity],
) -> list[SV20MarketIdentity]:
    """Return identities with SHIB/kSHIB explicitly deferred for canonical packs."""

    adjusted: list[SV20MarketIdentity] = []
    for identity in identities:
        if (
            identity.requested_symbol.upper() == "SHIB"
            and identity.resolved_venue_symbol
            and identity.resolved_venue_symbol.upper() != "SHIB"
        ):
            reasons = sorted(
                {
                    *identity.reason_codes,
                    "venue_symbol_alias_detected",
                    "venue_symbol_unit_semantics_deferred",
                    "canonical_evidence_excluded_symbol_deferred",
                }
            )
            adjusted.append(
                replace(
                    identity,
                    supported=False,
                    strategy_validation_eligible=False,
                    reason_codes=tuple(reasons),
                )
            )
            continue
        adjusted.append(identity)
    return adjusted


def blocked_datasets_for_identities(
    identities: Sequence[SV20MarketIdentity],
    *,
    import_reason_codes: tuple[str, ...],
    fetch_reason_codes: tuple[str, ...] = (),
) -> list[SV20CandleDataset]:
    rows: list[SV20CandleDataset] = []
    for identity in identities:
        for timeframe in SV20_TIMEFRAMES:
            symbol_reasons = tuple(identity.reason_codes)
            rows.append(
                SV20CandleDataset(
                    requested_symbol=identity.requested_symbol,
                    resolved_venue_symbol=identity.resolved_venue_symbol,
                    timeframe=timeframe,
                    fetch_attempted=False,
                    fetched=False,
                    normalized=False,
                    raw_file_written=False,
                    staged_for_replay=False,
                    db_imported=False,
                    canonical_evidence_ready=False,
                    target_window_ready=False,
                    candles=(),
                    fetch_reason_codes=fetch_reason_codes,
                    import_reason_codes=tuple(sorted(set(import_reason_codes + symbol_reasons))),
                )
            )
    return rows


def build_market_identity_manifest(
    *,
    identities: Sequence[SV20MarketIdentity],
    meta_payload: Any,
    generated_at: datetime,
) -> dict[str, Any]:
    universe = extract_hyperliquid_universe(meta_payload)
    by_name = {str(row.get("name") or ""): row for row in universe}
    markets: list[dict[str, Any]] = []
    for identity in identities:
        if not identity.supported or not identity.resolved_venue_symbol:
            continue
        meta_row = by_name.get(identity.resolved_venue_symbol, {})
        sz_decimals = int(identity.sz_decimals or 0)
        quantity_step = Decimal("1").scaleb(-sz_decimals)
        price_tick = Decimal("1").scaleb(-(6 - sz_decimals))
        max_leverage = meta_row.get("maxLeverage")
        instrument_key = canonical_market_identity_instrument_key(identity.requested_symbol)
        markets.append(
            {
                "instrument": {
                    "instrument_key": instrument_key,
                    "canonical_symbol": identity.requested_symbol,
                    "market_type": "perpetual",
                    "product_type": "linear",
                    "base_asset": identity.requested_symbol,
                    "quote_asset": "USDC",
                    "settlement_asset": "USDC",
                    "is_active": True,
                },
                "symbol": {
                    "venue": "hyperliquid",
                    "symbol": identity.requested_symbol,
                    "exchange_symbol": identity.resolved_venue_symbol,
                    "venue_asset_id": str(identity.asset_id),
                    "asset_id": str(identity.asset_id),
                    "market_type": "perpetual",
                    "product_type": "linear",
                    "base_asset": identity.requested_symbol,
                    "quote_asset": "USDC",
                    "settlement_asset": "USDC",
                    "price_tick_size": decimal_text(price_tick),
                    "quantity_step_size": decimal_text(quantity_step),
                    "min_order_size": decimal_text(quantity_step),
                    "size_decimals": sz_decimals,
                    "max_leverage": int(max_leverage) if max_leverage is not None else None,
                    "only_isolated": bool(meta_row.get("onlyIsolated", False)),
                    "is_perpetual": True,
                    "is_builder_deployed": False,
                    "is_strategy_eligible": False,
                    "is_trading_eligible": False,
                    "is_active": True,
                    "raw_metadata": {
                        "research_only_market_identity_seed": True,
                        "source": "hyperliquid_public_info_meta",
                        "sv_phase": "SV2.0.2",
                        "money_flow_version": SV20_MONEY_FLOW_VERSION,
                        "verification_checked_at_utc": iso_utc(generated_at),
                        "verification_endpoint": f"POST {HYPERLIQUID_MAINNET_PUBLIC_INFO_URL}",
                        "verification_request": {"type": "meta"},
                        "venue_asset_id_basis": "Perp asset id is the index of the coin in public meta.",
                        "hyperliquid_meta": meta_row,
                        "price_tick_size_basis": "Derived as 10^-(6 - szDecimals).",
                        "quantity_step_size_basis": "Derived as 10^-szDecimals.",
                        "operator_note": (
                            "Research-only identity for canonical Strategy Validation candle "
                            "import; strategy/trading eligibility remains false."
                        ),
                    },
                },
            }
        )
    return {
        "manifest_name": "sv2_0_2_hyperliquid_public_mainnet_expanded_universe",
        "description": (
            "Research-only public Hyperliquid perpetual USDC market identity manifest "
            "for SV2.0.2 DB-backed canonical evidence generation."
        ),
        "research_only": True,
        "operator_verified": True,
        "verified_by": "SV2.0.2 canonical evidence import",
        "source": "hyperliquid_public_info_meta",
        "sv_phase": "SV2.0.2",
        "venue": "hyperliquid",
        "markets": markets,
    }


def fetch_normalize_and_import_datasets(
    *,
    identities: Sequence[SV20MarketIdentity],
    start_at: datetime,
    end_at: datetime,
    work_dir: Path,
    timeout_seconds: float,
) -> tuple[list[SV20CandleDataset], list[dict[str, Any]]]:
    work_dir.mkdir(parents=True, exist_ok=True)
    datasets: list[SV20CandleDataset] = []
    import_results: list[dict[str, Any]] = []
    for identity in identities:
        for timeframe in SV20_TIMEFRAMES:
            if not identity.supported or not identity.resolved_venue_symbol:
                datasets.append(
                    SV20CandleDataset(
                        requested_symbol=identity.requested_symbol,
                        resolved_venue_symbol=identity.resolved_venue_symbol,
                        timeframe=timeframe,
                        fetch_attempted=False,
                        fetched=False,
                        normalized=False,
                        raw_file_written=False,
                        staged_for_replay=False,
                        db_imported=False,
                        canonical_evidence_ready=False,
                        target_window_ready=False,
                        candles=(),
                        fetch_reason_codes=("symbol_unsupported_fetch_skipped",),
                        import_reason_codes=(
                            "historical_import_blocked_symbol_unsupported",
                            *identity.reason_codes,
                        ),
                    )
                )
                continue
            try:
                raw = fetch_hyperliquid_public_info(
                    hyperliquid_candle_snapshot_payload(
                        coin=identity.resolved_venue_symbol,
                        timeframe=timeframe,
                        start_at=start_at,
                        end_at=end_at,
                    ),
                    url=HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
                    timeout_seconds=timeout_seconds,
                )
                candles = normalize_hyperliquid_candle_snapshot(
                    raw,
                    requested_symbol=identity.requested_symbol,
                    resolved_venue_symbol=identity.resolved_venue_symbol,
                    timeframe=timeframe,
                )
                import_path = write_import_candle_file(
                    work_dir=work_dir,
                    identity=identity,
                    timeframe=timeframe,
                    candles=candles,
                )
                result = import_strategy_validation_candles_from_path(
                    import_path,
                    environment=Environment.BACKTEST,
                    venue="hyperliquid",
                    timeframe=Timeframe(canonical_sv20_timeframe(timeframe)),
                    source_label=_SOURCE_LABEL,
                    file_format="json",
                    assume_naive_utc=False,
                )
                result_payload = strategy_validation_candle_import_result_to_dict(result)
                result_payload.update(
                    {
                        "requested_symbol": identity.requested_symbol,
                        "resolved_venue_symbol": identity.resolved_venue_symbol,
                        "timeframe": canonical_sv20_timeframe(timeframe),
                    }
                )
                import_results.append(result_payload)
                import_reasons = [
                    "historical_import_succeeded",
                    "canonical_hardened_import_succeeded",
                    "db_imported_true",
                ]
                if any(row.get("trade_count") is None for row in candles):
                    import_reasons.append(
                        "trade_count_unavailable_from_hyperliquid_public_candles_canonical_optional"
                    )
                target_window_ready = bool(candles) and target_start_is_covered(
                    candles[0]["close_time"],
                    timeframe,
                )
                datasets.append(
                    SV20CandleDataset(
                        requested_symbol=identity.requested_symbol,
                        resolved_venue_symbol=identity.resolved_venue_symbol,
                        timeframe=timeframe,
                        fetch_attempted=True,
                        fetched=True,
                        normalized=True,
                        raw_file_written=True,
                        staged_for_replay=True,
                        db_imported=True,
                        canonical_evidence_ready=False,
                        target_window_ready=target_window_ready,
                        candles=candles,
                        fetch_reason_codes=("hyperliquid_public_mainnet_fetch_succeeded",),
                        import_reason_codes=tuple(import_reasons),
                    )
                )
            except Exception as exc:  # noqa: BLE001 - row-specific blocker is useful.
                datasets.append(
                    SV20CandleDataset(
                        requested_symbol=identity.requested_symbol,
                        resolved_venue_symbol=identity.resolved_venue_symbol,
                        timeframe=timeframe,
                        fetch_attempted=True,
                        fetched=False,
                        normalized=False,
                        raw_file_written=False,
                        staged_for_replay=False,
                        db_imported=False,
                        canonical_evidence_ready=False,
                        target_window_ready=False,
                        candles=(),
                        fetch_reason_codes=(f"historical_fetch_or_import_failed:{type(exc).__name__}",),
                        import_reason_codes=(f"historical_import_blocked:{type(exc).__name__}",),
                    )
                )
    return datasets, import_results


def write_import_candle_file(
    *,
    work_dir: Path,
    identity: SV20MarketIdentity,
    timeframe: str,
    candles: Sequence[dict[str, Any]],
) -> Path:
    instrument_key = canonical_market_identity_instrument_key(identity.requested_symbol)
    rows = []
    for candle in candles:
        row = dict(candle)
        row["instrument_key"] = instrument_key
        rows.append(row)
    path = work_dir / (
        f"hyperliquid_public_{identity.requested_symbol.lower()}_"
        f"{canonical_sv20_timeframe(timeframe)}_sv2_0_2.json"
    )
    path.write_text(
        json.dumps(
            {
                "source": _SOURCE_LABEL,
                "requested_symbol": identity.requested_symbol,
                "resolved_venue_symbol": identity.resolved_venue_symbol,
                "timeframe": canonical_sv20_timeframe(timeframe),
                "candles": rows,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def write_sv202_campaign_configs(
    *,
    datasets: Sequence[SV20CandleDataset],
    identities: Sequence[SV20MarketIdentity],
    output_dir: Path,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    datasets_by_key = {
        (dataset.requested_symbol, canonical_sv20_timeframe(dataset.timeframe)): dataset
        for dataset in datasets
    }
    identity_by_symbol = {identity.requested_symbol: identity for identity in identities}
    paths: list[Path] = []
    for timeframe in SV20_TIMEFRAMES:
        tf = canonical_sv20_timeframe(timeframe)
        tf_datasets = [
            dataset
            for dataset in datasets
            if canonical_sv20_timeframe(dataset.timeframe) == tf
            and dataset.db_imported
            and dataset.candles
            and identity_by_symbol.get(dataset.requested_symbol)
            and identity_by_symbol[dataset.requested_symbol].supported
        ]
        if not tf_datasets:
            continue
        first_close = max(parse_utc(dataset.candles[0]["close_time"]) for dataset in tf_datasets)
        last_close = min(parse_utc(dataset.candles[-1]["close_time"]) for dataset in tf_datasets)
        start = first_close - timedelta(seconds=SV20_TIMEFRAME_SECONDS[tf])
        if last_close <= start:
            continue
        config_symbols = []
        for dataset in sorted(tf_datasets, key=lambda item: item.requested_symbol):
            if datasets_by_key.get((dataset.requested_symbol, tf)) is None:
                continue
            config_symbols.append(
                {
                    "symbol": dataset.requested_symbol,
                    "instrument_key": canonical_market_identity_instrument_key(dataset.requested_symbol),
                }
            )
        config = {
            "campaign_name": f"money_flow_sv2_0_2_hyperliquid_public_{tf}_canonical_db_imported",
            "description": (
                f"SV2.0.2 Money Flow v1.2 canonical DB-backed evidence for "
                f"{SV20_COMPONENT_BY_TIMEFRAME[tf]} using imported Hyperliquid public "
                "mainnet candles. This is research-only and not paper/live trading."
            ),
            "campaign_status": "sv2_0_2_canonical_db_imported_evidence",
            "money_flow_version": SV20_MONEY_FLOW_VERSION,
            "window_convention": _WINDOW_CONVENTION,
            "venue": "hyperliquid",
            "environment": "backtest",
            "data_source": _SOURCE_LABEL,
            "testnet_prices_used_as_strategy_truth": False,
            "requested_universe": list(SV20_REQUESTED_SYMBOLS),
            "symbols": config_symbols,
            "components": [SV20_COMPONENT_BY_TIMEFRAME[tf]],
            "fill_timings": ["next_candle_open", "next_candle_close"],
            "windows": [
                {
                    "label": f"sv2_0_2_public_{tf}_db_imported_common_window",
                    "start": iso_utc(start),
                    "end": iso_utc(last_close),
                    "description": (
                        f"Common imported {display_sv20_timeframe(tf)} close-slot window "
                        "across included symbols; Jan 2025 target coverage is reported "
                        "separately in the readiness table."
                    ),
                    "expected_regime_label": "founder_review_required",
                }
            ],
            "fee_bps_values": ["5"],
            "slippage_bps_values": ["3"],
            "initial_capital": "10000",
            "capital_sizing_modes": ["dynamic_equity_pct"],
            "position_notional_pct": "1.0",
            "output_dir": "reports/strategy_validation",
            "report_formats": ["json", "markdown"],
            "research_boundaries": dict(_NO_ORDER_FLAGS),
        }
        path = output_dir / f"money_flow_sv2_0_2_hyperliquid_public_{tf}_canonical.json"
        path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def generated_timeframes_from_review(
    review: MoneyFlowEvidenceReviewSummary | None,
) -> set[str]:
    if review is None:
        return set()
    payload = money_flow_evidence_review_to_dict(review)
    generated: set[str] = set()
    for result in payload["campaign_results"]:
        if not result.get("evidence_pack_generated"):
            continue
        audit_rows = result["data_readiness_audit"]["rows"]
        for row in audit_rows:
            if row.get("readiness_status") == "covered" and row.get("timeframe"):
                generated.add(canonical_sv20_timeframe(str(row["timeframe"])))
    return generated


def mark_canonical_ready_datasets(
    *,
    datasets: Sequence[SV20CandleDataset],
    generated_timeframes: set[str],
) -> list[SV20CandleDataset]:
    return [
        replace(
            dataset,
            canonical_evidence_ready=(
                dataset.db_imported and canonical_sv20_timeframe(dataset.timeframe) in generated_timeframes
            ),
        )
        for dataset in datasets
    ]


def canonical_evidence_rows_from_packs(evidence_pack_paths: Sequence[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pack_path in evidence_pack_paths:
        batch_path = Path(pack_path) / "batch_report.json"
        if not batch_path.exists():
            continue
        payload = json.loads(batch_path.read_text(encoding="utf-8"))
        for run in payload.get("comparison_summary", {}).get("run_summaries", []):
            metrics = run.get("metrics") or {}
            components = run.get("component_keys") or []
            component = components[0] if components else None
            timeframe = _timeframe_for_component(component)
            rows.append(
                {
                    "symbol": run.get("symbol"),
                    "timeframe": timeframe,
                    "display_timeframe": display_sv20_timeframe(timeframe) if timeframe else None,
                    "component": component,
                    "status": "canonical_evidence_ready" if run.get("status") == "completed" else "blocked",
                    "fill_timing": run.get("fill_timing"),
                    "ending_equity": metrics.get("ending_equity"),
                    "net_pnl": metrics.get("net_pnl"),
                    "trade_count": metrics.get("number_of_trades"),
                    "win_rate": metrics.get("win_rate"),
                    "max_drawdown": metrics.get("mark_to_market_max_drawdown"),
                    "evidence_pack_path": pack_path,
                    "reason_codes": run.get("reason_codes") or [],
                }
            )
    return rows


def summarize_open_position_handling(evidence_pack_paths: Sequence[str]) -> dict[str, Any]:
    forced_close_count = 0
    completed_run_count = 0
    for pack_path in evidence_pack_paths:
        batch_path = Path(pack_path) / "batch_report.json"
        if not batch_path.exists():
            continue
        payload = json.loads(batch_path.read_text(encoding="utf-8"))
        for run in payload.get("comparison_summary", {}).get("run_summaries", []):
            if run.get("status") == "completed":
                completed_run_count += 1
        forced_close_count += count_recursive_key_value(payload, "forced_exit", True)
    return {
        "policy": "force_close_at_dataset_end",
        "open_position_handling_explicit": True,
        "open_positions_at_end_count": forced_close_count,
        "forced_close_count": forced_close_count,
        "mtm_count": completed_run_count,
        "excluded_open_position_count": 0,
        "reason_codes": ["open_positions_are_force_closed_at_window_end_for_canonical_evidence"],
    }


def empty_open_position_summary() -> dict[str, Any]:
    return {
        "policy": "force_close_at_dataset_end",
        "open_position_handling_explicit": False,
        "open_positions_at_end_count": 0,
        "forced_close_count": 0,
        "mtm_count": 0,
        "excluded_open_position_count": 0,
        "reason_codes": ["canonical_evidence_packs_missing"],
    }


def count_recursive_key_value(value: Any, key: str, expected: Any) -> int:
    if isinstance(value, dict):
        return (1 if value.get(key) == expected else 0) + sum(
            count_recursive_key_value(item, key, expected) for item in value.values()
        )
    if isinstance(value, list):
        return sum(count_recursive_key_value(item, key, expected) for item in value)
    return 0


def sor_ev1_readiness_decision(
    *,
    db_blockers: Sequence[str],
    evidence_pack_paths: Sequence[str],
    readiness_rows: Sequence[dict[str, Any]],
) -> str:
    if db_blockers:
        return "SOR-EV1 remains blocked"
    if not evidence_pack_paths:
        return "SOR-EV1 remains blocked"
    if not any(row.get("timeframe") == "1d" and row.get("canonical_evidence_ready") for row in readiness_rows):
        return "SOR-EV1 remains blocked"
    if not all(row.get("evidence_ready") for row in readiness_rows if row.get("db_imported")):
        return "SOR-EV1 remains blocked"
    return "SOR-EV1 may proceed"


def render_sv202_report(summary: dict[str, Any]) -> str:
    sv202 = summary["sv2_0_2"]
    canonical_status = summary["canonical_evidence_status"]
    rows = summary["data_readiness"]
    imported_rows = [row for row in rows if row["db_imported"]]
    excluded_symbols = summary.get("excluded_symbols", [])
    evidence_rows = summary.get("evidence_rows", [])
    lines = [
        "# SV2.0.2 Canonical SV2 Evidence Packs",
        "",
        "Status: `implemented` where DB import and canonical pack generation completed; `blocked` rows are explicit data or symbol readiness gaps.",
        "",
        "SV2.0.2 imports normalized Hyperliquid public mainnet candles through the hardened Strategy Validation candle importer and then uses the existing canonical evidence-pack machinery. It does not submit orders, use private/signed/order endpoints, use API keys, use Hyperliquid testnet prices as strategy truth, optimize parameters, or enable live trading.",
        "",
        "## Summary",
        "",
        f"- Money Flow version: `{summary['money_flow_version']}`",
        "- 1D sleeve: `real Money Flow sleeve`",
        "- Existing 15m/1h/4h rules: `unchanged`",
        f"- Canonical evidence status: `{canonical_status['status']}`",
        f"- Evidence pack paths: `{canonical_status['evidence_pack_paths']}`",
        f"- SOR-EV1 readiness decision: `{sv202['sor_ev1_readiness_decision']}`",
        "",
        "## DB / Import Status",
        "",
        f"- Configured DB URL: `{sv202['db_status']['configured_database_url']}`",
        f"- DB reachable: `{sv202['db_status']['reachable']}`",
        f"- Schema status: `{sv202['db_status']['schema_status']}`",
        f"- Migrations current: `{sv202['db_status']['migrations_current']}`",
        f"- Persisted candle count before/at inspection: `{sv202['db_status']['persisted_candle_count']}`",
        f"- DB blockers: `{sv202['db_blocking_reason_codes']}`",
        f"- Import result count: `{len(sv202['import_results'])}`",
        "",
        "## Market Identity Status",
        "",
        "| requested | venue symbol | supported | asset id | szDecimals | evidence ready | reason codes |",
        "| --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    identity_by_symbol = {row["requested_symbol"]: row for row in summary["market_identities"]}
    evidence_ready_by_symbol = {
        row["requested_symbol"]: any(
            ready["requested_symbol"] == row["requested_symbol"] and ready["evidence_ready"]
            for ready in rows
        )
        for row in summary["market_identities"]
    }
    for symbol in SV20_REQUESTED_SYMBOLS:
        identity = identity_by_symbol.get(symbol)
        if not identity:
            continue
        lines.append(
            "| "
            f"`{symbol}` | "
            f"`{identity['resolved_venue_symbol']}` | "
            f"`{identity['supported']}` | "
            f"`{identity['asset_id']}` | "
            f"`{identity['sz_decimals']}` | "
            f"`{evidence_ready_by_symbol.get(symbol, False)}` | "
            f"`{identity['reason_codes']}` |"
        )
    lines.extend(
        [
            "",
            "## Imported Dataset Table",
            "",
            "| symbol | timeframe | fetched | normalized | raw file | db imported | canonical ready | candles | earliest | latest | target start met | reason codes |",
            "| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            f"`{row['requested_symbol']}` | "
            f"`{row['display_timeframe']}` | "
            f"`{row['fetched']}` | "
            f"`{row['normalized']}` | "
            f"`{row['raw_file_written']}` | "
            f"`{row['db_imported']}` | "
            f"`{row['canonical_evidence_ready']}` | "
            f"{row['candle_count']} | "
            f"`{row['earliest_candle']}` | "
            f"`{row['latest_candle']}` | "
            f"`{row['target_start_met']}` | "
            f"`{row['reason_codes']}` |"
        )
    lines.extend(
        [
            "",
            "## Excluded / Deferred Symbols",
            "",
        ]
    )
    if excluded_symbols:
        lines.extend(
            f"- `{item['requested_symbol']}`: `{item['reason_codes']}`"
            for item in excluded_symbols
        )
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Canonical Campaign Config Summary",
            "",
            f"- Campaign config paths: `{sv202['campaign_config_paths']}`",
            "- Timeframes: `15m`, `1h`, `4h`, `1d`",
            "- Initial equity: `10000 USDC` per independent scenario",
            "- Capital sizing mode: `dynamic_equity_pct`",
            "- Fill assumptions: `next_candle_open`, `next_candle_close`",
            "- Fee/slippage: `5 bps` / `3 bps`",
            "",
            "## Evidence Summary",
            "",
            "| timeframe | runs | symbols | avg ending equity | total trades | worst drawdown |",
            "| --- | ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for timeframe in SV20_TIMEFRAMES:
        tf_rows = [row for row in evidence_rows if row.get("timeframe") == timeframe]
        if not tf_rows:
            lines.append(f"| `{display_sv20_timeframe(timeframe)}` | 0 | `[]` | `None` | 0 | `None` |")
            continue
        ending_values = [Decimal(str(row["ending_equity"])) for row in tf_rows if row.get("ending_equity") is not None]
        drawdowns = [Decimal(str(row["max_drawdown"])) for row in tf_rows if row.get("max_drawdown") is not None]
        trade_count = sum(int(row.get("trade_count") or 0) for row in tf_rows)
        avg_ending = sum(ending_values) / Decimal(len(ending_values)) if ending_values else None
        worst_drawdown = max(drawdowns) if drawdowns else None
        symbols = sorted({str(row["symbol"]) for row in tf_rows if row.get("symbol")})
        lines.append(
            "| "
            f"`{display_sv20_timeframe(timeframe)}` | "
            f"{len(tf_rows)} | "
            f"`{symbols}` | "
            f"`{decimal_text(avg_ending) if avg_ending is not None else None}` | "
            f"{trade_count} | "
            f"`{decimal_text(worst_drawdown) if worst_drawdown is not None else None}` |"
        )
    lines.extend(
        [
            "",
            "## Open-Position Handling",
            "",
            f"- Policy: `{sv202['open_position_handling']['policy']}`",
            f"- Explicit: `{sv202['open_position_handling']['open_position_handling_explicit']}`",
            f"- Forced close count: `{sv202['open_position_handling']['forced_close_count']}`",
            f"- MTM run count: `{sv202['open_position_handling']['mtm_count']}`",
            f"- Excluded open-position count: `{sv202['open_position_handling']['excluded_open_position_count']}`",
            "",
            "## Limitations",
            "",
            "- Hyperliquid public candleSnapshot may be limited to the most recent 5000 candles; Jan 2025 target coverage is reported truthfully per row.",
            "- Evidence packs are research evidence, not proof of profitability and not approval for live trading.",
            "- SHIB/kSHIB unit semantics are deferred if alias units are not clean enough for canonical evidence.",
            "",
            "## No-Order / No-Live Confirmation",
            "",
            f"- Boundary flags: `{sv202['boundary_flags']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def _timeframe_for_component(component: str | None) -> str | None:
    if component is None:
        return None
    for timeframe, mapped_component in SV20_COMPONENT_BY_TIMEFRAME.items():
        if mapped_component == component:
            return timeframe
    return None


def decimal_text(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


if __name__ == "__main__":
    raise SystemExit(main())
