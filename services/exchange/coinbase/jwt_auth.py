"""Coinbase App / Advanced Trade REST JWT helpers."""

from __future__ import annotations

from base64 import urlsafe_b64encode
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
import secrets

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils


def _b64url(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def build_coinbase_rest_jwt(
    *,
    key_name: str,
    private_key_pem: str,
    request_method: str,
    request_host: str,
    request_path: str,
    now: datetime | None = None,
    nonce: str | None = None,
) -> str:
    issued_at = (now or datetime.now(UTC)).replace(microsecond=0)
    header = {
        "alg": "ES256",
        "kid": key_name,
        "nonce": nonce or secrets.token_hex(),
        "typ": "JWT",
    }
    payload = {
        "sub": key_name,
        "iss": "cdp",
        "nbf": int(issued_at.timestamp()),
        "exp": int((issued_at + timedelta(minutes=2)).timestamp()),
        "uri": f"{request_method.upper()} {request_host}{request_path}",
    }
    encoded_header = _b64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    encoded_payload = _b64url(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")

    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"),
        password=None,
    )
    der_signature = private_key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
    r_value, s_value = utils.decode_dss_signature(der_signature)
    raw_signature = r_value.to_bytes(32, "big") + s_value.to_bytes(32, "big")
    return f"{encoded_header}.{encoded_payload}.{_b64url(raw_signature)}"


def coinbase_request_hash(
    *,
    method: str,
    host: str,
    path: str,
) -> str:
    return sha256(f"{method.upper()} {host}{path}".encode("utf-8")).hexdigest()
