from __future__ import annotations

import os
from datetime import datetime
from time import perf_counter
from typing import Dict, Optional
from uuid import uuid4

import ray

from core.crypto.encryption_chunking import build_encryption_chunks
from core.crypto.encryption_worker import EncryptionWorker
from core.shared.key_store import InMemoryRsaKeyStore
from core.shared.models import (
	EncryptionChunk,
	EncryptionChunkResult,
	EncryptionChunkStatus,
	EncryptionResult,
	EncryptionStatus,
	EncryptionTask,
)
from utils.logger import get_logger


class EncryptionCoordinator:
	"""Coordinates distributed RSA encryption on Ray."""

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

	def encrypt(self, plaintext: str, recipient_id: str) -> EncryptionResult:
		if not plaintext:
			raise ValueError("plaintext must not be empty")

		self._ensure_ray()
		public_key = self.key_store.get_public_key(recipient_id)
		plaintext_bytes = plaintext.encode("utf-8")
		task = EncryptionTask(
			recipient_id=recipient_id,
			chunk_size=self.chunk_size,
			workers_count=self.workers_count,
			plaintext_length=len(plaintext_bytes),
			task_id=str(uuid4()),
			created_at=datetime.utcnow(),
			status=EncryptionStatus.RUNNING,
		)
		chunks = build_encryption_chunks(plaintext_bytes, self.chunk_size)
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
			"Task %s started for recipient %s with %s chunks and %s/%s workers",
			task.task_id,
			recipient_id,
			len(chunks),
			effective_workers,
			self.workers_count,
		)

		workers = [EncryptionWorker.remote(worker_id=index) for index in range(effective_workers)]
		pending: Dict[ray.ObjectRef, EncryptionChunk] = {}

		for index, chunk in enumerate(chunks):
			worker = workers[index % len(workers)]
			pending[worker.encrypt_chunk.remote(chunk, public_key)] = chunk

		chunk_results: list[EncryptionChunkResult] = []
		start_time = perf_counter()

		try:
			while pending:
				done_refs, _ = ray.wait(list(pending.keys()), num_returns=1, timeout=None)

				for ref in done_refs:
					chunk = pending.pop(ref, None)
					if chunk is None:
						continue

					try:
						result: EncryptionChunkResult = ray.get(ref)
					except Exception as exc:  # pragma: no cover - Ray transport
						self.log.exception("Chunk %s failed: %s", chunk.chunk_id, exc)
						result = EncryptionChunkResult(
							chunk_id=chunk.chunk_id,
							start=chunk.start,
							end=chunk.end,
							ciphertext_numbers=[],
							byte_length=len(chunk.payload),
							elapsed_seconds=0.0,
							worker_id=-1,
							status=EncryptionChunkStatus.FAILED,
							error=str(exc),
						)

					chunk_results.append(result)
		finally:
			elapsed = perf_counter() - start_time

		chunk_results.sort(key=lambda item: item.chunk_id)
		ciphertext_numbers = [value for result in chunk_results for value in result.ciphertext_numbers]
		status = (
			EncryptionStatus.COMPLETED
			if all(result.status is EncryptionChunkStatus.COMPLETED for result in chunk_results)
			else EncryptionStatus.FAILED
		)
		message = None if status is EncryptionStatus.COMPLETED else "At least one chunk failed"

		result = EncryptionResult(
			task_id=task.task_id,
			status=status,
			recipient_id=recipient_id,
			public_key_id=public_key.key_id,
			workers_count=effective_workers,
			chunk_size=self.chunk_size,
			plaintext_length=len(plaintext_bytes),
			elapsed_seconds=elapsed,
			chunks=chunk_results,
			ciphertext_numbers=ciphertext_numbers,
			message=message,
		)

		self.log.info(
			"Task %s completed for recipient %s in %.3fs",
			task.task_id,
			recipient_id,
			elapsed,
		)
		return result
