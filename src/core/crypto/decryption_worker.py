from __future__ import annotations

from time import perf_counter

import ray

from core.shared.models import (
	DecryptionChunk,
	DecryptionChunkResult,
	DecryptionChunkStatus,
	RsaPrivateKey,
)
from utils.logger import get_logger


@ray.remote
class DecryptionWorker:
	"""Ray actor that decrypts one ciphertext chunk at a time."""

	def __init__(self, worker_id: int) -> None:
		self.worker_id = worker_id
		self.log = get_logger(f"DecryptionWorker-{worker_id}")

	def decrypt_chunk(self, chunk: DecryptionChunk, private_key: RsaPrivateKey) -> DecryptionChunkResult:
		"""Decrypt one ciphertext chunk and record execution metadata.

		Args:
			chunk: Ciphertext chunk to decrypt.
			private_key: RSA private key to use.

		Returns:
			Chunk result with plaintext bytes and runtime details.
		"""
		start_time = perf_counter()
		try:
			plaintext_bytes = bytes(pow(value, private_key.d, private_key.n) for value in chunk.payload)
			status = DecryptionChunkStatus.COMPLETED
			error = None
		except Exception as exc:  # pragma: no cover - Ray transport / worker failure
			self.log.exception("Chunk %s failed: %s", chunk.chunk_id, exc)
			plaintext_bytes = b""
			status = DecryptionChunkStatus.FAILED
			error = str(exc)

		elapsed = perf_counter() - start_time
		return DecryptionChunkResult(
			chunk_id=chunk.chunk_id,
			start=chunk.start,
			end=chunk.end,
			plaintext_bytes=plaintext_bytes,
			byte_length=len(chunk.payload),
			elapsed_seconds=elapsed,
			worker_id=self.worker_id,
			status=status,
			error=error,
		)
