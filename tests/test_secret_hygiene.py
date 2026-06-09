"""Tests for the secret hygiene scanner.

Verifies: placeholder detection, bearer-token redaction-marker exclusion,
self-skip behaviour, test-dir KV-pattern skip, and a clean repo-scan assertion.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from scripts.check_secret_hygiene import scan_file, scan_targets

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# PEM block detection
# ---------------------------------------------------------------------------


def test_pem_block_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path, "bad.pem", "-----BEGIN RSA PRIVATE KEY-----\nABCDEF\n")
    hits = scan_file(p)
    assert any(name == "pem_private_key_block" for _, name, _ in hits)


def test_pem_block_ec_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path, "bad.pem", "-----BEGIN EC PRIVATE KEY-----\nABCDEF\n")
    hits = scan_file(p)
    assert any(name == "pem_private_key_block" for _, name, _ in hits)


# ---------------------------------------------------------------------------
# Bearer token detection
# ---------------------------------------------------------------------------


def test_bearer_token_real_value_flagged(tmp_path: Path) -> None:
    # Looks like a JWT (two dot-separated alphanumeric segments)
    p = _write(tmp_path, "bad.py", "Authorization: Bearer eyJhbGc.eyJzdWIiOiIxMjM0NTY3ODkwIn0\n")
    hits = scan_file(p)
    assert any(name == "bearer_token_value" for _, name, _ in hits)


def test_bearer_token_redaction_marker_not_flagged(tmp_path: Path) -> None:
    # `...` is a documentation redaction marker, not a real token
    p = _write(tmp_path, "ok.md", "- `Authorization: Bearer ...` values;\n")
    hits = scan_file(p)
    assert not any(name == "bearer_token_value" for _, name, _ in hits)


def test_bearer_token_dots_only_not_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path, "ok.md", "Authorization: Bearer ...\n")
    hits = scan_file(p)
    assert not any(name == "bearer_token_value" for _, name, _ in hits)


# ---------------------------------------------------------------------------
# Key-value pattern detection
# ---------------------------------------------------------------------------


def test_kv_real_value_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path, "bad.env", "EXCHANGE_SIGNING_PRIVATE_KEY=0xdeadbeefdeadbeef\n")
    hits = scan_file(p)
    assert any(name == "signing_private_key" for _, name, _ in hits)


def test_kv_empty_value_not_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path, "ok.env", "EXCHANGE_SIGNING_PRIVATE_KEY=\n")
    assert not scan_file(p)


def test_kv_placeholder_value_not_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path, "ok.env", "EXCHANGE_SIGNING_PRIVATE_KEY=replace_me\n")
    assert not scan_file(p)


def test_kv_your_key_here_not_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path, "ok.env", "EXCHANGE_SIGNING_PRIVATE_KEY=your_key_here\n")
    assert not scan_file(p)


def test_kv_skip_flag_suppresses_kv_patterns(tmp_path: Path) -> None:
    # When skip_kv_patterns=True, KV violations are not reported
    p = _write(tmp_path, "test_fixture.py", "EXCHANGE_SIGNING_PRIVATE_KEY=0xdeadbeefdeadbeef\n")
    hits = scan_file(p, skip_kv_patterns=True)
    assert not any(name == "signing_private_key" for _, name, _ in hits)


def test_kv_skip_flag_does_not_suppress_pem(tmp_path: Path) -> None:
    # PEM blocks are still caught even with skip_kv_patterns=True
    p = _write(
        tmp_path,
        "test_fixture.py",
        "-----BEGIN RSA PRIVATE KEY-----\nABCDEF\n",
    )
    hits = scan_file(p, skip_kv_patterns=True)
    assert any(name == "pem_private_key_block" for _, name, _ in hits)


# ---------------------------------------------------------------------------
# Full repo scan must be clean
# ---------------------------------------------------------------------------


def test_repo_scan_clean() -> None:
    results = scan_targets()
    repo_root = Path(__file__).resolve().parent.parent
    violations: list[str] = []
    for path, hits in sorted(results.items()):
        rel = path.relative_to(repo_root)
        for lineno, name, line in hits:
            violations.append(f"{rel}:{lineno} [{name}] {line[:100]}")
    assert not violations, "Secret hygiene violations found in repo:\n" + "\n".join(violations)
