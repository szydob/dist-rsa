from __future__ import annotations

from core.shared.models import RsaPublicKey


def encrypt_byte(value: int, public_key: RsaPublicKey) -> int:
	if value < 0 or value >= public_key.n:
		raise ValueError("Plaintext byte is out of range for the RSA modulus")
	return pow(value, public_key.e, public_key.n)


def encrypt_bytes(payload: bytes, public_key: RsaPublicKey) -> list[int]:
	if public_key.n <= 255:
		raise ValueError("RSA modulus must be greater than 255 for byte-wise demo encryption")
	return [encrypt_byte(byte_value, public_key) for byte_value in payload]
