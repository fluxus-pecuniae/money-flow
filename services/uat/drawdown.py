"""Runtime/UAT drawdown monitoring policy and state helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class UATDrawdownPolicy:
    threshold_pct: Decimal = Decimal("0.10")
    phase_requirement: str = (
        "UAT1 may proceed with monitor designed but not live-fed; "
        "UAT2 requires shadow/runtime state visible; "
        "UAT3 requires sandbox/live account drawdown feed wired and tested."
    )
    performance_validation: bool = False


@dataclass(frozen=True)
class UATDrawdownObservation:
    timestamp_utc: datetime
    observed_equity: Decimal
    realized_pnl: Decimal | None = None
    unrealized_pnl: Decimal | None = None


@dataclass(frozen=True)
class UATDrawdownState:
    candidate_id: str
    universe_asset_id: str | None
    timestamp_utc: datetime
    initial_observed_equity: Decimal
    current_observed_equity: Decimal
    realized_pnl: Decimal | None
    unrealized_pnl: Decimal | None
    max_observed_equity: Decimal
    max_drawdown_amount: Decimal
    max_drawdown_pct: Decimal
    drawdown_threshold_pct: Decimal
    threshold_breached: bool
    reason_codes: tuple[str, ...]
    shadow_or_simulated: bool


class UATDrawdownMonitor:
    """Tracks observed drawdown from caller-supplied equity values.

    The monitor does not fetch balances, subscribe to exchanges, or validate
    profitability. It provides operator-risk visibility for future UAT phases.
    """

    def __init__(
        self,
        *,
        candidate_id: str,
        initial_observed_equity: Decimal,
        policy: UATDrawdownPolicy | None = None,
        universe_asset_id: str | None = None,
        shadow_or_simulated: bool = True,
    ) -> None:
        if initial_observed_equity <= 0:
            raise ValueError("initial_observed_equity must be positive")
        self.candidate_id = candidate_id
        self.universe_asset_id = universe_asset_id
        self.policy = policy or UATDrawdownPolicy()
        self.initial_observed_equity = initial_observed_equity
        self.max_observed_equity = initial_observed_equity
        self.shadow_or_simulated = shadow_or_simulated

    def observe(self, observation: UATDrawdownObservation) -> UATDrawdownState:
        current = observation.observed_equity
        if current > self.max_observed_equity:
            self.max_observed_equity = current
        drawdown_amount = max(Decimal("0"), self.max_observed_equity - current)
        drawdown_pct = drawdown_amount / self.max_observed_equity
        threshold_breached = drawdown_pct >= self.policy.threshold_pct
        reason_codes: list[str] = []
        if threshold_breached:
            reason_codes.append("uat_drawdown_threshold_breached")
        if self.shadow_or_simulated:
            reason_codes.append("shadow_or_simulated_drawdown_not_account_truth")

        return UATDrawdownState(
            candidate_id=self.candidate_id,
            universe_asset_id=self.universe_asset_id,
            timestamp_utc=observation.timestamp_utc,
            initial_observed_equity=self.initial_observed_equity,
            current_observed_equity=current,
            realized_pnl=observation.realized_pnl,
            unrealized_pnl=observation.unrealized_pnl,
            max_observed_equity=self.max_observed_equity,
            max_drawdown_amount=drawdown_amount,
            max_drawdown_pct=drawdown_pct,
            drawdown_threshold_pct=self.policy.threshold_pct,
            threshold_breached=threshold_breached,
            reason_codes=tuple(reason_codes),
            shadow_or_simulated=self.shadow_or_simulated,
        )

