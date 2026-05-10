from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from core.config.settings import AppSettings
from core.security import REDACTED_VALUE, redact_sensitive_text
from services.exchange.aster.adapter import AsterExchangeAdapter
from services.exchange.base import VenueAdapterError
from services.exchange.hyperliquid.adapter import HyperliquidAdapterError, HyperliquidExchangeAdapter
from services.exchange.safety import (
    ExchangeEndpointCategory,
    HYPERLIQUID_UAT1_READ_ONLY_ALLOWLIST,
    classify_rest_endpoint,
)


class _CountingAsterTransport:
    def __init__(self) -> None:
        self.calls = 0

    async def __call__(self, method, path, params=None, body=None, headers=None):
        self.calls += 1
        return {"ok": True, "method": method, "path": path}


class _CountingHyperliquidTransport:
    def __init__(self) -> None:
        self.calls = 0

    async def __call__(self, payload):
        self.calls += 1
        return {"ok": True, "payload": payload}


def _safe_default_settings(**overrides: object) -> AppSettings:
    return AppSettings(
        _env_file=None,
        API_RUNTIME_MODE="development",
        ASTER_API_KEY="aster-key",
        ASTER_API_SECRET="aster-secret",
        EXCHANGE_ACCOUNT_ADDRESS="0xabc123",
        EXCHANGE_SIGNING_PRIVATE_KEY="0xabc",
        **overrides,
    )


def test_private_signed_adapter_request_is_blocked_before_transport() -> None:
    transport = _CountingAsterTransport()
    adapter = AsterExchangeAdapter(_safe_default_settings(), transport=transport)

    with pytest.raises(VenueAdapterError) as exc_info:
        asyncio.run(
            adapter._request(
                "GET",
                "/fapi/v2/balance",
                {"timestamp": 1, "signature": "abc123"},
                headers={"X-MBX-APIKEY": "aster-key"},
            )
        )

    assert transport.calls == 0
    assert "private_exchange_endpoints_disabled_by_runtime_policy" in exc_info.value.reason_codes


def test_order_adapter_request_is_blocked_before_transport() -> None:
    transport = _CountingAsterTransport()
    adapter = AsterExchangeAdapter(_safe_default_settings(), transport=transport)

    with pytest.raises(VenueAdapterError) as exc_info:
        asyncio.run(
            adapter._request_form_exact(
                "POST",
                "/fapi/v1/order",
                rendered_body="symbol=BTCUSDT&side=BUY",
                headers={"X-MBX-APIKEY": "aster-key"},
            )
        )

    assert transport.calls == 0
    assert "private_exchange_endpoints_disabled_by_runtime_policy" in exc_info.value.reason_codes
    assert "exchange_order_submission_disabled_by_runtime_policy" in exc_info.value.reason_codes


def test_public_read_only_adapter_request_is_classified_and_can_reach_fake_transport() -> None:
    transport = _CountingAsterTransport()
    adapter = AsterExchangeAdapter(_safe_default_settings(), transport=transport)

    result = asyncio.run(adapter._request("GET", "/fapi/v1/exchangeInfo", None))

    assert transport.calls == 1
    assert result["path"] == "/fapi/v1/exchangeInfo"
    assert (
        classify_rest_endpoint("GET", "/fapi/v1/exchangeInfo")
        == ExchangeEndpointCategory.PUBLIC_READ_ONLY
    )


def test_hyperliquid_private_info_request_is_blocked_before_transport() -> None:
    transport = _CountingHyperliquidTransport()
    adapter = HyperliquidExchangeAdapter(_safe_default_settings(), transport=transport)

    with pytest.raises(HyperliquidAdapterError) as exc_info:
        asyncio.run(adapter._info_request({"type": "userFills", "user": "0xabc123"}))

    assert transport.calls == 0
    assert "private_exchange_endpoints_disabled_by_runtime_policy" in exc_info.value.reason_codes


def test_hyperliquid_exchange_request_is_blocked_before_transport() -> None:
    transport = _CountingHyperliquidTransport()
    adapter = HyperliquidExchangeAdapter(_safe_default_settings(), transport=transport)

    with pytest.raises(HyperliquidAdapterError) as exc_info:
        asyncio.run(adapter._exchange_request({"action": {"type": "order"}}))

    assert transport.calls == 0
    assert "exchange_order_submission_disabled_by_runtime_policy" in exc_info.value.reason_codes


def test_hyperliquid_uat1_read_only_allowlist_exists_and_forbids_private_order_paths() -> None:
    policy = HYPERLIQUID_UAT1_READ_ONLY_ALLOWLIST

    assert policy.venue == "hyperliquid"
    assert policy.allowed_categories == (ExchangeEndpointCategory.PUBLIC_READ_ONLY,)
    assert ExchangeEndpointCategory.PRIVATE_READ_ONLY in policy.forbidden_categories
    assert ExchangeEndpointCategory.ORDER_SUBMISSION in policy.forbidden_categories
    assert policy.private_endpoint_status == "forbidden_in_uat1"
    assert policy.order_endpoint_status == "forbidden_in_uat1"


def test_redaction_helper_redacts_bearer_tokens_key_values_and_db_urls() -> None:
    raw = (
        "Authorization: Bearer abc123 api_key=key123 secret=sec123 password=pass123 "
        "postgresql+psycopg://user:dbpass@host:5432/money_flow"
    )

    redacted = redact_sensitive_text(raw)

    for secret in ("abc123", "key123", "sec123", "pass123", "dbpass"):
        assert secret not in redacted
    assert redacted.count(REDACTED_VALUE) >= 5


def test_uat02_report_records_policy_allowlist_redaction_and_readiness_truth() -> None:
    report = Path("docs/uat0_2_adapter_runtime_policy_and_redaction.md").read_text()

    assert "Adapter Safety Inventory" in report
    assert "Hyperliquid UAT1 Read-Only Allowlist" in report
    assert "`public_read_only`" in report
    assert "`private_read_only`" in report
    assert "`order_submission`" in report
    assert "Forbidden Endpoint Categories" in report
    assert "Redaction Verification Status" in report
    assert "`UAT1 is blocked`" in report
    assert "does not connect to exchanges" in report
    assert "does not submit orders" in report
    assert "Paper trading is not approved" in report
    assert "Live trading is not approved" in report
    forbidden = (
        "approved for paper trading",
        "ready for live trading",
        "proven profitable",
    )
    lower_report = report.lower()
    for phrase in forbidden:
        assert phrase not in lower_report
