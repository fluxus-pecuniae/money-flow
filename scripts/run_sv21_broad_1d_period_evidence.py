#!/usr/bin/env python3
"""Run SV2.1 broad Hyperliquid 1D period evidence.

Research-only tooling. Uses Hyperliquid public mainnet ``/info`` payloads only
(``meta`` and ``candleSnapshot``), writes generated raw/config artifacts to a
local work directory, imports normalized 1D candles through the Strategy
Validation candle importer, and optionally generates ignored evidence packs.
It does not use API keys, private/signed/order endpoints, testnet strategy
truth, live trading, or Money Flow rule changes.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

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
from services.strategy_validation.market_identity import canonical_market_identity_instrument_key
from services.strategy_validation.sv2 import (
    HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
    SV20_MONEY_FLOW_VERSION,
    fetch_hyperliquid_public_info,
    hyperliquid_candle_snapshot_payload,
    hyperliquid_meta_payload,
    iso_utc,
    normalize_hyperliquid_candle_snapshot,
    parse_utc,
)

DEFAULT_WORK_DIR = Path("/tmp/money-flow-sv21-broad-1d")
DEFAULT_OUTPUT = Path("docs/sv2_1_broad_hyperliquid_1d_period_evidence_summary.json")
DEFAULT_REPORT_OUTPUT = Path("docs/sv2_1_broad_hyperliquid_1d_period_evidence.md")
SV21_START_AT = parse_utc("2024-01-01T00:00:00Z")
WINDOW_CONVENTION = "(start_at, end_at]"
SOURCE_LABEL = "hyperliquid_public_mainnet_candleSnapshot"
FILL_TIMINGS = ("next_candle_open", "next_candle_close")
SV21_KNOWN_NO_PUBLIC_1D_SYMBOLS = (
    "AERO",
    "AXS",
    "AZTEC",
    "CC",
    "CHIP",
    "DASH",
    "FOGO",
    "ICP",
    "SKR",
    "STABLE",
    "XMR",
)
NO_ORDER_FLAGS = {
    "submits_orders": False,
    "calls_order_endpoints": False,
    "calls_private_or_signed_endpoints": False,
    "uses_api_keys": False,
    "uses_testnet_prices_as_strategy_truth": False,
    "enables_live_trading": False,
    "changes_production_money_flow_rules": False,
    "approves_paper_or_live": False,
}
SV21_FOUNDER_APPROVED_REQUESTED_SYMBOLS = (
    "BTC",
    "ETH",
    "SOL",
    "XRP",
    "DOGE",
    "HYPE",
    "BNB",
    "SUI",
    "AVAX",
    "TRON",
    "ADA",
    "ZEC",
    "LINK",
    "XMR",
    "TON",
    "LTC",
    "UNI",
    "DOT",
    "ASTER",
    "AAVE",
    "POL",
    "FIL",
    "TRUMP",
    "PEPE",
    "OKB",
)
SV21_FOUNDER_APPROVED_SYMBOL_ALIASES = {
    "TRON": "TRX",
    "PEPE": "kPEPE",
}
SV21_FOUNDER_APPROVED_EXCLUDED_SYMBOLS = {
    "PEPE": "pepe_kpepe_unit_semantics_deferred",
    "OKB": "okb_support_not_confirmed_or_public_mid_unavailable",
}
SV21_FOUNDER_APPROVED_RESOLVED_SYMBOLS = tuple(
    dict.fromkeys(
        SV21_FOUNDER_APPROVED_SYMBOL_ALIASES.get(symbol, symbol).upper()
        for symbol in SV21_FOUNDER_APPROVED_REQUESTED_SYMBOLS
        if symbol not in SV21_FOUNDER_APPROVED_EXCLUDED_SYMBOLS
    )
)


@dataclass(frozen=True, slots=True)
class SV21Identity:
    requested_symbol: str
    resolved_venue_symbol: str
    canonical_symbol: str
    asset_id: int
    sz_decimals: int
    max_leverage: int | None
    only_isolated: bool
    raw_metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SV21Dataset:
    symbol: str
    venue_symbol: str
    rows: int
    earliest_close: str | None
    latest_close: str | None
    imported: bool
    raw_path: str | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SV21PeriodResult:
    period: str
    symbol: str
    config_written: bool
    blocked: bool
    start_at: str
    end_at: str
    rows: int
    config_path: str | None
    evidence_pack_path: str | None
    reason_codes: tuple[str, ...]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--fetch-public-data", action="store_true")
    parser.add_argument("--generate-evidence-packs", action="store_true")
    parser.add_argument(
        "--universe-policy",
        choices=("founder_approved", "all_active_public_meta"),
        default="founder_approved",
        help=(
            "Universe to prepare. Defaults to the founder-approved PT-RT1 requested/resolved "
            "list instead of every active Hyperliquid public metadata symbol."
        ),
    )
    parser.add_argument("--symbol", action="append", default=[])
    parser.add_argument("--end-at", default=None)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--run-timestamp", default=None)
    parser.add_argument(
        "--collision-policy",
        choices=("unique_suffix", "fail_if_exists"),
        default=MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    generated_at = datetime.now(UTC).replace(microsecond=0)
    requested_end = parse_utc(args.end_at) if args.end_at else generated_at
    effective_end = latest_closed_1d(requested_end)
    run_timestamp = parse_utc(args.run_timestamp) if args.run_timestamp else generated_at
    args.work_dir.mkdir(parents=True, exist_ok=True)
    (args.work_dir / "raw_candles").mkdir(parents=True, exist_ok=True)
    (args.work_dir / "campaign_configs").mkdir(parents=True, exist_ok=True)

    db_status = inspect_strategy_validation_database_status(MoneyFlowBacktestService(get_settings()))
    db_blockers = db_blocking_reason_codes(db_status)
    identities: list[SV21Identity] = []
    datasets: list[SV21Dataset] = []
    import_results: list[dict[str, Any]] = []
    seed_result: dict[str, Any] | None = None
    period_results: list[SV21PeriodResult] = []
    evidence_pack_paths: list[str] = []

    if args.fetch_public_data:
        meta = fetch_hyperliquid_public_info(
            hyperliquid_meta_payload(),
            url=HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
            timeout_seconds=args.timeout_seconds,
        )
        identities = active_hyperliquid_identities_from_meta(meta)
        if args.universe_policy == "founder_approved":
            identities = filter_founder_approved_identities(identities)
        if args.symbol:
            wanted = {item.upper() for item in args.symbol}
            identities = [item for item in identities if item.canonical_symbol in wanted]
        manifest_path = args.work_dir / "sv2_1_broad_1d_market_identity_manifest.json"
        manifest_path.write_text(
            json.dumps(build_market_identity_manifest(identities, meta, generated_at), indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        if not db_blockers:
            seed_result = strategy_validation_market_identity_seed_result_to_dict(
                seed_strategy_validation_market_identity_from_manifest(
                    manifest_path,
                    operator_verified=True,
                    verified_by="SV2.1 broad 1D evidence import",
                )
            )
            for identity in identities:
                dataset, import_payload = fetch_import_1d_dataset(
                    identity=identity,
                    start_at=SV21_START_AT,
                    end_at=effective_end,
                    work_dir=args.work_dir,
                    timeout_seconds=args.timeout_seconds,
                )
                datasets.append(dataset)
                if import_payload is not None:
                    import_results.append(import_payload)
        else:
            for identity in identities:
                datasets.append(
                    SV21Dataset(
                        symbol=identity.canonical_symbol,
                        venue_symbol=identity.resolved_venue_symbol,
                        rows=0,
                        earliest_close=None,
                        latest_close=None,
                        imported=False,
                        raw_path=None,
                        reason_codes=tuple(db_blockers),
                    )
                )
        if args.universe_policy == "founder_approved":
            datasets.extend(founder_approved_missing_identity_datasets(identities))
    else:
        datasets = scan_existing_raw_datasets(
            args.work_dir,
            allowed_symbols=SV21_FOUNDER_APPROVED_RESOLVED_SYMBOLS
            if args.universe_policy == "founder_approved"
            else None,
        )
        if args.symbol:
            wanted = {item.upper() for item in args.symbol}
            datasets = [item for item in datasets if item.symbol in wanted]

    period_results, config_paths = write_period_campaign_configs(
        datasets=datasets,
        output_dir=args.work_dir / "campaign_configs",
        effective_end=effective_end,
    )
    if args.generate_evidence_packs and config_paths and not db_blockers:
        review = review_money_flow_evidence(
            config_paths,
            service=MoneyFlowBacktestService(get_settings()),
            output_dir="reports/strategy_validation",
            generate_evidence_packs=True,
            run_timestamp=run_timestamp,
            generated_at=generated_at,
            evidence_pack_collision_policy=args.collision_policy,
        )
        review_payload = money_flow_evidence_review_to_dict(review)
        evidence_pack_paths = list(review_payload["generated_evidence_pack_paths"])
        period_results = attach_evidence_paths(period_results, evidence_pack_paths)
    elif not args.generate_evidence_packs:
        evidence_pack_paths = scan_existing_sv21_evidence_pack_paths()
        if evidence_pack_paths:
            period_results = attach_evidence_paths(period_results, evidence_pack_paths)

    summary = build_summary(
        generated_at=generated_at,
        effective_end=effective_end,
        identities=identities,
        datasets=datasets,
        import_results=import_results,
        seed_result=seed_result,
        period_results=period_results,
        evidence_pack_paths=evidence_pack_paths,
        db_blockers=db_blockers,
        universe_policy=args.universe_policy,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(render_report(summary), encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"Wrote {args.report_output}")
    print(f"Campaign configs: {summary['campaign_config_count']} under {args.work_dir / 'campaign_configs'}")
    print(f"Evidence packs: {summary['evidence_pack_count']}")
    return 0


def latest_closed_1d(value: datetime) -> datetime:
    value = value.astimezone(UTC)
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def active_hyperliquid_identities_from_meta(meta: Any) -> list[SV21Identity]:
    universe = meta.get("universe", []) if isinstance(meta, dict) else []
    identities: list[SV21Identity] = []
    for asset_id, row in enumerate(universe):
        if not isinstance(row, dict):
            continue
        venue_symbol = str(row.get("name") or "")
        sz_decimals = row.get("szDecimals")
        if not venue_symbol or sz_decimals is None or bool(row.get("isDelisted") or row.get("delisted")):
            continue
        canonical = venue_symbol.upper()
        identities.append(
            SV21Identity(
                requested_symbol=canonical,
                resolved_venue_symbol=venue_symbol,
                canonical_symbol=canonical,
                asset_id=asset_id,
                sz_decimals=int(sz_decimals),
                max_leverage=int(row["maxLeverage"]) if row.get("maxLeverage") is not None else None,
                only_isolated=bool(row.get("onlyIsolated", False)),
                raw_metadata=row,
            )
        )
    return identities


def filter_founder_approved_identities(identities: Sequence[SV21Identity]) -> list[SV21Identity]:
    allowed = set(SV21_FOUNDER_APPROVED_RESOLVED_SYMBOLS)
    return [identity for identity in identities if identity.canonical_symbol.upper() in allowed]


def founder_approved_missing_identity_datasets(identities: Sequence[SV21Identity]) -> list[SV21Dataset]:
    seen = {identity.canonical_symbol.upper() for identity in identities}
    return [
        SV21Dataset(
            symbol=symbol,
            venue_symbol=symbol,
            rows=0,
            earliest_close=None,
            latest_close=None,
            imported=False,
            raw_path=None,
            reason_codes=("founder_approved_symbol_not_in_active_public_meta",),
        )
        for symbol in SV21_FOUNDER_APPROVED_RESOLVED_SYMBOLS
        if symbol not in seen
    ]


def build_market_identity_manifest(
    identities: Sequence[SV21Identity],
    meta_payload: Any,
    generated_at: datetime,
) -> dict[str, Any]:
    markets: list[dict[str, Any]] = []
    for identity in identities:
        quantity_step = Decimal("1").scaleb(-identity.sz_decimals)
        price_tick = Decimal("1").scaleb(-(6 - identity.sz_decimals))
        instrument_key = canonical_market_identity_instrument_key(identity.canonical_symbol)
        markets.append(
            {
                "instrument": {
                    "instrument_key": instrument_key,
                    "canonical_symbol": identity.canonical_symbol,
                    "market_type": "perpetual",
                    "product_type": "linear",
                    "base_asset": identity.canonical_symbol,
                    "quote_asset": "USDC",
                    "settlement_asset": "USDC",
                    "is_active": True,
                },
                "symbol": {
                    "venue": "hyperliquid",
                    "symbol": identity.canonical_symbol,
                    "exchange_symbol": identity.resolved_venue_symbol,
                    "venue_asset_id": str(identity.asset_id),
                    "asset_id": str(identity.asset_id),
                    "market_type": "perpetual",
                    "product_type": "linear",
                    "base_asset": identity.canonical_symbol,
                    "quote_asset": "USDC",
                    "settlement_asset": "USDC",
                    "price_tick_size": str(price_tick),
                    "quantity_step_size": str(quantity_step),
                    "min_order_size": str(quantity_step),
                    "size_decimals": identity.sz_decimals,
                    "max_leverage": identity.max_leverage,
                    "only_isolated": identity.only_isolated,
                    "is_perpetual": True,
                    "is_builder_deployed": False,
                    "is_strategy_eligible": False,
                    "is_trading_eligible": False,
                    "is_active": True,
                    "raw_metadata": {
                        "source": "hyperliquid_public_info_meta",
                        "sv_phase": "SV2.1",
                        "money_flow_version": SV20_MONEY_FLOW_VERSION,
                        "verification_checked_at_utc": iso_utc(generated_at),
                        "verification_endpoint": f"POST {HYPERLIQUID_MAINNET_PUBLIC_INFO_URL}",
                        "hyperliquid_meta": identity.raw_metadata,
                        "meta_symbol_count": len(meta_payload.get("universe", []))
                        if isinstance(meta_payload, dict)
                        else None,
                    },
                },
            }
        )
    return {
        "manifest_name": "sv2_1_broad_hyperliquid_1d_public_meta_universe",
        "research_only": True,
        "operator_verified": True,
        "verified_by": "SV2.1 broad 1D evidence import",
        "source": "hyperliquid_public_info_meta",
        "venue": "hyperliquid",
        "markets": markets,
    }


def fetch_import_1d_dataset(
    *,
    identity: SV21Identity,
    start_at: datetime,
    end_at: datetime,
    work_dir: Path,
    timeout_seconds: float,
) -> tuple[SV21Dataset, dict[str, Any] | None]:
    raw = fetch_hyperliquid_public_info(
        hyperliquid_candle_snapshot_payload(
            coin=identity.resolved_venue_symbol,
            timeframe="1d",
            start_at=start_at,
            end_at=end_at + timedelta(days=1),
        ),
        url=HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
        timeout_seconds=timeout_seconds,
    )
    candles = [
        row
        for row in normalize_hyperliquid_candle_snapshot(
            raw,
            requested_symbol=identity.canonical_symbol,
            resolved_venue_symbol=identity.resolved_venue_symbol,
            timeframe="1d",
        )
        if start_at < parse_utc(str(row["close_time"])) <= end_at
    ]
    raw_path = work_dir / "raw_candles" / f"hyperliquid_public_{identity.resolved_venue_symbol.lower()}_1d_sv2_1.json"
    instrument_key = canonical_market_identity_instrument_key(identity.canonical_symbol)
    import_rows = [dict(row, instrument_key=instrument_key) for row in candles]
    raw_path.write_text(
        json.dumps(
            {
                "source": SOURCE_LABEL,
                "symbol": identity.canonical_symbol,
                "venue_symbol": identity.resolved_venue_symbol,
                "timeframe": "1d",
                "candles": import_rows,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    result = import_strategy_validation_candles_from_path(
        raw_path,
        environment=Environment.BACKTEST,
        venue="hyperliquid",
        timeframe=Timeframe.D1,
        source_label=SOURCE_LABEL,
        file_format="json",
        assume_naive_utc=False,
    )
    payload = strategy_validation_candle_import_result_to_dict(result)
    payload.update({"symbol": identity.canonical_symbol, "venue_symbol": identity.resolved_venue_symbol})
    return (
        SV21Dataset(
            symbol=identity.canonical_symbol,
            venue_symbol=identity.resolved_venue_symbol,
            rows=len(candles),
            earliest_close=str(candles[0]["close_time"]) if candles else None,
            latest_close=str(candles[-1]["close_time"]) if candles else None,
            imported=True,
            raw_path=str(raw_path),
            reason_codes=(
                "hyperliquid_public_mainnet_fetch_succeeded",
                "historical_import_succeeded",
                "canonical_hardened_import_succeeded",
                "db_imported_true",
            ),
        ),
        payload,
    )


def scan_existing_raw_datasets(
    work_dir: Path,
    *,
    allowed_symbols: Sequence[str] | None = None,
) -> list[SV21Dataset]:
    allowed = {symbol.upper() for symbol in allowed_symbols or ()}
    rows: list[SV21Dataset] = []
    for path in sorted((work_dir / "raw_candles").glob("hyperliquid_public_*_1d_sv2_1.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        candles = payload.get("candles") or []
        symbol = str(payload.get("symbol") or payload.get("requested_symbol") or "").upper()
        if allowed and symbol not in allowed:
            continue
        venue_symbol = str(payload.get("venue_symbol") or payload.get("resolved_venue_symbol") or symbol)
        rows.append(
            SV21Dataset(
                symbol=symbol,
                venue_symbol=venue_symbol,
                rows=len(candles),
                earliest_close=candles[0].get("close_time") if candles else None,
                latest_close=candles[-1].get("close_time") if candles else None,
                imported=True,
                raw_path=str(path),
                reason_codes=("existing_raw_candle_file_loaded",),
            )
        )
    seen = {row.symbol for row in rows}
    for symbol in SV21_KNOWN_NO_PUBLIC_1D_SYMBOLS:
        if allowed and symbol not in allowed:
            continue
        if symbol not in seen:
            rows.append(
                SV21Dataset(
                    symbol=symbol,
                    venue_symbol=symbol,
                    rows=0,
                    earliest_close=None,
                    latest_close=None,
                    imported=False,
                    raw_path=None,
                    reason_codes=("no_public_1d_candles_available",),
                )
            )
    return rows


def period_specs(effective_end: datetime | None = None) -> list[tuple[str, datetime, datetime]]:
    ytd_end = effective_end or latest_closed_1d(datetime.now(UTC))
    return [
        ("2024", parse_utc("2024-01-01T00:00:00Z"), parse_utc("2025-01-01T00:00:00Z")),
        ("2025", parse_utc("2025-01-01T00:00:00Z"), parse_utc("2026-01-01T00:00:00Z")),
        ("YTD", parse_utc("2026-01-01T00:00:00Z"), ytd_end),
        ("ALL", SV21_START_AT, ytd_end),
    ]


def write_period_campaign_configs(
    *,
    datasets: Sequence[SV21Dataset],
    output_dir: Path,
    effective_end: datetime | None = None,
) -> tuple[list[SV21PeriodResult], list[Path]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[SV21PeriodResult] = []
    paths: list[Path] = []
    for dataset in sorted(datasets, key=lambda item: item.symbol):
        if not dataset.rows or not dataset.earliest_close or not dataset.latest_close:
            for label, desired_start, desired_end in period_specs(effective_end):
                results.append(
                    SV21PeriodResult(
                        period=label,
                        symbol=dataset.symbol,
                        config_written=False,
                        blocked=True,
                        start_at=iso_utc(desired_start),
                        end_at=iso_utc(desired_end),
                        rows=0,
                        config_path=None,
                        evidence_pack_path=None,
                        reason_codes=("no_public_1d_candles_available_in_period",),
                    )
                )
            continue
        first_close = parse_utc(dataset.earliest_close)
        last_close = parse_utc(dataset.latest_close)
        for label, desired_start, desired_end in period_specs(last_close):
            start = max(desired_start, first_close - timedelta(days=1))
            end = min(desired_end, last_close)
            rows = max(0, (end - start).days)
            if rows <= 0:
                results.append(
                    SV21PeriodResult(
                        period=label,
                        symbol=dataset.symbol,
                        config_written=False,
                        blocked=True,
                        start_at=iso_utc(start),
                        end_at=iso_utc(end),
                        rows=0,
                        config_path=None,
                        evidence_pack_path=None,
                        reason_codes=("no_public_1d_candles_available_in_period",),
                    )
                )
                continue
            campaign_name = (
                f"money_flow_sv2_1_hyperliquid_broad_1d_"
                f"{label.lower()}_{dataset.symbol.lower()}_canonical_db_imported"
            )
            config = {
                "campaign_name": campaign_name,
                "description": (
                    "SV2.1 founder-approved Hyperliquid public-mainnet 1D period evidence "
                    f"for {dataset.symbol} {label}; research-only generated evidence, no "
                    "production rule changes, no orders, no private endpoints."
                ),
                "campaign_status": "sv2_1_broad_1d_period_evidence",
                "money_flow_version": SV20_MONEY_FLOW_VERSION,
                "window_convention": "candle_close_time_start_exclusive_end_inclusive",
                "venue": "hyperliquid",
                "environment": "backtest",
                "data_source": SOURCE_LABEL,
                "symbols": [
                    {
                        "symbol": dataset.symbol,
                        "instrument_key": canonical_market_identity_instrument_key(dataset.symbol),
                    }
                ],
                "components": ["sleeve_1d"],
                "fill_timings": list(FILL_TIMINGS),
                "windows": [
                    {
                        "label": f"sv2_1_{label.lower()}_{dataset.symbol.lower()}_1d_available_window",
                        "start": iso_utc(start),
                        "end": iso_utc(end),
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
                "research_boundaries": NO_ORDER_FLAGS,
            }
            path = output_dir / f"{campaign_name}.json"
            path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            paths.append(path)
            results.append(
                SV21PeriodResult(
                    period=label,
                    symbol=dataset.symbol,
                    config_written=True,
                    blocked=False,
                    start_at=iso_utc(start),
                    end_at=iso_utc(end),
                    rows=rows,
                    config_path=str(path),
                    evidence_pack_path=None,
                    reason_codes=("period_campaign_config_written",),
                )
            )
    return results, paths


def attach_evidence_paths(
    results: Sequence[SV21PeriodResult],
    evidence_pack_paths: Sequence[str],
) -> list[SV21PeriodResult]:
    by_name = {Path(path).parent.name if Path(path).name.startswith("20") else Path(path).name: path for path in evidence_pack_paths}
    updated: list[SV21PeriodResult] = []
    for result in results:
        campaign = None
        if result.config_path:
            campaign = Path(result.config_path).stem
        updated.append(
            SV21PeriodResult(
                **{
                    **asdict(result),
                    "evidence_pack_path": by_name.get(str(campaign)),
                    "reason_codes": tuple([*result.reason_codes, "evidence_pack_generated"])
                    if campaign in by_name
                    else result.reason_codes,
                }
            )
        )
    return updated


def scan_existing_sv21_evidence_pack_paths() -> list[str]:
    root = Path("reports/strategy_validation")
    if not root.exists():
        return []
    all_paths: list[str] = []
    preferred_paths: list[str] = []
    for campaign_dir in root.glob("money_flow_sv2_1_hyperliquid_broad_1d_*_canonical_db_imported"):
        for run_dir in campaign_dir.iterdir():
            if run_dir.is_dir() and (run_dir / "batch_report.json").exists():
                all_paths.append(str(run_dir))
                if run_dir.name == "20260514T220500Z":
                    preferred_paths.append(str(run_dir))
    return sorted(preferred_paths or all_paths)


def db_blocking_reason_codes(status: Any) -> list[str]:
    if isinstance(status, dict):
        payload = status
    elif hasattr(status, "to_dict"):
        payload = status.to_dict()
    elif is_dataclass(status):
        payload = asdict(status)
    else:
        payload = dict(status)
    if payload.get("intended_strategy_validation_database") is not True:
        return ["intended_strategy_validation_db_required"]
    if payload.get("schema_ready_for_evidence_generation") is not True:
        return ["migrated_schema_ready_required"]
    return []


def build_summary(
    *,
    generated_at: datetime,
    effective_end: datetime,
    identities: Sequence[SV21Identity],
    datasets: Sequence[SV21Dataset],
    import_results: Sequence[dict[str, Any]],
    seed_result: dict[str, Any] | None,
    period_results: Sequence[SV21PeriodResult],
    evidence_pack_paths: Sequence[str],
    db_blockers: Sequence[str],
    universe_policy: str = "founder_approved",
) -> dict[str, Any]:
    period_counts = {
        period: {
            "config_written": sum(1 for row in period_results if row.period == period and row.config_written),
            "blocked": sum(1 for row in period_results if row.period == period and row.blocked),
        }
        for period in ("2024", "2025", "YTD", "ALL")
    }
    blocked_by_period: dict[str, list[str]] = {period: [] for period in ("2024", "2025", "YTD", "ALL")}
    for row in period_results:
        if row.blocked:
            blocked_by_period[row.period].append(row.symbol)
    return {
        "phase": "SV2.1",
        "status": "evidence_generated" if evidence_pack_paths else "prepared",
        "generated_at_utc": iso_utc(generated_at),
        "source_endpoint": f"POST {HYPERLIQUID_MAINNET_PUBLIC_INFO_URL}",
        "source_payloads": ["meta", "candleSnapshot"],
        "universe_policy": universe_policy,
        "requested_symbols": list(SV21_FOUNDER_APPROVED_REQUESTED_SYMBOLS)
        if universe_policy == "founder_approved"
        else [],
        "resolved_symbols": list(SV21_FOUNDER_APPROVED_RESOLVED_SYMBOLS)
        if universe_policy == "founder_approved"
        else [],
        "excluded_symbols": dict(SV21_FOUNDER_APPROVED_EXCLUDED_SYMBOLS)
        if universe_policy == "founder_approved"
        else {},
        "timeframe": "1d",
        "component": "sleeve_1d",
        "requested_start_at_utc": iso_utc(SV21_START_AT),
        "effective_closed_end_at_utc": iso_utc(effective_end),
        "active_symbol_count": len(identities) or len({row.symbol for row in datasets}),
        "dataset_count": len(datasets),
        "imported_dataset_count": sum(1 for row in datasets if row.imported),
        "campaign_config_count": sum(1 for row in period_results if row.config_written),
        "evidence_pack_count": len(evidence_pack_paths),
        "period_counts": period_counts,
        "blocked_symbols_by_period": {key: sorted(value) for key, value in blocked_by_period.items()},
        "datasets": [asdict(row) for row in datasets],
        "period_results": [asdict(row) for row in period_results],
        "evidence_pack_paths": list(evidence_pack_paths),
        "import_results": list(import_results),
        "market_identity_seed_result": seed_result,
        "db_blockers": list(db_blockers),
        "boundary_flags": NO_ORDER_FLAGS,
    }


def render_report(summary: dict[str, Any]) -> str:
    founder_approved = summary.get("universe_policy") == "founder_approved"
    title = (
        "SV2.1 Founder-Approved Hyperliquid 1D Period Evidence"
        if founder_approved
        else "SV2.1 Broad Hyperliquid 1D Period Evidence"
    )
    scope_sentence = (
        "SV2.1 regenerates 1D Money Flow v1.2 evidence across the founder-approved "
        "PT-RT1 requested/resolved Hyperliquid public-mainnet universe. PEPE/kPEPE "
        "and OKB remain excluded by resolver policy."
        if founder_approved
        else "SV2.1 regenerates 1D Money Flow v1.2 evidence across the broad active "
        "Hyperliquid public-mainnet metadata universe."
    )
    lines = [
        f"# {title}",
        "",
        f"Status: `{summary['status']}`",
        "",
        f"{scope_sentence} It is research-only: no orders, no private/signed/order endpoints, no API keys, no testnet strategy truth, no production rule changes, and no paper/live approval.",
        "",
        "## Summary",
        "",
        f"- Generated at UTC: `{summary['generated_at_utc']}`",
        f"- Source endpoint: `{summary['source_endpoint']}`",
        f"- Universe policy: `{summary['universe_policy']}`",
        f"- Active symbols targeted: `{summary['active_symbol_count']}`",
        f"- Timeframe/component: `{summary['timeframe']}` / `{summary['component']}`",
        f"- Requested start: `{summary['requested_start_at_utc']}`",
        f"- Effective end: `{summary['effective_closed_end_at_utc']}`",
        f"- Campaign configs written: `{summary['campaign_config_count']}`",
        f"- Evidence packs generated: `{summary['evidence_pack_count']}`",
        f"- DB blockers: `{summary['db_blockers']}`",
    ]
    if founder_approved:
        lines.extend(
            [
                f"- Requested founder symbols: `{', '.join(summary.get('requested_symbols') or [])}`",
                f"- Resolved evidence symbols: `{', '.join(summary.get('resolved_symbols') or [])}`",
                f"- Excluded resolver symbols: `{summary.get('excluded_symbols')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Period Sets",
            "",
            "| period | configs | blocked rows |",
            "| --- | ---: | ---: |",
        ]
    )
    for period in ("2024", "2025", "YTD", "ALL"):
        counts = summary["period_counts"].get(period, {"config_written": 0, "blocked": 0})
        lines.append(f"| `{period}` | {counts['config_written']} | {counts['blocked']} |")
    lines.extend(["", "## Data Gaps", ""])
    for period in ("2024", "2025", "YTD", "ALL"):
        symbols = summary["blocked_symbols_by_period"].get(period, [])
        detail = ", ".join(symbols) if symbols else "none"
        lines.append(f"- `{period}` blocked symbols: `{len(symbols)}` - `{detail}`")
    lines.extend(["", "## Generated Evidence Pack Paths", ""])
    if summary["evidence_pack_paths"]:
        lines.extend(f"- `{path}`" for path in summary["evidence_pack_paths"][:200])
        if len(summary["evidence_pack_paths"]) > 200:
            lines.append(f"- ... `{len(summary['evidence_pack_paths']) - 200}` additional paths omitted from Markdown report; see summary JSON.")
    else:
        lines.append("- No evidence packs generated.")
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- Production Money Flow rules changed: `False`",
            "- Paper/live approved: `False`",
            "- Orders submitted: `False`",
            "- Private/signed/order endpoints called: `False`",
            "- API keys used: `False`",
            "- Testnet data used as strategy truth: `False`",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
