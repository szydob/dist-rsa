from __future__ import annotations

from typing import Optional

from core.crypto.decryption_coordinator import DecryptionCoordinator
from core.shared.key_store import InMemoryRsaKeyStore
from core.shared.models import DecryptionResult


class DecryptionService:
    """Thin service layer for clients that want distributed RSA decryption."""

    def __init__(
        self,
        coordinator: Optional[DecryptionCoordinator] = None,
        key_store: Optional[InMemoryRsaKeyStore] = None,
    ) -> None:
        self.key_store = key_store or InMemoryRsaKeyStore()
        self.coordinator = coordinator or DecryptionCoordinator(key_store=self.key_store)

    def list_owners(self) -> list[str]:
        return self.key_store.list_private_owners()

    def decrypt(
        self,
        ciphertext_numbers: list[int],
        owner_id: str,
        *,
        workers_count: Optional[int] = None,
        chunk_size: Optional[int] = None,
    ) -> DecryptionResult:
        if workers_count is None and chunk_size is None:
            return self.coordinator.decrypt(ciphertext_numbers, owner_id)

        effective_workers_count = workers_count or self.coordinator.workers_count
        effective_chunk_size = chunk_size or self.coordinator.chunk_size
        temp_coordinator = DecryptionCoordinator(
            workers_count=effective_workers_count,
            chunk_size=effective_chunk_size,
            key_store=self.key_store,
            ray_address=self.coordinator.ray_address,
        )
        return temp_coordinator.decrypt(ciphertext_numbers, owner_id)
