"""SEL-EV1 Must 0 — strategy-type routing seam.

Research-only routing layer. Two strategy types coexist as parallel research
tracks and must never cross-contaminate each other's simulator, gate, or
evaluation:

- ``per_symbol`` (approach a): one rule evaluated independently per symbol.
  Routed to the existing per-symbol simulator
  (``goal_strat1.run_strategy_config``) and the breadth/anti-concentration
  candidate gate (``goal_strat1.evaluate_candidate_gate``). Concentration in a
  single symbol is a FAILURE for this type (the ZEC lesson).

- ``cross_sectional_selection`` (approach b): each period the universe is
  ranked and only the strongest name(s) are held. Routed to the SEL-EV1
  point-in-time portfolio simulator (``sel_ev1.simulate_selection_portfolio``)
  and the random-benchmark / rotation / OOS selection gate
  (``sel_ev1.evaluate_selection_gate``). Concentration at a point in time is
  the DESIGN here; the failure mode is instead being secretly a permanent
  single-name bet, which the selection gate's rotation/diversity check owns.

The seam is deliberately one-way-guarded: applying the per-symbol breadth gate
to a selection strategy (or the selection gate to a per-symbol strategy) raises
``StrategyTypeRoutingError`` instead of silently producing a wrong verdict.

This module only TAGS and ROUTES. It does not change the behavior or results
of any existing per-symbol lane or simulator; ``goal_strat1`` is untouched and
its output remains byte-identical (regression-checked in
``tests/test_sel_ev1_selection_evidence.py``).
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable

STRATEGY_TYPE_PER_SYMBOL = "per_symbol"
STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION = "cross_sectional_selection"
STRATEGY_TYPE_TIME_SERIES_MOMENTUM = "time_series_momentum"

STRATEGY_TYPES = (
    STRATEGY_TYPE_PER_SYMBOL,
    STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION,
    STRATEGY_TYPE_TIME_SERIES_MOMENTUM,
)

# Gate identities. Each gate may only ever be applied to its own strategy type.
PER_SYMBOL_GATE_ID = "per_symbol_breadth_friction_gate"
SELECTION_GATE_ID = "selection_random_benchmark_gate"
# TSMOM-EV1: time-series momentum is judged against BUY-AND-HOLD on a
# risk-adjusted basis (Sharpe + max drawdown) — NOT the selection
# random-benchmark gate and NOT the per-symbol breadth gate.
TSMOM_GATE_ID = "tsmom_buy_hold_risk_adjusted_gate"

# The existing founder Week 2 lanes are per-symbol strategies (approach a).
# Tagging them here changes nothing about how they run; it only makes the
# routing explicit so the selection gate can never be applied to them.
PER_SYMBOL_LANE_IDS = (
    "money_flow_v1_2_baseline",
    "avoid_low_rolling_range_20",
    "mf_orig_1d_stage2_breakout_resistance_full_equity",
)

# Cross-sectional selection configs are SEL-EV1-authored and use this prefix.
CROSS_SECTIONAL_SELECTION_ID_PREFIX = "sel_ev1_"

# Time-series momentum configs are TSMOM-EV1-authored and use this prefix.
TIME_SERIES_MOMENTUM_ID_PREFIX = "tsmom_ev1_"


class StrategyTypeRoutingError(RuntimeError):
    """A simulator/gate was applied to the wrong strategy type."""


@dataclass(frozen=True, slots=True)
class StrategyTypeRoute:
    strategy_type: str
    simulator_ref: str
    gate_ref: str
    gate_id: str
    evaluation: str


_ROUTES: dict[str, StrategyTypeRoute] = {
    STRATEGY_TYPE_PER_SYMBOL: StrategyTypeRoute(
        strategy_type=STRATEGY_TYPE_PER_SYMBOL,
        simulator_ref="services.strategy_validation.goal_strat1:run_strategy_config",
        gate_ref="services.strategy_validation.goal_strat1:evaluate_candidate_gate",
        gate_id=PER_SYMBOL_GATE_ID,
        evaluation="per_symbol_breadth_oos_candidate_evaluation",
    ),
    STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION: StrategyTypeRoute(
        strategy_type=STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION,
        simulator_ref=(
            "services.strategy_validation.sel_ev1:simulate_selection_portfolio"
        ),
        gate_ref="services.strategy_validation.sel_ev1:evaluate_selection_gate",
        gate_id=SELECTION_GATE_ID,
        evaluation="selection_random_benchmark_rotation_oos_evaluation",
    ),
    STRATEGY_TYPE_TIME_SERIES_MOMENTUM: StrategyTypeRoute(
        strategy_type=STRATEGY_TYPE_TIME_SERIES_MOMENTUM,
        simulator_ref=(
            "services.strategy_validation.tsmom_ev1:simulate_tsmom_portfolio"
        ),
        gate_ref="services.strategy_validation.tsmom_ev1:evaluate_tsmom_gate",
        gate_id=TSMOM_GATE_ID,
        evaluation="tsmom_buy_hold_risk_adjusted_oos_evaluation",
    ),
}


def strategy_type_for(strategy_id: str) -> str:
    """Resolve the strategy type for a strategy/lane id.

    SEL-EV1 selection configs carry the ``sel_ev1_`` prefix; TSMOM-EV1
    time-series momentum configs carry the ``tsmom_ev1_`` prefix. Everything
    else — the three Week 2 lanes and every GOAL-STRAT1/STRAT-DISC1-era
    per-symbol research config — is ``per_symbol``, which preserves existing
    behavior.
    """
    if strategy_id.startswith(CROSS_SECTIONAL_SELECTION_ID_PREFIX):
        return STRATEGY_TYPE_CROSS_SECTIONAL_SELECTION
    if strategy_id.startswith(TIME_SERIES_MOMENTUM_ID_PREFIX):
        return STRATEGY_TYPE_TIME_SERIES_MOMENTUM
    return STRATEGY_TYPE_PER_SYMBOL


def route_for(strategy_type: str) -> StrategyTypeRoute:
    try:
        return _ROUTES[strategy_type]
    except KeyError as exc:
        raise StrategyTypeRoutingError(f"unknown_strategy_type:{strategy_type}") from exc


def route_for_strategy_id(strategy_id: str) -> StrategyTypeRoute:
    return route_for(strategy_type_for(strategy_id))


def _resolve(ref: str) -> Callable[..., Any]:
    module_name, _, attr = ref.partition(":")
    return getattr(import_module(module_name), attr)


def resolve_simulator(strategy_type: str) -> Callable[..., Any]:
    """Return the simulator callable owned by this strategy type."""
    return _resolve(route_for(strategy_type).simulator_ref)


def resolve_gate(strategy_type: str) -> Callable[..., Any]:
    """Return the gate callable owned by this strategy type."""
    return _resolve(route_for(strategy_type).gate_ref)


def ensure_gate_applies(strategy_type: str, gate_id: str) -> None:
    """Refuse to apply a gate to the wrong strategy type.

    The per-symbol breadth/anti-concentration gate must never judge a
    selection strategy (concentration is its design), and the selection
    random-benchmark gate must never judge a per-symbol strategy.
    """
    route = route_for(strategy_type)
    if route.gate_id != gate_id:
        raise StrategyTypeRoutingError(
            f"gate_does_not_apply_to_strategy_type:{gate_id}:{strategy_type}"
        )


def routing_policy() -> dict[str, Any]:
    """JSON-ready description of the routing seam for evidence reports."""
    return {
        "strategy_types": list(STRATEGY_TYPES),
        "per_symbol_lane_ids": list(PER_SYMBOL_LANE_IDS),
        "cross_sectional_selection_id_prefix": CROSS_SECTIONAL_SELECTION_ID_PREFIX,
        "time_series_momentum_id_prefix": TIME_SERIES_MOMENTUM_ID_PREFIX,
        "routes": {
            strategy_type: {
                "simulator": route.simulator_ref,
                "gate": route.gate_ref,
                "gate_id": route.gate_id,
                "evaluation": route.evaluation,
            }
            for strategy_type, route in sorted(_ROUTES.items())
        },
        "cross_application_forbidden": True,
        "per_symbol_behavior_unchanged": True,
    }
