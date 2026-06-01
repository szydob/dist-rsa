from __future__ import annotations

from typing import Optional

from core.factorization.coordinator import FactorizationCoordinator
from core.shared.models import FactorizationResult


class FactorizationService:
    """Thin service layer for factorization clients."""

    def __init__(
        self,
        coordinator: Optional[FactorizationCoordinator] = None,
    ) -> None:
        self.coordinator = coordinator or FactorizationCoordinator()

    def factor(
        self,
        n: int,
        *,
        workers_count: Optional[int] = None,
        chunk_size: Optional[int] = None,
    ) -> FactorizationResult:
        """Factor an integer with optional coordinator overrides.

        Args:
            n: Integer to factor.
            workers_count: Optional worker-count override.
            chunk_size: Optional chunk-size override.

        Returns:
            The completed factorization result.
        """
        if workers_count is not None and workers_count <= 0:
            raise ValueError("workers_count must be positive")
        if chunk_size is not None and chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        if (
            workers_count is None or workers_count == self.coordinator.workers_count
        ) and (chunk_size is None or chunk_size == self.coordinator.chunk_size):
            return self.coordinator.factor(n)

        effective_workers_count = workers_count or self.coordinator.workers_count
        effective_chunk_size = chunk_size or self.coordinator.chunk_size
        temp_coordinator = FactorizationCoordinator(
            workers_count=effective_workers_count,
            chunk_size=effective_chunk_size,
            ray_address=self.coordinator.ray_address,
            max_workers=self.coordinator.max_workers,
        )
        return temp_coordinator.factor(n)
