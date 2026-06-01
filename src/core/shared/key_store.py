from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

from core.shared.models import RsaPrivateKey, RsaPublicKey


@dataclass(frozen=True)
class _KeyPair:
	"""In-memory RSA key pair used to seed the demo key store."""

	public_key: RsaPublicKey
	private_key: RsaPrivateKey


def _build_keypair(owner_id: str, key_suffix: str, prime_p: int, prime_q: int, exponent: int) -> _KeyPair:
	"""Build a matching RSA public/private key pair from demo primes.

	Args:
		owner_id: Logical owner for the key pair.
		key_suffix: Suffix used to make the key identifiers unique.
		prime_p: First RSA prime.
		prime_q: Second RSA prime.
		exponent: Public exponent.

	Returns:
		The generated RSA key pair.
	"""
	modulus = prime_p * prime_q
	phi = (prime_p - 1) * (prime_q - 1)
	private_exponent = pow(exponent, -1, phi)

	public_key = RsaPublicKey(
		key_id=f"{owner_id}-public-{key_suffix}",
		owner_id=owner_id,
		n=modulus,
		e=exponent,
	)
	private_key = RsaPrivateKey(
		key_id=f"{owner_id}-private-{key_suffix}",
		owner_id=owner_id,
		n=modulus,
		d=private_exponent,
	)
	return _KeyPair(public_key=public_key, private_key=private_key)


class InMemoryRsaKeyStore:
	"""Small in-memory RSA key store split into public and private collections.

	The store ships with two deterministic demo identities so the GUI can
	immediately demonstrate encryption and decryption without external setup.
	"""

	def __init__(self) -> None:
		alice = _build_keypair("alice", "v1", 61, 53, 65_537)
		bob = _build_keypair("bob", "v1", 71, 79, 65_537)

		self._public_keys: Dict[str, RsaPublicKey] = {
			alice.public_key.owner_id: alice.public_key,
			bob.public_key.owner_id: bob.public_key,
		}
		self._private_keys: Dict[str, RsaPrivateKey] = {
			alice.private_key.owner_id: alice.private_key,
			bob.private_key.owner_id: bob.private_key,
		}

	def list_public_recipients(self) -> list[str]:
		"""Return recipient IDs that have public keys available."""
		return sorted(self._public_keys.keys())

	def list_private_owners(self) -> list[str]:
		"""Return owner IDs that have private keys available."""
		return sorted(self._private_keys.keys())

	def get_public_key(self, recipient_id: str) -> RsaPublicKey:
		"""Return the public key for a recipient.

		Raises:
			KeyError: If the recipient is unknown.
		"""
		try:
			return self._public_keys[recipient_id]
		except KeyError as exc:
			raise KeyError(f"Unknown recipient_id: {recipient_id}") from exc

	def get_private_key(self, owner_id: str) -> RsaPrivateKey:
		"""Return the private key for an owner.

		Raises:
			KeyError: If the owner is unknown.
		"""
		try:
			return self._private_keys[owner_id]
		except KeyError as exc:
			raise KeyError(f"Unknown owner_id: {owner_id}") from exc

	def iter_public_keys(self) -> Iterable[RsaPublicKey]:
		"""Iterate over all public keys in the store."""
		return self._public_keys.values()

	def iter_private_keys(self) -> Iterable[RsaPrivateKey]:
		"""Iterate over all private keys in the store."""
		return self._private_keys.values()
