from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import urllib.parse
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils

from core.domain.enums import (
    DecisionAction,
    Environment,
    MarketType,
    OrderIntentStatus,
    OrderSide,
    OrderType,
    ProductType,
    StrategyFamily,
    SubmittedOrderStatus,
    Venue,
)
from db.models import (
    ClientModel,
    InstrumentModel,
    MandateAccountBindingModel,
    OrderIntentModel,
    StrategyMandateModel,
    SymbolModel,
    VenueAccountModel,
)
from services.execution.service import DefaultExecutionService
from services.exchange.aster.adapter import AsterExchangeAdapter
from services.exchange.base import VenueAdapterError
from services.exchange.binance.adapter import BinanceExchangeAdapter
from services.exchange.coinbase.adapter import CoinbaseAdvancedTradeExchangeAdapter
from services.exchange.hyperliquid.adapter import HyperliquidExchangeAdapter
from services.exchange.hyperliquid.signing import sign_l1_action
from services.exchange.kraken.adapter import KrakenExchangeAdapter
from services.exchange.okx.adapter import OkxExchangeAdapter
from tests.test_phase3_strategy import build_settings, build_test_session_factory


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def _decode_bearer_token(header_value: str) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]:
    assert header_value.startswith("Bearer ")
    token = header_value.removeprefix("Bearer ")
    encoded_header, encoded_payload, encoded_signature = token.split(".")
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    return (
        json.loads(_b64url_decode(encoded_header)),
        json.loads(_b64url_decode(encoded_payload)),
        _b64url_decode(encoded_signature),
        signing_input,
    )


def _generate_ec_private_key_pem() -> str:
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


def _parse_form_body(body: str) -> dict[str, str]:
    return dict(urllib.parse.parse_qsl(body, keep_blank_values=True))


def _verify_coinbase_jwt_signature(token_header: str, private_key_pem: str) -> None:
    header, payload, signature, signing_input = _decode_bearer_token(token_header)
    assert header["alg"] == "ES256"
    assert header["typ"] == "JWT"
    assert payload["iss"] == "cdp"
    assert len(signature) == 64
    der_signature = utils.encode_dss_signature(
        int.from_bytes(signature[:32], "big"),
        int.from_bytes(signature[32:], "big"),
    )
    private_key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
    public_key = private_key.public_key()
    public_key.verify(der_signature, signing_input, ec.ECDSA(hashes.SHA256()))


def _seed_submission_intent(
    session_factory,
    *,
    venue: Venue,
    account_suffix: str,
    symbol: str,
    exchange_symbol: str,
    market_type: MarketType,
    product_type: ProductType,
    venue_native_account_id: str,
    account_address: str,
    credentials_ref: str,
    account_auth: dict[str, str] | None = None,
    subaccount_label: str | None = None,
    action: DecisionAction = DecisionAction.REDUCE,
    side: OrderSide = OrderSide.SELL,
    order_type: OrderType = OrderType.MARKET,
    limit_price: Decimal | None = None,
    quantity: Decimal = Decimal("0.01"),
    reduce_only: bool = True,
    asset_id: int | None = None,
) -> tuple[str, str]:
    with session_factory() as session:
        client = session.query(ClientModel).filter(ClientModel.client_key == "client-submission").one_or_none()
        if client is None:
            client = ClientModel(
                client_key="client-submission",
                display_name="Client Submission",
                is_active=True,
            )
            session.add(client)
            session.flush()

        mandate = StrategyMandateModel(
            client_ref_id=client.id,
            mandate_key=f"money_flow::{venue.value}::{account_suffix}",
            family=StrategyFamily.MONEY_FLOW,
            enabled=True,
            allow_builder_deployed_for_strategy=False,
            allow_builder_deployed_for_trading=False,
            metadata={},
        )
        session.add(mandate)
        session.flush()

        account = VenueAccountModel(
            venue_account_key=f"{venue.value}-{account_suffix}",
            client_ref_id=client.id,
            venue=venue.value,
            environment=Environment.TESTNET,
            venue_native_account_id=venue_native_account_id,
            account_address=account_address,
            account_label=account_suffix,
            subaccount_label=subaccount_label,
            credentials_ref=credentials_ref,
            wallet_ref=None,
            is_active=True,
            trading_enabled=True,
            raw_metadata={"auth": dict(account_auth or {})},
        )
        session.add(account)
        session.flush()

        binding = MandateAccountBindingModel(
            strategy_mandate_ref_id=mandate.id,
            binding_key=f"{mandate.mandate_key}::{account.venue_account_key}",
            venue_account_ref_id=account.id,
            enabled=True,
            strategy_eligible=True,
            routing_eligible=True,
            trading_enabled=True,
            allow_builder_deployed_for_strategy=False,
            allow_builder_deployed_for_trading=False,
            metadata={},
        )
        session.add(binding)
        session.flush()

        settlement_asset = "USDT" if market_type == MarketType.PERPETUAL else None
        quote_asset = "USD" if venue in {Venue.COINBASE_ADVANCED_TRADE, Venue.KRAKEN} else "USDT"
        instrument_key = (
            f"{market_type.value}:{product_type.value}:{symbol}:{quote_asset}:"
            f"{settlement_asset or ''}"
        )
        instrument = session.query(InstrumentModel).filter(InstrumentModel.instrument_key == instrument_key).one_or_none()
        if instrument is None:
            instrument = InstrumentModel(
                instrument_key=instrument_key,
                canonical_symbol=symbol,
                market_type=market_type,
                product_type=product_type,
                base_asset=symbol,
                quote_asset=quote_asset,
                settlement_asset=settlement_asset,
                is_active=True,
            )
            session.add(instrument)
            session.flush()

        symbol_model = (
            session.query(SymbolModel)
            .filter(SymbolModel.venue == venue.value, SymbolModel.exchange_symbol == exchange_symbol)
            .one_or_none()
        )
        if symbol_model is None:
            symbol_model = SymbolModel(
                instrument_ref_id=instrument.id,
                venue=venue.value,
                symbol=symbol,
                exchange_symbol=exchange_symbol,
                venue_asset_id=exchange_symbol,
                asset_id=asset_id,
                market_type=market_type,
                product_type=product_type,
                base_asset=symbol,
                quote_asset=quote_asset,
                settlement_asset=settlement_asset,
                price_tick_size=Decimal("0.1"),
                quantity_step_size=Decimal("0.001"),
                min_order_size=Decimal("0.001"),
                size_decimals=3,
                max_leverage=20 if market_type == MarketType.PERPETUAL else None,
                only_isolated=False,
                is_perpetual=market_type == MarketType.PERPETUAL,
                is_builder_deployed=False,
                is_strategy_eligible=True,
                is_trading_eligible=True,
                is_active=True,
                raw_metadata={},
            )
            session.add(symbol_model)
            session.flush()

        intent = OrderIntentModel(
            environment=Environment.TESTNET,
            intent_id=f"intent-{venue.value}-{account_suffix}",
            decision_id=f"decision-{venue.value}-{account_suffix}",
            action=action,
            mandate_desired_trade_ref_id=None,
            desired_trade_key=f"trade-{venue.value}-{account_suffix}",
            sleeve_id="sleeve_1h",
            component_key="sleeve_1h",
            client_ref_id=client.id,
            strategy_mandate_ref_id=mandate.id,
            mandate_account_binding_ref_id=binding.id,
            binding_key=binding.binding_key,
            venue_account_ref_id=account.id,
            instrument_key=instrument.instrument_key,
            instrument_ref_id=instrument.id,
            symbol_id=symbol_model.id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            limit_price=limit_price,
            reduce_only=reduce_only,
            ttl_seconds=30,
            status=OrderIntentStatus.PREPARED,
            idempotency_key=f"idem-{venue.value}-{account_suffix}",
            provenance={"phase_boundary": "phase_4_3_2"},
            created_at=datetime.now(UTC),
        )
        session.add(intent)
        session.commit()
        return intent.intent_id, account.id


def _load_intent(session_factory, intent_id: str):
    execution = DefaultExecutionService(build_settings(), session_factory=session_factory)
    return asyncio.run(execution.get_child_intent(intent_id))


def test_hyperliquid_submit_path_uses_sdk_faithful_signing_and_targeted_wallet_context() -> None:
    session_factory = build_test_session_factory()
    account_private_key = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    intent_id, account_id = _seed_submission_intent(
        session_factory,
        venue=Venue.HYPERLIQUID,
        account_suffix="wallet-a",
        symbol="BTC",
        exchange_symbol="BTC",
        market_type=MarketType.PERPETUAL,
        product_type=ProductType.LINEAR,
        venue_native_account_id="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        account_address="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        credentials_ref="hl-wallet-a",
        account_auth={"signing_private_key": account_private_key},
        action=DecisionAction.REDUCE,
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        limit_price=Decimal("50000"),
        reduce_only=True,
        asset_id=0,
    )
    intent = _load_intent(session_factory, intent_id)
    captured: list[dict[str, object]] = []

    async def transport(payload):
        captured.append(dict(payload))
        return {"orderId": "hl-submit-1", "status": "accepted"}

    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_USE_TESTNET=True,
        EXECUTION_DRY_RUN=False,
        HYPERLIQUID_READ_ONLY_MODE=False,
        HYPERLIQUID_DRY_RUN_MODE=False,
        HYPERLIQUID_SUBMISSION_ENABLED=True,
        HYPERLIQUID_SUBMISSION_AUTHORIZED=True,
        EXCHANGE_SIGNING_PRIVATE_KEY="0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        EXCHANGE_ACCOUNT_ADDRESS="0x1111111111111111111111111111111111111111",
        EXCHANGE_CREDENTIALS_REF="hl-global-profile",
    )
    adapter = HyperliquidExchangeAdapter(settings, transport=transport, session_factory=session_factory)

    submitted = asyncio.run(adapter.submit_order(intent))

    assert submitted.venue_account_ref_id == account_id
    assert submitted.account_address == "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert submitted.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert captured
    exchange_payload = captured[0]
    assert "credentials_ref" not in exchange_payload
    assert exchange_payload["vaultAddress"] == "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    expected_signature = sign_l1_action(
        private_key=account_private_key,
        action=exchange_payload["action"],
        vault_address=exchange_payload["vaultAddress"],
        nonce=exchange_payload["nonce"],
        expires_after=None,
        is_mainnet=False,
    )
    assert exchange_payload["signature"] == expected_signature


def test_coinbase_submit_path_uses_documented_jwt_bearer_auth() -> None:
    session_factory = build_test_session_factory()
    targeted_pem = _generate_ec_private_key_pem()
    integration_pem = _generate_ec_private_key_pem()
    targeted_key_name = "organizations/org-1/apiKeys/account-a"
    integration_key_name = "organizations/org-1/apiKeys/integration-default"
    intent_id, account_id = _seed_submission_intent(
        session_factory,
        venue=Venue.COINBASE_ADVANCED_TRADE,
        account_suffix="acct-a",
        symbol="BTC",
        exchange_symbol="BTC-USD",
        market_type=MarketType.SPOT,
        product_type=ProductType.SPOT,
        venue_native_account_id="cb-brokerage-a",
        account_address="cb-account-a",
        credentials_ref="coinbase-profile-a",
        account_auth={
            "jwt_key_name": targeted_key_name,
            "jwt_private_key_pem": targeted_pem,
        },
        action=DecisionAction.OPEN,
        side=OrderSide.BUY,
        reduce_only=False,
    )
    intent = _load_intent(session_factory, intent_id)
    captured_headers: list[dict[str, str]] = []
    captured_bodies: list[str] = []

    async def transport(method, path, params=None, body=None, headers=None):
        if method == "GET" and path == "/api/v3/brokerage/accounts":
            return {"accounts": [{"available_balance": {"value": "500"}}]}
        if method == "POST" and path == "/api/v3/brokerage/orders":
            captured_headers.append(dict(headers or {}))
            captured_bodies.append(body)
            parsed_body = json.loads(body)
            return {
                "success": True,
                "success_response": {
                    "order_id": "cb-submit-1",
                    "client_order_id": parsed_body.get("client_order_id"),
                },
            }
        raise AssertionError((method, path, params, body, headers))

    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXECUTION_DRY_RUN=False,
        COINBASE_ADVANCED_READ_ONLY_MODE=False,
        COINBASE_ADVANCED_DRY_RUN_MODE=False,
        COINBASE_ADVANCED_SUBMISSION_ENABLED=True,
        COINBASE_ADVANCED_SUBMISSION_AUTHORIZED=True,
        COINBASE_ADVANCED_JWT_KEY_NAME=integration_key_name,
        COINBASE_ADVANCED_JWT_PRIVATE_KEY_PEM=integration_pem,
    )
    adapter = CoinbaseAdvancedTradeExchangeAdapter(settings, transport=transport, session_factory=session_factory)
    expected_preview = asyncio.run(adapter.prepare_order_preview(intent))

    submitted = asyncio.run(adapter.submit_order(intent))

    assert submitted.venue_account_ref_id == account_id
    assert submitted.exchange_order_id == "cb-submit-1"
    assert captured_headers
    assert captured_bodies
    headers = captured_headers[0]
    assert "CB-ACCOUNT-ID" not in headers
    header, payload, _signature, _input = _decode_bearer_token(headers["Authorization"])
    assert header["kid"] == targeted_key_name
    assert payload["sub"] == targeted_key_name
    assert payload["iss"] == "cdp"
    assert payload["uri"] == "POST api.coinbase.com/api/v3/brokerage/orders"
    expected_body = dict(expected_preview.payload or {})
    expected_body.pop("endpoint", None)
    assert captured_bodies[0] == json.dumps(
        expected_body,
        separators=(",", ":"),
        sort_keys=True,
    )
    _verify_coinbase_jwt_signature(headers["Authorization"], targeted_pem)


def test_http_submit_paths_use_targeted_account_auth_and_real_signatures() -> None:
    cases: list[tuple[Venue, type, dict[str, object], dict[str, str], str, str]] = [
        (
            Venue.ASTER,
            AsterExchangeAdapter,
            {
                "APP_ENV": Environment.TESTNET,
                "EXECUTION_DRY_RUN": False,
                "ASTER_READ_ONLY_MODE": False,
                "ASTER_DRY_RUN_MODE": False,
                "ASTER_SUBMISSION_ENABLED": True,
                "ASTER_SUBMISSION_AUTHORIZED": True,
                "ASTER_API_KEY": "integration-aster",
                "ASTER_API_SECRET": "integration-aster-secret",
            },
            {"api_key": "aster-key-a", "api_secret": "aster-secret-a"},
            "BTCUSDT",
            "/fapi/v1/order",
        ),
        (
            Venue.OKX,
            OkxExchangeAdapter,
            {
                "APP_ENV": Environment.TESTNET,
                "EXECUTION_DRY_RUN": False,
                "OKX_READ_ONLY_MODE": False,
                "OKX_DRY_RUN_MODE": False,
                "OKX_SUBMISSION_ENABLED": True,
                "OKX_SUBMISSION_AUTHORIZED": True,
                "OKX_API_KEY": "integration-okx",
                "OKX_API_SECRET": "integration-okx-secret",
                "OKX_API_PASSPHRASE": "integration-okx-pass",
            },
            {"api_key": "okx-key-a", "api_secret": "okx-secret-a", "api_passphrase": "okx-pass-a"},
            "BTC-USDT-SWAP",
            "/api/v5/trade/order",
        ),
        (
            Venue.BINANCE,
            BinanceExchangeAdapter,
            {
                "APP_ENV": Environment.TESTNET,
                "EXECUTION_DRY_RUN": False,
                "BINANCE_READ_ONLY_MODE": False,
                "BINANCE_DRY_RUN_MODE": False,
                "BINANCE_SUBMISSION_ENABLED": True,
                "BINANCE_SUBMISSION_AUTHORIZED": True,
                "BINANCE_API_KEY": "integration-binance",
                "BINANCE_API_SECRET": "integration-binance-secret",
            },
            {"api_key": "binance-key-a", "api_secret": "binance-secret-a"},
            "BTCUSDT",
            "/api/v3/order",
        ),
        (
            Venue.KRAKEN,
            KrakenExchangeAdapter,
            {
                "APP_ENV": Environment.TESTNET,
                "EXECUTION_DRY_RUN": False,
                "KRAKEN_READ_ONLY_MODE": False,
                "KRAKEN_DRY_RUN_MODE": False,
                "KRAKEN_SUBMISSION_ENABLED": True,
                "KRAKEN_SUBMISSION_AUTHORIZED": True,
                "KRAKEN_API_KEY": "integration-kraken",
                "KRAKEN_API_SECRET": base64.b64encode(b"integration-kraken-secret").decode("ascii"),
            },
            {
                "api_key": "kraken-key-a",
                "api_secret": base64.b64encode(b"kraken-secret-a").decode("ascii"),
            },
            "XBT/USD",
            "/0/private/AddOrder",
        ),
    ]

    for venue, adapter_cls, setting_overrides, account_auth, exchange_symbol, submit_path in cases:
        session_factory = build_test_session_factory()
        market_type = MarketType.PERPETUAL if venue in {Venue.ASTER, Venue.OKX} else MarketType.SPOT
        product_type = ProductType.LINEAR if market_type == MarketType.PERPETUAL else ProductType.SPOT
        intent_id, account_id = _seed_submission_intent(
            session_factory,
            venue=venue,
            account_suffix="acct-a",
            symbol="BTC",
            exchange_symbol=exchange_symbol,
            market_type=market_type,
            product_type=product_type,
            venue_native_account_id=f"{venue.value}-native-a",
            account_address=f"{venue.value}-acct-a",
            credentials_ref=f"{venue.value}-profile-a",
            account_auth=account_auth,
            subaccount_label="desk-a" if venue == Venue.OKX else None,
            action=DecisionAction.REDUCE if market_type == MarketType.PERPETUAL else DecisionAction.OPEN,
            side=OrderSide.SELL if market_type == MarketType.PERPETUAL else OrderSide.BUY,
            reduce_only=market_type == MarketType.PERPETUAL,
        )
        intent = _load_intent(session_factory, intent_id)
        captured_requests: list[dict[str, Any]] = []

        async def transport(method, path, params=None, body=None, headers=None):
            if venue == Venue.ASTER and method == "GET" and path == "/fapi/v2/balance":
                return [{"balance": "1000", "availableBalance": "800", "crossWalletBalance": "200"}]
            if venue == Venue.OKX and method == "GET" and path == "/api/v5/account/balance":
                return {"data": [{"totalEq": "1000", "availEq": "600", "details": [{"availEq": "600"}]}]}
            if venue == Venue.BINANCE and method == "GET" and path == "/api/v3/account":
                return {"balances": [{"asset": "USDT", "free": "700", "locked": "50"}]}
            if venue == Venue.KRAKEN and method == "POST" and path == "/0/private/Balance":
                return {"result": {"ZUSD": "900"}}
            if method == "POST" and path == submit_path:
                captured_requests.append({"headers": dict(headers or {}), "body": body, "path": path})
                parsed_body = (
                    json.loads(body)
                    if venue == Venue.OKX
                    else _parse_form_body(body or "")
                )
                if venue == Venue.OKX:
                    return {"data": [{"ordId": "okx-submit-1", "clOrdId": parsed_body.get("clOrdId")}], "code": "0"}
                if venue == Venue.KRAKEN:
                    return {"result": {"txid": ["kraken-submit-1"]}}
                return {
                    "orderId": f"{venue.value}-submit-1",
                    "clientOrderId": parsed_body.get("newClientOrderId"),
                    "status": "accepted",
                }
            raise AssertionError((venue, method, path, params, body, headers))

        adapter = adapter_cls(build_settings(**setting_overrides), transport=transport, session_factory=session_factory)
        capabilities = asyncio.run(adapter.get_venue_capabilities())
        submitted = asyncio.run(adapter.submit_order(intent))

        assert capabilities.adapter_supports_order_submission is True
        assert capabilities.supports_account_sync is True
        assert submitted.venue_account_ref_id == account_id
        assert submitted.account_address == f"{venue.value}-acct-a"
        assert captured_requests
        captured = captured_requests[0]
        headers = captured["headers"]
        raw_body = captured["body"]
        assert "X-MF-TARGET-ACCOUNT" not in headers
        assert "X-MF-TARGET-SUBACCOUNT" not in headers

        if venue in {Venue.ASTER, Venue.BINANCE}:
            body = _parse_form_body(raw_body or "")
            assert headers["X-MBX-APIKEY"] == account_auth["api_key"]
            expected_signing_payload = urllib.parse.urlencode(
                sorted({k: v for k, v in body.items() if k != "signature"}.items())
            )
            expected_signature = hmac.new(
                account_auth["api_secret"].encode("utf-8"),
                expected_signing_payload.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            assert body["signature"] == expected_signature
            assert raw_body == f"{expected_signing_payload}&signature={expected_signature}"
        elif venue == Venue.OKX:
            body = json.loads(raw_body)
            rendered_body = json.dumps(body, separators=(",", ":"), sort_keys=True)
            signing_payload = f"{headers['OK-ACCESS-TIMESTAMP']}POST{submit_path}{rendered_body}"
            expected_signature = base64.b64encode(
                hmac.new(
                    account_auth["api_secret"].encode("utf-8"),
                    signing_payload.encode("utf-8"),
                    hashlib.sha256,
                ).digest()
            ).decode("utf-8")
            assert headers["OK-ACCESS-KEY"] == account_auth["api_key"]
            assert headers["OK-ACCESS-PASSPHRASE"] == account_auth["api_passphrase"]
            assert headers["OK-ACCESS-SIGN"] == expected_signature
            assert raw_body == rendered_body
        elif venue == Venue.KRAKEN:
            body = _parse_form_body(raw_body or "")
            nonce = str(body["nonce"])
            post_data = urllib.parse.urlencode(sorted(body.items()))
            sha256_payload = hashlib.sha256((nonce + post_data).encode("utf-8")).digest()
            secret_bytes = base64.b64decode(account_auth["api_secret"])
            expected_signature = base64.b64encode(
                hmac.new(secret_bytes, submit_path.encode("utf-8") + sha256_payload, hashlib.sha512).digest()
            ).decode("utf-8")
            assert headers["API-Key"] == account_auth["api_key"]
            assert headers["API-Sign"] == expected_signature
            assert raw_body == post_data


def test_same_venue_multi_account_coinbase_submission_uses_targeted_jwt_contexts() -> None:
    session_factory = build_test_session_factory()
    first_pem = _generate_ec_private_key_pem()
    second_pem = _generate_ec_private_key_pem()
    first_key_name = "organizations/org-1/apiKeys/account-a"
    second_key_name = "organizations/org-1/apiKeys/account-b"
    first_intent_id, first_account_id = _seed_submission_intent(
        session_factory,
        venue=Venue.COINBASE_ADVANCED_TRADE,
        account_suffix="acct-a",
        symbol="BTC",
        exchange_symbol="BTC-USD",
        market_type=MarketType.SPOT,
        product_type=ProductType.SPOT,
        venue_native_account_id="cb-brokerage-a",
        account_address="cb-account-a",
        credentials_ref="coinbase-profile-a",
        account_auth={"jwt_key_name": first_key_name, "jwt_private_key_pem": first_pem},
        action=DecisionAction.OPEN,
        side=OrderSide.BUY,
        reduce_only=False,
    )
    second_intent_id, second_account_id = _seed_submission_intent(
        session_factory,
        venue=Venue.COINBASE_ADVANCED_TRADE,
        account_suffix="acct-b",
        symbol="BTC",
        exchange_symbol="BTC-USD",
        market_type=MarketType.SPOT,
        product_type=ProductType.SPOT,
        venue_native_account_id="cb-brokerage-b",
        account_address="cb-account-b",
        credentials_ref="coinbase-profile-b",
        account_auth={"jwt_key_name": second_key_name, "jwt_private_key_pem": second_pem},
        action=DecisionAction.OPEN,
        side=OrderSide.BUY,
        reduce_only=False,
    )
    captured_subjects: list[str] = []

    async def transport(method, path, params=None, body=None, headers=None):
        if method == "GET" and path == "/api/v3/brokerage/accounts":
            return {"accounts": [{"available_balance": {"value": "500"}}]}
        if method == "POST" and path == "/api/v3/brokerage/orders":
            _header, payload, _signature, _input = _decode_bearer_token(headers["Authorization"])
            captured_subjects.append(payload["sub"])
            parsed_body = json.loads(body)
            return {
                "success": True,
                "success_response": {
                    "order_id": f"cb-{payload['sub'].split('/')[-1]}",
                    "client_order_id": parsed_body.get("client_order_id"),
                },
            }
        raise AssertionError((method, path, params, body, headers))

    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXECUTION_DRY_RUN=False,
        COINBASE_ADVANCED_READ_ONLY_MODE=False,
        COINBASE_ADVANCED_DRY_RUN_MODE=False,
        COINBASE_ADVANCED_SUBMISSION_ENABLED=True,
        COINBASE_ADVANCED_SUBMISSION_AUTHORIZED=True,
        COINBASE_ADVANCED_JWT_KEY_NAME="organizations/org-1/apiKeys/integration-default",
        COINBASE_ADVANCED_JWT_PRIVATE_KEY_PEM=_generate_ec_private_key_pem(),
    )
    adapter = CoinbaseAdvancedTradeExchangeAdapter(settings, transport=transport, session_factory=session_factory)

    first_submitted = asyncio.run(adapter.submit_order(_load_intent(session_factory, first_intent_id)))
    second_submitted = asyncio.run(adapter.submit_order(_load_intent(session_factory, second_intent_id)))

    assert captured_subjects == [first_key_name, second_key_name]
    assert first_submitted.venue_account_ref_id == first_account_id
    assert second_submitted.venue_account_ref_id == second_account_id


def test_invalid_coinbase_jwt_material_fails_with_explicit_reason() -> None:
    session_factory = build_test_session_factory()
    intent_id, _account_id = _seed_submission_intent(
        session_factory,
        venue=Venue.COINBASE_ADVANCED_TRADE,
        account_suffix="broken-a",
        symbol="BTC",
        exchange_symbol="BTC-USD",
        market_type=MarketType.SPOT,
        product_type=ProductType.SPOT,
        venue_native_account_id="cb-brokerage-bad",
        account_address="cb-account-bad",
        credentials_ref="coinbase-bad-profile",
        account_auth={
            "jwt_key_name": "organizations/org-1/apiKeys/bad",
            "jwt_private_key_pem": "not-a-valid-pem",
        },
        action=DecisionAction.OPEN,
        side=OrderSide.BUY,
        reduce_only=False,
    )
    intent = _load_intent(session_factory, intent_id)

    async def transport(method, path, params=None, body=None, headers=None):
        if method == "GET" and path == "/api/v3/brokerage/accounts":
            return {"accounts": [{"available_balance": {"value": "500"}}]}
        raise AssertionError((method, path, params, body, headers))

    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXECUTION_DRY_RUN=False,
        COINBASE_ADVANCED_READ_ONLY_MODE=False,
        COINBASE_ADVANCED_DRY_RUN_MODE=False,
        COINBASE_ADVANCED_SUBMISSION_ENABLED=True,
        COINBASE_ADVANCED_SUBMISSION_AUTHORIZED=True,
        COINBASE_ADVANCED_JWT_KEY_NAME="organizations/org-1/apiKeys/integration-default",
        COINBASE_ADVANCED_JWT_PRIVATE_KEY_PEM=_generate_ec_private_key_pem(),
    )
    adapter = CoinbaseAdvancedTradeExchangeAdapter(settings, transport=transport, session_factory=session_factory)

    try:
        asyncio.run(adapter.submit_order(intent))
    except VenueAdapterError as exc:
        assert "auth_signing_failed" in exc.reason_codes
    else:
        raise AssertionError("Coinbase submission unexpectedly succeeded with invalid JWT material")


def test_unresolved_credential_reference_blocks_submission_truthfully() -> None:
    session_factory = build_test_session_factory()
    intent_id, _account_id = _seed_submission_intent(
        session_factory,
        venue=Venue.BINANCE,
        account_suffix="acct-a",
        symbol="BTC",
        exchange_symbol="BTCUSDT",
        market_type=MarketType.SPOT,
        product_type=ProductType.SPOT,
        venue_native_account_id="binance-native-a",
        account_address="binance-acct-a",
        credentials_ref="binance-profile-a",
        account_auth=None,
        action=DecisionAction.OPEN,
        side=OrderSide.BUY,
        reduce_only=False,
    )
    intent = _load_intent(session_factory, intent_id)

    async def transport(method, path, params=None, body=None, headers=None):
        raise AssertionError((method, path, params, body, headers))

    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXECUTION_DRY_RUN=False,
        BINANCE_READ_ONLY_MODE=False,
        BINANCE_DRY_RUN_MODE=False,
        BINANCE_SUBMISSION_ENABLED=True,
        BINANCE_SUBMISSION_AUTHORIZED=True,
        BINANCE_API_KEY="",
        BINANCE_API_SECRET="",
    )
    adapter = BinanceExchangeAdapter(settings, transport=transport, session_factory=session_factory)

    try:
        asyncio.run(adapter.submit_order(intent))
    except VenueAdapterError as exc:
        assert "credential_reference_unresolved" in exc.reason_codes
    else:
        raise AssertionError("submission unexpectedly succeeded with unresolved credential reference")
