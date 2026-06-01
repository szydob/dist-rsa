from __future__ import annotations

from time import perf_counter

import ray

from core.shared.models import (
	EncryptionChunk,
	EncryptionChunkResult,
	EncryptionChunkStatus,
	RsaPublicKey,
)
from core.shared.rsa_math import encrypt_bytes
from utils.logger import get_logger


@ray.remote
class EncryptionWorker:
	"""Ray actor that encrypts one plaintext chunk at a time."""

	def __init__(self, worker_id: int) -> None:
		self.worker_id = worker_id
		self.log = get_logger(f"EncryptionWorker-{worker_id}")

	def encrypt_chunk(self, chunk: EncryptionChunk, public_key: RsaPublicKey) -> EncryptionChunkResult:
		"""Encrypt one plaintext chunk and record execution metadata.

		Args:
			chunk: Plaintext chunk to encrypt.
			public_key: RSA public key to use.

		Returns:
			Chunk result with ciphertext integers and runtime details.
		"""
		start_time = perf_counter()
		try:
			ciphertext_numbers = encrypt_bytes(chunk.payload, public_key)
			status = EncryptionChunkStatus.COMPLETED
			error = None
		except Exception as exc:  # pragma: no cover - Ray transport / worker failure
			self.log.exception("Chunk %s failed: %s", chunk.chunk_id, exc)
			ciphertext_numbers = []
			status = EncryptionChunkStatus.FAILED
			error = str(exc)

		elapsed = perf_counter() - start_time
		return EncryptionChunkResult(
			chunk_id=chunk.chunk_id,
			start=chunk.start,
			end=chunk.end,
			ciphertext_numbers=ciphertext_numbers,
			byte_length=len(chunk.payload),
			elapsed_seconds=elapsed,
			worker_id=self.worker_id,
			status=status,
			error=error,
		)
