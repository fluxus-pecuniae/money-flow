(function () {
  "use strict";

  const DEFAULT_FILES = [
    "../../reports/strategy_validation_reviews/sv1_13_2_dynamic_equity_20260507T104500Z/money_flow_evidence_review.json",
    "../../reports/strategy_validation/money_flow_hyperliquid_public_ytd_recent_dynamic_equity_sleeve_15m/20260507T104500Z/batch_report.json",
    "../../reports/strategy_validation/money_flow_hyperliquid_public_ytd_recent_dynamic_equity_sleeve_1h/20260507T104500Z/batch_report.json",
    "../../reports/strategy_validation/money_flow_hyperliquid_public_ytd_recent_dynamic_equity_sleeve_4h/20260507T104500Z/batch_report.json",
  ];

  const SV115_BASELINE = [
    {
      component: "sleeve_15m",
      scenarios: 36,
      endingEquitySum: 274061.42,
      netPnlSum: -85938.58,
      minEndingEquity: 6459.22,
      maxDrawdown: 3645.61,
      trades: 7660,
    },
    {
      component: "sleeve_1h",
      scenarios: 36,
      endingEquitySum: 381997.91,
      netPnlSum: 21997.91,
      minEndingEquity: 8313.22,
      maxDrawdown: 2150.85,
      trades: 4484,
    },
    {
      component: "sleeve_4h",
      scenarios: 36,
      endingEquitySum: 287620.62,
      netPnlSum: -72379.38,
      minEndingEquity: 6772.35,
      maxDrawdown: 3492.34,
      trades: 1280,
    },
  ];

  const SV115_VARIANTS = [
    {
      id: "extension_limit_4h_1_5pct",
      label: "4h extension limit 1.5%",
      component: "sleeve_4h",
      baselineNet: -72379.38,
      variantNet: -41687.13,
      delta: 30692.25,
      methodology: "completed_trade_overlay_estimate",
      drawdown: 2179.32,
      filtered: 240,
      avoidedLosers: 196,
      missedWinners: 44,
      status: "overlay improved; needs true replay",
    },
    {
      id: "extension_limit_4h_2_0pct",
      label: "4h extension limit 2.0%",
      component: "sleeve_4h",
      baselineNet: -72379.38,
      variantNet: -66323.01,
      delta: 6056.37,
      methodology: "completed_trade_overlay_estimate",
      drawdown: 3093.98,
      filtered: 72,
      avoidedLosers: 52,
      missedWinners: 20,
      status: "overlay improved; needs true replay",
    },
    {
      id: "higher_low_confirmation_20c",
      label: "Higher-low confirmation",
      component: "sleeve_15m + sleeve_1h",
      baselineNet: -63940.66,
      variantNet: -81652.17,
      delta: -17711.51,
      methodology: "completed_trade_overlay_estimate",
      drawdown: 3645.61,
      filtered: 408,
      avoidedLosers: 251,
      missedWinners: 157,
      status: "deteriorated; damaged ETH 1h",
    },
    {
      id: "recent_low_invalidation_proxy_20c",
      label: "Recent-low invalidation proxy",
      component: "sleeve_1h + sleeve_4h",
      baselineNet: -50381.47,
      variantNet: 247743.31,
      delta: 298124.78,
      methodology: "lookahead_diagnostic_proxy",
      drawdown: 1937.18,
      filtered: 2088,
      avoidedLosers: 2088,
      missedWinners: 0,
      status: "upper-bound only; not candidate",
    },
    {
      id: "resistance_proximity_0_25pct",
      label: "Resistance proximity 0.25%",
      component: "all sleeves",
      baselineNet: -136320.05,
      variantNet: -107096.22,
      delta: 29223.83,
      methodology: "completed_trade_overlay_estimate",
      drawdown: 3492.34,
      filtered: 2974,
      avoidedLosers: 2251,
      missedWinners: 723,
      status: "overlay improved; slight ETH 1h damage",
    },
    {
      id: "resistance_proximity_0_50pct",
      label: "Resistance proximity 0.50%",
      component: "all sleeves",
      baselineNet: -136320.05,
      variantNet: -100502.45,
      delta: 35817.6,
      methodology: "completed_trade_overlay_estimate",
      drawdown: 3492.34,
      filtered: 5612,
      avoidedLosers: 4234,
      missedWinners: 1378,
      status: "overlay improved; damaged ETH 1h",
    },
    {
      id: "sideways_regime_avoidance_15m",
      label: "15m sideways avoidance",
      component: "sleeve_15m",
      baselineNet: -85938.58,
      variantNet: -6258.54,
      delta: 79680.04,
      methodology: "completed_trade_overlay_estimate",
      drawdown: 600.73,
      filtered: 6988,
      avoidedLosers: 5459,
      missedWinners: 1529,
      status: "reduced 15m losses; still negative",
    },
  ];

  const SV115_ETH_1H = [
    ["higher_low_confirmation_20c", 27143.25, 20406.69, -6736.57, "deteriorated"],
    ["recent_low_invalidation_proxy_20c", 27143.25, 118927.38, 91784.13, "preserved or improved, proxy caveat"],
    ["resistance_proximity_0_25pct", 27143.25, 26599.19, -544.06, "slightly deteriorated"],
    ["resistance_proximity_0_50pct", 27143.25, 3727.39, -23415.86, "damaged"],
  ];

  const SV115_FINDINGS = [
    "Most SV1.15 numbers are completed-trade overlay estimates, not full candle-by-candle forward replays.",
    "Recent-low invalidation is a lookahead diagnostic upper bound, not a candidate rule result until exact exit replay exists.",
    "Lower-RSI entry admission is not implemented; current evidence only supports RSI-zone attribution from completed trades.",
    "ETH 1h completed trades were stronger in the upper half of the current RSI band than the lower half.",
    "15m lower-band completed trades were negative across BTC, ETH, and SOL.",
    "4h RSI zones were negative across symbols in this campaign.",
    "ETH 1h continuation-style completed trades were stronger than pullback-style completed trades.",
    "No variant is authorized for production, paper trading, or live trading.",
  ];

  const SV115_METHODOLOGY = [
    "completed_trade_overlay_estimate: filters already-completed baseline trades; useful for ranking hypotheses, not authorizing rules.",
    "lookahead_diagnostic_proxy: uses completed-trade hindsight; current recent-low result is an upper-bound diagnostic only.",
    "reporting_only_attribution: labels completed trades without changing entries or exits.",
    "deferred_requires_rejected_signal_replay: lower-RSI admission needs rejected-signal instrumentation before true testing.",
  ];

  const state = {
    review: null,
    batches: [],
    selectedComponent: "all",
    activeView: "evidence",
  };

  const elements = {
    viewTabs: Array.from(document.querySelectorAll("[data-view]")),
    viewPanels: Array.from(document.querySelectorAll("[data-view-panel]")),
    status: document.querySelector("#review-status"),
    sourceLabel: document.querySelector("#data-source-label"),
    sourceDetail: document.querySelector("#data-source-detail"),
    fileInput: document.querySelector("#json-file-input"),
    metricPacks: document.querySelector("#metric-packs"),
    metricPacksDetail: document.querySelector("#metric-packs-detail"),
    metricRuns: document.querySelector("#metric-runs"),
    metricRunsDetail: document.querySelector("#metric-runs-detail"),
    metricCoverage: document.querySelector("#metric-coverage"),
    metricBoundary: document.querySelector("#metric-boundary"),
    componentFilter: document.querySelector("#component-filter"),
    boundaryFlags: document.querySelector("#boundary-flags"),
    componentCards: document.querySelector("#component-cards"),
    detailSubtitle: document.querySelector("#detail-subtitle"),
    timingChart: document.querySelector("#timing-chart"),
    symbolChart: document.querySelector("#symbol-chart"),
    regimeTable: document.querySelector("#regime-table"),
    checklist: document.querySelector("#review-checklist"),
    runTable: document.querySelector("#run-table"),
    experimentVariantCards: document.querySelector("#experiment-variant-cards"),
    experimentBaselineTable: document.querySelector("#experiment-baseline-table"),
    experimentEthTable: document.querySelector("#experiment-eth-table"),
    experimentFindings: document.querySelector("#experiment-findings"),
    experimentMethodology: document.querySelector("#experiment-methodology"),
    experimentTable: document.querySelector("#experiment-table"),
  };

  function decimal(value, fallback = 0) {
    if (value === null || value === undefined || value === "") return fallback;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function money(value) {
    const parsed = decimal(value);
    const sign = parsed < 0 ? "-" : "";
    return `${sign}$${Math.abs(parsed).toLocaleString(undefined, {
      maximumFractionDigits: 0,
    })}`;
  }

  function pct(value) {
    return `${(decimal(value) * 100).toLocaleString(undefined, {
      maximumFractionDigits: 1,
    })}%`;
  }

  function cleanComponentName(component) {
    return String(component || "unknown").replace("sleeve_", "").toUpperCase();
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function batchComponent(batch) {
    const matrixComponent = batch.assumptions_matrix?.components?.[0];
    const comparisonComponent = batch.comparison_summary?.component_comparison?.[0]?.component_keys;
    return matrixComponent || comparisonComponent || batch.batch_name || "unknown";
  }

  function batchSummary(batch) {
    const comparison = batch.comparison_summary || {};
    const componentComparison = comparison.component_comparison?.[0] || {};
    const coverage = comparison.data_coverage_comparison || [];
    const runs = batch.run_reports || [];
    const completedRuns = runs.filter((run) => run.status === "completed");
    const component = batchComponent(batch);
    const firstRun = completedRuns[0]?.report;
    const firstCoverage = coverage[0];
    const totalExpected = coverage.reduce(
      (sum, row) => sum + decimal(row.total_expected_candle_count),
      0,
    );
    const totalActual = coverage.reduce((sum, row) => sum + decimal(row.total_actual_candle_count), 0);

    return {
      batch,
      component,
      label: cleanComponentName(component),
      timeframe:
        firstRun?.component_reports?.[0]?.timeframe ||
        firstRun?.data_coverage_summary?.components?.[0]?.timeframe ||
        component.replace("sleeve_", ""),
      window:
        firstCoverage?.date_window ||
        `${firstRun?.start_at || "unknown"} -> ${firstRun?.end_at || "unknown"}`,
      completedRunCount: decimal(componentComparison.completed_run_count, completedRuns.length),
      blockedRunCount: decimal(componentComparison.blocked_run_count),
      totalNetPnl: decimal(componentComparison.total_net_pnl),
      averageNetPnl: decimal(componentComparison.average_net_pnl),
      totalTrades: decimal(componentComparison.total_trades),
      totalFees: decimal(componentComparison.total_fees),
      totalSlippage: decimal(componentComparison.total_slippage_cost),
      largestDrawdown: decimal(componentComparison.largest_mark_to_market_drawdown),
      coveragePercent: totalExpected > 0 ? totalActual / totalExpected : 0,
      expectedCandles: totalExpected,
      actualCandles: totalActual,
      fillTiming: comparison.fill_timing_comparison || [],
      symbols: comparison.symbol_comparison || [],
      regimes: comparison.regime_comparison || [],
      runSummaries: comparison.run_summaries || [],
      bestNetPnl: comparison.highest_observed_net_pnl_run || null,
      worstNetPnl: comparison.lowest_observed_net_pnl_run || null,
      bestWinRate: comparison.highest_observed_win_rate_run || null,
    };
  }

  function allSummaries() {
    return state.batches.map(batchSummary).sort((a, b) => a.component.localeCompare(b.component));
  }

  function activeSummaries() {
    const summaries = allSummaries();
    if (state.selectedComponent === "all") return summaries;
    return summaries.filter((summary) => summary.component === state.selectedComponent);
  }

  function setEmpty(target, message) {
    target.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
  }

  function setActiveView(view) {
    state.activeView = ["evidence", "experiments", "strategy"].includes(view) ? view : "evidence";
    elements.viewTabs.forEach((tab) => {
      tab.setAttribute("aria-selected", String(tab.dataset.view === state.activeView));
    });
    elements.viewPanels.forEach((panel) => {
      panel.hidden = panel.dataset.viewPanel !== state.activeView;
    });
  }

  function renderMetrics(summaries) {
    const generatedPaths = state.review?.generated_evidence_pack_paths || [];
    const packCount =
      generatedPaths.length ||
      state.review?.generated_campaign_count ||
      summaries.filter((summary) => summary.completedRunCount > 0).length;
    const totalRuns = summaries.reduce((sum, summary) => sum + summary.completedRunCount, 0);
    const totalExpected = summaries.reduce((sum, summary) => sum + summary.expectedCandles, 0);
    const totalActual = summaries.reduce((sum, summary) => sum + summary.actualCandles, 0);
    const coverage = totalExpected > 0 ? totalActual / totalExpected : 0;

    elements.status.textContent = state.review?.paper_readiness_review_status || "local review";
    elements.metricPacks.textContent = String(packCount);
    elements.metricPacksDetail.textContent =
      state.review?.blocked_campaign_count === 0 ? "generated" : "mixed";
    elements.metricRuns.textContent = String(totalRuns);
    elements.metricRunsDetail.textContent = `${summaries.length} component packs`;
    elements.metricCoverage.textContent = pct(coverage);
    elements.metricBoundary.textContent = state.review?.paper_readiness_review_status
      ? "review"
      : "blocked";
  }

  function renderFlags() {
    const flags = [
      ["No live artifacts", state.review?.creates_live_artifacts === false],
      ["No exchange adapters", state.review?.calls_exchange_adapters === false],
      ["No private endpoints", state.review?.calls_private_exchange_endpoints === false],
      ["No order endpoints", state.review?.calls_exchange_order_endpoints === false],
      ["Manual review", true],
    ];
    elements.boundaryFlags.innerHTML = flags
      .map(([label, ok]) => `<span class="pill ${ok ? "good" : "warn"}">${escapeHtml(label)}</span>`)
      .join("");
  }

  function renderFilters(summaries) {
    const components = ["all", ...summaries.map((summary) => summary.component)];
    elements.componentFilter.innerHTML = components
      .map((component) => {
        const label = component === "all" ? "All" : cleanComponentName(component);
        return `<button class="segment-button" type="button" role="tab" aria-selected="${
          state.selectedComponent === component
        }" data-component="${escapeHtml(component)}">${escapeHtml(label)}</button>`;
      })
      .join("");
    elements.componentFilter.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        state.selectedComponent = button.dataset.component || "all";
        render();
      });
    });
  }

  function renderComponentCards(summaries) {
    const maxMagnitude = Math.max(...summaries.map((summary) => Math.abs(summary.totalNetPnl)), 1);
    elements.componentCards.innerHTML = summaries
      .map((summary) => {
        const width = Math.max(3, Math.round((Math.abs(summary.totalNetPnl) / maxMagnitude) * 100));
        const isSelected =
          state.selectedComponent === "all" || state.selectedComponent === summary.component;
        return `
          <button class="component-card" type="button" aria-current="${isSelected}" data-component="${
            escapeHtml(summary.component)
          }">
            <div class="component-card-header">
              <span class="component-card-title">${escapeHtml(summary.label)}</span>
              <span>${escapeHtml(summary.timeframe)}</span>
            </div>
            <div class="pnl-track" aria-label="Sum net PnL across research runs magnitude">
              <div class="pnl-fill ${summary.totalNetPnl >= 0 ? "positive" : ""}" style="width:${width}%"></div>
            </div>
            <div class="component-card-metrics">
              <div class="mini-metric"><span>Sum Net</span><strong>${escapeHtml(money(summary.totalNetPnl))}</strong></div>
              <div class="mini-metric"><span>Sum Trades</span><strong>${escapeHtml(summary.totalTrades)}</strong></div>
              <div class="mini-metric"><span>Drawdown</span><strong>${escapeHtml(money(summary.largestDrawdown))}</strong></div>
            </div>
          </button>
        `;
      })
      .join("");
    elements.componentCards.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        state.selectedComponent = button.dataset.component || "all";
        render();
      });
    });
  }

  function renderBarList(target, rows, labelKey, valueKey, formatter) {
    if (!rows.length) {
      setEmpty(target, "No rows loaded.");
      return;
    }
    const values = rows.map((row) => decimal(row[valueKey]));
    const maxMagnitude = Math.max(...values.map(Math.abs), 1);
    target.innerHTML = rows
      .map((row) => {
        const value = decimal(row[valueKey]);
        const width = Math.max(3, Math.round((Math.abs(value) / maxMagnitude) * 100));
        return `
          <div class="bar-row">
            <span class="bar-label">${escapeHtml(row[labelKey] || "unknown")}</span>
            <div class="bar-track"><div class="bar-fill ${
              value >= 0 ? "positive" : ""
            }" style="width:${width}%"></div></div>
            <span class="bar-value">${escapeHtml(formatter(value))}</span>
          </div>
        `;
      })
      .join("");
  }

  function renderDetail(summaries) {
    const selected = summaries[0];
    if (!selected) {
      elements.detailSubtitle.textContent = "No component selected.";
      setEmpty(elements.timingChart, "Load evidence review and batch report JSON.");
      setEmpty(elements.symbolChart, "Load evidence review and batch report JSON.");
      setEmpty(elements.regimeTable, "Load evidence review and batch report JSON.");
      elements.checklist.innerHTML = "";
      return;
    }

    elements.detailSubtitle.textContent = `${selected.label} / ${selected.window} / grouped research sums, not one account`;
    renderBarList(
      elements.timingChart,
      selected.fillTiming,
      "fill_timing",
      "average_net_pnl",
      money,
    );
    renderBarList(elements.symbolChart, selected.symbols, "symbol", "total_net_pnl", money);
    renderRegimeTable(selected.regimes);
    renderChecklist();
  }

  function renderRegimeTable(rows) {
    if (!rows.length) {
      setEmpty(elements.regimeTable, "No regime rows loaded.");
      return;
    }
    elements.regimeTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Type</th>
            <th>Regime</th>
            <th>Trades</th>
            <th>Sum Net PnL</th>
            <th>Win Rate</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(row.regime_type || "")}</td>
                  <td>${escapeHtml(row.regime_label || "")}</td>
                  <td>${escapeHtml(row.total_trades ?? row.trade_count ?? 0)}</td>
                  <td>${escapeHtml(money(row.total_net_pnl ?? row.net_pnl))}</td>
                  <td>${escapeHtml(row.win_rate === null || row.win_rate === undefined ? "n/a" : pct(row.win_rate))}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderChecklist() {
    const criteria = state.review?.manual_paper_trading_readiness_criteria || [
      "Founder/operator review is complete; this is not an automated go/no-go decision.",
      "Observed performance survives next-candle timing assumptions.",
      "Drawdown remains within founder/operator research tolerance.",
    ];
    elements.checklist.innerHTML = criteria.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  }

  function renderRunTable(summaries) {
    const rows = summaries
      .flatMap((summary) => summary.runSummaries.map((row) => ({ ...row, component: summary.label })))
      .slice()
      .sort((a, b) => decimal(b.metrics?.net_pnl) - decimal(a.metrics?.net_pnl))
      .slice(0, 36);

    if (!rows.length) {
      setEmpty(elements.runTable, "No run summaries loaded.");
      return;
    }

    elements.runTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Component</th>
            <th>Symbol</th>
            <th>Fill</th>
            <th>Fee</th>
            <th>Slip</th>
            <th>Sizing</th>
            <th>Ending Equity</th>
            <th>Scenario Net PnL</th>
            <th>Win</th>
            <th>Trades</th>
            <th>Drawdown</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(row.component)}</td>
                  <td>${escapeHtml(row.symbol)}</td>
                  <td>${escapeHtml(row.fill_timing)}</td>
                  <td>${escapeHtml(row.fee_bps)}</td>
                  <td>${escapeHtml(row.slippage_bps)}</td>
                  <td>${escapeHtml(row.metrics?.capital_sizing_mode || row.capital_sizing_mode || "constant_initial_capital_notional_per_trade")}</td>
                  <td>${escapeHtml(money(row.metrics?.ending_equity ?? row.metrics?.net_pnl))}</td>
                  <td>${escapeHtml(money(row.metrics?.net_pnl))}</td>
                  <td>${escapeHtml(pct(row.metrics?.win_rate))}</td>
                  <td>${escapeHtml(row.metrics?.number_of_trades ?? 0)}</td>
                  <td>${escapeHtml(money(row.metrics?.mark_to_market_max_drawdown))}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderExperimentCards() {
    if (!elements.experimentVariantCards) return;
    const maxMagnitude = Math.max(...SV115_VARIANTS.map((row) => Math.abs(row.delta)), 1);
    elements.experimentVariantCards.innerHTML = SV115_VARIANTS.map((row) => {
      const width = Math.max(3, Math.round((Math.abs(row.delta) / maxMagnitude) * 100));
      return `
        <article class="component-card experiment-card" aria-current="${row.delta >= 0}">
          <div class="component-card-header">
            <span class="component-card-title">${escapeHtml(row.label)}</span>
            <span>${escapeHtml(row.component)}</span>
          </div>
          <p class="card-note">${escapeHtml(row.methodology)}</p>
          <div class="pnl-track" aria-label="Delta versus baseline magnitude">
            <div class="pnl-fill ${row.delta >= 0 ? "positive" : ""}" style="width:${width}%"></div>
          </div>
          <div class="component-card-metrics">
            <div class="mini-metric"><span>Delta</span><strong>${escapeHtml(money(row.delta))}</strong></div>
            <div class="mini-metric"><span>Filtered</span><strong>${escapeHtml(row.filtered)}</strong></div>
            <div class="mini-metric"><span>Status</span><strong>${escapeHtml(row.status)}</strong></div>
          </div>
        </article>
      `;
    }).join("");
  }

  function renderExperimentBaseline() {
    if (!elements.experimentBaselineTable) return;
    elements.experimentBaselineTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Component</th>
            <th>Scenarios</th>
            <th>Ending Equity Sum</th>
            <th>Net Account PnL Sum</th>
            <th>Min Ending Equity</th>
            <th>Max Drawdown</th>
            <th>Trades</th>
          </tr>
        </thead>
        <tbody>
          ${SV115_BASELINE.map((row) => `
            <tr>
              <td>${escapeHtml(row.component)}</td>
              <td>${escapeHtml(row.scenarios)}</td>
              <td>${escapeHtml(money(row.endingEquitySum))}</td>
              <td>${escapeHtml(money(row.netPnlSum))}</td>
              <td>${escapeHtml(money(row.minEndingEquity))}</td>
              <td>${escapeHtml(money(row.maxDrawdown))}</td>
              <td>${escapeHtml(row.trades)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderExperimentEth() {
    if (!elements.experimentEthTable) return;
    elements.experimentEthTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Variant</th>
            <th>Baseline Net Sum</th>
            <th>Variant Net Sum</th>
            <th>Delta</th>
            <th>ETH 1h Status</th>
          </tr>
        </thead>
        <tbody>
          ${SV115_ETH_1H.map(([variant, baseline, result, delta, status]) => `
            <tr>
              <td>${escapeHtml(variant)}</td>
              <td>${escapeHtml(money(baseline))}</td>
              <td>${escapeHtml(money(result))}</td>
              <td>${escapeHtml(money(delta))}</td>
              <td>${escapeHtml(status)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderExperimentFindings() {
    if (!elements.experimentFindings) return;
    elements.experimentFindings.innerHTML = SV115_FINDINGS.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    if (!elements.experimentMethodology) return;
    elements.experimentMethodology.innerHTML = SV115_METHODOLOGY.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  }

  function renderExperimentTable() {
    if (!elements.experimentTable) return;
    elements.experimentTable.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Variant</th>
            <th>Methodology</th>
            <th>Baseline Net</th>
            <th>Variant Net</th>
            <th>Delta</th>
            <th>Drawdown</th>
            <th>Filtered</th>
            <th>Losing Avoided</th>
            <th>Winning Missed</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${SV115_VARIANTS.map((row) => `
            <tr>
              <td>${escapeHtml(row.id)}</td>
              <td>${escapeHtml(row.methodology)}</td>
              <td>${escapeHtml(money(row.baselineNet))}</td>
              <td>${escapeHtml(money(row.variantNet))}</td>
              <td>${escapeHtml(money(row.delta))}</td>
              <td>${escapeHtml(money(row.drawdown))}</td>
              <td>${escapeHtml(row.filtered)}</td>
              <td>${escapeHtml(row.avoidedLosers)}</td>
              <td>${escapeHtml(row.missedWinners)}</td>
              <td>${escapeHtml(row.status)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderExperiments() {
    renderExperimentCards();
    renderExperimentBaseline();
    renderExperimentEth();
    renderExperimentFindings();
    renderExperimentTable();
  }

  function render() {
    const summaries = allSummaries();
    const selected = activeSummaries();
    renderMetrics(summaries);
    renderFlags();
    renderFilters(summaries);
    renderComponentCards(summaries);
    renderDetail(selected);
    renderRunTable(selected);
    renderExperiments();
  }

  function classifyJson(payload) {
    if (Array.isArray(payload?.campaign_results)) return "review";
    if (Array.isArray(payload?.run_reports)) return "batch";
    return "unknown";
  }

  async function loadDefaultFiles() {
    const loaded = [];
    for (const path of DEFAULT_FILES) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        loaded.push({ path, payload });
      } catch (error) {
        console.warn(`Could not load ${path}`, error);
      }
    }

    if (!loaded.length) {
      elements.sourceLabel.textContent = "Manual load";
      elements.sourceDetail.textContent = "Use the JSON loader to select local evidence files.";
      render();
      return;
    }

    state.review = null;
    state.batches = [];
    loaded.forEach(({ payload }) => {
      const type = classifyJson(payload);
      if (type === "review") state.review = payload;
      if (type === "batch") state.batches.push(payload);
    });

    elements.sourceLabel.textContent = "Dynamic equity reports loaded";
    elements.sourceDetail.textContent = `${loaded.length} JSON files from ignored SV1.13.2 dynamic_equity_pct reports paths.`;
    render();
  }

  function handleFiles(files) {
    const readers = Array.from(files).map(
      (file) =>
        new Promise((resolve) => {
          const reader = new FileReader();
          reader.onload = () => {
            try {
              resolve({ name: file.name, payload: JSON.parse(String(reader.result)) });
            } catch (error) {
              resolve({ name: file.name, error });
            }
          };
          reader.readAsText(file);
        }),
    );

    Promise.all(readers).then((items) => {
      const valid = items.filter((item) => item.payload);
      if (!valid.length) return;
      state.review = null;
      state.batches = [];
      valid.forEach(({ payload }) => {
        const type = classifyJson(payload);
        if (type === "review") state.review = payload;
        if (type === "batch") state.batches.push(payload);
      });
      state.selectedComponent = "all";
      elements.sourceLabel.textContent = "Manual JSON loaded";
      elements.sourceDetail.textContent = `${valid.length} local files selected.`;
      render();
    });
  }

  elements.fileInput.addEventListener("change", (event) => {
    handleFiles(event.target.files || []);
  });

  elements.viewTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      setActiveView(tab.dataset.view || "evidence");
    });
  });

  setActiveView(state.activeView);
  render();
  loadDefaultFiles();
})();
