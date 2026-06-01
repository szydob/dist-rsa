# src

Application source code for Distributed RSA.

## High-level architecture

- `gui.py`: Streamlit interface and user flows.
- `core/`: domain logic (factorization, crypto operations, shared models, persistent agent pool).
- `services/`: thin orchestration layer used by the UI.
- `monitor/`: Prometheus exporter and event endpoint.
- `utils/`: shared utility helpers.

## Execution model

Most heavy operations are distributed on Ray. Inputs are split into chunks, tasks are scheduled to workers or pool agents, and results are merged in coordinators.
