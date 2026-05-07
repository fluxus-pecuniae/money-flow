(function () {
  "use strict";

  const DEFAULT_FILES = [
    "../../reports/strategy_validation_reviews/sv1_13_2_dynamic_equity_20260507T104500Z/money_flow_evidence_review.json",
    "../../reports/strategy_validation/money_flow_hyperliquid_public_ytd_recent_dynamic_equity_sleeve_15m/20260507T104500Z/batch_report.json",
    "../../reports/strategy_validation/money_flow_hyperliquid_public_ytd_recent_dynamic_equity_sleeve_1h/20260507T104500Z/batch_report.json",
    "../../reports/strategy_validation/money_flow_hyperliquid_public_ytd_recent_dynamic_equity_sleeve_4h/20260507T104500Z/batch_report.json",
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
    state.activeView = view === "strategy" ? "strategy" : "evidence";
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
            <div class="pnl-track" aria-label="Net PnL magnitude">
              <div class="pnl-fill ${summary.totalNetPnl >= 0 ? "positive" : ""}" style="width:${width}%"></div>
            </div>
            <div class="component-card-metrics">
              <div class="mini-metric"><span>Net</span><strong>${escapeHtml(money(summary.totalNetPnl))}</strong></div>
              <div class="mini-metric"><span>Trades</span><strong>${escapeHtml(summary.totalTrades)}</strong></div>
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

    elements.detailSubtitle.textContent = `${selected.label} / ${selected.window}`;
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
            <th>Sizing</th>
            <th>Ending Equity</th>
            <th>Net PnL</th>
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
            <th>Net PnL</th>
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

  function render() {
    const summaries = allSummaries();
    const selected = activeSummaries();
    renderMetrics(summaries);
    renderFlags();
    renderFilters(summaries);
    renderComponentCards(summaries);
    renderDetail(selected);
    renderRunTable(selected);
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
