from __future__ import annotations

import ray

from core.encryption_coordinator import EncryptionCoordinator
from core.encryption_chunking import build_encryption_chunks
from core.key_store import InMemoryRsaKeyStore
from core.models import EncryptionStatus
from core.rsa_math import encrypt_bytes


def test_build_encryption_chunks():
    chunks = build_encryption_chunks(b"abcdef", chunk_size=2)
    assert [(chunk.start, chunk.end, chunk.payload) for chunk in chunks] == [
        (0, 2, b"ab"),
        (2, 4, b"cd"),
        (4, 6, b"ef"),
    ]


def test_encrypt_bytes_uses_public_key():
    key_store = InMemoryRsaKeyStore()
    public_key = key_store.get_public_key("alice")
    ciphertext = encrypt_bytes(b"AB", public_key)
    expected = [pow(byte_value, public_key.e, public_key.n) for byte_value in b"AB"]
    assert ciphertext == expected


def test_encryption_coordinator_encrypts_text(ray_session):
    coordinator = EncryptionCoordinator(workers_count=2, chunk_size=2)
    result = coordinator.encrypt("Hello", "alice")
    public_key = coordinator.key_store.get_public_key("alice")

    assert result.status is EncryptionStatus.COMPLETED
    assert result.recipient_id == "alice"
    assert result.public_key_id == public_key.key_id
    assert result.ciphertext_numbers == [
        pow(byte_value, public_key.e, public_key.n)
        for byte_value in "Hello".encode("utf-8")
    ]
    assert len(result.chunks) == 3
    assert {chunk.status.value for chunk in result.chunks} == {"completed"}
