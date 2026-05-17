"""Run PT-RT1 public-mainnet paper-observation readiness cycles.

The runner writes ignored runtime artifacts under ``reports/paper_runtime/``.
It uses only Hyperliquid public mainnet ``/info`` payloads for strategy truth.
PT-RT1.5 can submit/cancel/reconcile Hyperliquid testnet orders only from
scheduled Money Flow v1.2 baseline synthetic opens, with fixed 25 USDC notional
and a separate lifecycle ledger that never updates synthetic strategy PnL.
"""

from __future__ import annotations

import argparse
import os
import json
import sys
import time
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Protocol, Sequence

import httpx

from core.security import redact_sensitive_structure, redact_sensitive_text
from services.exchange.hyperliquid.signing import sign_l1_action, signer_address
from services.paper_runtime.hyperliquid_public_market_data import (
    HyperliquidPublicMarketDataConnector,
    candle_request_window,
    resolve_watchlist_from_public_data,
)
from services.paper_runtime.pt_rt1 import (
    PT_RT1_1B_RUNTIME_OUTPUT_PREFIX,
    PT_RT1_4_ACTIVE_TIMEFRAMES,
    PT_RT1_4_DISABLED_TIMEFRAME_STATUS,
    PT_RT1_4_DISABLED_TIMEFRAMES,
    PT_RT1_4_TIMEFRAME_REASON_CODES,
    PT_RT1_5_ACTIVE_REVIEW_START_UTC,
    PT_RT1_5_ACTIVE_TIMEFRAMES,
    PT_RT1_5_ARCHIVED_RUNTIME_SCOPES,
    PT_RT1_5_1_ACTIVE_REVIEW_START_UTC,
    PT_RT1_5_1_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
    PT_RT1_5_1_RUNTIME_OUTPUT_DIR,
    PT_RT1_5_1_RUNTIME_SCOPE,
    PT_RT1_5_2_ACTIVE_REVIEW_START_UTC,
    PT_RT1_5_2_EXACT_TESTNET_TRANSPORT_SMOKE_APPROVAL,
    PT_RT1_5_2_RUNTIME_OUTPUT_DIR,
    PT_RT1_5_2_RUNTIME_SCOPE,
    PT_RT1_5_2_TESTNET_SMOKE_PHASE_CAP,
    PT_RT1_5_2_TRANSPORT_SMOKE_OUTPUT_DIR,
    PT_RT1_5_2_TRANSPORT_SMOKE_SCOPE,
    PT_RT1_5_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
    PT_RT1_5_RUNTIME_OUTPUT_DIR,
    PT_RT1_5_RUNTIME_SCOPE,
    PT_RT1_5_TESTNET_DAILY_ORDER_CAP_DEFAULT,
    PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC,
    PT_RT1_5_TESTNET_PER_SYMBOL_DAILY_CAP_DEFAULT,
    PT_RT1_EXACT_TESTNET_PROBE_APPROVAL,
    PT_RT1_MAINNET_API_URL,
    PT_RT1_MAINNET_INFO_URL,
    PT_RT1_REQUESTED_SCANNER_SYMBOLS,
    PT_RT1_STRATEGY_LANES,
    PT_RT1_TESTNET_API_URL,
    PT_RT1_TESTNET_INFO_URL,
    PT_RT1_TESTNET_PROBE_NOTIONAL_CAP_USDC,
    PT_RT1_TESTNET_PROBE_NOTIONAL_USDC,
    TIMEFRAME_DURATIONS,
    DataHealth,
    PaperDecisionEvent,
    PT_RT15BaselineTestnetOrderPolicy,
    PT_RT15TestnetOrderCandidate,
    TestnetProbeCandidate,
    TestnetProbePolicy,
    build_pt_rt1_5_scheduler_status,
    build_pt_rt1_summary,
    canonical_candle_close,
    evaluate_paper_decision,
)
from services.uat.sandbox import (
    HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV,
    HYPERLIQUID_UAT_SANDBOX_ACCOUNT_IS_VAULT_ENV,
    HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ROLE_ENV,
    HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV,
    HYPERLIQUID_UAT_SANDBOX_MASTER_ACCOUNT_ENV,
    HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV,
    HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT_ENV,
    HYPERLIQUID_UAT_SANDBOX_VAULT_ADDRESS_ENV,
)


DEFAULT_OUTPUT_DIR = Path("reports/paper_runtime/pt_rt1_1b_smoke")
DECISION_LOG_MODES = ("compact", "full_audit", "signals_only")
ACTIONABLE_DECISION_ACTIONS = frozenset({"paper_opened", "paper_closed"})
COMPACT_ALWAYS_WRITE_ACTIONS = frozenset({"paper_opened", "paper_closed", "data_unavailable"})
DECISION_LOG_SIZE_WARNING_BYTES = 500 * 1024 * 1024
TESTNET_PROBE_AUDIT_LIMIT = 200
PT_RT1_2_EXACT_TRANSPORT_APPROVAL = (
    "I APPROVE PT-RT1.2 HYPERLIQUID TESTNET TRANSPORT PROBES ONLY. "
    "20 USDC MAX NOTIONAL. POST-ONLY ALO. SUBMIT CANCEL RECONCILE. "
    "TESTNET FILLS MUST NOT UPDATE STRATEGY PAPER PNL. LIVE TRADING IS NOT APPROVED."
)
PT_RT1_5_TESTNET_ORDER_TRANSPORT_KILL_SWITCH_ENV = "PT_RT_TESTNET_ORDER_TRANSPORT_KILL_SWITCH"
PT_RT1_5_2_DOTENV_KEYS = {
    HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV,
    HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV,
    HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT_ENV,
    HYPERLIQUID_UAT_SANDBOX_MASTER_ACCOUNT_ENV,
    HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV,
    HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ROLE_ENV,
    HYPERLIQUID_UAT_SANDBOX_ACCOUNT_IS_VAULT_ENV,
    HYPERLIQUID_UAT_SANDBOX_VAULT_ADDRESS_ENV,
    PT_RT1_5_TESTNET_ORDER_TRANSPORT_KILL_SWITCH_ENV,
}


class TestnetProbeTransport(Protocol):
    def __call__(self, order_shape: dict[str, Any], audit_row: dict[str, Any]) -> dict[str, Any]:
        """Submit/cancel/reconcile one testnet plumbing probe.

        Production runtime supplies no default signed transport here. Tests may
        inject a fake transport to verify lifecycle accounting without touching
        private/signed/order endpoints.
        """


class BaselineTestnetOrderTransport(Protocol):
    def __call__(self, order_shape: dict[str, Any], lifecycle_row: dict[str, Any]) -> dict[str, Any]:
        """Submit/cancel/reconcile one baseline-linked Hyperliquid testnet order."""


def _env_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on", "enabled", "active"}


def _abbrev_secretless(value: str | None) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    if len(text) <= 12:
        return "***"
    return f"{text[:6]}...{text[-4:]}"


def _load_scoped_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key not in PT_RT1_5_2_DOTENV_KEYS:
            continue
        values[key] = value.strip().strip('"').strip("'")
    return values


def _load_pt_rt1_5_2_env_file(path: Path) -> dict[str, Any]:
    values = _load_scoped_dotenv(path)
    loaded_keys: list[str] = []
    for key, value in values.items():
        if key not in os.environ and value:
            os.environ[key] = value
            loaded_keys.append(key)
    return {
        "env_file": str(path),
        "env_file_present": path.exists(),
        "loaded_key_names": sorted(loaded_keys),
        "loaded_secret_values_printed": False,
    }


def pt_rt1_5_2_signed_transport_env_status() -> dict[str, Any]:
    private_key = os.environ.get(HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV, "").strip()
    target_account = (
        os.environ.get(HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT_ENV, "").strip()
        or os.environ.get(HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV, "").strip()
        or os.environ.get(HYPERLIQUID_UAT_SANDBOX_MASTER_ACCOUNT_ENV, "").strip()
    )
    base_url = os.environ.get(HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV, PT_RT1_TESTNET_INFO_URL).strip()
    role = os.environ.get(HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ROLE_ENV, "user").strip().lower() or "user"
    is_vault = _env_truthy(os.environ.get(HYPERLIQUID_UAT_SANDBOX_ACCOUNT_IS_VAULT_ENV))
    vault_address = os.environ.get(HYPERLIQUID_UAT_SANDBOX_VAULT_ADDRESS_ENV, "").strip()
    reasons: list[str] = []
    signer_abbrev = None
    if not private_key:
        reasons.append("signed_testnet_private_key_missing")
    else:
        try:
            signer_abbrev = _abbrev_secretless(signer_address(private_key))
        except Exception:  # noqa: BLE001
            reasons.append("signed_testnet_private_key_invalid")
    if not target_account:
        reasons.append("signed_testnet_target_account_missing")
    normalized_base_url = base_url.rstrip("/")
    if normalized_base_url not in {PT_RT1_TESTNET_INFO_URL, PT_RT1_TESTNET_API_URL}:
        reasons.append("testnet_endpoint_required")
    if normalized_base_url in {PT_RT1_MAINNET_INFO_URL, PT_RT1_MAINNET_API_URL}:
        reasons.append("live_endpoint_forbidden")
    if role in {"subaccount", "vault"} or is_vault:
        if not vault_address:
            reasons.append("vault_address_required_for_subaccount_or_vault")
    elif vault_address:
        reasons.append("vault_address_forbidden_for_main_user")
    configured = not reasons and bool(private_key and target_account)
    return {
        "base_url_is_testnet": normalized_base_url in {PT_RT1_TESTNET_INFO_URL, PT_RT1_TESTNET_API_URL},
        "live_url_rejected": normalized_base_url not in {PT_RT1_MAINNET_INFO_URL, PT_RT1_MAINNET_API_URL},
        "private_key_present": bool(private_key),
        "private_key_printed": False,
        "target_account_abbrev": _abbrev_secretless(target_account),
        "signer_abbrev": signer_abbrev,
        "account_role": role,
        "signer_role": "local_env_signer" if private_key else "missing",
        "vaultAddress_present": bool(vault_address),
        "transport_client_configured": configured,
        "signed_testnet_transport_client_configured": configured,
        "reason_codes": reasons or ["signed_testnet_transport_client_configured"],
    }


class HyperliquidPT_RT15TestnetOrderTransport:
    """Path-scoped PT-RT1.5 Hyperliquid testnet transport.

    This is used only for baseline-linked plumbing lifecycle rows. Strategy
    truth remains public mainnet candles and synthetic PnL is never updated from
    the venue response.
    """

    def __init__(
        self,
        *,
        base_url: str,
        private_key: str,
        account_id: str,
        vault_address: str | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.private_key = private_key
        self.account_id = account_id.lower()
        self.vault_address = vault_address.lower() if vault_address else None
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "HyperliquidPT_RT15TestnetOrderTransport | None":
        private_key = os.environ.get(HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV, "").strip()
        account_id = (
            os.environ.get(HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT_ENV, "").strip()
            or os.environ.get(HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV, "").strip()
            or os.environ.get(HYPERLIQUID_UAT_SANDBOX_MASTER_ACCOUNT_ENV, "").strip()
        )
        if not private_key or not account_id:
            return None
        base_url = os.environ.get(HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV, PT_RT1_TESTNET_INFO_URL).strip()
        role = os.environ.get(HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ROLE_ENV, "user").strip().lower()
        is_vault = _env_truthy(os.environ.get(HYPERLIQUID_UAT_SANDBOX_ACCOUNT_IS_VAULT_ENV))
        vault_address = None
        if role in {"vault", "subaccount"} or is_vault:
            vault_address = os.environ.get(HYPERLIQUID_UAT_SANDBOX_VAULT_ADDRESS_ENV, "").strip() or None
        return cls(
            base_url=base_url,
            private_key=private_key,
            account_id=account_id,
            vault_address=vault_address,
        )

    def __call__(self, order_shape: dict[str, Any], lifecycle_row: dict[str, Any]) -> dict[str, Any]:
        if "api.hyperliquid-testnet.xyz" not in self.base_url:
            return {
                "status": "blocked",
                "order_endpoint_called": False,
                "signed_order_endpoint_called": False,
                "reason_codes": ["live_endpoint_forbidden"],
            }

        action = order_shape.get("action")
        if not isinstance(action, dict):
            return {
                "status": "blocked",
                "order_endpoint_called": False,
                "signed_order_endpoint_called": False,
                "reason_codes": ["testnet_order_shape_missing_action"],
            }

        lifecycle_path = ["created", "preflight_passed", "submitted"]
        order_payload = self._signed_payload(action)
        order_response: Any
        try:
            order_response = self._post_json("/exchange", order_payload)
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "unknown_state",
                "lifecycle_status_path": lifecycle_path,
                "order_endpoint_called": True,
                "signed_order_endpoint_called": True,
                "venue_order_id": None,
                "cancel_status": "not_attempted",
                "reconcile_status": "not_attempted",
                "venue_response": {"error": redact_sensitive_text(str(exc))},
                "reason_codes": ["testnet_order_transport_failed"],
                "testnet_fills_update_strategy_pnl": False,
            }

        order_status, oid, status_reasons = self._parse_order_response(order_response)
        if order_status == "open":
            lifecycle_path.append("accepted_open")
        elif order_status in {"filled", "partially_filled"}:
            lifecycle_path.append(order_status)
        elif order_status == "rejected":
            lifecycle_path.append("rejected")

        cancel_response: Any | None = None
        cancel_status = "not_required"
        cancel_called = False
        if order_status == "open" and oid is not None:
            lifecycle_path.append("cancel_requested")
            cancel_called = True
            asset_id = int(order_shape.get("asset_id") or 0)
            cancel_payload = self._signed_payload({"type": "cancel", "cancels": [{"a": asset_id, "o": int(oid)}]})
            try:
                cancel_response = self._post_json("/exchange", cancel_payload)
                cancel_status = "canceled" if self._action_ok(cancel_response) else "cancel_rejected"
                lifecycle_path.append(cancel_status)
            except Exception as exc:  # noqa: BLE001
                cancel_response = {"error": redact_sensitive_text(str(exc))}
                cancel_status = "cancel_unknown"
                status_reasons.append("testnet_order_cancel_transport_failed")
                lifecycle_path.append("unknown_state")

        reconcile_status = "not_attempted"
        open_order_remains = False
        reconciliation: dict[str, Any] = {}
        try:
            if oid is not None:
                reconciliation["order_status"] = self._post_json(
                    "/info",
                    {"type": "orderStatus", "user": self.account_id, "oid": int(oid)},
                )
            reconciliation["open_orders"] = self._post_json(
                "/info",
                {"type": "frontendOpenOrders", "user": self.account_id},
            )
            open_order_remains = self._open_order_remains(reconciliation.get("open_orders"), oid)
            reconcile_status = "open_order_remaining" if open_order_remains else "reconciled"
            lifecycle_path.append("reconciled")
        except Exception as exc:  # noqa: BLE001
            reconciliation["error"] = redact_sensitive_text(str(exc))
            reconcile_status = "unknown_state"
            status_reasons.append("testnet_order_reconcile_failed")
            lifecycle_path.append("unknown_state")

        final_status = "reconciled"
        if order_status == "rejected":
            final_status = "rejected"
        elif order_status == "filled":
            final_status = "filled"
        elif order_status == "partially_filled":
            final_status = "partially_filled"
        if open_order_remains or cancel_status == "cancel_unknown" or reconcile_status == "unknown_state":
            final_status = "unknown_state"

        return {
            "status": final_status,
            "lifecycle_status_path": lifecycle_path,
            "order_endpoint_called": True,
            "signed_order_endpoint_called": True,
            "cancel_endpoint_called": cancel_called,
            "venue_order_id": oid,
            "cancel_status": cancel_status,
            "reconcile_status": reconcile_status,
            "open_order_remains": open_order_remains,
            "venue_response": redact_sensitive_structure(order_response),
            "cancel_response": redact_sensitive_structure(cancel_response or {}),
            "reconciliation": redact_sensitive_structure(reconciliation),
            "reason_codes": list(dict.fromkeys(status_reasons or ["testnet_order_lifecycle_recorded"])),
            "testnet_fills_update_strategy_pnl": False,
            "strategy_pnl_updated_from_testnet": False,
        }

    def _signed_payload(self, action: dict[str, Any]) -> dict[str, Any]:
        nonce = int(time.time() * 1000)
        payload = {
            "action": action,
            "nonce": nonce,
            "signature": sign_l1_action(
                private_key=self.private_key,
                action=action,
                vault_address=self.vault_address,
                nonce=nonce,
                expires_after=None,
                is_mainnet=False,
            ),
            "expiresAfter": None,
        }
        # Hyperliquid main/user mode must omit vaultAddress.
        if self.vault_address:
            payload["vaultAddress"] = self.vault_address
        return payload

    def _post_json(self, path: str, payload: dict[str, Any]) -> Any:
        with httpx.Client(base_url=self.base_url, timeout=self.timeout_seconds) as client:
            response = client.post(path, json=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _parse_order_response(response: Any) -> tuple[str, str | None, list[str]]:
        if not isinstance(response, dict):
            return "unknown", None, ["testnet_order_response_shape_unknown"]
        if response.get("status") != "ok":
            return "rejected", None, ["testnet_order_rejected"]
        statuses = (((response.get("response") or {}).get("data") or {}).get("statuses") or [])
        first = statuses[0] if statuses else {}
        if isinstance(first, dict) and first.get("error") is not None:
            error_text = str(first.get("error"))
            mapped_reasons = ["testnet_order_rejected", error_text]
            lowered = error_text.lower()
            if "tick" in lowered or "price" in lowered:
                mapped_reasons.append("testnet_order_rejected_tick_size")
            if "size" in lowered or "lot" in lowered:
                mapped_reasons.append("testnet_order_rejected_lot_size")
            return "rejected", None, list(dict.fromkeys(mapped_reasons))
        if isinstance(first, dict) and isinstance(first.get("resting"), dict):
            return "open", str(first["resting"].get("oid")), ["testnet_order_accepted_open"]
        if isinstance(first, dict) and isinstance(first.get("filled"), dict):
            return "filled", str(first["filled"].get("oid")), ["testnet_order_unexpected_fill"]
        return "submitted", None, ["testnet_order_submitted_status_unclassified"]

    @staticmethod
    def _action_ok(response: Any) -> bool:
        if not isinstance(response, dict) or response.get("status") != "ok":
            return False
        statuses = (((response.get("response") or {}).get("data") or {}).get("statuses") or [])
        return not any(isinstance(item, dict) and item.get("error") for item in statuses)

    @staticmethod
    def _open_order_remains(open_orders_payload: Any, oid: str | None) -> bool:
        if oid is None or not isinstance(open_orders_payload, list):
            return False
        return any(isinstance(item, dict) and str(item.get("oid")) == str(oid) for item in open_orders_payload)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return _iso(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return value


def _ensure_ignored_output_dir(path: Path) -> None:
    normalized = Path(path)
    try:
        normalized.relative_to(PT_RT1_1B_RUNTIME_OUTPUT_PREFIX)
    except ValueError as exc:
        raise SystemExit("output_directory_not_under_ignored_reports_paper_runtime") from exc
    normalized.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(_json_safe(row), sort_keys=True) + "\n")


def _read_state(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {"state_status": "invalid_json"}
    return payload if isinstance(payload, dict) else {"state_status": "invalid_shape"}


def _lane_key(lane_id: str, symbol: str, timeframe: str) -> str:
    return f"{lane_id}|{symbol.upper()}|{timeframe}"


def _paper_signal_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("lane_id") or ""),
            str(row.get("strategy_id") or ""),
            str(row.get("symbol") or "").upper(),
            str(row.get("timeframe") or ""),
            str(row.get("signal_candle_close_time") or ""),
            "entry",
        ]
    )


def _dec(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return default


def _parse_iso_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _load_paper_runtime_state(prior_state: dict[str, Any]) -> dict[str, Any]:
    runtime = prior_state.get("paper_runtime") if isinstance(prior_state, dict) else None
    if not isinstance(runtime, dict):
        runtime = {}
    processed = runtime.get("processed_signal_keys")
    if not isinstance(processed, list):
        processed = []
    open_positions = runtime.get("open_positions_by_key")
    if not isinstance(open_positions, dict):
        open_positions = {}
    realized = runtime.get("realized_equity_by_lane")
    if not isinstance(realized, dict):
        realized = {}
    warm_start = runtime.get("warm_start_entry_context_by_key")
    if not isinstance(warm_start, dict):
        warm_start = {}
    unrealized = runtime.get("unrealized_pnl_by_lane")
    if not isinstance(unrealized, dict):
        unrealized = {}
    return {
        "runtime_start_utc": str(runtime.get("runtime_start_utc") or ""),
        "fresh_signal_only_after_runtime_start": bool(runtime.get("fresh_signal_only_after_runtime_start", False)),
        "warm_start_evaluation_completed": bool(runtime.get("warm_start_evaluation_completed", False)),
        "warm_start_entry_context_by_key": {
            str(key): value for key, value in warm_start.items() if isinstance(value, dict)
        },
        "startup_valid_signals_blocked_total": int(runtime.get("startup_valid_signals_blocked_total") or 0),
        "waiting_for_reset_signals_total": int(runtime.get("waiting_for_reset_signals_total") or 0),
        "fresh_post_start_opens_total": int(runtime.get("fresh_post_start_opens_total") or 0),
        "entry_context_resets_total": int(runtime.get("entry_context_resets_total") or 0),
        "processed_signal_keys": set(str(item) for item in processed),
        "open_positions_by_key": {
            str(key): value for key, value in open_positions.items() if isinstance(value, dict)
        },
        "realized_equity_by_lane": {
            str(key): str(value) for key, value in realized.items()
        },
        "unrealized_pnl_by_lane": {
            str(key): str(value) for key, value in unrealized.items()
        },
        "paper_opens_total": int(runtime.get("paper_opens_total") or 0),
        "paper_closes_total": int(runtime.get("paper_closes_total") or 0),
        "duplicate_signal_blocks_total": int(runtime.get("duplicate_signal_blocks_total") or 0),
        "last_processed_close_by_key": dict(runtime.get("last_processed_close_by_key") or {}),
        "last_evaluated_closed_candle_by_timeframe": dict(runtime.get("last_evaluated_closed_candle_by_timeframe") or {}),
        "testnet_order_keys": set(str(item) for item in runtime.get("testnet_order_keys") or []),
        "testnet_orders_total": int(runtime.get("testnet_orders_total") or 0),
    }


def _paper_runtime_state_payload(
    *,
    runtime_start_utc: str,
    fresh_signal_only_after_runtime_start: bool,
    warm_start_evaluation_completed: bool,
    warm_start_entry_context_by_key: dict[str, dict[str, Any]],
    startup_valid_signals_blocked_total: int,
    waiting_for_reset_signals_total: int,
    fresh_post_start_opens_total: int,
    entry_context_resets_total: int,
    processed_signal_keys: set[str],
    open_positions_by_key: dict[str, dict[str, Any]],
    realized_equity_by_lane: dict[str, str],
    unrealized_pnl_by_lane: dict[str, str],
    last_processed_close_by_key: dict[str, str],
    paper_opens_total: int,
    paper_closes_total: int,
    duplicate_signal_blocks_total: int,
    last_evaluated_closed_candle_by_timeframe: dict[str, str] | None = None,
    testnet_order_keys: set[str] | None = None,
    testnet_orders_total: int = 0,
) -> dict[str, Any]:
    return {
        "runtime_start_utc": runtime_start_utc,
        "fresh_signal_only_after_runtime_start": fresh_signal_only_after_runtime_start,
        "warm_start_evaluation_completed": warm_start_evaluation_completed,
        "warm_start_entry_context_by_key": warm_start_entry_context_by_key,
        "startup_valid_signals_blocked_total": startup_valid_signals_blocked_total,
        "waiting_for_reset_signals_total": waiting_for_reset_signals_total,
        "fresh_post_start_opens_total": fresh_post_start_opens_total,
        "entry_context_resets_total": entry_context_resets_total,
        "processed_signal_keys": sorted(processed_signal_keys),
        "open_positions_by_key": open_positions_by_key,
        "realized_equity_by_lane": realized_equity_by_lane,
        "unrealized_pnl_by_lane": unrealized_pnl_by_lane,
        "last_processed_close_by_key": last_processed_close_by_key,
        "last_evaluated_closed_candle_by_timeframe": dict(last_evaluated_closed_candle_by_timeframe or {}),
        "testnet_order_keys": sorted(testnet_order_keys or set()),
        "testnet_orders_total": testnet_orders_total,
        "paper_opens_total": paper_opens_total,
        "paper_closes_total": paper_closes_total,
        "duplicate_signal_blocks_total": duplicate_signal_blocks_total,
        "open_positions_count": len(open_positions_by_key),
    }


def _blocked_duplicate_row(row: dict[str, Any]) -> dict[str, Any]:
    reasons = list(row.get("reason_codes") or [])
    reasons.extend(["duplicate_signal_ignored", "existing_same_candle_signal_blocked"])
    return {
        **row,
        "action": "paper_hold",
        "position_after": row.get("position_before") or "flat",
        "reason_codes": list(dict.fromkeys(str(reason) for reason in reasons)),
        "paper_state_transition": "duplicate_open_blocked",
    }


def _open_position_from_decision(
    *,
    row: dict[str, Any],
    candle: Any,
    equity_before: Decimal,
) -> dict[str, Any]:
    fill_price = candle.close
    fee = equity_before * Decimal("5") / Decimal("10000")
    quantity = (equity_before - fee) / fill_price if fill_price > 0 else Decimal("0")
    return {
        "lane_id": row.get("lane_id"),
        "strategy_id": row.get("strategy_id"),
        "symbol": str(row.get("symbol") or "").upper(),
        "timeframe": row.get("timeframe"),
        "side": "long",
        "entry_signal_time": row.get("signal_candle_close_time"),
        "entry_fill_time": row.get("signal_candle_close_time"),
        "entry_price": str(fill_price),
        "quantity": str(quantity),
        "notional": str(equity_before),
        "fees": str(fee),
        "slippage": "0",
        "equity_before": str(equity_before),
        "open_reason_codes": list(row.get("reason_codes") or []),
        "status": "open",
        "current_price": None,
        "current_price_source": None,
        "current_price_time": None,
        "current_unrealized_pnl": None,
        "current_unrealized_pnl_pct": None,
        "position_notional": str(equity_before),
        "total_equity_impact": None,
        "mtm_reason_codes": ["mtm_price_unavailable"],
    }


def _warm_start_context_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("lane_id") or ""),
            str(row.get("strategy_id") or ""),
            str(row.get("symbol") or "").upper(),
            str(row.get("timeframe") or ""),
        ]
    )


def _block_open_for_warm_start(row: dict[str, Any], extra_reasons: Sequence[str]) -> dict[str, Any]:
    reasons = list(row.get("reason_codes") or [])
    reasons.extend(extra_reasons)
    return {
        **row,
        "action": "no_trade",
        "position_after": row.get("position_before") or "flat",
        "fresh_signal_after_runtime_start": False,
        "warm_start_signal_blocked": True,
        "paper_state_transition": "warm_start_open_blocked",
        "testnet_transport_blocked_reason": "testnet_order_requires_fresh_post_start_signal",
        "reason_codes": list(dict.fromkeys(str(reason) for reason in reasons)),
    }


def _apply_warm_start_signal_gate(
    *,
    decision_rows: Sequence[dict[str, Any]],
    warm_start_state: dict[str, dict[str, Any]],
    runtime_start_utc: str,
    warm_start_evaluation: bool,
    fresh_signal_only_after_runtime_start: bool,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    if not fresh_signal_only_after_runtime_start:
        return list(decision_rows), warm_start_state, {
            "enabled": False,
            "startup_valid_signals_blocked_this_cycle": 0,
            "waiting_for_reset_signals_this_cycle": 0,
            "fresh_post_start_opens_this_cycle": 0,
            "entry_context_resets_this_cycle": 0,
        }

    start_dt = _parse_iso_utc(runtime_start_utc) or _utc_now()
    next_state = {key: dict(value) for key, value in warm_start_state.items()}
    gated_rows: list[dict[str, Any]] = []
    startup_blocked = 0
    waiting_for_reset = 0
    fresh_opens = 0
    resets = 0

    for row in decision_rows:
        key = _warm_start_context_key(row)
        action = str(row.get("action") or "")
        entry_true = action == "paper_opened"
        signal_close = _parse_iso_utc(row.get("signal_candle_close_time"))
        context = next_state.get(
            key,
            {
                "initialized": False,
                "was_true": False,
                "already_true_at_runtime_start": False,
                "reset_observed": True,
            },
        )

        if not context.get("initialized") or warm_start_evaluation:
            context = {
                **context,
                "initialized": True,
                "was_true": entry_true,
                "already_true_at_runtime_start": entry_true,
                "reset_observed": not entry_true,
                "runtime_start_utc": runtime_start_utc,
                "last_observed_signal_candle_close_time": row.get("signal_candle_close_time"),
            }
            next_state[key] = context
            if entry_true:
                startup_blocked += 1
                gated_rows.append(
                    _block_open_for_warm_start(
                        row,
                        [
                            "warm_start_evaluation_completed",
                            "entry_context_already_true_at_runtime_start",
                            "signal_good_but_runtime_started_after_setup",
                            "warm_start_blocked_late_entry",
                        ],
                    )
                )
                continue
            reasons = list(row.get("reason_codes") or [])
            reasons.append("warm_start_evaluation_completed")
            gated_rows.append({**row, "reason_codes": list(dict.fromkeys(reasons))})
            continue

        if entry_true:
            signal_is_after_start = signal_close is not None and signal_close > start_dt
            if context.get("already_true_at_runtime_start") and not context.get("reset_observed"):
                context["was_true"] = True
                context["last_observed_signal_candle_close_time"] = row.get("signal_candle_close_time")
                next_state[key] = context
                waiting_for_reset += 1
                gated_rows.append(
                    _block_open_for_warm_start(
                        row,
                        [
                            "entry_context_already_true_waiting_for_reset",
                            "warm_start_blocked_late_entry",
                        ],
                    )
                )
                continue
            if context.get("was_true"):
                context["last_observed_signal_candle_close_time"] = row.get("signal_candle_close_time")
                next_state[key] = context
                waiting_for_reset += 1
                gated_rows.append(
                    _block_open_for_warm_start(
                        row,
                        [
                            "entry_context_already_true_waiting_for_reset",
                            "warm_start_blocked_late_entry",
                        ],
                    )
                )
                continue
            if not signal_is_after_start:
                context["was_true"] = True
                context["last_observed_signal_candle_close_time"] = row.get("signal_candle_close_time")
                next_state[key] = context
                startup_blocked += 1
                gated_rows.append(
                    _block_open_for_warm_start(
                        row,
                        [
                            "signal_good_but_runtime_started_after_setup",
                            "warm_start_blocked_late_entry",
                        ],
                    )
                )
                continue
            context["was_true"] = True
            context["reset_observed"] = True
            context["last_observed_signal_candle_close_time"] = row.get("signal_candle_close_time")
            next_state[key] = context
            reasons = list(row.get("reason_codes") or [])
            reasons.append("fresh_entry_signal_after_runtime_start")
            fresh_opens += 1
            gated_rows.append(
                {
                    **row,
                    "fresh_signal_after_runtime_start": True,
                    "warm_start_signal_blocked": False,
                    "reason_codes": list(dict.fromkeys(str(reason) for reason in reasons)),
                }
            )
            continue

        if context.get("was_true"):
            resets += 1
            reasons = list(row.get("reason_codes") or [])
            reasons.append("entry_context_reset_observed")
            row = {**row, "reason_codes": list(dict.fromkeys(str(reason) for reason in reasons))}
        context["was_true"] = False
        context["reset_observed"] = True
        context["last_observed_signal_candle_close_time"] = row.get("signal_candle_close_time")
        next_state[key] = context
        gated_rows.append(row)

    return gated_rows, next_state, {
        "enabled": True,
        "runtime_start_utc": runtime_start_utc,
        "warm_start_evaluation_this_cycle": warm_start_evaluation,
        "fresh_signal_only_after_runtime_start": True,
        "startup_valid_signals_blocked_this_cycle": startup_blocked,
        "waiting_for_reset_signals_this_cycle": waiting_for_reset,
        "fresh_post_start_opens_this_cycle": fresh_opens,
        "entry_context_resets_this_cycle": resets,
        "reason_codes": [
            "warm_start_evaluation_completed",
            "signal_good_but_runtime_started_after_setup",
            "entry_context_already_true_waiting_for_reset",
            "fresh_entry_signal_after_runtime_start",
        ],
    }


def _close_position_from_decision(
    *,
    row: dict[str, Any],
    position: dict[str, Any],
    candle: Any,
) -> tuple[dict[str, Any], Decimal]:
    entry_price = _dec(position.get("entry_price"))
    quantity = _dec(position.get("quantity"))
    equity_before = _dec(position.get("equity_before"), Decimal("10000"))
    entry_fees = _dec(position.get("fees"))
    exit_price = candle.close
    gross = (exit_price - entry_price) * quantity
    exit_fee = (exit_price * quantity) * Decimal("5") / Decimal("10000")
    net_pnl = gross - entry_fees - exit_fee
    equity_after = equity_before + net_pnl
    trade = {
        "paper_trade_id": f"pt_rt1_trade_{row.get('lane_id')}_{row.get('symbol')}_{row.get('timeframe')}_{row.get('signal_candle_close_time')}",
        "lane_id": row.get("lane_id"),
        "strategy_id": row.get("strategy_id"),
        "symbol": str(row.get("symbol") or "").upper(),
        "timeframe": row.get("timeframe"),
        "entry_time": position.get("entry_fill_time"),
        "exit_time": row.get("signal_candle_close_time"),
        "entry_price": str(entry_price),
        "exit_price": str(exit_price),
        "quantity": str(quantity),
        "gross_pnl": str(gross),
        "fees": str(entry_fees + exit_fee),
        "slippage": "0",
        "net_pnl": str(net_pnl),
        "equity_before": str(equity_before),
        "equity_after": str(equity_after),
        "entry_reason_codes": list(position.get("open_reason_codes") or []),
        "exit_reason_codes": list(row.get("reason_codes") or []),
        "paper_pnl_source": "synthetic_public_mainnet_paper_ledger",
        "testnet_fills_update_strategy_pnl": False,
    }
    return trade, equity_after


def _update_open_position_mtm(
    *,
    open_positions_by_key: dict[str, dict[str, Any]],
    scanner_rows: Sequence[Any],
    latest_closed_by_key: dict[tuple[str, str], Any],
    now: datetime,
) -> tuple[dict[str, str], dict[str, Any]]:
    mids_by_symbol: dict[str, Decimal] = {}
    for row in scanner_rows:
        symbol = str(getattr(row, "canonical_symbol", None) or getattr(row, "requested_symbol", "")).upper()
        mid = _dec(getattr(row, "public_mid", None), Decimal("0"))
        if symbol and mid > 0:
            mids_by_symbol[symbol] = mid

    unrealized_by_lane: dict[str, Decimal] = {}
    updated = 0
    unavailable = 0
    for position in open_positions_by_key.values():
        lane_id = str(position.get("lane_id") or "")
        symbol = str(position.get("symbol") or "").upper()
        timeframe = str(position.get("timeframe") or "")
        entry_price = _dec(position.get("entry_price"), Decimal("0"))
        quantity = _dec(position.get("quantity"), Decimal("0"))
        price: Decimal | None = mids_by_symbol.get(symbol)
        source = "public_mainnet_mid"
        source_time = _iso(now)
        reasons = ["mtm_source_public_mainnet_mid"]
        if price is None:
            candle = latest_closed_by_key.get((symbol, timeframe))
            if candle is not None:
                price = candle.close
                source = "latest_closed_candle"
                source_time = _iso(candle.close_time or canonical_candle_close(candle))
                reasons = ["mtm_source_latest_closed_candle"]
        if price is None or price <= 0 or entry_price <= 0 or quantity <= 0:
            unavailable += 1
            position.update(
                {
                    "current_price": None,
                    "current_price_source": None,
                    "current_price_time": None,
                    "current_unrealized_pnl": None,
                    "current_unrealized_pnl_pct": None,
                    "total_equity_impact": None,
                    "mtm_reason_codes": ["mtm_price_unavailable"],
                }
            )
            continue
        unrealized = (price - entry_price) * quantity
        notional = entry_price * quantity
        unrealized_pct = (unrealized / notional * Decimal("100")) if notional else Decimal("0")
        unrealized_by_lane[lane_id] = unrealized_by_lane.get(lane_id, Decimal("0")) + unrealized
        position.update(
            {
                "current_price": str(price),
                "current_price_source": source,
                "current_price_time": source_time,
                "current_unrealized_pnl": str(unrealized),
                "current_unrealized_pnl_pct": str(unrealized_pct),
                "position_notional": str(notional),
                "total_equity_impact": str(unrealized),
                "mtm_reason_codes": list(dict.fromkeys([*reasons, "mtm_unrealized_pnl_updated"])),
            }
        )
        updated += 1

    return {lane_id: str(value) for lane_id, value in unrealized_by_lane.items()}, {
        "open_positions_checked": len(open_positions_by_key),
        "open_positions_mtm_updated": updated,
        "open_positions_mtm_unavailable": unavailable,
        "preferred_source": "public_mainnet_allMids",
        "fallback_source": "latest_closed_public_mainnet_candle_close",
        "market_refresh_updates_mtm_without_signal_evaluation": True,
        "reason_codes": [
            "mtm_source_public_mainnet_mid",
            "mtm_source_latest_closed_candle",
            "mtm_price_unavailable",
            "mtm_unrealized_pnl_updated",
        ],
    }


def _summarize_data_unavailable(
    *,
    market_health: Sequence[dict[str, Any]],
    decision_rows: Sequence[dict[str, Any]],
    scanner_rows: Sequence[Any] = (),
) -> dict[str, Any]:
    market_rows = [
        row
        for row in market_health
        if row.get("strategy_data_status") == "candle_unavailable_blocking"
        or row.get("fully_closed_candle_status") != "closed_candle_ready"
    ]
    mid_warning_rows = [
        row
        for row in market_health
        if row.get("mid_health_status") in {"mid_warning_non_blocking", "mid_unavailable_but_candles_available"}
    ]
    decision_unavailable = [row for row in decision_rows if row.get("action") == "data_unavailable"]
    indicator_unavailable = [
        row
        for row in decision_unavailable
        if {"missing_indicator_field", "insufficient_history"} & set(str(reason) for reason in row.get("reason_codes") or [])
    ]
    scanner_blocked = [row for row in scanner_rows if getattr(row, "blocked", False)]

    def rollup(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        buckets: dict[tuple[str, str, str], int] = {}
        for row in rows:
            symbol = str(row.get("symbol") or row.get("requested_symbol") or "").upper()
            timeframe = str(row.get("timeframe") or "")
            reasons = row.get("reason_codes") or ["unknown"]
            primary_reason = str(reasons[0] if isinstance(reasons, list) and reasons else "unknown")
            buckets[(symbol, timeframe, primary_reason)] = buckets.get((symbol, timeframe, primary_reason), 0) + 1
        return [
            {"symbol": symbol, "timeframe": timeframe, "reason": reason, "count": count}
            for (symbol, timeframe, reason), count in sorted(buckets.items())
        ]

    return {
        "market_rows_checked": len(market_health),
        "market_rows_unavailable": len(market_rows),
        "scanner_identity_blocked": len(scanner_blocked),
        "mid_warning_non_blocking": len(mid_warning_rows),
        "market_rows_with_mid_warnings": len(mid_warning_rows),
        "candle_unavailable_blocking": len(market_rows),
        "indicator_unavailable_blocking": len(indicator_unavailable),
        "lane_expanded_data_unavailable_decisions": len(decision_unavailable),
        "lane_expansion_note": (
            "One blocking candle or indicator row can expand into one data_unavailable decision per strategy lane. "
            "Missing or stale mids are warning-only when closed candles are available."
        ),
        "market_unavailable_rollup": rollup(market_rows),
        "mid_warning_rollup": rollup(mid_warning_rows),
        "lane_decision_unavailable_rollup": rollup(decision_unavailable),
    }


def _decision_log_key(row: dict[str, Any]) -> str:
    reasons = ",".join(str(item) for item in row.get("reason_codes") or ())
    return "|".join(
        str(row.get(field) or "")
        for field in (
            "lane_id",
            "symbol",
            "timeframe",
            "signal_candle_close_time",
            "action",
        )
    ) + f"|{reasons}"


def _select_decision_log_rows(
    decision_rows: Sequence[dict[str, Any]],
    *,
    mode: str,
    seen_keys: set[str] | None = None,
) -> tuple[list[dict[str, Any]], set[str], dict[str, Any]]:
    if mode not in DECISION_LOG_MODES:
        raise ValueError(f"unsupported_decision_log_mode:{mode}")
    seen = set(seen_keys or set())
    selected: list[dict[str, Any]] = []

    for row in decision_rows:
        action = str(row.get("action") or "")
        if mode == "full_audit":
            selected.append(row)
            continue
        if mode == "signals_only":
            if action in ACTIONABLE_DECISION_ACTIONS:
                selected.append(row)
            continue
        if action in COMPACT_ALWAYS_WRITE_ACTIONS:
            selected.append(row)
            continue
        key = _decision_log_key(row)
        if key not in seen:
            selected.append(row)
            seen.add(key)

    suppressed = max(len(decision_rows) - len(selected), 0)
    stats = {
        "mode": mode,
        "evaluated_decisions_this_cycle": len(decision_rows),
        "written_decisions_this_cycle": len(selected),
        "suppressed_decisions_this_cycle": suppressed,
        "suppression_reason": (
            "none_full_audit"
            if mode == "full_audit"
            else "only_actionable_signals_written"
            if mode == "signals_only"
            else "repeated_non_actionable_decisions_suppressed"
        ),
    }
    return selected, seen, stats


def _filter_scanner_rows(rows: Sequence[Any], symbols: Sequence[str] | None, max_candle_symbols: int | None) -> list[Any]:
    selected = []
    requested = {item.upper() for item in symbols or ()}
    for row in rows:
        candidates = {row.requested_symbol.upper(), str(row.resolved_venue_symbol or "").upper(), str(row.canonical_symbol or "").upper()}
        if requested and not (requested & candidates):
            continue
        if row.scanner_eligible and not row.blocked:
            selected.append(row)
    if max_candle_symbols is not None:
        return selected[:max_candle_symbols]
    return selected


def _closed_prefix(candles: Sequence[Any], now: datetime) -> list[Any]:
    closed = [candle for candle in candles if canonical_candle_close(candle) <= now]
    return closed


def _testnet_probe_price(candle: Any) -> Decimal:
    # Buy-side post-only plumbing probes are kept below the latest public close so
    # they validate shape/precision without trying to become marketable.
    return (candle.close * Decimal("0.95")).quantize(Decimal("0.00000001"))


def _build_testnet_probe_audit_rows(
    *,
    decision_rows: Sequence[dict[str, Any]],
    scanner_rows: Sequence[Any],
    latest_closed_by_key: dict[tuple[str, str], Any],
    enabled: bool,
    approval_text: str,
    notional_usdc: Decimal,
    daily_cap: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    row_by_symbol = {
        str(row.canonical_symbol or row.requested_symbol).upper(): row
        for row in scanner_rows
        if row.scanner_eligible and not row.blocked
    }
    policy = TestnetProbePolicy()
    audit_rows: list[dict[str, Any]] = []
    actionable = [row for row in decision_rows if row.get("action") == "paper_opened"]
    for index, decision in enumerate(actionable[:TESTNET_PROBE_AUDIT_LIMIT]):
        symbol = str(decision.get("symbol") or "").upper()
        timeframe = str(decision.get("timeframe") or "")
        scanner_row = row_by_symbol.get(symbol)
        candle = latest_closed_by_key.get((symbol, timeframe))
        if scanner_row is None or candle is None:
            audit_rows.append(
                {
                    "lane": "testnet_plumbing_probe",
                    "environment": "hyperliquid_testnet_only",
                    "eligible": False,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "strategy_id": decision.get("strategy_id"),
                    "signal_candle_close_time": decision.get("signal_candle_close_time"),
                    "notional_usdc": str(notional_usdc),
                    "reason_codes": ["testnet_probe_context_unavailable"],
                    "testnet_fills_update_strategy_pnl": False,
                    "strategy_pnl_updated": False,
                    "signed_order_endpoint_called": False,
                    "order_endpoint_called": False,
                    "order_shape": None,
                }
            )
            continue
        price = _testnet_probe_price(candle)
        quantity = notional_usdc / price
        result = policy.evaluate(
            TestnetProbeCandidate(
                approval_text=approval_text,
                probes_enabled=enabled,
                kill_switch=not enabled,
                symbol=str(scanner_row.resolved_venue_symbol or symbol),
                asset_id=scanner_row.asset_id,
                sz_decimals=scanner_row.szDecimals,
                price=price,
                quantity=quantity,
                notional=notional_usdc,
                scanner_signal_eligible=True,
                daily_probe_count=index,
                daily_cap=daily_cap,
                notional_cap=PT_RT1_TESTNET_PROBE_NOTIONAL_CAP_USDC,
                precision_ready=bool(scanner_row.precision_ready),
                scanner_symbol_blocked=bool(scanner_row.blocked),
                unit_semantics_deferred=any("unit_semantics" in reason for reason in scanner_row.reason_codes),
            )
        )
        audit_rows.append(
            {
                **result.audit_row,
                "symbol": symbol,
                "venue_symbol": scanner_row.resolved_venue_symbol,
                "timeframe": timeframe,
                "strategy_id": decision.get("strategy_id"),
                "lane_id": decision.get("lane_id"),
                "signal_candle_close_time": decision.get("signal_candle_close_time"),
                "probe_price": str(price),
                "probe_quantity": str(quantity),
                "order_shape": result.order_shape,
            }
        )
    stats = {
        "enabled": enabled,
        "notional_usdc": str(notional_usdc),
        "notional_cap_usdc": str(PT_RT1_TESTNET_PROBE_NOTIONAL_CAP_USDC),
        "daily_cap": daily_cap,
        "signals_seen_this_cycle": len(actionable),
        "audit_rows_this_cycle": len(audit_rows),
        "eligible_probe_shapes_this_cycle": sum(1 for row in audit_rows if row.get("eligible") is True),
        "signed_order_endpoint_called": False,
        "order_endpoint_called": False,
        "testnet_fills_update_strategy_pnl": False,
        "transport_status": "not_submitted_by_pt_rt1_runtime",
    }
    return audit_rows, stats


def _apply_testnet_probe_transport(
    *,
    audit_rows: Sequence[dict[str, Any]],
    submit_enabled: bool,
    transport_approval_text: str,
    notional_usdc: Decimal,
    transport: TestnetProbeTransport | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    lifecycle_rows: list[dict[str, Any]] = []
    eligible_rows = [row for row in audit_rows if row.get("eligible") is True and row.get("order_shape")]
    if not submit_enabled:
        return lifecycle_rows, {
            "transport_mode": "audit_only",
            "transport_status": "audit_only_not_submitted",
            "submitted_this_cycle": 0,
            "cancel_attempted_this_cycle": 0,
            "reconciled_this_cycle": 0,
            "order_endpoint_called": False,
            "signed_order_endpoint_called": False,
            "testnet_fills_update_strategy_pnl": False,
            "strategy_pnl_updated": False,
            "reason_codes": ["testnet_probe_transport_not_requested"],
        }
    if transport_approval_text != PT_RT1_2_EXACT_TRANSPORT_APPROVAL:
        return lifecycle_rows, {
            "transport_mode": "submit_requested",
            "transport_status": "blocked_transport_approval_missing",
            "submitted_this_cycle": 0,
            "cancel_attempted_this_cycle": 0,
            "reconciled_this_cycle": 0,
            "order_endpoint_called": False,
            "signed_order_endpoint_called": False,
            "testnet_fills_update_strategy_pnl": False,
            "strategy_pnl_updated": False,
            "reason_codes": ["pt_rt1_2_exact_transport_approval_required"],
        }
    if notional_usdc != PT_RT1_TESTNET_PROBE_NOTIONAL_USDC:
        return lifecycle_rows, {
            "transport_mode": "submit_requested",
            "transport_status": "blocked_notional_not_20usdc",
            "submitted_this_cycle": 0,
            "cancel_attempted_this_cycle": 0,
            "reconciled_this_cycle": 0,
            "order_endpoint_called": False,
            "signed_order_endpoint_called": False,
            "testnet_fills_update_strategy_pnl": False,
            "strategy_pnl_updated": False,
            "reason_codes": ["testnet_probe_notional_must_be_20usdc"],
        }
    if transport is None:
        return lifecycle_rows, {
            "transport_mode": "submit_requested",
            "transport_status": "blocked_transport_not_configured",
            "submitted_this_cycle": 0,
            "cancel_attempted_this_cycle": 0,
            "reconciled_this_cycle": 0,
            "order_endpoint_called": False,
            "signed_order_endpoint_called": False,
            "testnet_fills_update_strategy_pnl": False,
            "strategy_pnl_updated": False,
            "reason_codes": ["signed_testnet_transport_client_not_configured"],
        }

    submitted = 0
    cancel_attempted = 0
    reconciled = 0
    for row in eligible_rows:
        order_shape = row.get("order_shape")
        if not isinstance(order_shape, dict):
            continue
        result = transport(order_shape, row)
        lifecycle = {
            "lane": "testnet_plumbing_probe",
            "environment": "hyperliquid_testnet_only",
            "symbol": row.get("symbol"),
            "timeframe": row.get("timeframe"),
            "strategy_id": row.get("strategy_id"),
            "lane_id": row.get("lane_id"),
            "notional_usdc": row.get("notional_usdc"),
            "submit_attempted": True,
            "cancel_attempted": bool(result.get("cancel_attempted")),
            "reconcile_attempted": bool(result.get("reconcile_attempted")),
            "transport_status": result.get("transport_status", "submitted_cancel_reconciled"),
            "venue_order_id": result.get("venue_order_id"),
            "sanitized_response": result.get("sanitized_response"),
            "order_endpoint_called": bool(result.get("order_endpoint_called", True)),
            "signed_order_endpoint_called": bool(result.get("signed_order_endpoint_called", True)),
            "testnet_fills_update_strategy_pnl": False,
            "strategy_pnl_updated": False,
        }
        lifecycle_rows.append(lifecycle)
        submitted += 1
        cancel_attempted += 1 if lifecycle["cancel_attempted"] else 0
        reconciled += 1 if lifecycle["reconcile_attempted"] else 0

    return lifecycle_rows, {
        "transport_mode": "submit_requested",
        "transport_status": "submitted_cancel_reconciled" if lifecycle_rows else "no_eligible_probe_shapes",
        "submitted_this_cycle": submitted,
        "cancel_attempted_this_cycle": cancel_attempted,
        "reconciled_this_cycle": reconciled,
        "order_endpoint_called": bool(lifecycle_rows),
        "signed_order_endpoint_called": bool(lifecycle_rows),
        "testnet_fills_update_strategy_pnl": False,
        "strategy_pnl_updated": False,
        "reason_codes": ["pt_rt1_2_transport_lifecycle_recorded"],
    }


def _testnet_order_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("lane_id") or ""),
            str(row.get("strategy_id") or ""),
            str(row.get("symbol") or "").upper(),
            str(row.get("timeframe") or ""),
            str(row.get("signal_candle_close_time") or ""),
            "buy",
        ]
    )


def _build_pt_rt1_5_testnet_order_lifecycle_rows(
    *,
    decision_rows: Sequence[dict[str, Any]],
    scanner_rows: Sequence[Any],
    latest_closed_by_key: dict[tuple[str, str], Any],
    transport_enabled: bool,
    approval_text: str,
    notional_usdc: Decimal,
    daily_cap: int,
    per_symbol_daily_cap: int,
    existing_order_keys: set[str],
    base_url: str,
    kill_switch: bool,
    transport: BaselineTestnetOrderTransport | None,
) -> tuple[list[dict[str, Any]], dict[str, Any], set[str]]:
    row_by_symbol = {
        str(row.canonical_symbol or row.requested_symbol).upper(): row
        for row in scanner_rows
        if row.scanner_eligible and not row.blocked
    }
    policy = PT_RT15BaselineTestnetOrderPolicy()
    lifecycle_rows: list[dict[str, Any]] = []
    submitted_keys = set(existing_order_keys)
    per_symbol_counts: dict[str, int] = {}
    baseline_open_rows = [
        row
        for row in decision_rows
        if row.get("action") == "paper_opened"
        and row.get("lane_id") == "money_flow_v1_2_baseline"
        and row.get("strategy_id") == "money_flow_v1_2_baseline"
    ]
    candidate_open_rows = [
        row
        for row in decision_rows
        if row.get("action") == "paper_opened"
        and row.get("lane_id") != "money_flow_v1_2_baseline"
    ]
    for index, decision in enumerate(baseline_open_rows):
        symbol = str(decision.get("symbol") or "").upper()
        timeframe = str(decision.get("timeframe") or "")
        scanner_row = row_by_symbol.get(symbol)
        candle = latest_closed_by_key.get((symbol, timeframe))
        order_key = _testnet_order_key(decision)
        duplicate = order_key in submitted_keys
        price = _testnet_probe_price(candle) if candle is not None else Decimal("0")
        per_symbol_count = per_symbol_counts.get(symbol, 0)
        result = policy.evaluate(
            PT_RT15TestnetOrderCandidate(
                lane_id=str(decision.get("lane_id") or ""),
                strategy_id=str(decision.get("strategy_id") or ""),
                action=str(decision.get("action") or ""),
                symbol=symbol,
                timeframe=timeframe,
                signal_candle_close_time=str(decision.get("signal_candle_close_time") or ""),
                scheduled_closed_candle_evaluation=bool(decision.get("scheduled_closed_candle_evaluation")),
                fresh_signal_after_runtime_start=bool(decision.get("fresh_signal_after_runtime_start")),
                warm_start_signal_blocked=bool(decision.get("warm_start_signal_blocked")),
                duplicate_order_key_seen=duplicate,
                scanner_signal_eligible=bool(scanner_row and scanner_row.scanner_eligible and not scanner_row.blocked),
                scanner_symbol_blocked=bool(scanner_row.blocked) if scanner_row else True,
                unit_semantics_deferred=(
                    any("unit_semantics" in str(reason) for reason in scanner_row.reason_codes)
                    if scanner_row
                    else False
                ),
                precision_ready=bool(scanner_row.precision_ready) if scanner_row else False,
                order_transport_enabled=transport_enabled,
                kill_switch=kill_switch,
                approval_text=approval_text,
                base_url=base_url,
                asset_id=scanner_row.asset_id if scanner_row else None,
                sz_decimals=scanner_row.szDecimals if scanner_row else None,
                price=price,
                synthetic_signal_notional=_dec(decision.get("equity_before"), Decimal("10000")),
                fixed_notional=notional_usdc,
                daily_order_count=index,
                daily_cap=daily_cap,
                per_symbol_daily_count=per_symbol_count,
                per_symbol_daily_cap=per_symbol_daily_cap,
            )
        )
        lifecycle_row = {
            **result.lifecycle_row,
            "testnet_order_key": order_key,
            "created_at_utc": _iso(_utc_now()),
            "transport_submit_configured": transport is not None,
            "signed_testnet_transport_client_configured": transport is not None,
            "trigger_reason_codes": list(decision.get("reason_codes") or []),
        }
        if result.eligible:
            submitted_keys.add(order_key)
            per_symbol_counts[symbol] = per_symbol_count + 1
            if transport is None:
                lifecycle_row = {
                    **lifecycle_row,
                    "status": "preflight_passed",
                    "next_status": "submit_when_signed_transport_client_configured",
                    "reason_codes": [
                        "testnet_order_shape_ready",
                        "fixed_testnet_plumbing_notional",
                        "signed_testnet_transport_client_not_configured",
                    ],
                }
            else:
                transport_result = transport(result.order_shape or {}, lifecycle_row)
                lifecycle_row = {
                    **lifecycle_row,
                    **transport_result,
                    "reason_codes": list(
                        dict.fromkeys(
                            [
                                "testnet_order_shape_ready",
                                "fixed_testnet_plumbing_notional",
                                "signed_testnet_transport_client_configured",
                                *list(transport_result.get("reason_codes") or []),
                            ]
                        )
                    ),
                }
        lifecycle_rows.append(lifecycle_row)

    signed_called = any(bool(row.get("signed_order_endpoint_called")) for row in lifecycle_rows)
    order_called = any(bool(row.get("order_endpoint_called")) for row in lifecycle_rows)
    stats = {
        "policy": "pt_rt1_5_baseline_only_fixed_25usdc",
        "transport_enabled": transport_enabled,
        "transport_submit_configured": transport is not None,
        "signed_testnet_transport_client_configured": transport is not None,
        "kill_switch_active": kill_switch,
        "approval_captured": approval_text
        in {
            PT_RT1_5_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
            PT_RT1_5_1_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
            PT_RT1_5_2_EXACT_TESTNET_TRANSPORT_SMOKE_APPROVAL,
        },
        "fixed_notional_usdc": str(notional_usdc),
        "baseline_open_signals_this_cycle": len(baseline_open_rows),
        "fresh_baseline_open_signals_this_cycle": sum(
            1 for row in baseline_open_rows if row.get("fresh_signal_after_runtime_start") is True
        ),
        "startup_or_late_baseline_open_signals_blocked_this_cycle": sum(
            1 for row in baseline_open_rows if row.get("fresh_signal_after_runtime_start") is not True
        ),
        "candidate_open_signals_blocked_this_cycle": len(candidate_open_rows),
        "lifecycle_rows_this_cycle": len(lifecycle_rows),
        "eligible_order_shapes_this_cycle": sum(1 for row in lifecycle_rows if row.get("status") in {"created", "preflight_passed", "submitted", "accepted_open", "reconciled", "canceled"}),
        "signed_order_endpoint_called": signed_called,
        "order_endpoint_called": order_called,
        "testnet_fills_update_strategy_pnl": False,
        "candidate_lane_transport_blocked": True,
        "reason_codes": [
            "baseline_only_trigger",
            "candidate_lane_transport_blocked",
            "fixed_testnet_plumbing_notional",
            *(["signed_testnet_transport_client_configured"] if transport is not None else ["signed_testnet_transport_client_not_configured"]),
            *(["testnet_order_transport_kill_switch_active"] if kill_switch else []),
        ],
    }
    return lifecycle_rows, stats, submitted_keys


def _build_pt_rt1_5_2_transport_smoke_lifecycle_row(
    *,
    scanner_rows: Sequence[Any],
    latest_closed_by_key: dict[tuple[str, str], Any],
    enabled: bool,
    approval_text: str,
    notional_usdc: Decimal,
    existing_order_keys: set[str],
    base_url: str,
    kill_switch: bool,
    transport: BaselineTestnetOrderTransport | None,
    max_testnet_orders_this_phase: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], set[str]]:
    smoke_key = "pt_rt1_5_2|transport_smoke_not_strategy_signal|25usdc|buy"
    if not enabled:
        return [], {
            "transport_smoke_enabled": False,
            "transport_smoke_used_this_cycle": False,
            "reason_codes": ["testnet_transport_smoke_not_requested"],
        }, existing_order_keys
    if max_testnet_orders_this_phase <= 0 or smoke_key in existing_order_keys:
        return [
            {
                "lane": "testnet_order_transport",
                "environment": "hyperliquid_testnet_only",
                "trigger_type": "transport_smoke_not_strategy_signal",
                "trigger_lane": "none",
                "status": "blocked",
                "notional": str(notional_usdc),
                "synthetic_trade_created": False,
                "strategy_pnl_update_from_testnet": False,
                "testnet_fills_update_strategy_pnl": False,
                "order_endpoint_called": False,
                "signed_order_endpoint_called": False,
                "reason_codes": ["pt_rt1_5_2_testnet_smoke_cap_reached"],
            }
        ], {
            "transport_smoke_enabled": True,
            "transport_smoke_used_this_cycle": False,
            "transport_smoke_blocked": True,
            "reason_codes": ["pt_rt1_5_2_testnet_smoke_cap_reached"],
        }, existing_order_keys

    selected: tuple[Any, Any, str] | None = None
    for row in scanner_rows:
        if not row.scanner_eligible or row.blocked or not row.precision_ready:
            continue
        symbol = str(row.canonical_symbol or row.requested_symbol).upper()
        for timeframe in PT_RT1_5_ACTIVE_TIMEFRAMES:
            candle = latest_closed_by_key.get((symbol, timeframe))
            if candle is not None:
                selected = (row, candle, timeframe)
                break
        if selected is not None:
            break
    if selected is None:
        return [
            {
                "lane": "testnet_order_transport",
                "environment": "hyperliquid_testnet_only",
                "trigger_type": "transport_smoke_not_strategy_signal",
                "trigger_lane": "none",
                "status": "blocked",
                "notional": str(notional_usdc),
                "synthetic_trade_created": False,
                "strategy_pnl_update_from_testnet": False,
                "testnet_fills_update_strategy_pnl": False,
                "order_endpoint_called": False,
                "signed_order_endpoint_called": False,
                "reason_codes": ["testnet_transport_smoke_market_context_unavailable"],
            }
        ], {
            "transport_smoke_enabled": True,
            "transport_smoke_used_this_cycle": False,
            "transport_smoke_blocked": True,
            "reason_codes": ["testnet_transport_smoke_market_context_unavailable"],
        }, existing_order_keys

    scanner_row, candle, timeframe = selected
    symbol = str(scanner_row.canonical_symbol or scanner_row.requested_symbol).upper()
    price = _testnet_probe_price(candle)
    policy = PT_RT15BaselineTestnetOrderPolicy()
    result = policy.evaluate(
        PT_RT15TestnetOrderCandidate(
            lane_id="money_flow_v1_2_baseline",
            strategy_id="money_flow_v1_2_baseline",
            action="paper_opened",
            symbol=symbol,
            timeframe=timeframe,
            signal_candle_close_time=_iso(canonical_candle_close(candle)),
            scheduled_closed_candle_evaluation=True,
            fresh_signal_after_runtime_start=True,
            warm_start_signal_blocked=False,
            duplicate_order_key_seen=False,
            scanner_signal_eligible=True,
            scanner_symbol_blocked=False,
            unit_semantics_deferred=False,
            precision_ready=bool(scanner_row.precision_ready),
            order_transport_enabled=True,
            kill_switch=kill_switch,
            approval_text=approval_text,
            base_url=base_url,
            asset_id=scanner_row.asset_id,
            sz_decimals=scanner_row.szDecimals,
            price=price,
            synthetic_signal_notional=Decimal("0"),
            fixed_notional=notional_usdc,
            daily_order_count=0,
            daily_cap=max_testnet_orders_this_phase,
            per_symbol_daily_count=0,
            per_symbol_daily_cap=max_testnet_orders_this_phase,
        )
    )
    lifecycle_row = {
        **result.lifecycle_row,
        "testnet_order_key": smoke_key,
        "created_at_utc": _iso(_utc_now()),
        "trigger_type": "transport_smoke_not_strategy_signal",
        "trigger_lane": "none",
        "trigger_reason": "testnet_transport_smoke_not_strategy_signal",
        "strategy_id": "none",
        "lane_id": "none",
        "synthetic_trade_created": False,
        "strategy_pnl_update_from_testnet": False,
        "strategy_pnl_updated_from_testnet": False,
        "transport_submit_configured": transport is not None,
        "signed_testnet_transport_client_configured": transport is not None,
        "reason_codes": list(
            dict.fromkeys(
                [
                    "testnet_transport_smoke_not_strategy_signal",
                    "fixed_testnet_plumbing_notional",
                    *list(result.reason_codes),
                ]
            )
        ),
    }
    submitted_keys = set(existing_order_keys)
    if result.eligible:
        submitted_keys.add(smoke_key)
        if transport is None:
            lifecycle_row = {
                **lifecycle_row,
                "status": "preflight_passed",
                "next_status": "submit_when_signed_transport_client_configured",
                "reason_codes": [
                    "testnet_transport_smoke_not_strategy_signal",
                    "testnet_order_shape_ready",
                    "fixed_testnet_plumbing_notional",
                    "signed_testnet_transport_client_not_configured",
                ],
            }
        else:
            transport_result = transport(result.order_shape or {}, lifecycle_row)
            lifecycle_row = {
                **lifecycle_row,
                **transport_result,
                "reason_codes": list(
                    dict.fromkeys(
                        [
                            "testnet_transport_smoke_not_strategy_signal",
                            "testnet_order_shape_ready",
                            "fixed_testnet_plumbing_notional",
                            "signed_testnet_transport_client_configured",
                            *list(transport_result.get("reason_codes") or []),
                        ]
                    )
                ),
            }
    return [lifecycle_row], {
        "transport_smoke_enabled": True,
        "transport_smoke_used_this_cycle": result.eligible,
        "transport_smoke_blocked": not result.eligible,
        "order_endpoint_called": bool(lifecycle_row.get("order_endpoint_called")),
        "signed_order_endpoint_called": bool(lifecycle_row.get("signed_order_endpoint_called")),
        "status": lifecycle_row.get("status"),
        "reason_codes": list(lifecycle_row.get("reason_codes") or []),
    }, submitted_keys


def _ensure_pt_rt1_5_2_transport_smoke_context(
    *,
    connector: HyperliquidPublicMarketDataConnector,
    scanner_rows: Sequence[Any],
    latest_closed_by_key: dict[tuple[str, str], Any],
    now: datetime,
) -> tuple[dict[tuple[str, str], Any], list[str]]:
    """Load one public-mainnet closed candle for explicit testnet smoke shaping.

    This does not evaluate strategy signals. It only supplies a recent closed
    public-mainnet price context so a separately approved testnet transport
    smoke can format a fixed-notional post-only order.
    """

    if latest_closed_by_key:
        return latest_closed_by_key, ["transport_smoke_context_already_available"]
    reasons: list[str] = []
    for row in scanner_rows:
        if not row.scanner_eligible or row.blocked or not row.precision_ready:
            continue
        symbol = str(row.canonical_symbol or row.requested_symbol).upper()
        venue_symbol = str(row.resolved_venue_symbol or row.requested_symbol)
        for timeframe in PT_RT1_5_ACTIVE_TIMEFRAMES:
            start_time, end_time = candle_request_window(timeframe=timeframe, now=now, bars=20)
            candle_result = connector.fetch_candle_snapshot(
                symbol=venue_symbol,
                timeframe=timeframe,
                start_time=start_time,
                end_time=end_time,
            )
            closed_candles = _closed_prefix(candle_result.candles, now)
            if closed_candles:
                latest_closed_by_key[(symbol, timeframe)] = closed_candles[-1]
                return latest_closed_by_key, ["transport_smoke_public_mainnet_context_loaded"]
            reasons.extend(candle_result.reason_codes)
    return latest_closed_by_key, list(dict.fromkeys(reasons or ["testnet_transport_smoke_market_context_unavailable"]))


def run_cycle(
    *,
    connector: HyperliquidPublicMarketDataConnector,
    output_dir: Path,
    symbols: Sequence[str] | None,
    timeframes: Sequence[str],
    max_candle_symbols: int | None,
    run_label: str = "PT-RT1.1B",
    decision_log_mode: str = "compact",
    testnet_probes_enabled: bool = False,
    testnet_probe_approval_text: str = "",
    testnet_probe_notional_usdc: Decimal = PT_RT1_TESTNET_PROBE_NOTIONAL_USDC,
    testnet_probe_daily_cap: int = TESTNET_PROBE_AUDIT_LIMIT,
    submit_testnet_probes: bool = False,
    testnet_probe_transport_approval_text: str = "",
    testnet_probe_transport: TestnetProbeTransport | None = None,
    signal_evaluation_mode: str = "poll",
    baseline_testnet_order_transport_enabled: bool = False,
    baseline_testnet_order_approval_text: str = "",
    baseline_testnet_order_notional_usdc: Decimal = PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC,
    baseline_testnet_order_daily_cap: int = PT_RT1_5_TESTNET_DAILY_ORDER_CAP_DEFAULT,
    baseline_testnet_order_per_symbol_daily_cap: int = PT_RT1_5_TESTNET_PER_SYMBOL_DAILY_CAP_DEFAULT,
    baseline_testnet_order_base_url: str = PT_RT1_TESTNET_INFO_URL,
    baseline_testnet_order_kill_switch: bool = False,
    baseline_testnet_order_transport: BaselineTestnetOrderTransport | None = None,
    fresh_signal_only_after_runtime_start: bool = False,
    pt_rt1_5_2_transport_smoke_enabled: bool = False,
    max_testnet_orders_this_phase: int = PT_RT1_5_2_TESTNET_SMOKE_PHASE_CAP,
    signed_transport_env_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = _utc_now()
    meta_result = connector.fetch_meta()
    mids_result = connector.fetch_all_mids()
    if meta_result.ok:
        scanner_rows = resolve_watchlist_from_public_data(
            meta_payload=meta_result.payload,
            mids_payload=mids_result.payload if mids_result.ok else {},
        )
    else:
        scanner_rows = ()

    selected_rows = _filter_scanner_rows(scanner_rows, symbols, max_candle_symbols)
    market_health: list[dict[str, Any]] = []
    decisions: list[PaperDecisionEvent] = []
    latest_chart: dict[str, Any] | None = None
    latest_closed_by_key: dict[tuple[str, str], Any] = {}
    prior_state = _read_state(output_dir / "state.json")
    paper_state = _load_paper_runtime_state(prior_state)
    processed_signal_keys: set[str] = paper_state["processed_signal_keys"]
    open_positions_by_key: dict[str, dict[str, Any]] = paper_state["open_positions_by_key"]
    realized_equity_by_lane: dict[str, str] = paper_state["realized_equity_by_lane"]
    last_processed_close_by_key: dict[str, str] = paper_state["last_processed_close_by_key"]
    last_evaluated_closed_candle_by_timeframe: dict[str, str] = paper_state[
        "last_evaluated_closed_candle_by_timeframe"
    ]
    testnet_order_keys: set[str] = paper_state["testnet_order_keys"]
    runtime_start_utc = paper_state["runtime_start_utc"] or _iso(now)
    warm_start_entry_context_by_key: dict[str, dict[str, Any]] = paper_state["warm_start_entry_context_by_key"]
    warm_start_evaluation_completed = bool(paper_state["warm_start_evaluation_completed"])
    warm_start_evaluation_this_cycle = fresh_signal_only_after_runtime_start and not warm_start_evaluation_completed
    scheduler_status = build_pt_rt1_5_scheduler_status(
        now=now,
        last_evaluated_closed_candle_by_timeframe=last_evaluated_closed_candle_by_timeframe,
    )
    due_timeframes = {
        timeframe
        for timeframe, payload in (scheduler_status.get("timeframes") or {}).items()
        if payload.get("is_due") is True
    }
    candle_close_only = signal_evaluation_mode == "candle_close_only"
    effective_due_timeframes = set(due_timeframes)
    if warm_start_evaluation_this_cycle:
        effective_due_timeframes.update(PT_RT1_5_ACTIVE_TIMEFRAMES)

    for row in selected_rows:
        for timeframe in timeframes:
            if timeframe in PT_RT1_4_DISABLED_TIMEFRAMES:
                disabled_reasons = list(PT_RT1_4_TIMEFRAME_REASON_CODES)
                market_health.append(
                    {
                        "symbol": row.canonical_symbol,
                        "requested_symbol": row.requested_symbol,
                        "resolved_venue_symbol": row.resolved_venue_symbol,
                        "timeframe": timeframe,
                        "source": "Hyperliquid public mainnet",
                        "endpoint_category": connector.endpoint_category,
                        "status": PT_RT1_4_DISABLED_TIMEFRAME_STATUS,
                        "strategy_data_status": "timeframe_excluded_from_active_scoreboard",
                        "candle_strategy_ready": False,
                        "mid_health_status": "not_evaluated_timeframe_paused",
                        "mid_health_blocks_strategy": False,
                        "candle_health_blocks_strategy": True,
                        "fully_closed_candle_status": "paused_legacy_timeframe",
                        "latest_candle_update": None,
                        "last_update_utc": _iso(now),
                        "reason_codes": disabled_reasons,
                    }
                )
                for lane in PT_RT1_STRATEGY_LANES:
                    symbol = str(row.canonical_symbol or row.requested_symbol).upper()
                    equity_before = _dec(realized_equity_by_lane.get(lane.lane_id), lane.initial_equity)
                    decisions.append(
                        PaperDecisionEvent(
                            lane_id=lane.lane_id,
                            strategy_id=lane.strategy_id,
                            symbol=symbol,
                            timeframe=timeframe,
                            signal_candle_open_time=None,
                            signal_candle_close_time=None,
                            decision_time=_iso(now),
                            candle_closed=False,
                            candle_status_reason=PT_RT1_4_DISABLED_TIMEFRAME_STATUS,
                            action="no_trade",
                            reason_codes=tuple(disabled_reasons),
                            indicator_snapshot={
                                "timeframe_status": PT_RT1_4_DISABLED_TIMEFRAME_STATUS,
                                "active_timeframes": list(PT_RT1_4_ACTIVE_TIMEFRAMES),
                            },
                            position_before="not_evaluated_timeframe_paused",
                            position_after="not_evaluated_timeframe_paused",
                            equity_before=equity_before,
                            equity_after=equity_before,
                        )
                    )
                continue
            if candle_close_only and timeframe not in effective_due_timeframes:
                market_health.append(
                    {
                        "symbol": row.canonical_symbol,
                        "requested_symbol": row.requested_symbol,
                        "resolved_venue_symbol": row.resolved_venue_symbol,
                        "timeframe": timeframe,
                        "source": "Hyperliquid public mainnet",
                        "endpoint_category": connector.endpoint_category,
                        "status": "market_refresh_only",
                        "strategy_data_status": "waiting_for_scheduled_closed_candle",
                        "candle_strategy_ready": False,
                        "mid_health_status": "mid_healthy" if row.data_health == DataHealth.HEALTHY else "mid_warning_non_blocking",
                        "mid_health_blocks_strategy": False,
                        "candle_health_blocks_strategy": True,
                        "fully_closed_candle_status": "signal_evaluation_waiting_for_candle_close",
                        "latest_candle_update": None,
                        "last_update_utc": _iso(now),
                        "reason_codes": [
                            "signal_evaluation_waiting_for_candle_close",
                            "market_refresh_only_no_signal_evaluation",
                            "intrabar_signal_evaluation_blocked",
                        ],
                    }
                )
                continue
            start_time, end_time = candle_request_window(timeframe=timeframe, now=now, bars=260)
            candle_result = connector.fetch_candle_snapshot(
                symbol=str(row.resolved_venue_symbol or row.requested_symbol),
                timeframe=timeframe,
                start_time=start_time,
                end_time=end_time,
            )
            closed_candles = _closed_prefix(candle_result.candles, now)
            if closed_candles:
                latest_closed_by_key[(str(row.canonical_symbol or row.requested_symbol).upper(), timeframe)] = closed_candles[-1]
            closed_status = "closed_candle_ready" if closed_candles else "candle_not_closed_or_unavailable"
            mid_warning = row.data_health == DataHealth.STALE
            candle_strategy_ready = bool(closed_candles) and candle_result.data_health == DataHealth.HEALTHY
            market_reason_codes = (
                [*row.reason_codes, *candle_result.reason_codes]
                if candle_strategy_ready
                else [*candle_result.reason_codes, *row.reason_codes]
            )
            market_health.append(
                {
                    "symbol": row.canonical_symbol,
                    "requested_symbol": row.requested_symbol,
                    "resolved_venue_symbol": row.resolved_venue_symbol,
                    "timeframe": timeframe,
                    "source": "Hyperliquid public mainnet",
                    "endpoint_category": connector.endpoint_category,
                    "status": candle_result.data_health.value,
                    "strategy_data_status": "candle_ready" if candle_strategy_ready else "candle_unavailable_blocking",
                    "candle_strategy_ready": candle_strategy_ready,
                    "mid_health_status": (
                        "mid_unavailable_but_candles_available"
                        if mid_warning and candle_strategy_ready
                        else "mid_warning_non_blocking"
                        if mid_warning
                        else "mid_healthy"
                    ),
                    "mid_health_blocks_strategy": False,
                    "candle_health_blocks_strategy": True,
                    "fully_closed_candle_status": closed_status,
                    "latest_candle_update": candle_result.latest_candle_update,
                    "last_update_utc": _iso(now),
                    "reason_codes": list(dict.fromkeys(market_reason_codes)),
                }
            )
            if closed_candles and latest_chart is None:
                latest_chart = {
                    "symbol": row.canonical_symbol,
                    "timeframe": timeframe,
                    "candles": [
                        {
                            "time": _iso(candle.open_time),
                            "open": str(candle.open),
                            "high": str(candle.high),
                            "low": str(candle.low),
                            "close": str(candle.close),
                            "volume": str(candle.volume),
                        }
                        for candle in closed_candles[-120:]
                    ],
                    "paper_markers": [],
                    "reason_code_toggle": True,
                }
            for lane in PT_RT1_STRATEGY_LANES:
                symbol = str(row.canonical_symbol or row.requested_symbol).upper()
                lane_position_key = _lane_key(lane.lane_id, symbol, timeframe)
                equity_before = _dec(realized_equity_by_lane.get(lane.lane_id), lane.initial_equity)
                decisions.append(
                    evaluate_paper_decision(
                        lane=lane,
                        symbol=symbol,
                        timeframe=timeframe,
                        candles=closed_candles,
                        now=now,
                        data_health=DataHealth.HEALTHY if candle_strategy_ready else DataHealth.UNAVAILABLE,
                        position_open=lane_position_key in open_positions_by_key,
                        equity_before=equity_before,
                    )
                )

    base_summary = build_pt_rt1_summary()
    scanner_payload = [asdict(row) for row in scanner_rows] if scanner_rows else base_summary["scanner_universe"]
    lane_payload = base_summary["strategy_lanes"]
    raw_decision_rows = [event.as_json_dict() for event in decisions]
    if candle_close_only:
        enriched_rows: list[dict[str, Any]] = []
        for row in raw_decision_rows:
            reasons = list(row.get("reason_codes") or [])
            timeframe = str(row.get("timeframe") or "")
            if timeframe in due_timeframes and timeframe not in PT_RT1_4_DISABLED_TIMEFRAMES:
                reasons.append("signal_evaluation_started_after_closed_candle")
                row = {
                    **row,
                    "scheduled_closed_candle_evaluation": True,
                    "signal_evaluation_mode": "candle_close_only",
                    "reason_codes": list(dict.fromkeys(reasons)),
                }
            elif warm_start_evaluation_this_cycle and timeframe in PT_RT1_5_ACTIVE_TIMEFRAMES:
                reasons.append("warm_start_evaluation_completed")
                row = {
                    **row,
                    "scheduled_closed_candle_evaluation": False,
                    "warm_start_evaluation": True,
                    "signal_evaluation_mode": "candle_close_only",
                    "reason_codes": list(dict.fromkeys(reasons)),
                }
            elif timeframe in PT_RT1_4_DISABLED_TIMEFRAMES:
                reasons.append("timeframe_paused_no_signal_evaluation")
                row = {
                    **row,
                    "scheduled_closed_candle_evaluation": False,
                    "signal_evaluation_mode": "candle_close_only",
                    "reason_codes": list(dict.fromkeys(reasons)),
                }
            enriched_rows.append(row)
        raw_decision_rows = enriched_rows
    raw_decision_rows, warm_start_entry_context_by_key, warm_start_gate_stats = _apply_warm_start_signal_gate(
        decision_rows=raw_decision_rows,
        warm_start_state=warm_start_entry_context_by_key,
        runtime_start_utc=runtime_start_utc,
        warm_start_evaluation=warm_start_evaluation_this_cycle,
        fresh_signal_only_after_runtime_start=fresh_signal_only_after_runtime_start,
    )
    decision_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    duplicate_signal_blocks_this_cycle = 0
    paper_opens_this_cycle = 0
    paper_closes_this_cycle = 0
    for row in raw_decision_rows:
        symbol = str(row.get("symbol") or "").upper()
        timeframe = str(row.get("timeframe") or "")
        lane_id = str(row.get("lane_id") or "")
        lane_position_key = _lane_key(lane_id, symbol, timeframe)
        candle = latest_closed_by_key.get((symbol, timeframe))
        if row.get("signal_candle_close_time"):
            last_processed_close_by_key[lane_position_key] = str(row["signal_candle_close_time"])
        if row.get("action") == "paper_opened":
            signal_key = _paper_signal_key(row)
            if signal_key in processed_signal_keys or lane_position_key in open_positions_by_key:
                duplicate_signal_blocks_this_cycle += 1
                decision_rows.append(_blocked_duplicate_row(row))
                continue
            processed_signal_keys.add(signal_key)
            equity_before = _dec(realized_equity_by_lane.get(lane_id), Decimal("10000"))
            if candle is not None:
                position = _open_position_from_decision(row=row, candle=candle, equity_before=equity_before)
                open_positions_by_key[lane_position_key] = position
                realized_equity_by_lane[lane_id] = str(equity_before - _dec(position.get("fees")))
                paper_opens_this_cycle += 1
                row = {
                    **row,
                    "paper_state_transition": "opened_synthetic_position",
                    "paper_position_key": lane_position_key,
                    "paper_pnl_source": "synthetic_public_mainnet_paper_ledger",
                    "testnet_fills_update_strategy_pnl": False,
                }
            else:
                row = {
                    **row,
                    "action": "data_unavailable",
                    "reason_codes": list(row.get("reason_codes") or []) + ["paper_open_context_candle_missing"],
                    "paper_state_transition": "open_blocked_context_missing",
                }
        elif row.get("action") == "paper_closed":
            position = open_positions_by_key.get(lane_position_key)
            if position is None or candle is None:
                row = {
                    **row,
                    "action": "paper_hold",
                    "reason_codes": list(row.get("reason_codes") or []) + ["paper_position_missing"],
                    "paper_state_transition": "close_blocked_position_missing",
                }
            else:
                trade, equity_after = _close_position_from_decision(row=row, position=position, candle=candle)
                trade_rows.append(trade)
                realized_equity_by_lane[lane_id] = str(equity_after)
                open_positions_by_key.pop(lane_position_key, None)
                paper_closes_this_cycle += 1
                row = {
                    **row,
                    "paper_state_transition": "closed_synthetic_position",
                    "paper_position_key": lane_position_key,
                    "paper_pnl_source": "synthetic_public_mainnet_paper_ledger",
                    "testnet_fills_update_strategy_pnl": False,
                    "trade_net_pnl": trade["net_pnl"],
                    "equity_after": trade["equity_after"],
                }
        elif row.get("action") == "data_unavailable":
            pass
        decision_rows.append(row)

    unrealized_pnl_by_lane, mtm_stats = _update_open_position_mtm(
        open_positions_by_key=open_positions_by_key,
        scanner_rows=selected_rows,
        latest_closed_by_key=latest_closed_by_key,
        now=now,
    )
    total_equity_by_lane = {
        lane.lane_id: str(_dec(realized_equity_by_lane.get(lane.lane_id), lane.initial_equity) + _dec(unrealized_pnl_by_lane.get(lane.lane_id)))
        for lane in PT_RT1_STRATEGY_LANES
    }

    if candle_close_only:
        for timeframe in due_timeframes:
            closed_time = (scheduler_status.get("timeframes") or {}).get(timeframe, {}).get("closed_candle_time")
            if closed_time:
                last_evaluated_closed_candle_by_timeframe[timeframe] = str(closed_time)

    prior_seen_keys = set(prior_state.get("decision_log_seen_keys") or [])
    decision_log_rows, decision_log_seen_keys, decision_log_stats = _select_decision_log_rows(
        decision_rows,
        mode=decision_log_mode,
        seen_keys=prior_seen_keys,
    )
    intended_entry_signals = [row for row in decision_rows if row.get("action") == "paper_opened"]
    testnet_probe_rows, testnet_probe_stats = _build_testnet_probe_audit_rows(
        decision_rows=decision_rows,
        scanner_rows=selected_rows,
        latest_closed_by_key=latest_closed_by_key,
        enabled=testnet_probes_enabled,
        approval_text=testnet_probe_approval_text,
        notional_usdc=testnet_probe_notional_usdc,
        daily_cap=testnet_probe_daily_cap,
    )
    testnet_transport_rows, testnet_transport_stats = _apply_testnet_probe_transport(
        audit_rows=testnet_probe_rows,
        submit_enabled=submit_testnet_probes,
        transport_approval_text=testnet_probe_transport_approval_text,
        notional_usdc=testnet_probe_notional_usdc,
        transport=testnet_probe_transport,
    )
    testnet_order_lifecycle_rows, testnet_order_lifecycle_stats, testnet_order_keys = (
        _build_pt_rt1_5_testnet_order_lifecycle_rows(
            decision_rows=decision_rows,
            scanner_rows=selected_rows,
            latest_closed_by_key=latest_closed_by_key,
            transport_enabled=baseline_testnet_order_transport_enabled,
            approval_text=baseline_testnet_order_approval_text,
            notional_usdc=baseline_testnet_order_notional_usdc,
            daily_cap=baseline_testnet_order_daily_cap,
            per_symbol_daily_cap=baseline_testnet_order_per_symbol_daily_cap,
            existing_order_keys=testnet_order_keys,
            base_url=baseline_testnet_order_base_url,
            kill_switch=baseline_testnet_order_kill_switch,
            transport=baseline_testnet_order_transport,
        )
        if run_label in {"PT-RT1.5", "PT-RT1.5.1", "PT-RT1.5.2"}
        else ([], {}, testnet_order_keys)
    )
    transport_smoke_stats: dict[str, Any] = {"transport_smoke_enabled": False, "transport_smoke_used_this_cycle": False}
    if (
        run_label == "PT-RT1.5.2"
        and pt_rt1_5_2_transport_smoke_enabled
        and testnet_order_lifecycle_stats.get("fresh_baseline_open_signals_this_cycle", 0) == 0
    ):
        latest_closed_by_key, smoke_context_reasons = _ensure_pt_rt1_5_2_transport_smoke_context(
            connector=connector,
            scanner_rows=selected_rows,
            latest_closed_by_key=latest_closed_by_key,
            now=now,
        )
        transport_smoke_rows, transport_smoke_stats, testnet_order_keys = _build_pt_rt1_5_2_transport_smoke_lifecycle_row(
            scanner_rows=selected_rows,
            latest_closed_by_key=latest_closed_by_key,
            enabled=pt_rt1_5_2_transport_smoke_enabled,
            approval_text=baseline_testnet_order_approval_text,
            notional_usdc=baseline_testnet_order_notional_usdc,
            existing_order_keys=testnet_order_keys,
            base_url=baseline_testnet_order_base_url,
            kill_switch=baseline_testnet_order_kill_switch,
            transport=baseline_testnet_order_transport,
            max_testnet_orders_this_phase=max_testnet_orders_this_phase,
        )
        testnet_order_lifecycle_rows.extend(transport_smoke_rows)
        testnet_order_lifecycle_stats = {
            **testnet_order_lifecycle_stats,
            "lifecycle_rows_this_cycle": len(testnet_order_lifecycle_rows),
            "transport_smoke_enabled": transport_smoke_stats.get("transport_smoke_enabled", False),
            "transport_smoke_used_this_cycle": transport_smoke_stats.get("transport_smoke_used_this_cycle", False),
            "transport_smoke_status": transport_smoke_stats.get("status"),
            "order_endpoint_called": bool(
                testnet_order_lifecycle_stats.get("order_endpoint_called")
                or transport_smoke_stats.get("order_endpoint_called")
            ),
            "signed_order_endpoint_called": bool(
                testnet_order_lifecycle_stats.get("signed_order_endpoint_called")
                or transport_smoke_stats.get("signed_order_endpoint_called")
            ),
            "reason_codes": list(
                dict.fromkeys(
                    [
                        *list(testnet_order_lifecycle_stats.get("reason_codes") or []),
                        *smoke_context_reasons,
                        *list(transport_smoke_stats.get("reason_codes") or []),
                    ]
                )
            ),
        }
    data_unavailable_summary = _summarize_data_unavailable(
        market_health=market_health,
        decision_rows=decision_rows,
        scanner_rows=scanner_rows,
    )
    runtime_status = "verified" if meta_result.ok and market_health else "blocked"
    if not meta_result.ok:
        runtime_status = "blocked_public_mainnet_network_unavailable"
    is_pt_rt1_1c = run_label == "PT-RT1.1C"
    is_pt_rt1_2 = run_label == "PT-RT1.2"
    is_pt_rt1_3 = run_label == "PT-RT1.3"
    is_pt_rt1_5 = run_label == "PT-RT1.5"
    is_pt_rt1_5_1 = run_label == "PT-RT1.5.1"
    is_pt_rt1_5_2 = run_label == "PT-RT1.5.2"
    active_scope = (
        PT_RT1_5_2_RUNTIME_SCOPE
        if is_pt_rt1_5_2
        else PT_RT1_5_1_RUNTIME_SCOPE
        if is_pt_rt1_5_1
        else PT_RT1_5_RUNTIME_SCOPE
        if is_pt_rt1_5
        else "pt_rt1_4_1_active_week"
    )
    active_start = (
        PT_RT1_5_2_ACTIVE_REVIEW_START_UTC
        if is_pt_rt1_5_2
        else PT_RT1_5_1_ACTIVE_REVIEW_START_UTC
        if is_pt_rt1_5_1
        else PT_RT1_5_ACTIVE_REVIEW_START_UTC
        if is_pt_rt1_5
        else base_summary["active_review_start_utc"]
    )
    active_output_dir = (
        PT_RT1_5_2_RUNTIME_OUTPUT_DIR
        if is_pt_rt1_5_2
        else PT_RT1_5_1_RUNTIME_OUTPUT_DIR
        if is_pt_rt1_5_1
        else PT_RT1_5_RUNTIME_OUTPUT_DIR
    )
    summary = {
        **base_summary,
        "phase": run_label,
        "revision": run_label,
        "status": (
            "candle_truth_data_health_cycle_verified"
            if is_pt_rt1_3 and runtime_status == "verified"
            else "candle_truth_data_health_cycle_blocked"
            if is_pt_rt1_3
            else "week1_active_candle_close_scheduler_cycle_verified"
            if is_pt_rt1_5 and runtime_status == "verified"
            else "week1_active_candle_close_scheduler_cycle_blocked"
            if is_pt_rt1_5
            else "signed_testnet_transport_warm_start_mtm_cycle_verified"
            if is_pt_rt1_5_1 and runtime_status == "verified"
            else "signed_testnet_transport_warm_start_mtm_cycle_blocked"
            if is_pt_rt1_5_1
            else "signed_testnet_transport_smoke_cycle_verified"
            if is_pt_rt1_5_2 and runtime_status == "verified"
            else "signed_testnet_transport_smoke_cycle_blocked"
            if is_pt_rt1_5_2
            else "runtime_correctness_cycle_verified"
            if is_pt_rt1_2 and runtime_status == "verified"
            else "runtime_correctness_cycle_blocked"
            if is_pt_rt1_2
            else
            "runtime_collection_cycle_verified"
            if is_pt_rt1_1c and runtime_status == "verified"
            else "runtime_readiness_smoke"
            if runtime_status == "verified"
            else runtime_status
        ),
        "market_data_endpoint_policy": {
            "strategy_truth_endpoint": PT_RT1_MAINNET_INFO_URL,
            "endpoint_category": "public_read_only",
            "allowed_public_info_types": base_summary["strategy_truth_lane"]["allowed_info_types"],
            "forbidden_payloads_rejected": True,
            "testnet_url_is_strategy_truth": False,
            "api_keys_required": False,
            "data_health_semantics": "candle_strategy_truth",
            "mid_health_blocks_strategy": False,
            "candle_health_blocks_strategy": True,
        },
        "connection_status": {
            "hyperliquid_public_mainnet": (
                "connected"
                if meta_result.ok and mids_result.ok
                else "connected_degraded_mids_unavailable"
                if meta_result.ok
                else "disconnected"
            ),
            "endpoint_category": "public_read_only",
            "last_update_utc": _iso(now),
            "meta_reason_codes": list(meta_result.reason_codes),
            "mids_reason_codes": list(mids_result.reason_codes),
            "no_private_signed_order_endpoints": True,
            "no_api_keys": True,
        },
        "data_health_semantics": "candle_strategy_truth",
        "mid_health_blocks_strategy": False,
        "candle_health_blocks_strategy": True,
        "active_review_scope": active_scope,
        "active_review_start_utc": active_start,
        "archived_runtime_scopes": list(PT_RT1_5_ARCHIVED_RUNTIME_SCOPES),
        "active_week_reset_policy": {
            "default_scope": active_scope,
            "output_dir": active_output_dir,
            "old_runtime_rows_archived_not_deleted": True,
            "default_show_archived_rows": False,
            "reason_codes": [
                *(
                    [
                        "pt_rt1_5_1_smoke_archived",
                        "pre_pt_rt1_5_2_runtime",
                        "active_week_reset_after_signed_transport_smoke",
                    ]
                    if is_pt_rt1_5_2
                    else
                    [
                        "pre_warm_start_gate_runtime_archived",
                        "archived_smoke_rows_hidden_by_default",
                        "active_week_reset_after_warm_start_hotfix",
                    ]
                    if is_pt_rt1_5_1
                    else [
                        "pre_week1_runtime_archived",
                        "archived_position_hidden_by_default",
                        "active_week_ui_reset",
                        "active_week_scoring_only",
                    ]
                ),
            ],
        },
        "signal_evaluation_cadence": {
            "mode": signal_evaluation_mode,
            "strategy_signal_evaluation": "candle-close only" if candle_close_only else "poll",
            "market_refresh": "active",
            "fresh_signal_only_after_runtime_start": fresh_signal_only_after_runtime_start,
            "active_timeframes": list(PT_RT1_5_ACTIVE_TIMEFRAMES),
            "disabled_timeframes": list(PT_RT1_4_DISABLED_TIMEFRAMES),
            "scheduler_status": scheduler_status,
        },
        "warm_start_gate": {
            **warm_start_gate_stats,
            "active": fresh_signal_only_after_runtime_start,
            "warm_start_evaluation_completed": warm_start_evaluation_completed or warm_start_evaluation_this_cycle,
            "startup_valid_signals_blocked_total": paper_state["startup_valid_signals_blocked_total"]
            + warm_start_gate_stats.get("startup_valid_signals_blocked_this_cycle", 0),
            "waiting_for_reset_signals_total": paper_state["waiting_for_reset_signals_total"]
            + warm_start_gate_stats.get("waiting_for_reset_signals_this_cycle", 0),
            "fresh_post_start_opens_total": paper_state["fresh_post_start_opens_total"]
            + warm_start_gate_stats.get("fresh_post_start_opens_this_cycle", 0),
            "entry_context_resets_total": paper_state["entry_context_resets_total"]
            + warm_start_gate_stats.get("entry_context_resets_this_cycle", 0),
            "testnet_orders_from_startup_signals_blocked": True,
        },
        "scanner_universe": scanner_payload,
        "watchlist_status": {
            "requested_symbols": list(PT_RT1_REQUESTED_SCANNER_SYMBOLS),
            "resolved_rows": len(scanner_payload),
            "eligible_rows": sum(1 for row in scanner_payload if row.get("scanner_eligible") is True),
            "blocked_rows": sum(1 for row in scanner_payload if row.get("blocked") is True),
        },
        "market_data_health": market_health or base_summary["market_data_health"],
        "data_unavailable_summary": data_unavailable_summary,
        "strategy_lanes": lane_payload,
        "intended_entry_signals": intended_entry_signals[:200],
        "closed_trades": trade_rows[:200],
        "latest_decisions": decision_rows[:200],
        "live_chart": latest_chart or {
            "status": "data_not_available_in_pt_rt1_runtime",
            "reason_codes": ["public_mainnet_network_unavailable" if not meta_result.ok else "no_closed_candles_loaded"],
            "paper_markers": [],
        },
        "testnet_plumbing_status": {
            "status": "enabled_audit_only" if testnet_probes_enabled else "ready_but_disabled",
            "disabled_by_default": False if testnet_probes_enabled else True,
            "kill_switch_active": False if testnet_probes_enabled else True,
            "approval_required": True,
            "approval_captured": testnet_probe_approval_text == PT_RT1_EXACT_TESTNET_PROBE_APPROVAL,
            "daily_cap_configured": True,
            "daily_cap": testnet_probe_daily_cap,
            "notional_cap_configured": True,
            "probe_notional_usdc": str(testnet_probe_notional_usdc),
            "probe_notional_cap_usdc": str(PT_RT1_TESTNET_PROBE_NOTIONAL_CAP_USDC),
            "probe_audit_rows_this_cycle": testnet_probe_stats["audit_rows_this_cycle"],
            "eligible_probe_shapes_this_cycle": testnet_probe_stats["eligible_probe_shapes_this_cycle"],
            "transport_mode": testnet_transport_stats["transport_mode"],
            "transport_rows_this_cycle": len(testnet_transport_rows),
            "transport_submitted_this_cycle": testnet_transport_stats["submitted_this_cycle"],
            "transport_cancel_attempted_this_cycle": testnet_transport_stats["cancel_attempted_this_cycle"],
            "transport_reconciled_this_cycle": testnet_transport_stats["reconciled_this_cycle"],
            "post_only_required": True,
            "cancel_reconcile_required": True,
            "testnet_fills_do_not_update_strategy_pnl": True,
            "signed_order_endpoint_called": testnet_transport_stats["signed_order_endpoint_called"],
            "order_endpoint_called": testnet_transport_stats["order_endpoint_called"],
            "transport_status": testnet_transport_stats["transport_status"],
            "reason_codes": [
                *(
                    ["testnet_probe_order_shapes_created_audit_only", "testnet_probe_20usdc_per_signal"]
                    if testnet_probes_enabled
                    else [
                        "testnet_probe_not_enabled",
                        "testnet_probe_kill_switch_active",
                        "testnet_probe_approval_missing",
                        "testnet_probe_ready_but_disabled",
                    ]
                ),
                *testnet_transport_stats.get("reason_codes", []),
            ],
        },
        "testnet_order_policy": {
            "policy": "pt_rt1_5_2_baseline_only_fixed_25usdc_fresh_signal_or_one_smoke"
            if is_pt_rt1_5_2
            else "pt_rt1_5_1_baseline_only_fixed_25usdc_fresh_signal_only"
            if is_pt_rt1_5_1
            else "pt_rt1_5_baseline_only_fixed_25usdc",
            "order_transport_enabled": baseline_testnet_order_transport_enabled,
            "transport_submit_configured": testnet_order_lifecycle_stats.get("transport_submit_configured", False),
            "signed_testnet_transport_client_configured": testnet_order_lifecycle_stats.get(
                "signed_testnet_transport_client_configured",
                False,
            ),
            "kill_switch_active": testnet_order_lifecycle_stats.get("kill_switch_active", baseline_testnet_order_kill_switch),
            "approval_captured": baseline_testnet_order_approval_text
            in {
                PT_RT1_5_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
                PT_RT1_5_1_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
                PT_RT1_5_2_EXACT_TESTNET_TRANSPORT_SMOKE_APPROVAL,
            },
            "eligible_trigger": "money_flow_v1_2_baseline paper_opened only",
            "active_timeframes": list(PT_RT1_5_ACTIVE_TIMEFRAMES),
            "fixed_notional_usdc": str(baseline_testnet_order_notional_usdc),
            "fresh_signal_after_runtime_start_required": fresh_signal_only_after_runtime_start,
            "startup_valid_signals_can_send_testnet_orders": False,
            "candidate_lane_transport_blocked": True,
            "mf_orig_lane_transport_blocked": True,
            "wildcard_lane_transport_blocked": True,
            "public_mainnet_data_remains_strategy_truth": True,
            "testnet_prices_are_strategy_truth": False,
            "testnet_fills_update_strategy_pnl": False,
            "lifecycle_rows_this_cycle": testnet_order_lifecycle_stats.get("lifecycle_rows_this_cycle", 0),
            "eligible_order_shapes_this_cycle": testnet_order_lifecycle_stats.get("eligible_order_shapes_this_cycle", 0),
            "signed_order_endpoint_called": testnet_order_lifecycle_stats.get("signed_order_endpoint_called", False),
            "order_endpoint_called": testnet_order_lifecycle_stats.get("order_endpoint_called", False),
            "transport_smoke_allowed_once": is_pt_rt1_5_2,
            "transport_smoke_used_this_cycle": testnet_order_lifecycle_stats.get("transport_smoke_used_this_cycle", False),
            "max_testnet_orders_this_phase": max_testnet_orders_this_phase if is_pt_rt1_5_2 else None,
            "reason_codes": testnet_order_lifecycle_stats.get(
                "reason_codes",
                ["baseline_only_trigger", "fixed_testnet_plumbing_notional"],
            ),
        },
        "signed_transport_env_status": signed_transport_env_status
        or {"transport_client_configured": testnet_order_lifecycle_stats.get("transport_submit_configured", False)},
        "testnet_smoke_status": {
            "allowed_once": is_pt_rt1_5_2,
            "trigger_type": (
                "transport_smoke_not_strategy_signal"
                if testnet_order_lifecycle_stats.get("transport_smoke_used_this_cycle")
                else "baseline_fresh_signal"
                if testnet_order_lifecycle_stats.get("fresh_baseline_open_signals_this_cycle", 0)
                else "none"
            ),
            "transport_smoke_used_this_cycle": testnet_order_lifecycle_stats.get("transport_smoke_used_this_cycle", False),
            "fresh_baseline_open_signals_this_cycle": testnet_order_lifecycle_stats.get(
                "fresh_baseline_open_signals_this_cycle",
                0,
            ),
            "max_testnet_orders_this_phase": max_testnet_orders_this_phase if is_pt_rt1_5_2 else None,
            "order_endpoint_called": testnet_order_lifecycle_stats.get("order_endpoint_called", False),
            "signed_order_endpoint_called": testnet_order_lifecycle_stats.get("signed_order_endpoint_called", False),
            "strategy_pnl_update_from_testnet": False,
            "reason_codes": testnet_order_lifecycle_stats.get("reason_codes", []),
        },
        "testnet_order_lifecycle": {
            "rows_this_cycle": len(testnet_order_lifecycle_rows),
            "status_counts": {
                status: sum(1 for row in testnet_order_lifecycle_rows if row.get("status") == status)
                for status in ("created", "preflight_passed", "submitted", "accepted_open", "filled", "partially_filled", "rejected", "cancel_requested", "canceled", "reconciled", "unknown_state", "blocked")
            },
            "rows": testnet_order_lifecycle_rows[:200],
            "separate_from_synthetic_trades": True,
        },
        "runtime_command": {
            "duration_hours_example": ".venv/bin/python scripts/run_pt_rt1_paper_observation.py --duration-hours 24 --output-dir reports/paper_runtime/pt_rt1_1c_24h_dry_run --enable-testnet-probes --founder-approved-testnet-probes-20usdc --testnet-probe-notional-usdc 20 --public-mainnet-only",
            "pt_rt1_5_week1_active_example": ".venv/bin/python scripts/run_pt_rt1_paper_observation.py --duration-hours 24 --output-dir reports/paper_runtime/pt_rt1_5_week1_active --pt-rt1-5-week1-active --signal-evaluation-mode candle_close_only --enable-pt-rt1-5-baseline-testnet-orders --founder-approved-pt-rt1-5-baseline-testnet-orders-25usdc --pt-rt1-5-testnet-order-notional-usdc 25 --disable-testnet-probes --public-mainnet-only",
            "pt_rt1_5_2_transport_smoke_example": ".venv/bin/python scripts/run_pt_rt1_paper_observation.py --duration-minutes 15 --output-dir reports/paper_runtime/pt_rt1_5_2_transport_smoke --pt-rt1-5-week1-active --signal-evaluation-mode candle_close_only --fresh-signal-only-after-runtime-start --enable-baseline-testnet-transport --founder-approved-pt-rt1-5-2-testnet-transport-smoke --pt-rt1-5-testnet-order-notional-usdc 25 --max-testnet-orders-this-phase 1 --public-mainnet-only",
            "pt_rt1_5_2_week1_active_example": ".venv/bin/python scripts/run_pt_rt1_paper_observation.py --duration-hours 24 --output-dir reports/paper_runtime/pt_rt1_5_2_week1_active --pt-rt1-5-week1-active --signal-evaluation-mode candle_close_only --fresh-signal-only-after-runtime-start --enable-baseline-testnet-transport --founder-approved-pt-rt1-5-2-baseline-testnet-orders-25usdc --pt-rt1-5-testnet-order-notional-usdc 25 --public-mainnet-only",
            "smoke_example": ".venv/bin/python scripts/run_pt_rt1_paper_observation.py --duration-minutes 1 --output-dir reports/paper_runtime/pt_rt1_1b_smoke --disable-testnet-probes --public-mainnet-only",
            "output_dir": str(output_dir),
        },
        "smoke_run_status": {
            "status": runtime_status,
            "public_mainnet_fetch_attempted": True,
            "watchlist_resolved": bool(scanner_rows),
            "decisions_recorded": len(decision_rows),
            "decisions_written": len(decision_log_rows),
            "decision_log_mode": decision_log_mode,
            "legacy_probe_orders_submitted": testnet_transport_stats["submitted_this_cycle"] > 0,
            "baseline_testnet_order_endpoint_called": testnet_order_lifecycle_stats.get("order_endpoint_called", False),
            "live_orders_submitted": False,
            "baseline_testnet_order_lifecycle_rows": len(testnet_order_lifecycle_rows),
            "pt_rt1_5_2_transport_smoke_used": testnet_order_lifecycle_stats.get("transport_smoke_used_this_cycle", False),
            "fresh_signal_gate_prevents_startup_mass_opens": fresh_signal_only_after_runtime_start,
            "startup_valid_signals_opened": False if fresh_signal_only_after_runtime_start else None,
            "mtm_open_positions_updated": mtm_stats.get("open_positions_mtm_updated", 0),
            "testnet_probes_enabled": testnet_probes_enabled,
            "testnet_probe_notional_usdc": str(testnet_probe_notional_usdc),
            "private_signed_order_endpoints_called": bool(
                testnet_transport_stats["signed_order_endpoint_called"]
                or testnet_order_lifecycle_stats.get("signed_order_endpoint_called", False)
            ),
            "testnet_order_endpoints_called": bool(
                testnet_transport_stats["order_endpoint_called"]
                or testnet_order_lifecycle_stats.get("order_endpoint_called", False)
            ),
        },
        "paper_runtime_state": {
            "open_positions_count": len(open_positions_by_key),
            "processed_signal_keys_total": len(processed_signal_keys),
            "paper_opens_this_cycle": paper_opens_this_cycle,
            "paper_closes_this_cycle": paper_closes_this_cycle,
            "duplicate_signal_blocks_this_cycle": duplicate_signal_blocks_this_cycle,
            "paper_opens_total": paper_state["paper_opens_total"] + paper_opens_this_cycle,
            "paper_closes_total": paper_state["paper_closes_total"] + paper_closes_this_cycle,
            "duplicate_signal_blocks_total": paper_state["duplicate_signal_blocks_total"] + duplicate_signal_blocks_this_cycle,
            "open_positions_by_key": open_positions_by_key,
            "realized_equity_by_lane": realized_equity_by_lane,
            "unrealized_pnl_by_lane": unrealized_pnl_by_lane,
            "total_equity_by_lane": total_equity_by_lane,
            "last_evaluated_closed_candle_by_timeframe": last_evaluated_closed_candle_by_timeframe,
            "testnet_order_keys_total": len(testnet_order_keys),
            "testnet_orders_total": paper_state["testnet_orders_total"] + len(testnet_order_lifecycle_rows),
            "paper_pnl_source": "synthetic_public_mainnet_paper_ledger",
            "testnet_fills_update_strategy_pnl": False,
        },
        "open_position_mtm": mtm_stats,
        "next_phase_decision": (
            "PT-RT1.5.2 may continue signed testnet lifecycle observation after fresh baseline signals"
            if is_pt_rt1_5_2 and runtime_status == "verified"
            else "PT-RT1.5.2 blocked"
            if is_pt_rt1_5_2
            else "PT-RT1.5.2 may continue signed testnet lifecycle observation after fresh baseline signals"
            if is_pt_rt1_5_1 and runtime_status == "verified"
            else "PT-RT1.5.1 blocked"
            if is_pt_rt1_5_1
            else
            "PT-RT1.3 may continue paper observation; missing/stale mids are warning-only when closed candles are available"
            if is_pt_rt1_3 and runtime_status == "verified"
            else "PT-RT1.3 blocked"
            if is_pt_rt1_3
            else "PT-RT1.5 active Week 1 may continue with candle-close signal evaluation and baseline-only testnet lifecycle gates"
            if is_pt_rt1_5 and runtime_status == "verified"
            else "PT-RT1.5 blocked"
            if is_pt_rt1_5
            else "PT-RT1.2 may continue paper observation; signed testnet transport remains blocked unless exact transport approval and a configured client are present"
            if is_pt_rt1_2 and runtime_status == "verified"
            else "PT-RT1.2 blocked"
            if is_pt_rt1_2
            else
            "PT-RT1.1D may evaluate 24-hour runtime artifacts after completion"
            if is_pt_rt1_1c and runtime_status == "verified"
            else "PT-RT1.1D blocked"
            if is_pt_rt1_1c
            else
            "PT-RT1.1C may start 24-hour probes-disabled runtime collection"
            if runtime_status == "verified"
            else "PT-RT1.1C blocked"
        ),
    }
    _append_jsonl(output_dir / "decisions.jsonl", decision_log_rows)
    decisions_size = (output_dir / "decisions.jsonl").stat().st_size if (output_dir / "decisions.jsonl").exists() else 0
    summary["decision_log_stats"] = {
        **decision_log_stats,
        "decisions_jsonl_size_bytes": decisions_size,
        "decisions_jsonl_warning_threshold_bytes": DECISION_LOG_SIZE_WARNING_BYTES,
        "decisions_jsonl_warning": decisions_size >= DECISION_LOG_SIZE_WARNING_BYTES,
    }
    _write_json(output_dir / "summary.json", summary)
    _write_json(
        output_dir / "state.json",
        {
            "generated_at_utc": _iso(now),
            "strategy_lanes": lane_payload,
            "decision_log_mode": decision_log_mode,
            "decision_log_seen_keys": sorted(decision_log_seen_keys),
            "paper_runtime": _paper_runtime_state_payload(
                runtime_start_utc=runtime_start_utc,
                fresh_signal_only_after_runtime_start=fresh_signal_only_after_runtime_start,
                warm_start_evaluation_completed=warm_start_evaluation_completed or warm_start_evaluation_this_cycle,
                warm_start_entry_context_by_key=warm_start_entry_context_by_key,
                startup_valid_signals_blocked_total=paper_state["startup_valid_signals_blocked_total"]
                + warm_start_gate_stats.get("startup_valid_signals_blocked_this_cycle", 0),
                waiting_for_reset_signals_total=paper_state["waiting_for_reset_signals_total"]
                + warm_start_gate_stats.get("waiting_for_reset_signals_this_cycle", 0),
                fresh_post_start_opens_total=paper_state["fresh_post_start_opens_total"]
                + warm_start_gate_stats.get("fresh_post_start_opens_this_cycle", 0),
                entry_context_resets_total=paper_state["entry_context_resets_total"]
                + warm_start_gate_stats.get("entry_context_resets_this_cycle", 0),
                processed_signal_keys=processed_signal_keys,
                open_positions_by_key=open_positions_by_key,
                realized_equity_by_lane=realized_equity_by_lane,
                unrealized_pnl_by_lane=unrealized_pnl_by_lane,
                last_processed_close_by_key=last_processed_close_by_key,
                paper_opens_total=paper_state["paper_opens_total"] + paper_opens_this_cycle,
                paper_closes_total=paper_state["paper_closes_total"] + paper_closes_this_cycle,
                duplicate_signal_blocks_total=paper_state["duplicate_signal_blocks_total"]
                + duplicate_signal_blocks_this_cycle,
                last_evaluated_closed_candle_by_timeframe=last_evaluated_closed_candle_by_timeframe,
                testnet_order_keys=testnet_order_keys,
                testnet_orders_total=paper_state["testnet_orders_total"] + len(testnet_order_lifecycle_rows),
            ),
        },
    )
    _write_json(output_dir / "data_health.json", {"generated_at_utc": _iso(now), "rows": market_health})
    _write_json(output_dir / "equity_curves.json", {"generated_at_utc": _iso(now), "lanes": lane_payload})
    _append_jsonl(output_dir / "runtime_audit.jsonl", [summary["connection_status"], summary["testnet_plumbing_status"]])
    _append_jsonl(output_dir / "testnet_probe_audit.jsonl", testnet_probe_rows)
    _append_jsonl(output_dir / "testnet_probe_transport.jsonl", testnet_transport_rows)
    _append_jsonl(output_dir / "testnet_order_lifecycle.jsonl", testnet_order_lifecycle_rows)
    _append_jsonl(output_dir / "trades.jsonl", trade_rows)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    duration = parser.add_mutually_exclusive_group(required=True)
    duration.add_argument("--duration-hours", type=Decimal)
    duration.add_argument("--duration-minutes", type=Decimal)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    probe_mode = parser.add_mutually_exclusive_group(required=False)
    probe_mode.add_argument("--disable-testnet-probes", action="store_true")
    probe_mode.add_argument("--disable-legacy-testnet-probes", action="store_true")
    probe_mode.add_argument("--enable-testnet-probes", action="store_true")
    parser.add_argument("--founder-approved-testnet-probes-20usdc", action="store_true")
    parser.add_argument("--submit-testnet-probes", action="store_true")
    parser.add_argument("--founder-approved-pt-rt1-2-testnet-transport-20usdc", action="store_true")
    parser.add_argument("--testnet-probe-notional-usdc", type=Decimal, default=PT_RT1_TESTNET_PROBE_NOTIONAL_USDC)
    parser.add_argument("--testnet-probe-daily-cap", type=int, default=TESTNET_PROBE_AUDIT_LIMIT)
    parser.add_argument("--pt-rt1-5-week1-active", action="store_true")
    parser.add_argument("--enable-pt-rt1-5-baseline-testnet-orders", action="store_true")
    parser.add_argument("--enable-baseline-testnet-transport", action="store_true")
    parser.add_argument("--founder-approved-pt-rt1-5-baseline-testnet-orders-25usdc", action="store_true")
    parser.add_argument("--founder-approved-pt-rt1-5-1-baseline-testnet-orders-25usdc", action="store_true")
    parser.add_argument("--founder-approved-pt-rt1-5-2-testnet-transport-smoke", action="store_true")
    parser.add_argument("--founder-approved-pt-rt1-5-2-baseline-testnet-orders-25usdc", action="store_true")
    parser.add_argument(
        "--pt-rt1-5-testnet-order-notional-usdc",
        type=Decimal,
        default=PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC,
    )
    parser.add_argument(
        "--pt-rt1-5-testnet-daily-order-cap",
        type=int,
        default=PT_RT1_5_TESTNET_DAILY_ORDER_CAP_DEFAULT,
    )
    parser.add_argument(
        "--pt-rt1-5-testnet-per-symbol-daily-cap",
        type=int,
        default=PT_RT1_5_TESTNET_PER_SYMBOL_DAILY_CAP_DEFAULT,
    )
    parser.add_argument("--signal-evaluation-mode", choices=("poll", "candle_close_only"), default="poll")
    parser.add_argument("--fresh-signal-only-after-runtime-start", action="store_true")
    parser.add_argument(
        "--max-testnet-orders-this-phase",
        type=int,
        default=PT_RT1_5_2_TESTNET_SMOKE_PHASE_CAP,
    )
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--public-mainnet-only", action="store_true")
    parser.add_argument("--poll-seconds", type=Decimal, default=Decimal("60"))
    parser.add_argument("--symbol", action="append", dest="symbols")
    parser.add_argument("--timeframe", action="append", choices=tuple(TIMEFRAME_DURATIONS), dest="timeframes")
    parser.add_argument("--max-cycles", type=int)
    parser.add_argument("--max-candle-symbols", type=int)
    parser.add_argument("--decision-log-mode", choices=DECISION_LOG_MODES, default="compact")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.public_mainnet_only:
        raise SystemExit("public_mainnet_only_required_for_strategy_truth")
    if args.enable_testnet_probes and not args.founder_approved_testnet_probes_20usdc:
        raise SystemExit("founder_approved_testnet_probes_20usdc_required")
    if args.submit_testnet_probes and not args.enable_testnet_probes:
        raise SystemExit("submit_testnet_probes_requires_enable_testnet_probes")
    if args.submit_testnet_probes and not args.founder_approved_pt_rt1_2_testnet_transport_20usdc:
        raise SystemExit("founder_approved_pt_rt1_2_testnet_transport_20usdc_required")
    if args.testnet_probe_notional_usdc != PT_RT1_TESTNET_PROBE_NOTIONAL_USDC:
        raise SystemExit("testnet_probe_notional_must_be_20usdc")
    if args.testnet_probe_daily_cap <= 0:
        raise SystemExit("positive_testnet_probe_daily_cap_required")
    output_dir_posix = Path(args.output_dir).as_posix()
    is_pt_rt1_5_2_output = output_dir_posix in {
        PT_RT1_5_2_TRANSPORT_SMOKE_OUTPUT_DIR,
        PT_RT1_5_2_RUNTIME_OUTPUT_DIR,
    }
    is_pt_rt1_5_2_requested = (
        is_pt_rt1_5_2_output
        or args.founder_approved_pt_rt1_5_2_testnet_transport_smoke
        or args.founder_approved_pt_rt1_5_2_baseline_testnet_orders_25usdc
    )
    baseline_transport_requested = (
        args.enable_pt_rt1_5_baseline_testnet_orders or args.enable_baseline_testnet_transport
        or args.founder_approved_pt_rt1_5_2_testnet_transport_smoke
        or args.founder_approved_pt_rt1_5_2_baseline_testnet_orders_25usdc
    )
    is_pt_rt1_5_1_smoke = (
        not is_pt_rt1_5_2_requested
        and (
            args.fresh_signal_only_after_runtime_start
            or output_dir_posix == PT_RT1_5_1_RUNTIME_OUTPUT_DIR
        )
    )
    if args.pt_rt1_5_week1_active:
        allowed_pt_rt15_output_dirs = {PT_RT1_5_RUNTIME_OUTPUT_DIR}
        if is_pt_rt1_5_1_smoke:
            allowed_pt_rt15_output_dirs.add(PT_RT1_5_1_RUNTIME_OUTPUT_DIR)
        if is_pt_rt1_5_2_requested:
            allowed_pt_rt15_output_dirs.update(
                {PT_RT1_5_2_TRANSPORT_SMOKE_OUTPUT_DIR, PT_RT1_5_2_RUNTIME_OUTPUT_DIR}
            )
        if output_dir_posix not in allowed_pt_rt15_output_dirs:
            raise SystemExit("pt_rt1_5_output_dir_must_be_reports_paper_runtime_pt_rt1_5_week1_active")
        if args.enable_testnet_probes:
            raise SystemExit("pt_rt1_5_uses_disable_testnet_probes_and_baseline_order_transport")
        if args.signal_evaluation_mode == "poll":
            args.signal_evaluation_mode = "candle_close_only"
    if output_dir_posix == PT_RT1_5_1_RUNTIME_OUTPUT_DIR and not args.fresh_signal_only_after_runtime_start:
        raise SystemExit("pt_rt1_5_1_smoke_requires_fresh_signal_only_after_runtime_start")
    if is_pt_rt1_5_2_output and not args.fresh_signal_only_after_runtime_start:
        raise SystemExit("pt_rt1_5_2_requires_fresh_signal_only_after_runtime_start")
    if baseline_transport_requested and not args.pt_rt1_5_week1_active:
        raise SystemExit("pt_rt1_5_baseline_testnet_orders_require_pt_rt1_5_week1_active")
    if (
        baseline_transport_requested
        and not args.founder_approved_pt_rt1_5_baseline_testnet_orders_25usdc
        and not args.founder_approved_pt_rt1_5_1_baseline_testnet_orders_25usdc
        and not args.founder_approved_pt_rt1_5_2_testnet_transport_smoke
        and not args.founder_approved_pt_rt1_5_2_baseline_testnet_orders_25usdc
    ):
        raise SystemExit("founder_approved_pt_rt1_5_baseline_testnet_orders_25usdc_required")
    if args.pt_rt1_5_testnet_order_notional_usdc != PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC:
        raise SystemExit("pt_rt1_5_testnet_order_notional_must_be_25usdc")
    if args.pt_rt1_5_testnet_daily_order_cap <= 0:
        raise SystemExit("positive_pt_rt1_5_testnet_daily_order_cap_required")
    if args.pt_rt1_5_testnet_per_symbol_daily_cap <= 0:
        raise SystemExit("positive_pt_rt1_5_testnet_per_symbol_daily_cap_required")
    if args.max_testnet_orders_this_phase < 0:
        raise SystemExit("nonnegative_max_testnet_orders_this_phase_required")
    env_load_status = _load_pt_rt1_5_2_env_file(args.env_file) if is_pt_rt1_5_2_requested else {}
    signed_transport_env_status = pt_rt1_5_2_signed_transport_env_status() if is_pt_rt1_5_2_requested else None
    if signed_transport_env_status is not None:
        signed_transport_env_status = {**signed_transport_env_status, "env_load_status": env_load_status}
    _ensure_ignored_output_dir(args.output_dir)
    duration = timedelta(
        hours=float(args.duration_hours or Decimal("0")),
        minutes=float(args.duration_minutes or Decimal("0")),
    )
    if duration <= timedelta(0):
        raise SystemExit("positive_duration_required")
    connector = HyperliquidPublicMarketDataConnector()
    baseline_testnet_order_base_url = os.environ.get(
        HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV,
        PT_RT1_TESTNET_INFO_URL,
    ).strip()
    baseline_testnet_order_kill_switch = _env_truthy(
        os.environ.get(PT_RT1_5_TESTNET_ORDER_TRANSPORT_KILL_SWITCH_ENV)
    )
    baseline_testnet_order_transport: BaselineTestnetOrderTransport | None = None
    if baseline_transport_requested and not baseline_testnet_order_kill_switch:
        baseline_testnet_order_transport = HyperliquidPT_RT15TestnetOrderTransport.from_env()
    end_time = _utc_now() + duration
    run_label = (
        "PT-RT1.5.2"
        if args.pt_rt1_5_week1_active and is_pt_rt1_5_2_requested
        else
        "PT-RT1.5.1"
        if args.pt_rt1_5_week1_active and is_pt_rt1_5_1_smoke
        else
        "PT-RT1.5"
        if args.pt_rt1_5_week1_active
        else "PT-RT1.3"
        if args.enable_testnet_probes
        else "PT-RT1.1C"
        if "pt_rt1_1c" in str(args.output_dir)
        else "PT-RT1.1B"
    )
    cycle = 0
    last_summary: dict[str, Any] = {}
    while True:
        cycle += 1
        last_summary = run_cycle(
            connector=connector,
            output_dir=args.output_dir,
            symbols=args.symbols,
            timeframes=args.timeframes or PT_RT1_4_ACTIVE_TIMEFRAMES,
            max_candle_symbols=args.max_candle_symbols,
            run_label=run_label,
            decision_log_mode=args.decision_log_mode,
            testnet_probes_enabled=args.enable_testnet_probes,
            testnet_probe_approval_text=(
                PT_RT1_EXACT_TESTNET_PROBE_APPROVAL if args.founder_approved_testnet_probes_20usdc else ""
            ),
            testnet_probe_notional_usdc=args.testnet_probe_notional_usdc,
            testnet_probe_daily_cap=args.testnet_probe_daily_cap,
            submit_testnet_probes=args.submit_testnet_probes,
            testnet_probe_transport_approval_text=(
                PT_RT1_2_EXACT_TRANSPORT_APPROVAL
                if args.founder_approved_pt_rt1_2_testnet_transport_20usdc
                else ""
            ),
            signal_evaluation_mode=args.signal_evaluation_mode,
            baseline_testnet_order_transport_enabled=baseline_transport_requested,
            baseline_testnet_order_approval_text=(
                PT_RT1_5_2_EXACT_TESTNET_TRANSPORT_SMOKE_APPROVAL
                if (
                    args.founder_approved_pt_rt1_5_2_testnet_transport_smoke
                    or args.founder_approved_pt_rt1_5_2_baseline_testnet_orders_25usdc
                )
                else
                PT_RT1_5_1_EXACT_BASELINE_TESTNET_ORDER_APPROVAL
                if args.founder_approved_pt_rt1_5_1_baseline_testnet_orders_25usdc
                else
                PT_RT1_5_EXACT_BASELINE_TESTNET_ORDER_APPROVAL
                if args.founder_approved_pt_rt1_5_baseline_testnet_orders_25usdc
                else ""
            ),
            baseline_testnet_order_notional_usdc=args.pt_rt1_5_testnet_order_notional_usdc,
            baseline_testnet_order_daily_cap=args.pt_rt1_5_testnet_daily_order_cap,
            baseline_testnet_order_per_symbol_daily_cap=args.pt_rt1_5_testnet_per_symbol_daily_cap,
            baseline_testnet_order_base_url=baseline_testnet_order_base_url,
            baseline_testnet_order_kill_switch=baseline_testnet_order_kill_switch,
            baseline_testnet_order_transport=baseline_testnet_order_transport,
            fresh_signal_only_after_runtime_start=args.fresh_signal_only_after_runtime_start,
            pt_rt1_5_2_transport_smoke_enabled=args.founder_approved_pt_rt1_5_2_testnet_transport_smoke,
            max_testnet_orders_this_phase=args.max_testnet_orders_this_phase,
            signed_transport_env_status=signed_transport_env_status,
        )
        if args.max_cycles is not None and cycle >= args.max_cycles:
            break
        now = _utc_now()
        if now >= end_time:
            break
        sleep_seconds = min(float(args.poll_seconds), max(0.0, (end_time - now).total_seconds()))
        if sleep_seconds:
            time.sleep(sleep_seconds)
    print(json.dumps(_json_safe({"summary_path": str(args.output_dir / "summary.json"), "status": last_summary.get("status")}), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
