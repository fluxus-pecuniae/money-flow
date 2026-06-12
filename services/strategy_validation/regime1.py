"""REGIME1 — market-regime risk-off filter: when NOT to be long.

RISK TOOL, NOT ALPHA. Trend's one durable, validated property across
TSMOM-EV1 / TREND-OVERLAY1 / TREND-SUITE1 is drawdown defense — every
profitable claim failed, but stepping aside in broad downtrends reliably
cut the bear drawdown. REGIME1 turns that into a reusable market-regime
filter: a breadth-based ``risk_on`` / ``risk_off`` state from the liquid
majors that (a) works standalone as a risk-off bell and (b) is an
importable gate other strategies call to suppress LONGS in a market-wide
downtrend. It reduces downside exposure; it does not predict returns and
must never be read as a profit claim.

The signal (Must 1) — closed candles only, no-lookahead:
  - per asset: the validated TSMOM trailing-return sign
    (``tsmom_ev1.tsmom_signal``, reused — not re-derived);
  - breadth(t) = fraction of universe assets whose trend sign is up at t;
  - bellwether: BTC's own trend sign;
  - state: ``risk_on`` iff breadth >= threshold, with the BTC rule either
    ``vote`` (BTC counts only as one breadth vote) or ``required`` (BTC's
    trend must itself be up). A graded ``risk_score`` (the breadth value,
    0..1) is exposed for display; the gate itself is binary by design.
  - bounded grid (3 lookbacks x 3 thresholds x 2 BTC rules = 18), chosen on
    the train split only.

The honest gate (Must 2): the filter must EARN its use on a long book —
equal-weight liquid majors, always-long vs regime-gated (long when
``risk_on``, cash otherwise), EXEC-EV1 conservative friction, deep DATA1
history, chronological + anchored walk-forward OOS. Pass
(``regime_filter_reduces_drawdown_oos`` — explicitly a risk-tool verdict,
not an alpha claim) requires a MATERIAL OOS max-drawdown reduction with
risk-adjusted performance not worse than always-long, drawdown reduced in
every walk-forward fold, enough OOS sample, and a verified no-lookahead
probe. The whipsaw cost (flip frequency, risk-off spells that proved
false, return given up vs always-long) is reported in full — a filter that
cuts drawdown but bleeds in chop is characterized honestly, never hidden.

Reuse: the long books are simulated through the unchanged
``tsmom_ev1.simulate_tsmom_portfolio`` benchmark seams (signal_provider;
equal-weight via vol_targeting=False). REGIME1 adds NO new strategy type
and NO new verdict route — it is a filter, like TREND-OVERLAY1; the
importable seam lives in ``strategy_types.REGIME_FILTER_REF``.

Pure and deterministic: Decimal arithmetic, no I/O, no network.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Mapping, Sequence

try:  # pragma: no cover - exercised implicitly by both import contexts
    from services.strategy_validation import tsmom_ev1 as _tsmom_ev1
except Exception:  # heavy package __init__ unavailable outside pytest
    import importlib.util
    import sys
    from pathlib import Path

    def _load_sibling(filename: str, alias: str):
        if alias in sys.modules:
            return sys.modules[alias]
        module_path = Path(__file__).resolve().with_name(filename)
        spec = importlib.util.spec_from_file_location(alias, module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"unable_to_load_module:{module_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[alias] = module
        spec.loader.exec_module(module)
        return module

    _tsmom_ev1 = _load_sibling("tsmom_ev1.py", "regime1_tsmom_ev1")

tsmom_ev1 = _tsmom_ev1
tsmom_signal = _tsmom_ev1.tsmom_signal
curve_stats = _tsmom_ev1.curve_stats
_money = _tsmom_ev1._money

PHASE = "REGIME1"

DISCLAIMER = (
    "RISK-OFF FILTER / DRAWDOWN CONTROL, NOT ALPHA: this signal reduces "
    "downside exposure in broad downtrends; it does not predict returns and "
    "does not guarantee profit (the gated book gives up return in choppy "
    "markets - the whipsaw cost is reported, not hidden). Signal only - not "
    "an order, not trading advice; nothing here submits orders or enables "
    "any trading mode."
)

STATE_RISK_ON = "risk_on"
STATE_RISK_OFF = "risk_off"

VERDICT_PASS = "regime_filter_reduces_drawdown_oos"
VERDICT_FAIL = "regime_filter_does_not_reduce_drawdown_oos"

# Bounded grid (train-only choice): the validated TSMOM lookbacks, breadth
# thresholds around the half mark, and the two documented BTC rules.
REGIME_LOOKBACKS = (30, 60, 90)
BREADTH_THRESHOLDS = (Decimal("0.4"), Decimal("0.5"), Decimal("0.6"))
BTC_RULES = ("vote", "required")
BELLWETHER_SYMBOL = "BTC"

# Risk-tool gate parameters (documented up front, never tuned on outcomes):
# a MATERIAL drawdown reduction is at least this relative cut vs always-long.
MIN_RELATIVE_DD_REDUCTION = Decimal("0.30")
MIN_OOS_DAYS = 90
MIN_FOLD_DAYS = 60


@dataclass(frozen=True, slots=True)
class RegimeConfig:
    config_id: str
    lookback_days: int
    breadth_threshold: Decimal
    btc_rule: str  # vote | required
    bellwether: str = BELLWETHER_SYMBOL


def generate_regime_configs() -> list[RegimeConfig]:
    """The full bounded grid; parameters are chosen on the train split only."""
    configs: list[RegimeConfig] = []
    for lookback in REGIME_LOOKBACKS:
        for threshold in BREADTH_THRESHOLDS:
            for btc_rule in BTC_RULES:
                thr = str(threshold).replace("0.", "")
                configs.append(
                    RegimeConfig(
                        config_id=f"regime1_lb{lookback}_br{thr}_btc_{btc_rule}_1d",
                        lookback_days=lookback,
                        breadth_threshold=threshold,
                        btc_rule=btc_rule,
                    )
                )
    return configs


# The deployed default is pinned to the committed evidence summary's
# train-only choice (test-enforced, like TREND-OVERLAY1): re-tuning the
# deployed filter without new evidence fails CI. NOTE the committed verdict:
# this config did NOT clear the drawdown-reduction gate (it missed the 30%
# material bar and worsened drawdown in the chop fold) — the state it emits
# is informational risk context, not a validated control, and every surface
# says so.
DEFAULT_CONFIG = RegimeConfig(
    config_id="regime1_lb30_br5_btc_vote_1d",
    lookback_days=30,
    breadth_threshold=Decimal("0.5"),
    btc_rule="vote",
)
COMMITTED_VERDICT_NOTE = (
    "evidence verdict: regime_filter_does_not_reduce_drawdown_oos — the "
    "train-chosen filter did not clear its pre-committed drawdown-reduction "
    "gate (missed the 30% material bar; worsened drawdown in the chop fold); "
    "the emitted state is informational risk context, not a validated control"
)


# ---------------------------------------------------------------------------
# The regime state (closed candles only; causal by construction)
# ---------------------------------------------------------------------------


def regime_state_at(
    closes_by_symbol: Mapping[str, Sequence[Decimal]],
    idx_by_symbol: Mapping[str, int],
    config: RegimeConfig,
) -> dict[str, Any] | None:
    """The market-regime state from data up to and including each symbol's
    candle at its index — None during warm-up (insufficient history).

    breadth = fraction of symbols whose trailing trend sign is up; the
    state is ``risk_on`` iff breadth >= threshold AND (btc_rule == 'vote'
    or BTC's own sign is up). ``risk_score`` is the graded breadth (0..1),
    exposed for display only — the gate is binary.
    """
    ups = 0
    total = 0
    btc_up: bool | None = None
    for symbol in sorted(closes_by_symbol):
        sig = tsmom_signal(closes_by_symbol[symbol], idx_by_symbol[symbol], config.lookback_days)
        if sig is None:
            return None  # warm-up: never guess a state
        total += 1
        if sig == 1:
            ups += 1
        if symbol == config.bellwether:
            btc_up = sig == 1
    if total == 0 or btc_up is None:
        return None
    breadth = Decimal(ups) / Decimal(total)
    risk_on = breadth >= config.breadth_threshold and (config.btc_rule == "vote" or btc_up)
    return {
        "state": STATE_RISK_ON if risk_on else STATE_RISK_OFF,
        "risk_on": risk_on,
        "breadth": breadth,
        "breadth_up_count": ups,
        "universe_size": total,
        "btc_trend_up": btc_up,
        "risk_score": breadth,  # graded 0..1, informational
        "config_id": config.config_id,
        "disclaimer": DISCLAIMER,
    }


def compute_regime_series(
    universe: Any, config: RegimeConfig
) -> list[tuple[datetime, dict[str, Any]]]:
    """The regime state at every aligned close of a SelectionUniverse where
    every symbol has enough history (warm-up closes are omitted, never
    guessed)."""
    symbols = universe.symbols
    closes = {s: [c.close for c in universe.datasets[s].candles] for s in symbols}
    series: list[tuple[datetime, dict[str, Any]]] = []
    for t in universe.timeline:
        idx_map: dict[str, int] = {}
        ok = True
        for s in symbols:
            idx = universe.index_by_time[s].get(t)
            if idx is None:
                ok = False
                break
            idx_map[s] = idx
        if not ok:
            continue
        state = regime_state_at(closes, idx_map, config)
        if state is not None:
            series.append((t, state))
    return series


def verify_regime_point_in_time(
    universe: Any, config: RegimeConfig, sample_times: Sequence[datetime]
) -> bool:
    """True iff the regime state provably ignores the future: truncating
    every symbol's candles right after t reproduces the state at t, and
    tampering with every close AFTER t cannot change it."""
    symbols = universe.symbols
    closes = {s: [c.close for c in universe.datasets[s].candles] for s in symbols}
    for t in sample_times:
        idx_map = {s: universe.index_by_time[s][t] for s in symbols}
        full = regime_state_at(closes, idx_map, config)
        truncated = {s: closes[s][: idx_map[s] + 1] for s in symbols}
        if regime_state_at(truncated, idx_map, config) != full:
            return False
        tampered = {
            s: [
                c if j <= idx_map[s] else c * Decimal("-7") + Decimal("1")
                for j, c in enumerate(closes[s])
            ]
            for s in symbols
        }
        if regime_state_at(tampered, idx_map, config) != full:
            return False
    return True


# ---------------------------------------------------------------------------
# The importable gate (Must 3): other phases suppress longs in risk-off
# ---------------------------------------------------------------------------


class RegimeGateError(RuntimeError):
    """The gate was asked about a time it has no closed-candle state for."""


class RegimeGate:
    """Read-only risk-off gate over a computed regime-state series.

    ``is_risk_on(as_of)`` returns the state at the LATEST closed candle at
    or before ``as_of`` — asking about a time before the first state raises
    (the gate never guesses). The intended use is suppressing LONG entries
    while ``risk_off``; it is drawdown control, not a return prediction.
    """

    def __init__(self, series: Sequence[tuple[datetime, dict[str, Any]]], config: RegimeConfig):
        if not series:
            raise RegimeGateError("regime_gate_requires_a_non_empty_state_series")
        self._times = [t for t, _ in series]
        self._states = [state for _, state in series]
        self.config = config
        self.disclaimer = DISCLAIMER

    def state_at(self, as_of: datetime) -> dict[str, Any]:
        pos = bisect_right(self._times, as_of)
        if pos == 0:
            raise RegimeGateError(f"no_regime_state_at_or_before:{as_of.isoformat()}")
        return dict(self._states[pos - 1])

    def is_risk_on(self, as_of: datetime) -> bool:
        return bool(self.state_at(as_of)["risk_on"])

    @property
    def first_state_time(self) -> datetime:
        return self._times[0]

    @property
    def last_state_time(self) -> datetime:
        return self._times[-1]


def build_regime_gate(datasets: Sequence[Any], config: RegimeConfig | None = None) -> RegimeGate:
    """Build the importable gate from goal_strat1 Datasets (closed daily
    candles, timestamps = close times). Default config is the committed
    train-only choice — re-tuning it without new evidence fails CI."""
    sel_ev1 = _load_sel_ev1()
    universe = sel_ev1.SelectionUniverse(list(datasets))
    cfg = config or DEFAULT_CONFIG
    return RegimeGate(compute_regime_series(universe, cfg), cfg)


def _load_sel_ev1():
    try:
        from services.strategy_validation import sel_ev1

        return sel_ev1
    except Exception:  # pragma: no cover - sibling-loading context
        import importlib.util
        import sys
        from pathlib import Path

        alias = "regime1_sel_ev1"
        if alias in sys.modules:
            return sys.modules[alias]
        module_path = Path(__file__).resolve().with_name("sel_ev1.py")
        spec = importlib.util.spec_from_file_location(alias, module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"unable_to_load_module:{module_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[alias] = module
        spec.loader.exec_module(module)
        return module


# ---------------------------------------------------------------------------
# Signal providers for the two books (benchmark plumbing through tsmom_ev1)
# ---------------------------------------------------------------------------


def always_long_provider(_symbol: str, _idx: int) -> int:
    return 1


def gated_long_provider(
    universe: Any, config: RegimeConfig
) -> Callable[[str, int], int | None]:
    """+1 while ``risk_on`` at that symbol's decision candle, 0 (cash) in
    ``risk_off``, None during warm-up — evaluated from closes up to and
    including the decision index only (causal by construction)."""
    symbols = universe.symbols
    closes = {s: [c.close for c in universe.datasets[s].candles] for s in symbols}
    time_by_index = {
        s: {i: c.timestamp for i, c in enumerate(universe.datasets[s].candles)}
        for s in symbols
    }

    def provider(symbol: str, idx: int) -> int | None:
        t = time_by_index[symbol].get(idx)
        if t is None:
            return None
        idx_map: dict[str, int] = {}
        for s in symbols:
            other_idx = universe.index_by_time[s].get(t)
            if other_idx is None:
                return None
            idx_map[s] = other_idx
        state = regime_state_at(closes, idx_map, config)
        if state is None:
            return None
        return 1 if state["risk_on"] else 0

    return provider


# ---------------------------------------------------------------------------
# Whipsaw cost (Must 2): characterized honestly, never hidden
# ---------------------------------------------------------------------------


def whipsaw_stats(
    series: Sequence[tuple[datetime, dict[str, Any]]],
    always_long_curve: Sequence[tuple[datetime, Decimal]],
    *,
    after: datetime | None = None,
) -> dict[str, Any]:
    """Flip frequency, risk-off spells, and what the filter cost/saved
    measured against the ALWAYS-LONG book's own daily PnL during risk-off
    days: spells where always-long gained are FALSE risk-offs (return given
    up); spells where it lost are drawdown avoided."""
    window = [(t, s) for t, s in series if after is None or t > after]
    pnl_by_day: dict[datetime, Decimal] = {}
    for i in range(1, len(always_long_curve)):
        t, value = always_long_curve[i]
        pnl_by_day[t] = value - always_long_curve[i - 1][1]
    flips = 0
    spells: list[dict[str, Any]] = []
    current_spell: dict[str, Any] | None = None
    risk_off_days = 0
    for i, (t, state) in enumerate(window):
        if i > 0 and state["risk_on"] != window[i - 1][1]["risk_on"]:
            flips += 1
        if not state["risk_on"]:
            risk_off_days += 1
            day_pnl = pnl_by_day.get(t, Decimal("0"))
            if current_spell is None:
                current_spell = {"start": t, "days": 0, "always_long_net": Decimal("0")}
            current_spell["days"] += 1
            current_spell["end"] = t
            current_spell["always_long_net"] += day_pnl
        elif current_spell is not None:
            spells.append(current_spell)
            current_spell = None
    if current_spell is not None:
        spells.append(current_spell)
    false_spells = [s for s in spells if s["always_long_net"] > 0]
    days = len(window)
    years = Decimal(days) / Decimal("365") if days else Decimal("0")
    return {
        "days": days,
        "risk_off_days": risk_off_days,
        "risk_off_fraction": _money(Decimal(risk_off_days) / Decimal(days)) if days else None,
        "state_flips": flips,
        "flips_per_year": _money(Decimal(flips) / years) if years > 0 else None,
        "risk_off_spells": len(spells),
        "mean_spell_days": _money(
            Decimal(sum(s["days"] for s in spells)) / Decimal(len(spells))
        )
        if spells
        else None,
        "false_risk_off_spells": len(false_spells),
        "return_given_up_in_false_risk_off": _money(
            sum((s["always_long_net"] for s in false_spells), Decimal("0"))
        ),
        "drawdown_avoided_in_true_risk_off": _money(
            sum((s["always_long_net"] for s in spells if s["always_long_net"] <= 0), Decimal("0"))
        ),
        "spell_detail": [
            {
                "start": str(s["start"]),
                "end": str(s["end"]),
                "days": s["days"],
                "always_long_net_during_spell": str(_money(s["always_long_net"])),
                "false_risk_off": s["always_long_net"] > 0,
            }
            for s in spells
        ],
    }


# ---------------------------------------------------------------------------
# The risk-tool gate (Must 2) — drawdown reduction, never an alpha claim
# ---------------------------------------------------------------------------


def evaluate_regime_filter_gate(
    *,
    always_oos_stats: Mapping[str, Any],
    gated_oos_stats: Mapping[str, Any],
    fold_dd_reductions: Sequence[Mapping[str, Any]],
    no_lookahead_verified: bool,
    min_relative_dd_reduction: Decimal = MIN_RELATIVE_DD_REDUCTION,
    min_oos_days: int = MIN_OOS_DAYS,
) -> dict[str, Any]:
    """The honest risk-tool verdict. PASS requires ALL of:
      - OOS max drawdown MATERIALLY reduced: gated <= (1 - reduction) x
        always-long;
      - risk-adjusted not worse: gated OOS Sharpe >= always-long OOS Sharpe
        (the filter may give up raw return — that is its nature — but it
        must not be a worse risk-adjusted hold);
      - drawdown reduced in EVERY walk-forward fold (vs always-long over
        the same fold);
      - enough OOS days; and the no-lookahead probe verified.
    The verdict is a RISK-TOOL pass (drawdown reduction), explicitly never
    an alpha claim — the qualifier travels in the output and every surface.
    """
    reasons: list[str] = []
    always_dd = always_oos_stats.get("max_drawdown_pct")
    gated_dd = gated_oos_stats.get("max_drawdown_pct")
    if always_dd is None or gated_dd is None or (
        Decimal(str(gated_dd))
        > (Decimal("1") - min_relative_dd_reduction) * Decimal(str(always_dd))
    ):
        reasons.append("oos_drawdown_not_materially_reduced")
    always_sharpe = always_oos_stats.get("sharpe_annual")
    gated_sharpe = gated_oos_stats.get("sharpe_annual")
    if gated_sharpe is None or (
        always_sharpe is not None and Decimal(str(gated_sharpe)) < Decimal(str(always_sharpe))
    ):
        reasons.append("oos_risk_adjusted_worse_than_always_long")
    if not fold_dd_reductions or any(
        fold.get("gated_max_drawdown_pct") is None
        or fold.get("always_max_drawdown_pct") is None
        or Decimal(str(fold["gated_max_drawdown_pct"]))
        >= Decimal(str(fold["always_max_drawdown_pct"]))
        for fold in fold_dd_reductions
    ):
        reasons.append("walk_forward_drawdown_not_reduced_in_every_fold")
    if (gated_oos_stats.get("days") or 0) < min_oos_days:
        reasons.append("rejected_low_oos_days")
    if not no_lookahead_verified:
        reasons.append("no_lookahead_unverified")
    status = VERDICT_PASS if not reasons else VERDICT_FAIL
    qualifiers = ["risk_tool_not_alpha_no_profit_claim"]
    always_ret = always_oos_stats.get("total_return_pct")
    gated_ret = gated_oos_stats.get("total_return_pct")
    if (
        always_ret is not None
        and gated_ret is not None
        and Decimal(str(gated_ret)) < Decimal(str(always_ret))
    ):
        qualifiers.append("gives_up_return_vs_always_long_by_design")
    return {
        "gate_id": "regime1_risk_off_filter_gate",
        "status": status,
        "passed": status == VERDICT_PASS,
        "verdict_semantics": "risk-tool pass: material OOS drawdown reduction at not-worse risk-adjusted performance — explicitly NOT an alpha claim",
        "reason_codes": reasons or ["regime_filter_gate_passed"],
        "qualifiers": qualifiers,
        "always_long_oos": dict(always_oos_stats),
        "gated_oos": dict(gated_oos_stats),
        "min_relative_dd_reduction": str(min_relative_dd_reduction),
        "fold_dd_reductions": [dict(f) for f in fold_dd_reductions],
        "min_oos_days_required": min_oos_days,
        "no_lookahead_verified": no_lookahead_verified,
        "disclaimer": DISCLAIMER,
    }


def boundary_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "risk_tool_not_alpha": True,
        "signal_only_no_orders": True,
        "changes_production_money_flow_rules": False,
        "changes_per_symbol_lane_behavior_or_results": False,
        "changes_selection_lane_behavior_or_results": False,
        "changes_tsmom_lane_behavior_or_results": False,
        "mutates_active_pt_rt_runtime": False,
        "mutates_runtime_artifacts": False,
        "creates_order_intent": False,
        "creates_prepared_venue_order": False,
        "creates_submitted_order": False,
        "submits_live_orders": False,
        "submits_testnet_orders": False,
        "calls_private_signed_or_order_endpoints": False,
        "approves_live_trading": False,
        "approves_production_strategy": False,
        "modeled_depth_not_real": True,
    }
