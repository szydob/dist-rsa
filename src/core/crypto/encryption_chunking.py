from __future__ import annotations

from typing import List

from core.shared.models import EncryptionChunk


def build_encryption_chunks(payload: bytes, chunk_size: int) -> List[EncryptionChunk]:
	"""Split bytes payload into ordered chunks for Ray workers."""
	if chunk_size <= 0:
		raise ValueError("chunk_size must be positive")

	if not payload:
		return []

	chunks: List[EncryptionChunk] = []
	chunk_id = 0
	for start in range(0, len(payload), chunk_size):
		end = min(start + chunk_size, len(payload))
		chunks.append(
			EncryptionChunk(
				chunk_id=chunk_id,
				start=start,
				end=end,
				payload=payload[start:end],
			)
		)
		chunk_id += 1

	return chunks
