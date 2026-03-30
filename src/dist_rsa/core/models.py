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
    message: Optional[str] = None
