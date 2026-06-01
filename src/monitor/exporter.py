"""Prometheus exporter and event endpoint for agent pool monitoring."""

from __future__ import annotations

import asyncio
import os
from fastapi import FastAPI
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.core import CollectorRegistry
from starlette.responses import Response

from core.agent_pool.event_log import read_events
from services.agent_pool_service import AgentPoolService


app = FastAPI()

# Define Prometheus metrics
REGISTRY = CollectorRegistry()
POOL_SIZE = Gauge("agent_pool_size", "Total agents in pool", registry=REGISTRY)
BUSY_AGENTS = Gauge("agent_pool_busy_agents", "Number of busy agents", registry=REGISTRY)
TOTAL_JOBS = Gauge("agent_pool_total_jobs", "Total jobs completed by pool", registry=REGISTRY)
PEAK_UTIL = Gauge("agent_pool_peak_util_percent", "Peak pool utilization percent", registry=REGISTRY)
AGENT_UTIL = Gauge(
    "agent_pool_agent_utilization_percent",
    "Current utilization percent per agent",
    ["agent_id", "efficiency_level"],
    registry=REGISTRY,
)
AGENT_JOBS = Gauge(
    "agent_pool_agent_total_jobs_completed",
    "Total jobs completed per agent",
    ["agent_id", "efficiency_level"],
    registry=REGISTRY,
)


def collect_metrics(service: AgentPoolService) -> None:
    """Refresh Prometheus gauges from the current agent pool state."""
    try:
        stats = service.get_pool_stats()
    except Exception:
        return

    POOL_SIZE.set(stats.get("pool_size", 0))
    BUSY_AGENTS.set(stats.get("busy_agents", 0))
    TOTAL_JOBS.set(stats.get("total_jobs_completed", 0))
    PEAK_UTIL.set(stats.get("average_utilization_percent", 0.0))

    for agent in stats.get("agent_stats", []):
        labels = {
            "agent_id": str(agent.agent_id),
            "efficiency_level": getattr(agent.efficiency_level, "value", str(agent.efficiency_level)),
        }
        AGENT_UTIL.labels(**labels).set(agent.current_utilization_percent)
        AGENT_JOBS.labels(**labels).set(agent.total_jobs_completed)


@app.get("/metrics")
async def metrics() -> Response:
    """Return the latest Prometheus metrics payload."""
    service = get_service()
    collect_metrics(service)
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


_service_instance: AgentPoolService | None = None


def get_service() -> AgentPoolService:
    """Return the shared AgentPoolService instance used by the exporter."""
    global _service_instance
    if _service_instance is None:
        _service_instance = AgentPoolService()
    return _service_instance


@app.get("/events")
async def events(limit: int = 200):
    """Return the most recent agent-pool events."""
    return read_events(limit=limit)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("EXPORTER_PORT", "9000")))
