from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from services.exchange.hyperliquid.precision import HyperliquidPrecisionFormatter
from services.exchange.hyperliquid.signing import signer_address
from services.uat.sandbox import (
    HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV,
    HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ROLE_ENV,
    HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV,
    HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV,
    HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT_ENV,
    HYPERLIQUID_UAT_SANDBOX_VAULT_ADDRESS_ENV,
    SandboxAccountStateSnapshot,
    SandboxDrawdownFeedStatus,
    build_sandbox_account_drawdown_feed,
)
from services.uat.sandbox_order import (
    UAT31FirstSandboxOrderAttemptService,
    UAT33RejectReason,
    UAT33_UNIVERSE_SYMBOLS,
    build_uat31_market_plan,
    build_uat33_idempotency_key,
    evaluate_uat32_account_api_wallet_readiness,
    resolve_hyperliquid_uat_account_target,
    validate_uat33_universe_precision,
)


NOW = datetime(2026, 5, 10, 20, 0, tzinfo=UTC)


def _env() -> dict[str, str]:
    private_key = "0x" + ("1" * 64)
    account = signer_address(private_key)
    return {
        HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV: private_key,
        HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV: account,
        HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT_ENV: account,
        HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV: "https://api.hyperliquid-testnet.xyz",
    }


def test_normal_user_mode_omits_vault_address_and_does_not_copy_account() -> None:
    env = _env()
    env[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ROLE_ENV] = "user"
    result = resolve_hyperliquid_uat_account_target(
        env=env,
        signer=signer_address(env[HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV]),
        account_role_payload={"role": "user"},
    )

    assert result.allowed is True
    assert result.target is not None
    assert result.target.vault_address is None
    assert result.summary["vaultAddress_present"] is False


def test_subaccount_mode_includes_explicit_vault_address() -> None:
    env = _env()
    subaccount = "0x" + ("2" * 40)
    env[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ROLE_ENV] = "subaccount"
    env[HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT_ENV] = subaccount
    result = resolve_hyperliquid_uat_account_target(
        env=env,
        signer=signer_address(env[HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV]),
        account_role_payload={"role": "subAccount", "data": {"master": env[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV]}},
    )

    assert result.allowed is True
    assert result.target is not None
    assert result.target.vault_address == subaccount.lower()
    assert result.summary["vaultAddress_present"] is True


def test_confirmed_legacy_subaccount_account_can_be_used_as_vault_address() -> None:
    env = _env()
    subaccount = "0x" + ("2" * 40)
    env[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV] = subaccount
    env.pop(HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT_ENV)
    env[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ROLE_ENV] = "subaccount"
    result = resolve_hyperliquid_uat_account_target(
        env=env,
        signer=signer_address(env[HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV]),
        account_role_payload={"role": "subAccount"},
    )

    assert result.allowed is True
    assert result.target is not None
    assert result.target.vault_address == subaccount.lower()


def test_agent_authorized_for_master_is_accepted_for_subaccount_target() -> None:
    env = _env()
    subaccount = "0x" + ("2" * 40)
    master = env[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV]
    feed = build_sandbox_account_drawdown_feed(
        snapshot=SandboxAccountStateSnapshot(
            venue="hyperliquid",
            sandbox_account_id=subaccount,
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
        account_id=subaccount,
        signer="0x" + ("7" * 40),
        account_role_payload={"role": "subAccount", "data": {"master": master}},
        signer_role_payload={"role": "agent", "data": {"user": master}},
        drawdown_feed=feed,
        requested_notional=Decimal("9.9"),
        now_utc=NOW,
    )

    assert readiness.allowed is True
    assert readiness.api_wallet_authorized_for_account is True


def test_vault_mode_includes_explicit_vault_address() -> None:
    env = _env()
    vault = "0x" + ("3" * 40)
    env[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ROLE_ENV] = "vault"
    env[HYPERLIQUID_UAT_SANDBOX_VAULT_ADDRESS_ENV] = vault
    result = resolve_hyperliquid_uat_account_target(
        env=env,
        signer=signer_address(env[HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV]),
        account_role_payload={"role": "vault"},
    )

    assert result.allowed is True
    assert result.target is not None
    assert result.target.vault_address == vault.lower()


def test_unknown_account_role_blocks_payload_construction() -> None:
    env = _env()
    env[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ROLE_ENV] = "mystery"
    result = resolve_hyperliquid_uat_account_target(
        env=env,
        signer="0x" + ("4" * 40),
        account_role_payload={"role": "mystery"},
    )

    assert result.blocked is True
    assert UAT33RejectReason.UNKNOWN_ACCOUNT_ROLE in result.reason_codes


def test_subaccount_mode_requires_explicit_target_or_vault_address() -> None:
    env = _env()
    env[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ROLE_ENV] = "subaccount"
    env.pop(HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT_ENV)
    env.pop(HYPERLIQUID_UAT_SANDBOX_VAULT_ADDRESS_ENV, None)
    result = resolve_hyperliquid_uat_account_target(
        env=env,
        signer=signer_address(env[HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV]),
        account_role_payload=None,
    )

    assert result.blocked is True
    assert UAT33RejectReason.VAULT_ADDRESS_REQUIRED in result.reason_codes


def test_normal_account_with_vault_address_blocks() -> None:
    env = _env()
    env[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ROLE_ENV] = "master"
    env[HYPERLIQUID_UAT_SANDBOX_VAULT_ADDRESS_ENV] = "0x" + ("5" * 40)
    result = resolve_hyperliquid_uat_account_target(
        env=env,
        signer=signer_address(env[HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV]),
        account_role_payload={"role": "user"},
    )

    assert result.blocked is True
    assert UAT33RejectReason.NORMAL_ACCOUNT_VAULT_FORBIDDEN in result.reason_codes


def test_payload_summary_abbreviates_addresses_and_excludes_private_key() -> None:
    env = _env()
    result = resolve_hyperliquid_uat_account_target(
        env=env,
        signer=signer_address(env[HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV]),
        account_role_payload={"role": "user"},
    )
    serialized = str(result.summary)

    assert env[HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV] not in serialized
    assert result.summary["target_account_abbrev"].startswith("0x")
    assert "..." in result.summary["target_account_abbrev"]


def test_signed_payload_omits_vault_for_normal_user_and_includes_for_subaccount() -> None:
    env = _env()
    signer = signer_address(env[HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV])
    normal = resolve_hyperliquid_uat_account_target(
        env=env,
        signer=signer,
        account_role_payload={"role": "user"},
    )
    sub_env = dict(env)
    sub_env[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ROLE_ENV] = "subaccount"
    sub_env[HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT_ENV] = "0x" + ("6" * 40)
    sub = resolve_hyperliquid_uat_account_target(
        env=sub_env,
        signer=signer,
        account_role_payload={"role": "subAccount"},
    )
    action = {"type": "order", "orders": [], "grouping": "na"}

    normal_payload = UAT31FirstSandboxOrderAttemptService._signed_payload(
        action=action,
        private_key=env[HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV],
        account_id=env[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV],
        is_mainnet=False,
        account_target=normal.target,
    )
    sub_payload = UAT31FirstSandboxOrderAttemptService._signed_payload(
        action=action,
        private_key=env[HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV],
        account_id=sub_env[HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT_ENV],
        is_mainnet=False,
        account_target=sub.target,
    )

    assert normal_payload["vaultAddress"] is None
    assert sub_payload["vaultAddress"] == sub_env[HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT_ENV].lower()


def test_precision_formatter_respects_hyperliquid_price_and_size_rules() -> None:
    formatter = HyperliquidPrecisionFormatter(asset_id=4, symbol="ETH", sz_decimals=4)

    price = formatter.format_price_down(Decimal("2375.79"))
    size = formatter.format_size_down(Decimal("0.00423456"))

    assert formatter.max_price_decimals == 2
    assert price.wire_value == "2375.7"
    assert size.wire_value == "0.0042"
    assert "5_sig_figs" in price.reason
    assert "sz_decimals_4" in size.reason


def test_precision_formatter_allows_integer_prices_above_five_significant_figures() -> None:
    formatter = HyperliquidPrecisionFormatter(asset_id=0, symbol="BTC", sz_decimals=5)

    assert formatter.format_price_down(Decimal("123456")).wire_value == "123456"


def test_market_plan_uses_precision_formatter_for_valid_eth_price() -> None:
    plan, reasons = build_uat31_market_plan(
        meta_payload={"universe": [{"name": "BTC", "szDecimals": 5}, {"name": "ETH", "szDecimals": 4}]},
        l2_book_payload={"levels": [[{"px": "2375.79"}], [{"px": "2376.01"}]]},
        max_notional=Decimal("10"),
        cloid=build_uat33_idempotency_key(account_id=_env()[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV], observed_at_utc=NOW),
    )

    assert reasons == ()
    assert plan is not None
    assert str(plan.limit_price) == "2375.7"
    assert str(plan.quantity) == "0.0042"
    assert plan.estimated_notional < Decimal("10")


def test_uat_universe_precision_validation_covers_all_symbols() -> None:
    meta = {
        "universe": [
            {"name": symbol, "szDecimals": 4 if symbol == "ETH" else 5 if symbol == "BTC" else 2}
            for symbol in UAT33_UNIVERSE_SYMBOLS
        ]
    }
    mids = {"mids": {symbol: "123.456789" for symbol in UAT33_UNIVERSE_SYMBOLS}}
    rows = validate_uat33_universe_precision(meta_payload=meta, mids_payload=mids)

    assert {row.symbol for row in rows} == set(UAT33_UNIVERSE_SYMBOLS)
    assert all(row.precision_validation_passed for row in rows)
    assert all(row.formatted_sample_post_only_buy_price is not None for row in rows)
    assert all(row.formatted_sample_size is not None for row in rows)
