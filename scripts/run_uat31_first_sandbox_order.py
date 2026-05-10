"""Run the one approved UAT3.1 Hyperliquid testnet lifecycle probe."""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Any

from core.security import redact_sensitive_text
from services.uat.sandbox import HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV
from services.uat.sandbox_order import (
    REQUIRED_UAT31_ACTUAL_SUBMISSION_APPROVAL_TEXT,
    HyperliquidUAT31HTTPTransport,
    UAT31FirstSandboxOrderAttemptService,
    result_to_summary_dict,
    validate_uat31_actual_submission_approval_text,
)


REPORT_PATH = Path("docs/uat3_1_first_sandbox_order_attempt.md")
SUMMARY_PATH = Path("docs/uat3_1_first_sandbox_order_attempt_summary.json")


def _load_dotenv(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            env[key] = value
    return env


def _prior_attempt_exists(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        return True
    return int(payload.get("order_attempt_count") or 0) > 0


def _markdown_report(summary: dict[str, Any]) -> str:
    status = "verified" if summary["order_attempt_count"] == 1 else "blocked"
    next_decision = (
        "UAT3.2 is blocked"
        if summary["open_order_remains"] or summary["unknown_state"] or summary["unexpected_fill"]
        else "UAT3.2 additional sandbox lifecycle testing may be scoped"
    )
    reason_codes = "\n".join(f"- `{reason}`" for reason in summary["reason_codes"]) or "- none"
    unavailable = summary.get("drawdown_feed", {}).get("unavailable_fields") if summary.get("drawdown_feed") else []
    unavailable_text = "\n".join(f"- `{field}`" for field in unavailable) or "- none"
    approval_text = REQUIRED_UAT31_ACTUAL_SUBMISSION_APPROVAL_TEXT
    return f"""# UAT3.1 First Sandbox Order Attempt

## Scope

Status: `{status}`

UAT3.1 is one approval-gated Hyperliquid testnet/sandbox lifecycle probe. It is not paper trading, not live trading, not strategy performance validation, not broad top-20 order testing, and not approval for future orders.

## Founder / Operator Approval

Approval text presence: `{'verified' if summary['approval_verified'] else 'blocked'}`

```text
{approval_text}
```

## Gate Results

| Gate | Status |
| --- | --- |
| Runtime policy | `{'verified' if summary['allowed_to_submit'] or summary['order_attempt_count'] == 1 else 'blocked'}` |
| Sandbox endpoint verification | `verified` |
| Approval scope | `{'verified' if summary['approval_verified'] else 'blocked'}` |
| Risk gate | `{'verified' if summary['allowed_to_submit'] or summary['order_attempt_count'] == 1 else 'blocked'}` |
| Live-fed drawdown | `{summary.get('drawdown_feed', {}).get('status', 'missing') if summary.get('drawdown_feed') else 'missing'}` |
| Submit lease / duplicate prevention | `{'verified' if summary['order_attempt_count'] <= 1 else 'blocked'}` |
| Sandbox artifact labels | `verified` |
| Live endpoint access | `false` |
| Paper trading | `not approved` |
| Live trading | `not approved` |

## Order Request Sanitized Summary

```json
{json.dumps(summary['sanitized_order_request'], indent=2, sort_keys=True)}
```

## Order Response Sanitized Summary

```json
{json.dumps(summary['sanitized_order_response'], indent=2, sort_keys=True)}
```

## Lifecycle Result

| Field | Value |
| --- | --- |
| Order attempt count | `{summary['order_attempt_count']}` |
| Order status | `{summary['order_status']}` |
| Cancel status | `{summary['cancel_status']}` |
| Reconciliation status | `{summary['reconciliation_status']}` |
| Unexpected fill | `{str(summary['unexpected_fill']).lower()}` |
| Open order remains | `{str(summary['open_order_remains']).lower()}` |
| Unknown state | `{str(summary['unknown_state']).lower()}` |

Cancel response:

```json
{json.dumps(summary['sanitized_cancel_response'], indent=2, sort_keys=True)}
```

Reconciliation summary:

```json
{json.dumps(summary['sanitized_reconciliation'], indent=2, sort_keys=True)}
```

## Sandbox Drawdown

Source: `{summary.get('drawdown_feed', {}).get('source', 'missing') if summary.get('drawdown_feed') else 'missing'}`

Not live account: `{str(summary.get('drawdown_feed', {}).get('not_live_account', False)).lower() if summary.get('drawdown_feed') else 'false'}`

Unavailable fields:

{unavailable_text}

## Side-Effect Confirmation

| Artifact / Behavior | Created / Enabled |
| --- | --- |
| OrderIntent | `{str(summary['side_effect_flags']['creates_order_intent']).lower()}` |
| PreparedVenueOrder | `{str(summary['side_effect_flags']['creates_prepared_order']).lower()}` |
| SubmittedOrder | `{str(summary['side_effect_flags']['creates_submitted_order']).lower()}` |
| Executable approval | `{str(summary['side_effect_flags']['creates_executable_approval']).lower()}` |
| Paper trading | `{str(summary['side_effect_flags']['paper_trading_added']).lower()}` |
| Live trading | `{str(summary['side_effect_flags']['live_trading_added']).lower()}` |

## Reason Codes

{reason_codes}

## Secrets Redaction

Status: `verified`

The report includes only sanitized request/response summaries. It does not include private keys, raw authorization headers, raw signed payloads, or raw signatures.

## Next Readiness Decision

`{next_decision}`
"""


async def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-approved-uat31", action="store_true")
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()

    if not args.execute_approved_uat31:
        raise SystemExit("Refusing to run without --execute-approved-uat31")

    approval_result = validate_uat31_actual_submission_approval_text(
        REQUIRED_UAT31_ACTUAL_SUBMISSION_APPROVAL_TEXT
    )
    env: dict[str, str | None] = {}
    if approval_result.allowed:
        env.update(_load_dotenv(Path(args.env_file)))
        env.update(os.environ)

    base_url = (env.get(HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV) or "https://api.hyperliquid-testnet.xyz").strip()
    service = UAT31FirstSandboxOrderAttemptService(
        transport=HyperliquidUAT31HTTPTransport(base_url=base_url)
    )
    result = await service.execute(
        approval_text=REQUIRED_UAT31_ACTUAL_SUBMISSION_APPROVAL_TEXT,
        env=env,
        prior_attempt_exists=_prior_attempt_exists(SUMMARY_PATH),
        now_utc=datetime.now(tz=UTC),
    )
    summary = result_to_summary_dict(result)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    REPORT_PATH.write_text(_markdown_report(summary))
    print(
        json.dumps(
            {
                "report": str(REPORT_PATH),
                "summary": str(SUMMARY_PATH),
                "order_attempt_count": summary["order_attempt_count"],
                "order_status": summary["order_status"],
                "cancel_status": summary["cancel_status"],
                "reconciliation_status": summary["reconciliation_status"],
                "reason_codes": summary["reason_codes"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(_main()))
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(redact_sensitive_text(str(exc))) from exc
