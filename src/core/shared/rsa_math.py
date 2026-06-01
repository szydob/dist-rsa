"""RSA helper functions shared by encryption workers and coordinators."""

from __future__ import annotations

from core.shared.models import RsaPublicKey


def encrypt_byte(value: int, public_key: RsaPublicKey) -> int:
	"""Encrypt a single byte value with RSA.

	Args:
		value: Plaintext byte value.
		public_key: RSA public key to use for encryption.

	Returns:
		The encrypted integer representation of the byte.

	Raises:
		ValueError: If the value cannot be represented by the modulus.
	"""
	if value < 0 or value >= public_key.n:
		raise ValueError("Plaintext byte is out of range for the RSA modulus")
	return pow(value, public_key.e, public_key.n)


def encrypt_bytes(payload: bytes, public_key: RsaPublicKey) -> list[int]:
	"""Encrypt a byte string as a list of RSA integers.

	Args:
		payload: Plaintext bytes to encrypt.
		public_key: RSA public key to use for encryption.

	Returns:
		Encrypted integers in the same order as the input bytes.

	Raises:
		ValueError: If the modulus is too small for the byte-wise demo format.
	"""
	if public_key.n <= 255:
		raise ValueError("RSA modulus must be greater than 255 for byte-wise demo encryption")
	return [encrypt_byte(byte_value, public_key) for byte_value in payload]
