# core

Core domain logic for Distributed RSA.

## Modules

- `agent_pool/`: persistent Ray actor pool for long-running factorization workloads.
- `crypto/`: distributed RSA encryption/decryption coordinators, chunking, and workers.
- `factorization/`: distributed factorization coordinators, chunking, and workers.
- `shared/`: common data models, RSA math helpers, and key store.

## Design intent

`core` contains framework-independent logic. UI and service layers call into this package, but business logic and distributed execution are implemented here.
