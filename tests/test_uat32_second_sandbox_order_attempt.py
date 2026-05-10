from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from services.exchange.hyperliquid.signing import signer_address
from services.uat.sandbox import (
    HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV,
    HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV,
    HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV,
    SandboxAccountStateSnapshot,
    SandboxDrawdownFeedStatus,
    build_sandbox_account_drawdown_feed,
)
from services.uat.sandbox_order import (
    REQUIRED_UAT32_ACTUAL_SUBMISSION_APPROVAL_TEXT,
    UAT32RejectReason,
    UAT32SecondSandboxOrderAttemptService,
    build_uat32_artifact_labels,
    evaluate_uat32_account_api_wallet_readiness,
    result_to_uat32_summary_dict,
    validate_uat31_manual_probe_labels,
    validate_uat32_actual_submission_approval_text,
)


NOW = datetime(2026, 5, 10, 18, 30, tzinfo=UTC)


class FakeUAT32Transport:
    def __init__(
        self,
        *,
        order_response: dict[str, Any] | None = None,
        account_role: dict[str, Any] | None = None,
        signer_role: dict[str, Any] | None = None,
        account_value: str = "1000",
        target_account: str | None = None,
    ) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.order_response = order_response or {
            "status": "ok",
            "response": {
                "type": "order",
                "data": {"statuses": [{"resting": {"oid": 223456}}]},
            },
        }
        self.account_role = account_role or {"role": "user"}
        self.signer_role = signer_role or {"role": "user"}
        self.account_value = account_value
        self.target_account = target_account or _env()[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV]

    async def post_json(self, path: str, payload: dict[str, Any]) -> Any:
        self.calls.append((path, payload))
        if path == "/info" and payload.get("type") == "meta":
            return {"universe": [{"name": "BTC", "szDecimals": 5}, {"name": "ETH", "szDecimals": 4}]}
        if path == "/info" and payload.get("type") == "l2Book":
            return {"levels": [[{"px": "2500.00", "sz": "1"}], [{"px": "2501.00", "sz": "1"}]]}
        if path == "/info" and payload.get("type") == "userRole":
            if str(payload.get("user", "")).lower() == self.target_account.lower():
                return self.account_role
            return self.signer_role
        if path == "/info" and payload.get("type") == "clearinghouseState":
            return {"marginSummary": {"accountValue": self.account_value}, "assetPositions": []}
        if path == "/info" and payload.get("type") == "orderStatus":
            return {
                "order": {
                    "status": "canceled",
                    "order": {"oid": 223456, "sz": "0.004", "origSz": "0.004"},
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


def _exchange_order_calls(transport: FakeUAT32Transport) -> list[dict[str, Any]]:
    return [payload for path, payload in transport.calls if path == "/exchange" and payload["action"]["type"] == "order"]


def test_approval_text_required_before_actual_sandbox_submit() -> None:
    missing = validate_uat32_actual_submission_approval_text("")
    present = validate_uat32_actual_submission_approval_text(REQUIRED_UAT32_ACTUAL_SUBMISSION_APPROVAL_TEXT)

    assert missing.blocked is True
    assert UAT32RejectReason.APPROVAL_REQUIRED in missing.reason_codes
    assert present.allowed is True


def test_missing_approval_blocks_order_call() -> None:
    transport = FakeUAT32Transport()
    result = asyncio.run(
        UAT32SecondSandboxOrderAttemptService(transport=transport).execute(
            approval_text="UAT3.1 approval is not enough",
            env=_env(),
            prior_attempt_exists=False,
            now_utc=NOW,
        )
    )

    assert result.blocked is True
    assert result.lifecycle.order_attempt_count == 0
    assert transport.calls == []


def test_fixed_key_account_api_wallet_readiness_is_checked() -> None:
    feed = build_sandbox_account_drawdown_feed(
        snapshot=SandboxAccountStateSnapshot(
            venue="hyperliquid",
            sandbox_account_id=_env()[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV],
            timestamp_utc=NOW,
            sandbox_account_equity=Decimal("1000"),
            sandbox_realized_pnl=None,
            sandbox_unrealized_pnl=None,
            open_positions_summary=(),
            max_sandbox_equity=Decimal("1000"),
            min_sandbox_equity=Decimal("1000"),
            source="sandbox_account",
            not_live_account=True,
        ),
        drawdown_threshold=Decimal("0.05"),
        status=SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED,
    )
    readiness = evaluate_uat32_account_api_wallet_readiness(
        account_id=_env()[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV],
        signer=_env()[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV],
        account_role_payload={"role": "user"},
        signer_role_payload={"role": "user"},
        drawdown_feed=feed,
        requested_notional=Decimal("9.9"),
        now_utc=NOW,
    )

    assert readiness.allowed is True
    assert readiness.sandbox_account_equity_available is True
    assert readiness.api_wallet_authorized_for_account is True


def test_fixed_key_readiness_blocks_missing_api_wallet_before_exchange_order_call() -> None:
    target_account = "0x" + ("2" * 40)
    transport = FakeUAT32Transport(signer_role={"role": "missing"}, target_account=target_account)
    env = _env()
    env[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV] = target_account
    result = asyncio.run(
        UAT32SecondSandboxOrderAttemptService(transport=transport).execute(
            approval_text=REQUIRED_UAT32_ACTUAL_SUBMISSION_APPROVAL_TEXT,
            env=env,
            prior_attempt_exists=False,
            now_utc=NOW,
        )
    )

    assert UAT32RejectReason.FIXED_KEY_READINESS_FAILED in result.reason_codes
    assert UAT32RejectReason.TESTNET_API_WALLET_NOT_FOUND in result.reason_codes
    assert result.lifecycle.order_attempt_count == 0
    assert _exchange_order_calls(transport) == []


def test_fixed_key_readiness_blocks_insufficient_sandbox_equity() -> None:
    transport = FakeUAT32Transport(account_value="1")
    result = asyncio.run(
        UAT32SecondSandboxOrderAttemptService(transport=transport).execute(
            approval_text=REQUIRED_UAT32_ACTUAL_SUBMISSION_APPROVAL_TEXT,
            env=_env(),
            prior_attempt_exists=False,
            now_utc=NOW,
        )
    )

    assert UAT32RejectReason.ACCOUNT_EQUITY_INSUFFICIENT in result.reason_codes
    assert result.lifecycle.order_attempt_count == 0
    assert _exchange_order_calls(transport) == []


def test_sandbox_testnet_endpoint_required_and_live_endpoint_blocks() -> None:
    transport = FakeUAT32Transport()
    env = _env()
    env[HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV] = "https://api.hyperliquid.xyz"
    result = asyncio.run(
        UAT32SecondSandboxOrderAttemptService(transport=transport).execute(
            approval_text=REQUIRED_UAT32_ACTUAL_SUBMISSION_APPROVAL_TEXT,
            env=env,
            prior_attempt_exists=False,
            now_utc=NOW,
        )
    )

    assert UAT32RejectReason.SANDBOX_ENDPOINT_REQUIRED in result.reason_codes
    assert result.lifecycle.order_attempt_count == 0
    assert transport.calls == []


def test_one_order_max_prior_attempt_blocks() -> None:
    transport = FakeUAT32Transport()
    result = asyncio.run(
        UAT32SecondSandboxOrderAttemptService(transport=transport).execute(
            approval_text=REQUIRED_UAT32_ACTUAL_SUBMISSION_APPROVAL_TEXT,
            env=_env(),
            prior_attempt_exists=True,
            now_utc=NOW,
        )
    )

    assert UAT32RejectReason.PRIOR_ATTEMPT_EXISTS in result.reason_codes
    assert result.lifecycle.order_attempt_count == 0
    assert transport.calls == []


def test_manual_lifecycle_probe_labels_are_required() -> None:
    labels = build_uat32_artifact_labels()
    assert validate_uat31_manual_probe_labels(labels).allowed is True

    missing = validate_uat31_manual_probe_labels(
        type(labels)(base=labels.base, not_strategy_signal=False)
    )
    assert "not_strategy_signal_label_missing_or_false" in missing.reason_codes


def test_order_transport_called_only_when_all_gates_pass_and_cancel_if_open() -> None:
    transport = FakeUAT32Transport()
    result = asyncio.run(
        UAT32SecondSandboxOrderAttemptService(transport=transport).execute(
            approval_text=REQUIRED_UAT32_ACTUAL_SUBMISSION_APPROVAL_TEXT,
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


def test_cancel_called_only_for_submitted_sandbox_order_if_open() -> None:
    transport = FakeUAT32Transport()
    result = asyncio.run(
        UAT32SecondSandboxOrderAttemptService(transport=transport).execute(
            approval_text=REQUIRED_UAT32_ACTUAL_SUBMISSION_APPROVAL_TEXT,
            env=_env(),
            prior_attempt_exists=False,
            now_utc=NOW,
        )
    )

    cancel_calls = [
        payload for path, payload in transport.calls if path == "/exchange" and payload["action"]["type"] == "cancel"
    ]
    assert result.lifecycle.exchange_order_id == "223456"
    assert len(cancel_calls) == 1
    assert cancel_calls[0]["action"]["cancels"][0]["o"] == 223456


def test_unexpected_fill_stops_without_second_order() -> None:
    transport = FakeUAT32Transport(
        order_response={
            "status": "ok",
            "response": {
                "type": "order",
                "data": {"statuses": [{"filled": {"oid": 777, "totalSz": "0.004"}}]},
            },
        }
    )
    result = asyncio.run(
        UAT32SecondSandboxOrderAttemptService(transport=transport).execute(
            approval_text=REQUIRED_UAT32_ACTUAL_SUBMISSION_APPROVAL_TEXT,
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


def test_stale_drawdown_blocks_before_order_call() -> None:
    feed = build_sandbox_account_drawdown_feed(
        snapshot=SandboxAccountStateSnapshot(
            venue="hyperliquid",
            sandbox_account_id=_env()[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV],
            timestamp_utc=NOW - timedelta(hours=1),
            sandbox_account_equity=Decimal("1000"),
            sandbox_realized_pnl=None,
            sandbox_unrealized_pnl=None,
            open_positions_summary=(),
            max_sandbox_equity=Decimal("1000"),
            min_sandbox_equity=Decimal("1000"),
            source="sandbox_account",
            not_live_account=True,
        ),
        drawdown_threshold=Decimal("0.05"),
        status=SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED,
    )
    readiness = evaluate_uat32_account_api_wallet_readiness(
        account_id=_env()[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV],
        signer=_env()[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV],
        account_role_payload={"role": "user"},
        signer_role_payload={"role": "user"},
        drawdown_feed=feed,
        requested_notional=Decimal("9.9"),
        now_utc=NOW,
    )

    assert readiness.allowed is False
    assert UAT32RejectReason.DRAWDOWN_FEED_STALE in readiness.reason_codes


def test_summary_redacts_secrets_and_preserves_boundaries() -> None:
    result = asyncio.run(
        UAT32SecondSandboxOrderAttemptService(transport=FakeUAT32Transport()).execute(
            approval_text=REQUIRED_UAT32_ACTUAL_SUBMISSION_APPROVAL_TEXT,
            env=_env(),
            prior_attempt_exists=False,
            now_utc=NOW,
        )
    )
    summary = result_to_uat32_summary_dict(result)

    assert summary["side_effect_flags"]["creates_order_intent"] is False
    assert summary["side_effect_flags"]["creates_prepared_order"] is False
    assert summary["side_effect_flags"]["creates_submitted_order"] is False
    assert summary["side_effect_flags"]["creates_executable_approval"] is False
    assert summary["sandbox_labels"]["manual_sandbox_lifecycle_probe"] is True
    assert summary["sandbox_labels"]["not_live"] is True
    assert summary["sandbox_labels"]["not_paper"] is True
    serialized = str(summary)
    assert _env()[HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV] not in serialized
    assert "'signature':" not in str(summary["sanitized_order_request"]).lower()


def test_uat32_report_exists_and_records_readiness_and_uat4_request() -> None:
    report = Path("docs/uat3_2_second_sandbox_order_attempt.md")
    assert report.exists()
    text = report.read_text()
    assert "UAT3.2 Second Sandbox Order Attempt" in text
    assert "Fixed-Key Account / API-Wallet Readiness" in text
    assert "UAT3.3" in text
    assert "UAT4.0 — Live UAT Trading Dashboard / Chart Cockpit" in text
