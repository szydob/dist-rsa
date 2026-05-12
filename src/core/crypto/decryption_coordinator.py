from __future__ import annotations

import os
from datetime import datetime
from time import perf_counter
from typing import Dict, Optional
from uuid import uuid4

import ray

from core.crypto.decryption_chunking import build_decryption_chunks
from core.crypto.decryption_worker import DecryptionWorker
from core.shared.key_store import InMemoryRsaKeyStore
from core.shared.models import (
	DecryptionChunk,
	DecryptionChunkResult,
	DecryptionChunkStatus,
	DecryptionResult,
	DecryptionStatus,
	DecryptionTask,
)
from utils.logger import get_logger


class DecryptionCoordinator:
	"""Coordinates distributed RSA decryption on Ray."""

	def __init__(
		self,
		workers_count: int = 4,
		chunk_size: int = 32,
		max_workers: int = 64,
		key_store: Optional[InMemoryRsaKeyStore] = None,
		ray_address: Optional[str] = None,
		log_level: str = "INFO",
	) -> None:
		if workers_count <= 0:
			raise ValueError("workers_count must be positive")
		if chunk_size <= 0:
			raise ValueError("chunk_size must be positive")
		if max_workers <= 0:
			raise ValueError("max_workers must be positive")

		self.workers_count = workers_count
		self.chunk_size = chunk_size
		self.max_workers = max_workers
		self.key_store = key_store or InMemoryRsaKeyStore()
		self.ray_address = ray_address
		self.log = get_logger(self.__class__.__name__, level=log_level)

	def _ensure_ray(self) -> None:
		if not ray.is_initialized():
			ray.init(
				address=self.ray_address or "local",
				include_dashboard=False,
				ignore_reinit_error=True,
				namespace="dist-rsa",
				log_to_driver=False,
			)

	def decrypt(self, ciphertext_numbers: list[int], owner_id: str) -> DecryptionResult:
		if not ciphertext_numbers:
			raise ValueError("ciphertext_numbers must not be empty")

		self._ensure_ray()
		private_key = self.key_store.get_private_key(owner_id)
		task = DecryptionTask(
			owner_id=owner_id,
			chunk_size=self.chunk_size,
			workers_count=self.workers_count,
			ciphertext_length=len(ciphertext_numbers),
			task_id=str(uuid4()),
			created_at=datetime.utcnow(),
			status=DecryptionStatus.RUNNING,
		)
		chunks = build_decryption_chunks(ciphertext_numbers, self.chunk_size)
		available_cpus = max(os.cpu_count() or 1, 1)
		effective_workers = max(
			1,
			min(
				self.workers_count,
				self.max_workers,
				available_cpus,
				len(chunks),
			),
		)
		self.log.info(
			"Task %s started for owner %s with %s chunks and %s/%s workers",
			task.task_id,
			owner_id,
			len(chunks),
			effective_workers,
			self.workers_count,
		)

		workers = [DecryptionWorker.remote(worker_id=index) for index in range(effective_workers)]
		pending: Dict[ray.ObjectRef, DecryptionChunk] = {}

		for index, chunk in enumerate(chunks):
			worker = workers[index % len(workers)]
			pending[worker.decrypt_chunk.remote(chunk, private_key)] = chunk

		chunk_results: list[DecryptionChunkResult] = []
		start_time = perf_counter()

		try:
			while pending:
				done_refs, _ = ray.wait(list(pending.keys()), num_returns=1, timeout=None)

				for ref in done_refs:
					chunk = pending.pop(ref, None)
					if chunk is None:
						continue

					try:
						result: DecryptionChunkResult = ray.get(ref)
					except Exception as exc:  # pragma: no cover - Ray transport
						self.log.exception("Chunk %s failed: %s", chunk.chunk_id, exc)
						result = DecryptionChunkResult(
							chunk_id=chunk.chunk_id,
							start=chunk.start,
							end=chunk.end,
							plaintext_bytes=b"",
							byte_length=len(chunk.payload),
							elapsed_seconds=0.0,
							worker_id=-1,
							status=DecryptionChunkStatus.FAILED,
							error=str(exc),
						)

					chunk_results.append(result)
		finally:
			elapsed = perf_counter() - start_time

		chunk_results.sort(key=lambda item: item.chunk_id)
		plaintext_bytes = b"".join(result.plaintext_bytes for result in chunk_results)
		status = (
			DecryptionStatus.COMPLETED
			if all(result.status is DecryptionChunkStatus.COMPLETED for result in chunk_results)
			else DecryptionStatus.FAILED
		)
		message = None if status is DecryptionStatus.COMPLETED else "At least one chunk failed"

		result = DecryptionResult(
			task_id=task.task_id,
			status=status,
			owner_id=owner_id,
			private_key_id=private_key.key_id,
			workers_count=effective_workers,
			chunk_size=self.chunk_size,
			ciphertext_length=len(ciphertext_numbers),
			elapsed_seconds=elapsed,
			chunks=chunk_results,
			plaintext=plaintext_bytes.decode("utf-8", errors="replace"),
			message=message,
		)

		self.log.info(
			"Task %s completed for owner %s in %.3fs",
			task.task_id,
			owner_id,
			elapsed,
		)
		return result
