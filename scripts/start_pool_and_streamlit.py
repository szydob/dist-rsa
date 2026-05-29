#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import time
import traceback

import ray

from core.agent_pool.pool import AgentPool


def _start_ray_head() -> subprocess.Popen[str]:
    env = os.environ.copy()
    env.setdefault("RAY_DISABLE_USAGE_STATS", "1")
    env.setdefault("RAY_ADDRESS", "auto")

    print("Starting Ray head for container...")
    return subprocess.Popen(
        [
            "ray",
            "start",
            "--head",
            "--port=6379",
            "--dashboard-host=0.0.0.0",
            "--include-dashboard=false",
        ],
        env=env,
    )


def main() -> None:
    os.environ.setdefault("RAY_ADDRESS", "auto")
    ray_head = _start_ray_head()

    try:
        for _ in range(30):
            try:
                if not ray.is_initialized():
                    ray.init(
                        address="auto",
                        include_dashboard=False,
                        namespace="dist-rsa",
                        log_to_driver=False,
                    )
                break
            except Exception:
                time.sleep(1)

        print("Starting AgentPool at container startup...")
        try:
            pool = AgentPool()
            summary = pool.get_pool_summary()
            print("AgentPool initialized:", summary)
        except Exception:
            print("AgentPool initialization failed:")
            traceback.print_exc()

        # Give a moment for ray processes to settle.
        time.sleep(1)
        # Start exporter for Prometheus scraping
        print("Starting metrics exporter on :9000...")
        exporter_proc = subprocess.Popen([
            "python",
            "-u",
            "-m",
            "uvicorn",
            "src.monitor.exporter:app",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
        ], env=os.environ.copy())

        print("Launching Streamlit...")
        os.execvp(
            "streamlit",
            [
                "streamlit",
                "run",
                "src/gui.py",
                "--server.address=0.0.0.0",
                "--server.port=8501",
            ],
        )
    finally:
        try:
            if ray.is_initialized():
                ray.shutdown()
        except Exception:
            pass

        try:
            ray_head.terminate()
            ray_head.wait(timeout=10)
        except Exception:
            pass
        try:
            exporter_proc.terminate()
            exporter_proc.wait(timeout=5)
        except Exception:
            pass


if __name__ == "__main__":
    main()
