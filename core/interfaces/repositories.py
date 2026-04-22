"""Persistence contract definitions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar

T = TypeVar("T")


class Repository(Protocol[T]):
    async def get(self, entity_id: str) -> T | None: ...

    async def list(self, limit: int = 100) -> Sequence[T]: ...

    async def upsert(self, entity: T) -> T: ...


class EventRepository(Protocol[T]):
    async def append(self, event: T) -> T: ...

    async def recent(self, limit: int = 100) -> Sequence[T]: ...

