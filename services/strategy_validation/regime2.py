"""REGIME2 — objective-aligned regime filter: fix the criterion, hold the bars.

RISK TOOL, NOT ALPHA. REGIME1 proved the breadth/bellwether mechanism is
real (gated beat always-long OOS on return, Sharpe, drawdown, and vol, and
called the live bear correctly) but FAILED its pre-committed gate because
the config was selected on TRAIN SHARPE — a criterion that rewards fast,
stay-long filters when a drawdown-control tool needs a slow one. REGIME2
changes exactly that one thing: selection on the OBJECTIVE (train drawdown
reduction, with a whipsaw tie-break), and nothing else.

THE HONESTY GUARD (this phase is confirmatory, so the discipline is
TIGHTER, not looser):
  - The search is NOT widened: REGIME1's exact grid (the same
    {30,60,90} x {0.4,0.5,0.6} x {vote,required} set), the same universe,
    window, friction, books, folds, and OOS methods. No new knobs.
  - The criterion and every gate below are PRE-REGISTERED in this module
    and the Decision Log, and committed to git BEFORE the selection runs.
    The criterion is chosen on principle (the tool's objective is drawdown
    control), not because REGIME1's hindsight table showed a passer.
  - REGIME1's bars hold UNCHANGED: the 30% OOS drawdown-reduction material
    bar, drawdown reduced vs always-long in EVERY walk-forward fold (which
    subsumes "the chop fold must not worsen" — strictly stronger), OOS
    Sharpe not worse than always-long, plus a pre-stated return-retention
    tolerance. A miss on any bar is an honest fail and is recorded as one.

Everything else (state calculator, whipsaw accounting, simulator harness,
importable gate machinery, disclaimers) is REGIME1's, reused verbatim.

Pure and deterministic: Decimal arithmetic, no I/O, no network.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping, Sequence

try:  # pragma: no cover - exercised implicitly by both import contexts
    from services.strategy_validation import regime1 as _regime1
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

    _regime1 = _load_sibling("regime1.py", "regime2_regime1")

regime1 = _regime1
RegimeConfig = _regime1.RegimeConfig
DISCLAIMER = _regime1.DISCLAIMER
VERDICT_PASS = _regime1.VERDICT_PASS
VERDICT_FAIL = _regime1.VERDICT_FAIL
_money = _regime1._money

PHASE = "REGIME2"

# ---------------------------------------------------------------------------
# PRE-REGISTRATION (committed before selection ran — see the Decision Log
# entry and this file's git history; the evidence runner emits this block
# verbatim into the committed summary).
# ---------------------------------------------------------------------------

# Selection criterion (the ONE change from REGIME1): train-only,
# objective-aligned. Primary: the LOWEST gated train max drawdown (the
# always-long train book is identical across configs, so this is exactly
# the largest train drawdown reduction). Whipsaw tie-break: configs within
# TIE_BAND_PP percentage points of the best train drawdown are ties, and
# the tie with the FEWEST train state flips wins (a config that cuts
# drawdown by flipping constantly is not preferred); final deterministic
# tie-break: config_id lexicographic. Selection NEVER sees OOS data.
TIE_BAND_PP = Decimal("2.0")

# Return-retention tolerance (pre-stated): the gated book may give up OOS
# total return vs always-long — that is a drawdown tool's nature — but not
# more than this many percentage points.
RETURN_TOLERANCE_PP = Decimal("25")

PRE_REGISTRATION = {
    "registered_in": "services/strategy_validation/regime2.py + money-flow/03_Decision_Log.md, committed to git before the selection run",
    "search_space": (
        "REGIME1's exact grid, unchanged: lookback {30,60,90} x breadth threshold "
        "{0.4,0.5,0.6} x BTC rule {vote,required} = 18 configs; same universe (DATA1 "
        "Binance 7 majors), window, friction, books, warm-up, folds, and OOS methods; "
        "the search was NOT widened"
    ),
    "selection_criterion": (
        f"train-only, objective-aligned: lowest gated train max drawdown (= largest "
        f"train drawdown reduction vs the shared always-long book); configs within "
        f"{TIE_BAND_PP} percentage points of the best are ties broken by FEWEST train "
        f"state flips (whipsaw penalty), then config_id; OOS is never seen by selection"
    ),
    "gates_all_required_pre_registered": [
        "OOS max-drawdown reduction >= 30% vs always-long (REGIME1 bar, unchanged)",
        "drawdown reduced vs always-long in EVERY walk-forward fold (REGIME1 bar, unchanged; strictly stronger than 'the chop fold must not worsen')",
        "OOS Sharpe >= always-long OOS Sharpe (REGIME1 bar, unchanged)",
        f"OOS total return >= always-long OOS total return - {RETURN_TOLERANCE_PP}pp (return-retention tolerance, pre-stated)",
        "minimum OOS days (REGIME1 bar, unchanged)",
        "no-lookahead probe verified (REGIME1 bar, unchanged)",
    ],
    "principle": (
        "the criterion is chosen because the tool's OBJECTIVE is drawdown control "
        "(REGIME1's lesson: train Sharpe rewards fast stay-long filters), not because "
        "REGIME1's hindsight table showed a passer; a miss on any gate is an honest fail"
    ),
}


# ---------------------------------------------------------------------------
# Selection (Must 1) — train only, objective-aligned, whipsaw tie-break
# ---------------------------------------------------------------------------


def select_by_train_drawdown(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Pick the config by the pre-registered criterion.

    ``rows``: per-config ``{config_id, train_max_drawdown_pct, train_flips}``
    (train-window values ONLY — the caller must never pass OOS-derived
    numbers; the evidence runner computes them strictly up to the split).
    Returns the chosen row plus the full ranking for the committed summary.
    """
    usable = [r for r in rows if r.get("train_max_drawdown_pct") is not None]
    if not usable:
        raise ValueError("regime2_selection_requires_train_drawdowns")
    best_dd = min(Decimal(str(r["train_max_drawdown_pct"])) for r in usable)
    ties = [
        r
        for r in usable
        if Decimal(str(r["train_max_drawdown_pct"])) <= best_dd + TIE_BAND_PP
    ]
    chosen = sorted(
        ties,
        key=lambda r: (int(r["train_flips"]), str(r["config_id"])),
    )[0]
    ranking = sorted(
        usable,
        key=lambda r: (
            Decimal(str(r["train_max_drawdown_pct"])),
            int(r["train_flips"]),
            str(r["config_id"]),
        ),
    )
    return {
        "chosen": dict(chosen),
        "tie_band_pp": str(TIE_BAND_PP),
        "ties_considered": [str(r["config_id"]) for r in ties],
        "ranking": [
            {
                "config_id": str(r["config_id"]),
                "train_max_drawdown_pct": str(r["train_max_drawdown_pct"]),
                "train_flips": int(r["train_flips"]),
            }
            for r in ranking
        ],
    }


def train_flips(series: Sequence[tuple[Any, Mapping[str, Any]]], *, up_to) -> int:
    """State flips strictly within the train window (selection input)."""
    window = [(t, s) for t, s in series if t <= up_to]
    return sum(
        1
        for i in range(1, len(window))
        if window[i][1]["risk_on"] != window[i - 1][1]["risk_on"]
    )


# ---------------------------------------------------------------------------
# The gate (Must 2): REGIME1's bars unchanged + the return-retention bar
# ---------------------------------------------------------------------------


def evaluate_regime_filter_gate_v2(
    *,
    always_oos_stats: Mapping[str, Any],
    gated_oos_stats: Mapping[str, Any],
    return_tolerance_pp: Decimal = RETURN_TOLERANCE_PP,
    **gate_kwargs: Any,
) -> dict[str, Any]:
    """REGIME1's full gate (30% material drawdown reduction, drawdown
    reduced in every fold, Sharpe not worse, min OOS days, no-lookahead) —
    every bar UNCHANGED — plus the pre-registered return-retention bar:
    gated OOS total return must be within ``return_tolerance_pp`` of
    always-long. Still a risk-tool verdict, never an alpha claim."""
    gate = _regime1.evaluate_regime_filter_gate(
        always_oos_stats=always_oos_stats,
        gated_oos_stats=gated_oos_stats,
        **gate_kwargs,
    )
    reasons = [] if gate["passed"] else [
        r for r in gate["reason_codes"] if r != "regime_filter_gate_passed"
    ]
    always_ret = always_oos_stats.get("total_return_pct")
    gated_ret = gated_oos_stats.get("total_return_pct")
    if (
        always_ret is None
        or gated_ret is None
        or Decimal(str(gated_ret)) < Decimal(str(always_ret)) - return_tolerance_pp
    ):
        reasons.append("oos_return_given_up_beyond_tolerance")
    passed = not reasons
    out = dict(gate)
    out["gate_id"] = "regime2_risk_off_filter_gate"
    out["status"] = VERDICT_PASS if passed else VERDICT_FAIL
    out["passed"] = passed
    out["reason_codes"] = reasons or ["regime_filter_gate_passed"]
    out["return_tolerance_pp"] = str(return_tolerance_pp)
    out["pre_registration"] = PRE_REGISTRATION
    return out


def boundary_flags() -> dict[str, bool]:
    flags = dict(_regime1.boundary_flags())
    flags.update(
        {
            "criterion_and_gates_pre_registered_before_selection": True,
            "search_space_not_widened_from_regime1": True,
            "regime1_bars_held_unchanged": True,
        }
    )
    return flags
