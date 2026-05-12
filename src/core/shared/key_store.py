from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

from core.shared.models import RsaPrivateKey, RsaPublicKey


@dataclass(frozen=True)
class _KeyPair:
	public_key: RsaPublicKey
	private_key: RsaPrivateKey


def _build_keypair(owner_id: str, key_suffix: str, prime_p: int, prime_q: int, exponent: int) -> _KeyPair:
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
	"""Small in-memory RSA key store split into public and private collections."""

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
		return sorted(self._public_keys.keys())

	def list_private_owners(self) -> list[str]:
		return sorted(self._private_keys.keys())

	def get_public_key(self, recipient_id: str) -> RsaPublicKey:
		try:
			return self._public_keys[recipient_id]
		except KeyError as exc:
			raise KeyError(f"Unknown recipient_id: {recipient_id}") from exc

	def get_private_key(self, owner_id: str) -> RsaPrivateKey:
		try:
			return self._private_keys[owner_id]
		except KeyError as exc:
			raise KeyError(f"Unknown owner_id: {owner_id}") from exc

	def iter_public_keys(self) -> Iterable[RsaPublicKey]:
		return self._public_keys.values()

	def iter_private_keys(self) -> Iterable[RsaPrivateKey]:
		return self._private_keys.values()
