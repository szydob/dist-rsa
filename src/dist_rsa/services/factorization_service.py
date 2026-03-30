from __future__ import annotations

from typing import Optional

from dist_rsa.core.coordinator import FactorizationCoordinator
from dist_rsa.core.models import FactorizationResult


class FactorizationService:
    """Thin service layer for clients (e.g., GUI or API)."""

    def __init__(
        self,
        coordinator: Optional[FactorizationCoordinator] = None,
    ) -> None:
        self.coordinator = coordinator or FactorizationCoordinator()

    def factor(self, n: int, *, chunk_size: Optional[int] = None) -> FactorizationResult:
        """Execute factorization with optional chunk_size override."""
        if chunk_size is not None and chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        if chunk_size is None or chunk_size == self.coordinator.chunk_size:
            return self.coordinator.factor(n)

        temp_coordinator = FactorizationCoordinator(
            chunk_size=chunk_size,
            ray_address=self.coordinator.ray_address,
        )
        return temp_coordinator.factor(n)
