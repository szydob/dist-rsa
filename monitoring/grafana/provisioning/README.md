# provisioning

Grafana provisioning files used during container startup.

## Subfolders

- `dashboards/`: dashboard provider setup and dashboard JSON files.
- `datasources/`: datasource definitions (Prometheus in this project).

## Behavior

Grafana reads these files on startup and configures itself automatically.
