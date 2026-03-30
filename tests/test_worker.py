from __future__ import annotations

import ray

from dist_rsa.core.models import Chunk, ChunkStatus
from dist_rsa.core.worker import factor_chunk


def test_worker_finds_divisor(ray_session):
    chunk = Chunk(chunk_id=1, start=2, end=5)
    result = ray.get(factor_chunk.remote(21, chunk))
    assert result.divisor == 3
    assert result.status is ChunkStatus.FOUND
    assert result.checked == 2  # 2 then 3


def test_worker_handles_no_divisor(ray_session):
    chunk = Chunk(chunk_id=2, start=2, end=4)
    result = ray.get(factor_chunk.remote(17, chunk))
    assert result.divisor is None
    assert result.status is ChunkStatus.COMPLETED
    assert result.checked == 3
