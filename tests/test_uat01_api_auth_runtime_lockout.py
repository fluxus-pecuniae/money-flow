from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.app.dependencies import get_app_settings
from apps.api.app.main import app
from core.config.settings import AppSettings
from core.security import REDACTED_VALUE, redact_sensitive_structure


def _settings() -> AppSettings:
    return AppSettings(
        _env_file=None,
        API_RUNTIME_MODE="development",
        API_AUTH_DISABLED_FOR_TESTS=False,
        API_READ_ONLY_OPERATOR_TOKEN="read-token",
        API_OPERATOR_TOKEN="operator-token",
        API_ADMIN_TOKEN="admin-token",
        API_AUTOMATION_ADMIN_TOKEN="automation-token",
        API_UAT_ADMIN_TOKEN="uat-token",
    )


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_sensitive_v1_route_rejects_unauthenticated_access() -> None:
    app.dependency_overrides[get_app_settings] = _settings
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/submitted-orders")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401


def test_read_only_scope_cannot_use_admin_consume_or_submit_surfaces() -> None:
    app.dependency_overrides[get_app_settings] = _settings
    try:
        with TestClient(app) as client:
            consume_response = client.post(
                "/api/v1/routing-automation/approvals/approval-1/consume",
                json={"actor": "operator"},
                headers=_headers("read-token"),
            )
            submit_response = client.post(
                "/api/v1/child-intents/intent-1/submit",
                headers=_headers("read-token"),
            )
            cancel_response = client.post(
                "/api/v1/submitted-orders/submitted-1/cancel",
                headers=_headers("read-token"),
            )
    finally:
        app.dependency_overrides.clear()

    assert consume_response.status_code == 403
    assert submit_response.status_code == 403
    assert cancel_response.status_code == 403


def test_admin_consume_rejects_non_admin_operator_scope() -> None:
    app.dependency_overrides[get_app_settings] = _settings
    try:
        with TestClient(app) as client:
            operator_response = client.post(
                "/api/v1/routing-automation/approvals/approval-1/consume",
                json={"actor": "operator"},
                headers=_headers("operator-token"),
            )
    finally:
        app.dependency_overrides.clear()

    assert operator_response.status_code == 403


def test_account_and_private_exchange_surfaces_require_admin_scope() -> None:
    app.dependency_overrides[get_app_settings] = _settings
    try:
        with TestClient(app) as client:
            accounts_response = client.get("/api/v1/accounts", headers=_headers("read-token"))
            private_state_response = client.get(
                "/api/v1/venues/hyperliquid/private-state-summary",
                headers=_headers("read-token"),
            )
    finally:
        app.dependency_overrides.clear()

    assert accounts_response.status_code == 403
    assert private_state_response.status_code == 403


def test_test_auth_bypass_is_limited_to_test_runtime() -> None:
    def test_settings() -> AppSettings:
        return AppSettings(
            _env_file=None,
            API_RUNTIME_MODE="test",
            API_AUTH_DISABLED_FOR_TESTS=True,
        )

    def dev_settings() -> AppSettings:
        return AppSettings(
            _env_file=None,
            API_RUNTIME_MODE="development",
            API_AUTH_DISABLED_FOR_TESTS=True,
        )

    try:
        app.dependency_overrides[get_app_settings] = test_settings
        with TestClient(app) as client:
            test_response = client.get("/api/v1/config/summary")
        app.dependency_overrides[get_app_settings] = dev_settings
        with TestClient(app) as client:
            dev_response = client.get("/api/v1/config/summary")
    finally:
        app.dependency_overrides.clear()

    assert test_response.status_code == 200
    assert dev_response.status_code == 401


def test_runtime_safety_defaults_fail_closed() -> None:
    settings = AppSettings(_env_file=None, API_RUNTIME_MODE="development")

    assert settings.runtime_safety.paper_trading_enabled is False
    assert settings.runtime_safety.live_trading_enabled is False
    assert settings.runtime_safety.exchange_order_submission_enabled is False
    assert settings.runtime_safety.private_exchange_endpoints_enabled is False
    assert settings.runtime_safety.live_endpoint_lockout_enabled is True
    assert settings.runtime_safety.order_endpoint_lockout_enabled is True
    assert settings.runtime_safety.private_endpoint_lockout_enabled is True


def test_config_summary_exposes_lockout_truth_without_secrets() -> None:
    app.dependency_overrides[get_app_settings] = _settings
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/config/summary", headers=_headers("read-token"))
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert payload["api_auth_enabled"] is True
    assert payload["api_runtime_mode"] == "development"
    assert payload["paper_trading_enabled"] is False
    assert payload["live_trading_enabled"] is False
    assert payload["exchange_order_submission_enabled"] is False
    assert payload["private_exchange_endpoints_enabled"] is False
    assert payload["live_endpoint_lockout_enabled"] is True
    assert payload["order_endpoint_lockout_enabled"] is True
    assert "admin-token" not in str(payload)
    assert "read-token" not in str(payload)


def test_representative_secret_redaction() -> None:
    redacted = redact_sensitive_structure(
        {
            "api_key": "abc",
            "Authorization": "Bearer secret-token",
            "nested": {"db_password": "pass", "safe": "visible"},
            "url": "postgresql+psycopg://user:pass@localhost:5432/money_flow",
        }
    )

    assert redacted["api_key"] == REDACTED_VALUE
    assert redacted["Authorization"] == REDACTED_VALUE
    assert redacted["nested"]["db_password"] == REDACTED_VALUE
    assert redacted["nested"]["safe"] == "visible"
    assert "pass" not in redacted["url"]
    assert REDACTED_VALUE in redacted["url"]


def test_uat01_report_records_auth_runtime_and_readiness_truth() -> None:
    report = Path("docs/uat0_1_api_auth_runtime_lockout.md").read_text()

    assert "Sensitive Route Inventory" in report
    assert "`read_only_operator`" in report
    assert "`automation_admin` or `admin`" in report
    assert "Runtime Mode Policy" in report
    assert "`live_trading_enabled` | `false`" in report
    assert "`exchange_order_submission_enabled` | `false`" in report
    assert "`private_exchange_endpoints_enabled` | `false`" in report
    assert "API_RUNTIME_MODE=test" in report
    assert "`UAT1 is blocked`" in report
    assert "Paper trading is not approved" in report
    assert "Live trading is not approved" in report
    assert "Exchange order submission is not approved" in report
    forbidden = (
        "approved for paper trading",
        "ready for live trading",
        "proven profitable",
    )
    lower_report = report.lower()
    for phrase in forbidden:
        assert phrase not in lower_report
