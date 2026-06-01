# monitoring

Monitoring stack configuration for the project.

## What is here

- `prometheus.yml`: scrape configuration (Prometheus targets and intervals).
- `grafana/`: Grafana provisioning files (dashboards and datasources).

## How it works

- The exporter service in `src/monitor/exporter.py` exposes Prometheus metrics at `/metrics`.
- Prometheus scrapes the exporter and stores time-series data.
- Grafana reads Prometheus as a datasource and displays the pre-provisioned dashboard.

## Goal

Provide fast feedback about agent pool behavior:

- pool size,
- active/busy agents,
- total processed jobs,
- per-agent utilization and throughput indicators.
