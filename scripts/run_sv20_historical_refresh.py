#!/usr/bin/env python3
"""Build SV2.0 Hyperliquid public historical readiness/evidence summary.

The script uses Hyperliquid mainnet public `info` only. It never uses API keys,
private/signed endpoints, testnet strategy truth, or order endpoints.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from services.strategy_validation.sv2 import (
    HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
    SV20_REQUESTED_SYMBOLS,
    SV20_TARGET_START_AT,
    SV20_TIMEFRAMES,
    SV20CandleDataset,
    build_sv20_readiness_rows,
    build_sv20_summary,
    fetch_hyperliquid_public_info,
    hyperliquid_candle_snapshot_payload,
    hyperliquid_meta_payload,
    normalize_hyperliquid_candle_snapshot,
    parse_utc,
    resolve_hyperliquid_market_identities,
    run_sv20_baseline_evidence_rows,
    target_start_is_covered,
)


DEFAULT_OUTPUT = Path("docs/sv2_0_historical_data_refresh_summary.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--meta-json", type=Path, default=None)
    parser.add_argument("--fetch-public-data", action="store_true")
    parser.add_argument("--end-at", default=None)
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    return parser.parse_args()


def _load_meta(args: argparse.Namespace) -> object:
    if args.meta_json:
        return json.loads(args.meta_json.read_text(encoding="utf-8"))
    if args.fetch_public_data:
        return fetch_hyperliquid_public_info(
            hyperliquid_meta_payload(),
            url=HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
            timeout_seconds=args.timeout_seconds,
        )
    return {"universe": []}


def main() -> int:
    args = parse_args()
    end_at = parse_utc(args.end_at) if args.end_at else datetime.now(UTC).replace(microsecond=0)
    start_at = parse_utc(SV20_TARGET_START_AT)
    meta = _load_meta(args)
    identities = resolve_hyperliquid_market_identities(meta)
    datasets: list[SV20CandleDataset] = []
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
                        import_reason_codes=("historical_import_blocked_symbol_unsupported",),
                    )
                )
                continue
            if not args.fetch_public_data:
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
                        fetch_reason_codes=("historical_fetch_not_requested",),
                        import_reason_codes=(
                            "historical_import_not_attempted",
                            "db_import_not_attempted",
                            "canonical_hardened_import_not_run",
                        ),
                    )
                )
                continue
            try:
                payload = hyperliquid_candle_snapshot_payload(
                    coin=identity.resolved_venue_symbol,
                    timeframe=timeframe,
                    start_at=start_at,
                    end_at=end_at,
                )
                raw = fetch_hyperliquid_public_info(
                    payload,
                    url=HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
                    timeout_seconds=args.timeout_seconds,
                )
                candles = normalize_hyperliquid_candle_snapshot(
                    raw,
                    requested_symbol=identity.requested_symbol,
                    resolved_venue_symbol=identity.resolved_venue_symbol,
                    timeframe=timeframe,
                )
                target_window_ready = bool(candles) and target_start_is_covered(candles[0]["close_time"], timeframe)
                datasets.append(
                    SV20CandleDataset(
                        requested_symbol=identity.requested_symbol,
                        resolved_venue_symbol=identity.resolved_venue_symbol,
                        timeframe=timeframe,
                        fetch_attempted=True,
                        fetched=True,
                        normalized=True,
                        raw_file_written=False,
                        staged_for_replay=True,
                        db_imported=False,
                        canonical_evidence_ready=False,
                        target_window_ready=target_window_ready,
                        candles=candles,
                        fetch_reason_codes=("hyperliquid_public_mainnet_fetch_succeeded",),
                        import_reason_codes=(
                            "historical_staged_for_replay_only",
                            "db_import_not_attempted",
                            "canonical_hardened_import_not_run",
                        ),
                    )
                )
            except Exception as exc:  # pragma: no cover - depends on network/API availability.
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
                        fetch_reason_codes=(f"historical_fetch_failed:{exc.__class__.__name__}",),
                        import_reason_codes=("historical_import_blocked_fetch_failed",),
                    )
                )
    readiness = build_sv20_readiness_rows(identities, datasets)
    evidence_rows = run_sv20_baseline_evidence_rows(datasets)
    summary = build_sv20_summary(
        identities=identities,
        readiness_rows=readiness,
        evidence_rows=evidence_rows,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"Requested symbols: {', '.join(SV20_REQUESTED_SYMBOLS)}")
    print(f"Endpoint: {HYPERLIQUID_MAINNET_PUBLIC_INFO_URL} public info only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
