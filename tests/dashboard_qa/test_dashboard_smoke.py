"""DASH-QA1 — nine browser-level smoke checks for the Money Flow OS dashboard.

Pins the documented regressions so they cannot silently return (updated in
lockstep with the DASH-IA1 2-tab consolidation):
  1. Paper Trading is the default tab and loads.
  2. Terminal layout visible (status strip + full-width filter bar + rails +
     chart + bottom blotter + testnet footer — the DASH-IA1 reflow).
  3. Chart does not grow the page infinitely (autoSize/ResizeObserver guard).
  4. Tab switching persists state (aria-selected + prior selection retained).
  5. Bottom blotter tab does not reset across refresh cycles.
  6. Retired tabs absent: Audit (DASH-PT1.1) and Historical Replay / The Lab /
     Strategy (DASH-IA1); nav is exactly Paper Trading + Research Log.
  7. The three active lanes from current_truth.json appear in their surviving
     home: the Paper Trading status strip (the Strategy tab is retired).
  8. 15m is paused/legacy, never an active scoring timeframe.
  9. Synthetic / testnet / no-live boundary labels visible in the paper view,
     including the relocated full-width Testnet Order Transport footer.

Grounded in real selectors from apps/dashboard/index.html and expected truth
from current_truth.json (the TRUTH1 registry).
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.browser

NAV = ".view-tabs"
PAPER_TAB = '.view-tab[data-view="paper-observation"]'
RESEARCH_LOG_TAB = '.view-tab[data-view="research-log"]'
RETIRED_TAB_VIEWS = ("historical-replay", "evidence-lab", "strategy", "evidence", "audit")

PAPER_VIEW = "#paper-observation-view"
TERMINAL_GRID = "#paper-observation-terminal-grid"
LEFT_RAIL = "#paper-observation-terminal-grid .paper-observation-left-rail"
CENTER_STAGE = "#paper-observation-terminal-grid .paper-observation-center-stage"
RIGHT_RAIL = "#paper-observation-terminal-grid .paper-observation-right-rail"
BOTTOM_BLOTTER = "#paper-observation-bottom-blotter"
BLOTTER_TABS = ".paper-observation-blotter-tabs [data-paper-terminal-tab]"
HEALTH_BANNER = "#paper-observation-health-banner"
TIMEFRAME_FILTER = "#paper-observation-timeframe-filter"
FILTER_BAR = "#paper-observation-view .paper-observation-filterbar"
TESTNET_FOOTER = "#paper-observation-view .paper-observation-testnet-footer"
RESEARCH_LOG_VIEW = "#research-log-view"

# Bounded waits for refresh-cycle observation (the dashboard polls ~1s in places).
REFRESH_OBSERVATION_MS = 4_000
BLOTTER_OBSERVATION_MS = 3_000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _goto(page: Page, url: str) -> None:
    """Navigate without waiting for full network idle.

    The dashboard's background timers (even with ?disableLivePolling=true)
    keep the network from going idle for 500ms on slower CI runners, which
    causes `wait_until="networkidle"` to time out after 30s. The DOM and
    init scripts are what we actually need — wait_until="load" + an explicit
    nav-tabs visibility check is sufficient and works on both macOS and Ubuntu.
    """
    page.goto(url, wait_until="load")
    expect(page.locator(NAV)).to_be_visible()
    # Confirm the view tabs have been rendered so click handlers are attached.
    expect(page.locator(PAPER_TAB)).to_be_visible()


def _open_paper(page: Page, url: str) -> None:
    _goto(page, url)
    page.locator(PAPER_TAB).click()
    expect(page.locator(PAPER_VIEW)).to_be_visible()


# ---------------------------------------------------------------------------
# 1. Paper Trading loads
# ---------------------------------------------------------------------------


def test_paper_trading_tab_loads(page: Page, dashboard_url: str) -> None:
    _goto(page, dashboard_url)
    # DASH-IA1: Paper Trading is the default tab — visible without a click.
    expect(page.locator(PAPER_TAB)).to_have_attribute("aria-selected", "true")
    expect(page.locator(PAPER_VIEW)).to_be_visible()
    # Research Log starts hidden and opens on click.
    expect(page.locator(RESEARCH_LOG_VIEW)).to_be_hidden()
    page.locator(RESEARCH_LOG_TAB).click()
    expect(page.locator(RESEARCH_LOG_VIEW)).to_be_visible()
    page.locator(PAPER_TAB).click()
    expect(page.locator(PAPER_VIEW)).to_be_visible()


# ---------------------------------------------------------------------------
# 2. Terminal layout visible
# ---------------------------------------------------------------------------


def test_terminal_layout_visible(page: Page, dashboard_url: str) -> None:
    _open_paper(page, dashboard_url)
    expect(page.locator(HEALTH_BANNER)).to_be_visible()
    # DASH-IA1 reflow: Global Filters are a full-width bar under the status
    # strip (outside the terminal grid), not inside the left rail.
    expect(page.locator(FILTER_BAR)).to_be_visible()
    filter_bar_in_left_rail = page.locator(
        f"{LEFT_RAIL} .paper-observation-filterbar"
    ).count()
    assert filter_bar_in_left_rail == 0, "Global Filters must not sit inside the left rail"
    expect(page.locator(TERMINAL_GRID)).to_be_visible()
    expect(page.locator(LEFT_RAIL)).to_be_visible()
    expect(page.locator(CENTER_STAGE)).to_be_visible()
    expect(page.locator(RIGHT_RAIL)).to_be_visible()
    expect(page.locator(BOTTOM_BLOTTER)).to_be_visible()
    # DASH-IA1 reflow: Testnet Order Transport is a full-width footer card.
    expect(page.locator(TESTNET_FOOTER)).to_be_visible()
    testnet_in_right_rail = page.locator(
        f"{RIGHT_RAIL} .paper-observation-testnet-panel"
    ).count()
    assert testnet_in_right_rail == 0, "Testnet transport must not sit inside the right rail"


# ---------------------------------------------------------------------------
# 3. Chart does not grow the page infinitely
# ---------------------------------------------------------------------------


CHART_HEIGHT_JS = """
() => {
  const el = document.getElementById('paper-observation-live-chart');
  return el ? el.getBoundingClientRect().height : 0;
}
"""


def test_chart_does_not_grow_page(page: Page, dashboard_url: str) -> None:
    """Guard the autoSize / ResizeObserver feedback-loop P0.

    Measures the live-chart container's own bounding-box height (not the whole
    document's scrollHeight, which moves around during deferred render of lazy
    widgets unrelated to the chart). The documented bug had the chart resize
    its container, the ResizeObserver fire, the chart resize again, and so on —
    that would show up as continuous growth of the chart container itself.
    """
    _open_paper(page, dashboard_url)
    expect(page.locator("#paper-observation-live-chart")).to_be_visible()
    # Brief settle for the chart's initial resize.
    page.wait_for_timeout(500)
    initial = float(page.evaluate(CHART_HEIGHT_JS))
    # Observe through refresh cycles.
    page.wait_for_timeout(REFRESH_OBSERVATION_MS)
    final = float(page.evaluate(CHART_HEIGHT_JS))
    drift = abs(final - initial)
    # Tight tolerance: chart should not grow more than 50 px after first paint.
    assert drift < 50, (
        f"#paper-observation-live-chart height drifted by {drift:.0f}px "
        f"({initial:.0f} -> {final:.0f}) — possible autoSize feedback loop"
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
    page.locator(RESEARCH_LOG_TAB).click()
    expect(page.locator(RESEARCH_LOG_TAB)).to_have_attribute("aria-selected", "true")
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


def test_retired_tabs_absent_and_nav_is_two(page: Page, dashboard_url: str) -> None:
    _goto(page, dashboard_url)
    # DASH-PT1.1 retired Audit; DASH-IA1 retired Historical Replay, The Lab
    # (evidence-lab), Strategy, and renamed Evidence -> Research Log.
    for view in RETIRED_TAB_VIEWS:
        assert page.locator(f'.view-tab[data-view="{view}"]').count() == 0, (
            f"Retired nav tab still present: {view}"
        )
    nav_buttons = [t.strip() for t in page.locator(".view-tabs .view-tab").all_text_contents()]
    assert nav_buttons == ["Paper Trading", "Research Log"], (
        f"Nav must be exactly Paper Trading + Research Log; saw: {nav_buttons}"
    )
    for retired_label in ("Audit", "Historical Replay", "The Lab", "Strategy", "Evidence"):
        assert retired_label not in nav_buttons


# ---------------------------------------------------------------------------
# 7. Strategy shows only the three active lanes
# ---------------------------------------------------------------------------


def test_active_lanes_visible_in_surviving_home(
    page: Page, dashboard_url: str, current_truth: dict
) -> None:
    """DASH-IA1 relocation of check #7: the Strategy tab is retired, so the
    three active lanes must appear in their surviving home — the Paper Trading
    status strip (rendered as color-coded lane chips)."""
    _open_paper(page, dashboard_url)
    expect(page.locator(HEALTH_BANNER)).to_be_visible()
    banner_text = page.locator(HEALTH_BANNER).inner_text()
    expected_lane_ids = [lane["lane_id"] for lane in current_truth["active_lanes"]]
    assert len(expected_lane_ids) == 3, (
        f"current_truth.json declares {len(expected_lane_ids)} active lanes; expected 3"
    )
    for lane_id in expected_lane_ids:
        assert lane_id in banner_text, (
            f"Paper Trading status strip missing active lane id: {lane_id}"
        )


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
    # DASH-IA1: the relocated full-width Testnet Order Transport footer keeps
    # its safety labels visible at the bottom of the paper view.
    footer = page.locator(TESTNET_FOOTER)
    expect(footer).to_be_visible()
    footer_text = footer.inner_text().lower()
    assert "testnet" in footer_text
    assert "synthetic-only" in footer_text or "synthetic" in footer_text
