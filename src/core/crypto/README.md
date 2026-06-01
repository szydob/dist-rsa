# crypto

Distributed RSA encryption and decryption pipeline.

## Files

- `encryption_chunking.py`: splits plaintext bytes into fixed-size chunks.
- `encryption_worker.py`: Ray worker logic for encrypting one chunk.
- `encryption_coordinator.py`: orchestrates encryption jobs, worker fan-out, and result merge.
- `decryption_chunking.py`: splits ciphertext numbers into chunks.
- `decryption_worker.py`: Ray worker logic for decrypting one chunk.
- `decryption_coordinator.py`: orchestrates decryption jobs and output reconstruction.

## Execution flow

1. Validate input and load RSA key material from shared key store.
2. Split input into ordered chunks.
3. Spawn a bounded number of Ray workers.
4. Distribute chunk tasks across workers.
5. Collect chunk results as they finish.
6. Sort by chunk id and merge in original order.

This preserves output correctness even when worker completion order is different.
