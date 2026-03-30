from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import ray


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

existing_pythonpath = os.environ.get("PYTHONPATH", "")
paths = [p for p in existing_pythonpath.split(os.pathsep) if p]
if str(SRC) not in paths:
    paths.insert(0, str(SRC))
    os.environ["PYTHONPATH"] = os.pathsep.join(paths)


@pytest.fixture(scope="function")
def ray_session():
    """Start a fresh local Ray session for each test using Ray."""
    if ray.is_initialized():
        ray.shutdown()
    ray.init(ignore_reinit_error=True, num_cpus=2, include_dashboard=False)
    try:
        yield
    finally:
        ray.shutdown()
