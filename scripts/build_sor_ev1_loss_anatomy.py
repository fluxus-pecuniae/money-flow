from __future__ import annotations

import argparse
from pathlib import Path

from services.strategy_validation.sor_ev1 import build_sor_ev1_report, write_sor_ev1_outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build SOR-EV1 evidence-only Money Flow loss anatomy report.")
    parser.add_argument("--markdown-output", default="docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants.md")
    parser.add_argument("--json-output", default="docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants_summary.json")
    args = parser.parse_args()
    report = build_sor_ev1_report()
    write_sor_ev1_outputs(report, Path(args.markdown_output), Path(args.json_output))
    print(f"wrote {args.markdown_output}")
    print(f"wrote {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
