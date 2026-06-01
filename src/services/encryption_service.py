from __future__ import annotations

from typing import Optional

from core.crypto.encryption_coordinator import EncryptionCoordinator
from core.shared.key_store import InMemoryRsaKeyStore
from core.shared.models import EncryptionResult


class EncryptionService:
    """Thin service layer for distributed RSA encryption."""

    def __init__(
        self,
        coordinator: Optional[EncryptionCoordinator] = None,
        key_store: Optional[InMemoryRsaKeyStore] = None,
    ) -> None:
        self.key_store = key_store or InMemoryRsaKeyStore()
        self.coordinator = coordinator or EncryptionCoordinator(key_store=self.key_store)

    def list_recipients(self) -> list[str]:
        """Return the available encryption recipients."""
        return self.key_store.list_public_recipients()

    def encrypt(
        self,
        plaintext: str,
        recipient_id: str,
        *,
        workers_count: Optional[int] = None,
        chunk_size: Optional[int] = None,
    ) -> EncryptionResult:
        """Encrypt plaintext for a recipient using the configured coordinator.

        Args:
            plaintext: Message to encrypt.
            recipient_id: Recipient identifier from the key store.
            workers_count: Optional override for worker count.
            chunk_size: Optional override for chunk size.

        Returns:
            The completed encryption result.
        """
        if workers_count is None and chunk_size is None:
            return self.coordinator.encrypt(plaintext, recipient_id)

        effective_workers_count = workers_count or self.coordinator.workers_count
        effective_chunk_size = chunk_size or self.coordinator.chunk_size
        temp_coordinator = EncryptionCoordinator(
            workers_count=effective_workers_count,
            chunk_size=effective_chunk_size,
            key_store=self.key_store,
            ray_address=self.coordinator.ray_address,
        )
        return temp_coordinator.encrypt(plaintext, recipient_id)
