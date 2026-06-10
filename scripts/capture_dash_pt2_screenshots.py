#!/usr/bin/env python3
"""DASH-PT2 visual verification — capture Paper Trading screenshots.

Serves the repo root locally (same approach as tests/dashboard_qa/conftest.py),
opens the dashboard with live polling disabled, switches to the Paper Trading
view, and captures screenshots for founder review: desktop + mobile widths in
the dark theme, plus desktop light and red-zone.

Display-only verification tooling: no network beyond localhost, no runtime,
no orders, no approvals.

Usage:
    .venv/bin/python scripts/capture_dash_pt2_screenshots.py --label after
"""

from __future__ import annotations

import argparse
import contextlib
import http.server
import socket
import socketserver
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "dash_pt2_screenshots"
PAPER_TAB = '.view-tab[data-view="paper-observation"]'
PAPER_VIEW = "#paper-observation-view"
THEME_SELECTOR = "#dashboard-theme-selector"

SHOTS = (
    # (name suffix, viewport, theme, full_page)
    ("desktop-dark", {"width": 1600, "height": 1000}, "dark", False),
    ("desktop-dark-full", {"width": 1600, "height": 1000}, "dark", True),
    ("mobile-dark", {"width": 390, "height": 844}, "dark", False),
    ("desktop-light", {"width": 1600, "height": 1000}, "light", False),
    ("desktop-red-zone", {"width": 1600, "height": 1000}, "red-zone", False),
)


def _free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default="after", help="before|after filename prefix")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    port = _free_port()

    class _Handler(_QuietHandler):
        def __init__(self, *handler_args: object, **kwargs: object) -> None:
            super().__init__(*handler_args, directory=str(REPO_ROOT), **kwargs)  # type: ignore[arg-type]

    server = socketserver.ThreadingTCPServer(("127.0.0.1", port), _Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{port}/apps/dashboard/index.html?disableLivePolling=true"

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for name, viewport, theme, full_page in SHOTS:
                page = browser.new_page(viewport=viewport)
                page.goto(url, wait_until="load")
                page.locator(PAPER_TAB).click()
                page.locator(PAPER_VIEW).wait_for(state="visible")
                # The dashboard defaults to red-zone for fresh visitors, so the
                # theme must always be selected explicitly (including dark).
                page.select_option(THEME_SELECTOR, theme)
                page.wait_for_timeout(1200)  # settle chart + deferred renders
                out = args.output_dir / f"{args.label}-paper-trading-{name}.png"
                page.screenshot(path=str(out), full_page=full_page)
                print(f"captured {out}")
                page.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
