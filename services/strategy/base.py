"""Shared strategy family framework."""

from __future__ import annotations

from typing import Protocol

from core.domain.models import StrategyEvaluationInput, StrategyEvaluationResult, StrategyFamilyStatus


class StrategyFamilyModule(Protocol):
    async def evaluate(self, evaluation_input: StrategyEvaluationInput) -> StrategyEvaluationResult: ...

    async def get_family_status(self) -> StrategyFamilyStatus: ...
