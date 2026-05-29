# Distributed RSA

Distributed Systems 2026 project: Distributed RSA encoding/decoding with Ray

Current scope:
- package management with `uv`,
- containerized development with Docker,
- simple Streamlit GUI.


## Project structure

- `pyproject.toml` — Python dependencies (`uv`)
- `Dockerfile` — container image definition
- `docker-compose.yml` — local dev orchestration
- `src/gui.py` — Streamlit interface

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
