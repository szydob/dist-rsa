from __future__ import annotations

from core.decryption_chunking import build_decryption_chunks
from core.decryption_coordinator import DecryptionCoordinator
from core.key_store import InMemoryRsaKeyStore
from core.models import DecryptionStatus
from core.rsa_math import encrypt_bytes


def test_build_decryption_chunks():
    chunks = build_decryption_chunks([11, 22, 33, 44, 55], chunk_size=2)
    assert [(chunk.start, chunk.end, chunk.payload) for chunk in chunks] == [
        (0, 2, [11, 22]),
        (2, 4, [33, 44]),
        (4, 5, [55]),
    ]


def test_decryption_coordinator_decrypts_text(ray_session):
    key_store = InMemoryRsaKeyStore()
    public_key = key_store.get_public_key("alice")
    private_key = key_store.get_private_key("alice")
    plaintext = "Hello"
    ciphertext = encrypt_bytes(plaintext.encode("utf-8"), public_key)

    coordinator = DecryptionCoordinator(workers_count=2, chunk_size=2, key_store=key_store)
    result = coordinator.decrypt(ciphertext, "alice")

    assert result.status is DecryptionStatus.COMPLETED
    assert result.owner_id == "alice"
    assert result.private_key_id == private_key.key_id
    assert result.plaintext == plaintext
    assert result.ciphertext_length == len(ciphertext)
    assert len(result.chunks) == 3
    assert {chunk.status.value for chunk in result.chunks} == {"completed"}
