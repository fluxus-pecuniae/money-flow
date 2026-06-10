"""DASH-QA1 — nine browser-level smoke checks for the Paper Trading dashboard.

Pins the documented regressions so they cannot silently return:
  1. Paper Trading tab loads.
  2. Terminal layout visible (grid + left/center/right rails + bottom blotter).
  3. Chart does not grow the page infinitely (autoSize/ResizeObserver guard).
  4. Tab switching persists state (aria-selected + prior selection retained).
  5. Bottom blotter tab does not reset across refresh cycles.
  6. Audit tab absent (DASH-PT1.1 removed it).
  7. Strategy tab shows exactly the three active lanes from current_truth.json.
  8. 15m is paused/legacy, never an active scoring timeframe.
  9. Synthetic / testnet / no-live boundary labels visible in the paper view.

Grounded in real selectors from apps/dashboard/index.html and expected truth
from current_truth.json (the TRUTH1 registry).
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.browser

PAPER_TAB = '.view-tab[data-view="paper-observation"]'
HISTORICAL_TAB = '.view-tab[data-view="historical-replay"]'
STRATEGY_TAB = '.view-tab[data-view="strategy"]'

PAPER_VIEW = "#paper-observation-view"
TERMINAL_GRID = "#paper-observation-terminal-grid"
LEFT_RAIL = "#paper-observation-terminal-grid .paper-observation-left-rail"
CENTER_STAGE = "#paper-observation-terminal-grid .paper-observation-center-stage"
RIGHT_RAIL = "#paper-observation-terminal-grid .paper-observation-right-rail"
BOTTOM_BLOTTER = "#paper-observation-bottom-blotter"
BLOTTER_TABS = ".paper-observation-blotter-tabs [data-paper-terminal-tab]"
HEALTH_BANNER = "#paper-observation-health-banner"
TIMEFRAME_FILTER = "#paper-observation-timeframe-filter"

# Bounded waits for refresh-cycle observation (the dashboard polls ~1s in places).
REFRESH_OBSERVATION_MS = 4_000
BLOTTER_OBSERVATION_MS = 3_000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _open_paper(page: Page, url: str) -> None:
    page.goto(url, wait_until="networkidle")
    page.locator(PAPER_TAB).click()
    expect(page.locator(PAPER_VIEW)).to_be_visible()


# ---------------------------------------------------------------------------
# 1. Paper Trading loads
# ---------------------------------------------------------------------------


def test_paper_trading_tab_loads(page: Page, dashboard_url: str) -> None:
    page.goto(dashboard_url, wait_until="networkidle")
    # Default tab is Historical Replay; Paper view must start hidden.
    expect(page.locator(PAPER_VIEW)).to_be_hidden()
    page.locator(PAPER_TAB).click()
    expect(page.locator(PAPER_TAB)).to_have_attribute("aria-selected", "true")
    expect(page.locator(PAPER_VIEW)).to_be_visible()


# ---------------------------------------------------------------------------
# 2. Terminal layout visible
# ---------------------------------------------------------------------------


def test_terminal_layout_visible(page: Page, dashboard_url: str) -> None:
    _open_paper(page, dashboard_url)
    expect(page.locator(TERMINAL_GRID)).to_be_visible()
    expect(page.locator(LEFT_RAIL)).to_be_visible()
    expect(page.locator(CENTER_STAGE)).to_be_visible()
    expect(page.locator(RIGHT_RAIL)).to_be_visible()
    expect(page.locator(BOTTOM_BLOTTER)).to_be_visible()


# ---------------------------------------------------------------------------
# 3. Chart does not grow the page infinitely
# ---------------------------------------------------------------------------


def test_chart_does_not_grow_page(page: Page, dashboard_url: str) -> None:
    _open_paper(page, dashboard_url)
    # Allow initial layout to settle.
    page.wait_for_timeout(500)
    initial_height = page.evaluate("() => document.body.scrollHeight")
    # Observe through refresh cycles with polling disabled.
    page.wait_for_timeout(REFRESH_OBSERVATION_MS)
    final_height = page.evaluate("() => document.body.scrollHeight")
    # Tight tolerance: anything > 200 px drift across 4s indicates a feedback loop.
    drift = abs(int(final_height) - int(initial_height))
    assert drift < 200, (
        f"document.body.scrollHeight drifted by {drift}px "
        f"({initial_height} -> {final_height}) — possible chart autoSize feedback loop"
    )


# ---------------------------------------------------------------------------
# 4. Tab switching persists state
# ---------------------------------------------------------------------------


def test_tab_switching_persists_blotter_state(page: Page, dashboard_url: str) -> None:
    _open_paper(page, dashboard_url)
    # Default blotter tab is "open"; switch to "signals".
    page.locator('[data-paper-terminal-tab="signals"]').click()
    expect(page.locator('[data-paper-terminal-tab="signals"]')).to_have_attribute(
        "aria-selected", "true"
    )
    # Leave paper view, come back.
    page.locator(HISTORICAL_TAB).click()
    expect(page.locator(HISTORICAL_TAB)).to_have_attribute("aria-selected", "true")
    expect(page.locator(PAPER_VIEW)).to_be_hidden()
    page.locator(PAPER_TAB).click()
    expect(page.locator(PAPER_VIEW)).to_be_visible()
    # Blotter selection must be retained.
    expect(page.locator('[data-paper-terminal-tab="signals"]')).to_have_attribute(
        "aria-selected", "true"
    )


# ---------------------------------------------------------------------------
# 5. Bottom blotter tab does not reset every second
# ---------------------------------------------------------------------------


def test_blotter_tab_does_not_reset_under_refresh(page: Page, dashboard_url: str) -> None:
    _open_paper(page, dashboard_url)
    page.locator('[data-paper-terminal-tab="diagnostics"]').click()
    expect(page.locator('[data-paper-terminal-tab="diagnostics"]')).to_have_attribute(
        "aria-selected", "true"
    )
    page.wait_for_timeout(BLOTTER_OBSERVATION_MS)
    # After refresh cycles, the same blotter tab must still be selected.
    expect(page.locator('[data-paper-terminal-tab="diagnostics"]')).to_have_attribute(
        "aria-selected", "true"
    )
    expect(page.locator('[data-paper-terminal-tab="open"]')).not_to_have_attribute(
        "aria-selected", "true"
    )


# ---------------------------------------------------------------------------
# 6. Audit tab absent
# ---------------------------------------------------------------------------


def test_no_audit_tab(page: Page, dashboard_url: str) -> None:
    page.goto(dashboard_url, wait_until="networkidle")
    assert page.locator('.view-tab[data-view="audit"]').count() == 0
    # No nav tab whose visible text is exactly "Audit"
    nav_buttons = page.locator(".view-tabs .view-tab").all_text_contents()
    assert "Audit" not in [t.strip() for t in nav_buttons], (
        f"Expected no 'Audit' nav tab; saw: {nav_buttons}"
    )


# ---------------------------------------------------------------------------
# 7. Strategy shows only the three active lanes
# ---------------------------------------------------------------------------


def test_strategy_view_shows_only_active_lanes(
    page: Page, dashboard_url: str, current_truth: dict
) -> None:
    page.goto(dashboard_url, wait_until="networkidle")
    page.locator(STRATEGY_TAB).click()
    expect(page.locator("#strategy-view")).to_be_visible()
    body_text = page.locator("#strategy-view").inner_text()
    expected_lane_ids = [lane["lane_id"] for lane in current_truth["active_lanes"]]
    assert len(expected_lane_ids) == 3, (
        f"current_truth.json declares {len(expected_lane_ids)} active lanes; expected 3"
    )
    for lane_id in expected_lane_ids:
        assert lane_id in body_text, f"Strategy view missing active lane id: {lane_id}"
    # The active slate heading must be present and call out Week 2 + synthetic / not-approved.
    heading = page.locator("#strategy-map-title")
    expect(heading).to_be_visible()
    heading_text = heading.inner_text().lower()
    assert "week 2" in heading_text or "active strategy" in heading_text


# ---------------------------------------------------------------------------
# 8. 15m not active
# ---------------------------------------------------------------------------


def test_timeframe_filter_15m_paused_only(
    page: Page, dashboard_url: str, current_truth: dict
) -> None:
    _open_paper(page, dashboard_url)
    expect(page.locator(TIMEFRAME_FILTER)).to_be_visible()

    options = page.evaluate(
        """() => Array.from(document.querySelectorAll(
            '#paper-observation-timeframe-filter option'
        )).map(o => ({ value: o.value, label: o.textContent.trim() }))"""
    )
    assert options, "Timeframe filter has no options"

    expected_active = current_truth["active_timeframes"]
    expected_paused = current_truth["paused_timeframes"]
    assert expected_active == ["1h", "4h", "1d"], (
        f"current_truth active_timeframes drifted: {expected_active}"
    )
    assert expected_paused == ["15m"], f"current_truth paused_timeframes drifted: {expected_paused}"

    # Every active timeframe must appear as an option value.
    option_values = [o["value"] for o in options]
    for tf in expected_active:
        assert tf in option_values, f"Active timeframe option missing: {tf}"

    # 15m may appear, but ONLY tagged as paused/legacy/disabled — never as a bare active value.
    for o in options:
        if o["value"] == "15m":
            pytest.fail(
                "15m appears as a bare active scoring option (value='15m'); "
                "it must be marked paused/legacy/disabled."
            )
        if "15m" in o["label"]:
            lower = o["label"].lower()
            assert any(marker in lower for marker in ("paused", "legacy", "disabled")), (
                f"15m option label must be tagged paused/legacy/disabled: {o['label']!r}"
            )


# ---------------------------------------------------------------------------
# 9. Synthetic / testnet / no-live labels visible
# ---------------------------------------------------------------------------


def test_paper_view_boundary_labels_visible(page: Page, dashboard_url: str) -> None:
    _open_paper(page, dashboard_url)
    paper_text = page.locator(PAPER_VIEW).inner_text().lower()
    assert "synthetic" in paper_text, "Paper view must mention 'synthetic' PnL/positions"
    assert "testnet" in paper_text, "Paper view must mention 'testnet' lifecycle separation"
    assert "live trading is not approved" in paper_text or "live trading" in paper_text, (
        "Paper view must surface the no-live-trading boundary"
    )
