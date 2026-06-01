# factorization

Distributed integer factorization logic used by both direct factorization and RSA attack flows.

## Files

- `chunking.py`: builds divisor-search chunks from 2 to floor(sqrt(n)).
- `worker.py`: Ray remote function that checks one chunk for divisors.
- `coordinator.py`: schedules chunk tasks, aggregates results, and stops early when a factor is found.

## Algorithm outline

- Build fixed-size chunk ranges covering the divisor search space.
- Run chunk checks in parallel on Ray workers.
- Track checked candidates and completed chunks.
- On first found divisor p, compute q = n / p and cancel pending work best-effort.

## Scheduling behavior

Chunk ranges are generated in ascending order and processed through a queue; workers receive new chunks as slots become free.
