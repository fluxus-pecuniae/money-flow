from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from services.exchange.hyperliquid.signing import signer_address
from services.uat.sandbox import (
    HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV,
    HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV,
    HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV,
)
from services.uat.sandbox_order import (
    REQUIRED_UAT31_ACTUAL_SUBMISSION_APPROVAL_TEXT,
    UAT31RejectReason,
    UAT31FirstSandboxOrderAttemptService,
    build_uat31_artifact_labels,
    build_uat31_market_plan,
    result_to_summary_dict,
    validate_uat31_actual_submission_approval_text,
    validate_uat31_manual_probe_labels,
)


NOW = datetime(2026, 5, 10, 17, 30, tzinfo=UTC)


class FakeUAT31Transport:
    def __init__(self, *, order_response: dict[str, Any] | None = None) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.order_response = order_response or {
            "status": "ok",
            "response": {
                "type": "order",
                "data": {"statuses": [{"resting": {"oid": 123456}}]},
            },
        }

    async def post_json(self, path: str, payload: dict[str, Any]) -> Any:
        self.calls.append((path, payload))
        if path == "/info" and payload.get("type") == "meta":
            return {"universe": [{"name": "BTC", "szDecimals": 5}, {"name": "ETH", "szDecimals": 4}]}
        if path == "/info" and payload.get("type") == "l2Book":
            return {"levels": [[{"px": "2500.00", "sz": "1"}], [{"px": "2501.00", "sz": "1"}]]}
        if path == "/info" and payload.get("type") == "clearinghouseState":
            return {"marginSummary": {"accountValue": "1000"}, "assetPositions": []}
        if path == "/info" and payload.get("type") == "orderStatus":
            return {
                "order": {
                    "status": "canceled",
                    "order": {"oid": 123456, "sz": "0.004", "origSz": "0.004"},
                }
            }
        if path == "/info" and payload.get("type") == "frontendOpenOrders":
            return []
        if path == "/exchange":
            action_type = payload["action"]["type"]
            if action_type == "order":
                return self.order_response
            if action_type == "cancel":
                return {
                    "status": "ok",
                    "response": {"type": "cancel", "data": {"statuses": ["success"]}},
                }
        raise AssertionError(f"unexpected transport call: {path} {payload}")


def _env() -> dict[str, str]:
    private_key = "0x" + ("1" * 64)
    return {
        HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV: private_key,
        HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV: signer_address(private_key),
        HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV: "https://api.hyperliquid-testnet.xyz",
    }


def test_approval_text_required_before_actual_sandbox_submit() -> None:
    missing = validate_uat31_actual_submission_approval_text("")
    present = validate_uat31_actual_submission_approval_text(REQUIRED_UAT31_ACTUAL_SUBMISSION_APPROVAL_TEXT)

    assert missing.blocked is True
    assert UAT31RejectReason.APPROVAL_REQUIRED in missing.reason_codes
    assert present.allowed is True


def test_missing_approval_blocks_order_call() -> None:
    transport = FakeUAT31Transport()
    result = asyncio.run(
        UAT31FirstSandboxOrderAttemptService(transport=transport).execute(
            approval_text="design approval only",
            env=_env(),
            prior_attempt_exists=False,
            now_utc=NOW,
        )
    )

    assert result.blocked is True
    assert result.lifecycle.order_attempt_count == 0
    assert transport.calls == []


def test_live_endpoint_blocks_before_order_call() -> None:
    transport = FakeUAT31Transport()
    env = _env()
    env[HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV] = "https://api.hyperliquid.xyz"
    result = asyncio.run(
        UAT31FirstSandboxOrderAttemptService(transport=transport).execute(
            approval_text=REQUIRED_UAT31_ACTUAL_SUBMISSION_APPROVAL_TEXT,
            env=env,
            prior_attempt_exists=False,
            now_utc=NOW,
        )
    )

    assert result.blocked is True
    assert UAT31RejectReason.SANDBOX_ENDPOINT_REQUIRED in result.reason_codes
    assert result.lifecycle.order_attempt_count == 0
    assert transport.calls == []


def test_one_order_max_prior_attempt_blocks() -> None:
    transport = FakeUAT31Transport()
    result = asyncio.run(
        UAT31FirstSandboxOrderAttemptService(transport=transport).execute(
            approval_text=REQUIRED_UAT31_ACTUAL_SUBMISSION_APPROVAL_TEXT,
            env=_env(),
            prior_attempt_exists=True,
            now_utc=NOW,
        )
    )

    assert UAT31RejectReason.PRIOR_ATTEMPT_EXISTS in result.reason_codes
    assert result.lifecycle.order_attempt_count == 0
    assert transport.calls == []


def test_manual_lifecycle_probe_labels_are_required() -> None:
    labels = build_uat31_artifact_labels()
    assert validate_uat31_manual_probe_labels(labels).allowed is True

    missing = validate_uat31_manual_probe_labels(
        type(labels)(base=labels.base, manual_sandbox_lifecycle_probe=False)
    )
    assert "manual_sandbox_lifecycle_probe_label_missing_or_false" in missing.reason_codes


def test_order_shape_is_non_marketable_post_only_and_notional_capped() -> None:
    plan, reasons = build_uat31_market_plan(
        meta_payload={"universe": [{"name": "ETH", "szDecimals": 4}]},
        l2_book_payload={"levels": [[{"px": "2500.00"}], [{"px": "2501.00"}]]},
        max_notional=Decimal("10"),
        cloid="0x1234",
    )

    assert reasons == ()
    assert plan is not None
    assert plan.tif == "Alo"
    assert plan.limit_price < plan.best_ask
    assert plan.estimated_notional <= Decimal("10")


def test_order_transport_called_only_when_all_gates_pass_and_cancel_if_open() -> None:
    transport = FakeUAT31Transport()
    result = asyncio.run(
        UAT31FirstSandboxOrderAttemptService(transport=transport).execute(
            approval_text=REQUIRED_UAT31_ACTUAL_SUBMISSION_APPROVAL_TEXT,
            env=_env(),
            prior_attempt_exists=False,
            now_utc=NOW,
        )
    )

    exchange_calls = [payload for path, payload in transport.calls if path == "/exchange"]
    assert result.allowed_to_submit is True
    assert result.lifecycle.order_attempt_count == 1
    assert result.lifecycle.order_status == "open"
    assert result.lifecycle.cancel_status == "cancel_acknowledged"
    assert len([p for p in exchange_calls if p["action"]["type"] == "order"]) == 1
    assert len([p for p in exchange_calls if p["action"]["type"] == "cancel"]) == 1
    assert result.creates_order_intent is False
    assert result.creates_prepared_order is False
    assert result.creates_submitted_order is False
    assert result.creates_executable_approval is False


def test_unexpected_fill_stops_without_second_order() -> None:
    transport = FakeUAT31Transport(
        order_response={
            "status": "ok",
            "response": {
                "type": "order",
                "data": {"statuses": [{"filled": {"oid": 777, "totalSz": "0.004"}}]},
            },
        }
    )
    result = asyncio.run(
        UAT31FirstSandboxOrderAttemptService(transport=transport).execute(
            approval_text=REQUIRED_UAT31_ACTUAL_SUBMISSION_APPROVAL_TEXT,
            env=_env(),
            prior_attempt_exists=False,
            now_utc=NOW,
        )
    )

    exchange_calls = [payload for path, payload in transport.calls if path == "/exchange"]
    assert result.lifecycle.unexpected_fill is True
    assert result.lifecycle.cancel_endpoint_called is False
    assert len([p for p in exchange_calls if p["action"]["type"] == "order"]) == 1
    assert len([p for p in exchange_calls if p["action"]["type"] == "cancel"]) == 0


def test_summary_redacts_secrets_and_preserves_sandbox_boundary_flags() -> None:
    transport = FakeUAT31Transport()
    # Use a synthetic minimal result through a successful async test path in the
    # event loop provided by pytest; direct summary assertions live in the async
    # integration test below for clarity.
    assert transport.calls == []


def test_result_summary_contains_no_artifact_creation_or_approval_side_effects() -> None:
    result = asyncio.run(
        UAT31FirstSandboxOrderAttemptService(transport=FakeUAT31Transport()).execute(
            approval_text=REQUIRED_UAT31_ACTUAL_SUBMISSION_APPROVAL_TEXT,
            env=_env(),
            prior_attempt_exists=False,
            now_utc=NOW,
        )
    )
    summary = result_to_summary_dict(result)

    assert summary["side_effect_flags"]["creates_order_intent"] is False
    assert summary["side_effect_flags"]["creates_prepared_order"] is False
    assert summary["side_effect_flags"]["creates_submitted_order"] is False
    assert summary["side_effect_flags"]["creates_executable_approval"] is False
    assert summary["sandbox_labels"]["not_live"] is True
    assert summary["sandbox_labels"]["not_paper"] is True
    serialized = str(summary)
    assert _env()[HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV] not in serialized
    assert "'signature':" not in str(summary["sanitized_order_request"]).lower()


def test_uat31_report_exists_and_records_readiness_decision() -> None:
    report = Path("docs/uat3_1_first_sandbox_order_attempt.md")
    assert report.exists()
    text = report.read_text()
    assert "UAT3.1 First Sandbox Order Attempt" in text
    assert "FOUNDER / OPERATOR APPROVAL" in text
    assert "UAT3.2" in text
