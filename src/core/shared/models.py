"""Shared dataclasses and status enums used across the application."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


class FactorizationStatus(str, Enum):
	"""Lifecycle states for factorization tasks."""

	PENDING = "pending"
	RUNNING = "running"
	FOUND = "found"
	NOT_FOUND = "not_found"
	FAILED = "failed"
	CANCELLED = "cancelled"


class ChunkStatus(str, Enum):
	"""Lifecycle states for factorization chunks."""

	PENDING = "pending"
	RUNNING = "running"
	COMPLETED = "completed"
	FOUND = "found"
	FAILED = "failed"


@dataclass
class FactorizationTask:
	"""Metadata for a factorization job."""

	n: int
	chunk_size: int
	search_limit: int
	task_id: str = field(default_factory=lambda: str(uuid4()))
	created_at: datetime = field(default_factory=datetime.utcnow)
	status: FactorizationStatus = FactorizationStatus.PENDING


@dataclass
class Chunk:
	"""Search interval assigned to a worker or actor."""

	chunk_id: int
	start: int
	end: int
	status: ChunkStatus = ChunkStatus.PENDING


@dataclass
class ChunkResult:
	"""Result of evaluating a factorization chunk."""

	chunk_id: int
	start: int
	end: int
	divisor: Optional[int]
	elapsed_seconds: float
	checked: int
	status: ChunkStatus
	error: Optional[str] = None


@dataclass
class FactorizationResult:
	"""Summary returned after a factorization run completes."""

	task_id: str
	status: FactorizationStatus
	p: Optional[int]
	q: Optional[int]
	elapsed_seconds: float
	checked_chunks: int
	checked_candidates: int
	peak_pool_utilization_percent: Optional[float] = None
	message: Optional[str] = None


class EncryptionStatus(str, Enum):
	"""Lifecycle states for encryption tasks."""

	PENDING = "pending"
	RUNNING = "running"
	COMPLETED = "completed"
	FAILED = "failed"


class EncryptionChunkStatus(str, Enum):
	"""Lifecycle states for encryption chunks."""

	PENDING = "pending"
	RUNNING = "running"
	COMPLETED = "completed"
	FAILED = "failed"


@dataclass(frozen=True)
class RsaPublicKey:
	"""RSA public key descriptor used for encryption."""

	key_id: str
	owner_id: str
	n: int
	e: int


@dataclass(frozen=True)
class RsaPrivateKey:
	"""RSA private key descriptor used for decryption."""

	key_id: str
	owner_id: str
	n: int
	d: int


@dataclass
class EncryptionTask:
	"""Metadata for a distributed encryption job."""

	recipient_id: str
	chunk_size: int
	workers_count: int
	plaintext_length: int
	task_id: str = field(default_factory=lambda: str(uuid4()))
	created_at: datetime = field(default_factory=datetime.utcnow)
	status: EncryptionStatus = EncryptionStatus.PENDING


@dataclass
class EncryptionChunk:
	"""A byte range prepared for RSA encryption."""

	chunk_id: int
	start: int
	end: int
	payload: bytes
	status: EncryptionChunkStatus = EncryptionChunkStatus.PENDING


@dataclass
class EncryptionChunkResult:
	"""Result of encrypting one plaintext chunk."""

	chunk_id: int
	start: int
	end: int
	ciphertext_numbers: list[int]
	byte_length: int
	elapsed_seconds: float
	worker_id: int
	status: EncryptionChunkStatus
	error: Optional[str] = None


@dataclass
class EncryptionResult:
	"""Summary returned after distributed encryption finishes."""

	task_id: str
	status: EncryptionStatus
	recipient_id: str
	public_key_id: str
	workers_count: int
	chunk_size: int
	plaintext_length: int
	elapsed_seconds: float
	chunks: list[EncryptionChunkResult]
	ciphertext_numbers: list[int]
	message: Optional[str] = None


class DecryptionStatus(str, Enum):
	"""Lifecycle states for decryption tasks."""

	PENDING = "pending"
	RUNNING = "running"
	COMPLETED = "completed"
	FAILED = "failed"


class DecryptionChunkStatus(str, Enum):
	"""Lifecycle states for decryption chunks."""

	PENDING = "pending"
	RUNNING = "running"
	COMPLETED = "completed"
	FAILED = "failed"


@dataclass
class DecryptionTask:
	"""Metadata for a distributed decryption job."""

	owner_id: str
	chunk_size: int
	workers_count: int
	ciphertext_length: int
	task_id: str = field(default_factory=lambda: str(uuid4()))
	created_at: datetime = field(default_factory=datetime.utcnow)
	status: DecryptionStatus = DecryptionStatus.PENDING


@dataclass
class DecryptionChunk:
	"""A ciphertext slice prepared for RSA decryption."""

	chunk_id: int
	start: int
	end: int
	payload: list[int]
	status: DecryptionChunkStatus = DecryptionChunkStatus.PENDING


@dataclass
class DecryptionChunkResult:
	"""Result of decrypting one ciphertext chunk."""

	chunk_id: int
	start: int
	end: int
	plaintext_bytes: bytes
	byte_length: int
	elapsed_seconds: float
	worker_id: int
	status: DecryptionChunkStatus
	error: Optional[str] = None


@dataclass
class DecryptionResult:
	"""Summary returned after distributed decryption finishes."""

	task_id: str
	status: DecryptionStatus
	owner_id: str
	private_key_id: str
	workers_count: int
	chunk_size: int
	ciphertext_length: int
	elapsed_seconds: float
	chunks: list[DecryptionChunkResult]
	plaintext: str
	message: Optional[str] = None


class AttackStatus(str, Enum):
	"""Lifecycle states for RSA attack runs."""

	PENDING = "pending"
	RUNNING = "running"
	COMPLETED = "completed"
	FAILED = "failed"


@dataclass
class AttackResult:
	"""Summary returned after an RSA attack run finishes."""

	task_id: str
	status: AttackStatus
	n: int
	e: int
	p: Optional[int]
	q: Optional[int]
	phi: Optional[int]
	d: Optional[int]
	factorization_elapsed_seconds: float
	total_elapsed_seconds: float
	message: Optional[str] = None
