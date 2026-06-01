from __future__ import annotations

from time import perf_counter
from typing import Optional

import ray

from core.shared.models import Chunk, ChunkResult, ChunkStatus


@ray.remote
def factor_chunk(n: int, chunk: Chunk) -> ChunkResult:
	"""Search for a divisor of n within one chunk.

	Args:
		n: Integer to factor.
		chunk: Search interval to evaluate.

	Returns:
		Chunk result with divisor information and runtime metadata.
	"""
	start_time = perf_counter()
	divisor: Optional[int] = None
	checked = 0

	for candidate in range(chunk.start, chunk.end + 1):
		checked += 1
		if n % candidate == 0:
			divisor = candidate
			break

	elapsed = perf_counter() - start_time
	status = ChunkStatus.FOUND if divisor is not None else ChunkStatus.COMPLETED

	return ChunkResult(
		chunk_id=chunk.chunk_id,
		start=chunk.start,
		end=chunk.end,
		divisor=divisor,
		elapsed_seconds=elapsed,
		checked=checked,
		status=status,
	)
