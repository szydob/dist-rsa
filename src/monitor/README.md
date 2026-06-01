# monitor

Monitoring endpoints for Prometheus and event inspection.

## Main file

- `exporter.py`: FastAPI app exposing:
  - `/metrics`: Prometheus metrics for pool and per-agent status,
  - `/events`: recent JSONL event log entries.

## Metric source

Exporter reads runtime statistics from `AgentPoolService` and publishes Gauges such as pool size, busy agents, completed jobs, and per-agent utilization.
