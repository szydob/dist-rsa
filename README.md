# Distributed RSA

Distributed Systems 2026 project: Distributed RSA encoding/decoding with Ray

Current scope:
- package management with `uv`,
- containerized development with Docker,
- simple Streamlit GUI.

The application demonstrates distributed RSA-related workloads on Ray:

- text encryption,
- text decryption,
- integer factorization,
- RSA attack simulation,
- persistent heterogeneous agent-pool factorization.


## Project structure

- `pyproject.toml` — Python dependencies (`uv`)
- `Dockerfile` — container image definition
- `docker-compose.yml` — local dev orchestration
- `src/gui.py` — Streamlit interface

Each major subfolder now contains its own `README.md` with module-level details.

## How The Application Works

At startup, the stack runs:

1. Ray runtime (distributed execution backend).
2. Persistent agent pool (for Agent Pool mode).
3. Metrics exporter (FastAPI + Prometheus endpoint).
4. Streamlit GUI.

The GUI calls service classes from `src/services`, which delegate to coordinators in `src/core`.
Coordinators split inputs into chunks, dispatch chunk tasks to Ray workers/actors, and merge results.

## UI Modes

The Streamlit app provides 5 modes (tabs):

1. **Encrypt text**
	- Splits plaintext bytes into chunks.
	- Encrypts chunks in parallel with RSA public key.
	- Reorders chunk results by `chunk_id` to preserve original text order.

2. **Decrypt text**
	- Splits ciphertext integer list into chunks.
	- Decrypts chunks in parallel with RSA private key.
	- Reassembles plaintext in original chunk order.

3. **Factorization**
	- Searches divisors of `n` in range `[2, floor(sqrt(n))]`.
	- Uses distributed chunk checks on Ray workers.
	- Stops early when a factor is found.

4. **RSA attack**
	- Runs factorization for RSA modulus `n`.
	- Computes `phi = (p - 1) * (q - 1)`.
	- Recovers private exponent `d = e^-1 mod phi`.

5. **Agent Pool Attack**
	- Runs factorization on a persistent pool of Ray actors.
	- Designed for long-running/background tasks and observability.
	- Integrates with Prometheus/Grafana and JSONL event logs.

## Chunking And Scheduling

### Factorization chunk creation

- Search limit is `floor(sqrt(n))`.
- Chunks are fixed-size contiguous ranges.
- Example for `chunk_size = 1000`: `[2..1001]`, `[1002..2001]`, etc.
- Chunks are generated in ascending order.

### Standard factorization scheduling

- Chunks are consumed from a FIFO queue.
- Up to `effective_workers` chunks run concurrently.
- When one chunk finishes, next waiting chunk is assigned.
- If divisor is found, coordinator stops submitting further work.

### Agent Pool scheduling (important)

Agent Pool mode is **not random**.

- The pool is heterogeneous:
  - normal agents,
  - fast agents,
  - slow agents.
- Chunk queue is still FIFO (next chunk in ascending range order).
- Agent assignment uses a weighted cyclic strategy:
  - fast agents appear more often in the assignment cycle,
  - normal agents with medium frequency,
  - slow agents least often.
- For very small workloads (or the very last chunks), scheduler can switch to a prioritized list where fast agents are selected first.

In short: **chunk order is sequential; agent choice is deterministic weighted scheduling, not per-agent randomness**.

## Monitoring And Observability

Monitoring is built-in for Agent Pool mode:

- Prometheus metrics from exporter (`/metrics`).
- Grafana dashboard (`agent-pool`) provisioned from files.
- Event timeline in `logs/agent_pool_events.jsonl`.

Useful metrics include:

- pool size,
- busy agents,
- total completed jobs,
- per-agent utilization,
- per-agent completed jobs.

## Prerequisites

- Docker Desktop (or Docker Engine)

## Quick Start

Build container

```bash
docker compose up --build
```

Note: only `src` is mounted into the container.

Then open:

`http://localhost:8501`

You should see GUI.

## Stop

```bash
docker compose down
```

## Monitoring (Prometheus + Grafana)

The project includes a Prometheus + Grafana stack for live metrics and dashboards.

- Grafana UI: http://localhost:3000 (default credentials: `admin` / `admin`)
- Prometheus UI: http://localhost:9090
- Streamlit app metrics exporter: http://localhost:9000/metrics

Open Grafana and load the pre-provisioned dashboard named "Agent Pool" (uid: `agent-pool`).

Tips:
- Set Grafana refresh to `auto` to observe short spikes from the agent pool.
- Prometheus scrape interval is configured short (250ms) to catch brief utilization spikes.
- If a new "Start Pool Attack (background)" run leaves old values visible, restart the app service to reset per-run metrics:

```bash
docker compose restart app
```

If you want to inspect raw metric values use Prometheus expression browser at `http://localhost:9090/graph` and query `agent_pool_agent_utilization_percent`.
