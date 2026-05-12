from __future__ import annotations

from typing import List

from core.shared.models import DecryptionChunk


def build_decryption_chunks(ciphertext_numbers: list[int], chunk_size: int) -> List[DecryptionChunk]:
	if chunk_size <= 0:
		raise ValueError("chunk_size must be positive")

	if not ciphertext_numbers:
		return []

	chunks: List[DecryptionChunk] = []
	chunk_id = 0
	for start in range(0, len(ciphertext_numbers), chunk_size):
		end = min(start + chunk_size, len(ciphertext_numbers))
		chunks.append(
			DecryptionChunk(
				chunk_id=chunk_id,
				start=start,
				end=end,
				payload=ciphertext_numbers[start:end],
			)
		)
		chunk_id += 1

	return chunks
