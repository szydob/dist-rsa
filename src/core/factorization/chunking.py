from __future__ import annotations

import math
from typing import Iterable, List

from core.shared.models import Chunk


def calculate_search_limit(n: int) -> int:
	"""Return upper bound for divisor search (inclusive)."""
	if n <= 1:
		raise ValueError("n must be greater than 1")
	return math.isqrt(n)


def build_chunks(n: int, chunk_size: int) -> List[Chunk]:
	"""Split the divisor search space into fixed-size chunks."""
	if chunk_size <= 0:
		raise ValueError("chunk_size must be positive")

	limit = calculate_search_limit(n)
	chunks: List[Chunk] = []
	start = 2
	chunk_id = 0

	while start <= limit:
		end = min(start + chunk_size - 1, limit)
		chunks.append(Chunk(chunk_id=chunk_id, start=start, end=end))
		start = end + 1
		chunk_id += 1

	return chunks


def iter_chunks(n: int, chunk_size: int) -> Iterable[Chunk]:
	"""Generator form of build_chunks for streaming scenarios."""
	if chunk_size <= 0:
		raise ValueError("chunk_size must be positive")

	limit = calculate_search_limit(n)
	start = 2
	chunk_id = 0

	while start <= limit:
		end = min(start + chunk_size - 1, limit)
		yield Chunk(chunk_id=chunk_id, start=start, end=end)
		start = end + 1
		chunk_id += 1
