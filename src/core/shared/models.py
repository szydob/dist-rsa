from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


class FactorizationStatus(str, Enum):
	PENDING = "pending"
	RUNNING = "running"
	FOUND = "found"
	NOT_FOUND = "not_found"
	FAILED = "failed"
	CANCELLED = "cancelled"


class ChunkStatus(str, Enum):
	PENDING = "pending"
	RUNNING = "running"
	COMPLETED = "completed"
	FOUND = "found"
	FAILED = "failed"


@dataclass
class FactorizationTask:
	n: int
	chunk_size: int
	search_limit: int
	task_id: str = field(default_factory=lambda: str(uuid4()))
	created_at: datetime = field(default_factory=datetime.utcnow)
	status: FactorizationStatus = FactorizationStatus.PENDING


@dataclass
class Chunk:
	chunk_id: int
	start: int
	end: int
	status: ChunkStatus = ChunkStatus.PENDING


@dataclass
class ChunkResult:
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
	PENDING = "pending"
	RUNNING = "running"
	COMPLETED = "completed"
	FAILED = "failed"


class EncryptionChunkStatus(str, Enum):
	PENDING = "pending"
	RUNNING = "running"
	COMPLETED = "completed"
	FAILED = "failed"


@dataclass(frozen=True)
class RsaPublicKey:
	key_id: str
	owner_id: str
	n: int
	e: int


@dataclass(frozen=True)
class RsaPrivateKey:
	key_id: str
	owner_id: str
	n: int
	d: int


@dataclass
class EncryptionTask:
	recipient_id: str
	chunk_size: int
	workers_count: int
	plaintext_length: int
	task_id: str = field(default_factory=lambda: str(uuid4()))
	created_at: datetime = field(default_factory=datetime.utcnow)
	status: EncryptionStatus = EncryptionStatus.PENDING


@dataclass
class EncryptionChunk:
	chunk_id: int
	start: int
	end: int
	payload: bytes
	status: EncryptionChunkStatus = EncryptionChunkStatus.PENDING


@dataclass
class EncryptionChunkResult:
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
	PENDING = "pending"
	RUNNING = "running"
	COMPLETED = "completed"
	FAILED = "failed"


class DecryptionChunkStatus(str, Enum):
	PENDING = "pending"
	RUNNING = "running"
	COMPLETED = "completed"
	FAILED = "failed"


@dataclass
class DecryptionTask:
	owner_id: str
	chunk_size: int
	workers_count: int
	ciphertext_length: int
	task_id: str = field(default_factory=lambda: str(uuid4()))
	created_at: datetime = field(default_factory=datetime.utcnow)
	status: DecryptionStatus = DecryptionStatus.PENDING


@dataclass
class DecryptionChunk:
	chunk_id: int
	start: int
	end: int
	payload: list[int]
	status: DecryptionChunkStatus = DecryptionChunkStatus.PENDING


@dataclass
class DecryptionChunkResult:
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
	PENDING = "pending"
	RUNNING = "running"
	COMPLETED = "completed"
	FAILED = "failed"


@dataclass
class AttackResult:
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
