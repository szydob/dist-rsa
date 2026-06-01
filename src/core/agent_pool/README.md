# agent_pool

Persistent Ray actor pool for factorization tasks.

## Main components

- `agent.py`: `PoolAgent` actor, efficiency profiles, and per-agent statistics.
- `pool.py`: pool lifecycle and detached actor initialization.
- `pool_coordinator.py`: chunk scheduling and result aggregation for pool-based factorization.
- `event_log.py`: JSONL event logging utilities.

## Agent model

Agents are heterogeneous by efficiency level:

- normal (majority),
- fast,
- slow.

The pool is created once and reused across tasks.

## Chunk scheduling strategy

- Search space chunks are created in ascending order.
- Chunks are consumed from a FIFO queue.
- Agent assignment is weighted by efficiency (fast agents appear more often in the cycle).
- For very small workloads and at the tail end of a task, scheduling can prioritize fast agents.

This is deterministic scheduling, not random chunk selection.

## Observability

Events are appended to JSONL logs and metrics are exported through the monitoring module for Grafana/Prometheus.
