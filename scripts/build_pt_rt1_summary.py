"""Build the committed PT-RT1 configuration summary.

This writes configuration/status metadata only. It does not fetch market data,
does not call exchange endpoints, and does not create runtime paper ledgers.
"""

from __future__ import annotations

import json
from pathlib import Path

from services.paper_runtime.pt_rt1 import build_pt_rt1_summary


OUTPUT_PATH = Path("docs/pt_rt1_real_time_paper_observation_and_testnet_plumbing_summary.json")


def main() -> None:
    OUTPUT_PATH.write_text(
        json.dumps(build_pt_rt1_summary(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
