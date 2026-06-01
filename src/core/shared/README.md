# shared

Shared models and reusable utilities for all modules.

## Files

- `models.py`: typed dataclasses and status enums for tasks, chunks, and results.
- `key_store.py`: in-memory RSA key store used by encryption/decryption services.
- `rsa_math.py`: RSA-related math helpers.

## Why this module exists

All layers (core, services, UI, and monitoring) use common structures from this folder. Centralizing models keeps interfaces consistent across encryption, decryption, factorization, and attack workflows.
