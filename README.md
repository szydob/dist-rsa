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
- `src/dist_rsa/gui.py` — Streamlit interface

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