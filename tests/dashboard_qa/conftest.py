"""DASH-QA1 browser-smoke harness.

Serves the repo root over an ephemeral localhost HTTP server and opens
`/apps/dashboard/index.html?disableLivePolling=true` in headless Chromium.

No external network. Live polling is disabled via query flag so the dashboard
falls back to committed/local JSON.

Run once:  playwright install chromium
"""

from __future__ import annotations

import contextlib
import http.server
import json
import socket
import socketserver
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def current_truth() -> dict:  # type: ignore[type-arg]
    """Load the TRUTH1 registry once per session for cross-test grounding."""
    return json.loads((REPO_ROOT / "current_truth.json").read_text(encoding="utf-8"))


def _free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return  # suppress access log spam during tests


@pytest.fixture(scope="session")
def dashboard_base_url() -> Iterator[str]:
    """Serve REPO_ROOT on a free localhost port; yield the base URL."""
    port = _free_port()

    class _Handler(_QuietHandler):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, directory=str(REPO_ROOT), **kwargs)  # type: ignore[arg-type]

    server = socketserver.ThreadingTCPServer(("127.0.0.1", port), _Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture(scope="session")
def dashboard_url(dashboard_base_url: str) -> str:
    return f"{dashboard_base_url}/apps/dashboard/index.html?disableLivePolling=true"
