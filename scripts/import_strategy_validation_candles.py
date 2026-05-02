"""Import offline/public historical candles for Strategy Validation research."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from core.domain.enums import Environment, Timeframe
from services.strategy_validation import (
    import_strategy_validation_candles_from_path,
    strategy_validation_candle_import_result_to_dict,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Import public/offline historical candles for Money Flow Strategy Validation. "
            "This is research-only: it upserts Candle rows, does not call exchanges, "
            "does not create live trading artifacts, and does not route or submit."
        ),
    )
    parser.add_argument("--input", required=True, help="CSV or JSON candle file path.")
    parser.add_argument(
        "--format",
        choices=("auto", "csv", "json"),
        default="auto",
        help="Input file format. Default infers from file extension.",
    )
    parser.add_argument(
        "--environment",
        required=True,
        choices=tuple(item.value for item in Environment),
        help="Environment to attach to imported candle rows.",
    )
    parser.add_argument("--venue", required=True, help="Venue/source for imported candle rows.")
    parser.add_argument(
        "--timeframe",
        required=True,
        choices=tuple(item.value for item in Timeframe),
        help="Timeframe for imported candle rows.",
    )
    parser.add_argument(
        "--source-label",
        help=(
            "Optional public/offline data source label. The current candle model has no "
            "per-candle provenance field, so this label is reported in the import summary only."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = import_strategy_validation_candles_from_path(
        Path(args.input),
        environment=Environment(args.environment),
        venue=args.venue,
        timeframe=Timeframe(args.timeframe),
        source_label=args.source_label,
        file_format=args.format,
    )
    print(
        json.dumps(
            strategy_validation_candle_import_result_to_dict(result),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
