# scripts

Utility scripts used to bootstrap and run the full local stack.

## Main script

- `start_pool_and_streamlit.py`

## Runtime flow

1. Starts a Ray head node inside the container.
2. Connects to Ray and initializes the persistent AgentPool.
3. Starts the metrics exporter (FastAPI + Prometheus endpoint) on port 9000.
4. Launches Streamlit UI on port 8501.

## Why this script exists

The script ensures Ray, the agent pool, exporter, and UI are started in a predictable order, which makes the Agent Pool mode immediately available after startup.
