"""Minimal Hyperliquid SDK-faithful signing helpers for order submission."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import msgpack
from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils import keccak, to_hex


def address_to_bytes(address: str) -> bytes:
    normalized = address.lower()
    return bytes.fromhex(normalized[2:] if normalized.startswith("0x") else normalized)


def float_to_wire(value: Decimal) -> str:
    normalized = value.normalize()
    return f"{normalized:f}"


def action_hash(
    action: dict[str, Any],
    vault_address: str | None,
    nonce: int,
    expires_after: int | None,
) -> bytes:
    payload = msgpack.packb(action)
    payload += nonce.to_bytes(8, "big")
    if vault_address is None:
        payload += b"\x00"
    else:
        payload += b"\x01"
        payload += address_to_bytes(vault_address)
    if expires_after is not None:
        payload += b"\x00"
        payload += expires_after.to_bytes(8, "big")
    return keccak(payload)


def construct_phantom_agent(connection_id: bytes, is_mainnet: bool) -> dict[str, Any]:
    return {
        "source": "a" if is_mainnet else "b",
        "connectionId": connection_id,
    }


def l1_payload(phantom_agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "domain": {
            "chainId": 1337,
            "name": "Exchange",
            "verifyingContract": "0x0000000000000000000000000000000000000000",
            "version": "1",
        },
        "types": {
            "Agent": [
                {"name": "source", "type": "string"},
                {"name": "connectionId", "type": "bytes32"},
            ],
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
        },
        "primaryType": "Agent",
        "message": phantom_agent,
    }


def sign_l1_action(
    *,
    private_key: str,
    action: dict[str, Any],
    vault_address: str | None,
    nonce: int,
    expires_after: int | None,
    is_mainnet: bool,
) -> dict[str, Any]:
    wallet = Account.from_key(private_key)
    payload_hash = action_hash(action, vault_address, nonce, expires_after)
    structured_data = encode_typed_data(
        full_message=l1_payload(construct_phantom_agent(payload_hash, is_mainnet))
    )
    signed = wallet.sign_message(structured_data)
    return {
        "r": to_hex(signed.r),
        "s": to_hex(signed.s),
        "v": signed.v,
    }


def signer_address(private_key: str) -> str:
    return Account.from_key(private_key).address.lower()
