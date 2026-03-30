from __future__ import annotations

from datetime import datetime
from time import perf_counter
from typing import Dict, List, Optional
from uuid import uuid4

import ray

from dist_rsa.core.chunking import build_chunks, calculate_search_limit
from dist_rsa.core.models import (
    Chunk,
    ChunkResult,
    ChunkStatus,
    FactorizationResult,
    FactorizationStatus,
    FactorizationTask,
)
from dist_rsa.core.worker import factor_chunk
from dist_rsa.utils.logger import get_logger


class FactorizationCoordinator:
    """Coordinates distributed factorization tasks on Ray."""

    def __init__(
        self,
        chunk_size: int = 10_000,
        ray_address: Optional[str] = None,
        log_level: str = "INFO",
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        self.chunk_size = chunk_size
        self.ray_address = ray_address
        self.log = get_logger(self.__class__.__name__, level=log_level)

    def _ensure_ray(self) -> None:
        if not ray.is_initialized():
            ray.init(
                address=self.ray_address or "local",
                include_dashboard=False,
                ignore_reinit_error=True,
                namespace="dist-rsa",
                log_to_driver=False,
            )

    def factor(self, n: int) -> FactorizationResult:
        if n <= 3:
            raise ValueError("n must be greater than 3")

        self._ensure_ray()
        task = self._build_task(n)
        chunks = build_chunks(n, self.chunk_size)

        self.log.info("Task %s started with %s chunks", task.task_id, len(chunks))

        pending: Dict[ray.ObjectRef, Chunk] = {
            factor_chunk.remote(n, chunk): chunk for chunk in chunks
        }
        results: List[ChunkResult] = []

        p: Optional[int] = None
        q: Optional[int] = None
        checked_candidates = 0

        start_time = perf_counter()

        try:
            while pending:
                done_refs, running_refs = ray.wait(
                    list(pending.keys()), num_returns=1, timeout=None
                )

                for ref in done_refs:
                    chunk = pending.pop(ref, None)
                    if chunk is None:
                        continue

                    try:
                        result: ChunkResult = ray.get(ref)
                    except Exception as exc:  # pragma: no cover - Ray transport
                        self.log.exception("Chunk %s failed: %s", chunk.chunk_id, exc)
                        result = ChunkResult(
                            chunk_id=chunk.chunk_id,
                            start=chunk.start,
                            end=chunk.end,
                            divisor=None,
                            elapsed_seconds=0.0,
                            checked=0,
                            status=ChunkStatus.FAILED,
                            error=str(exc),
                        )

                    results.append(result)
                    checked_candidates += result.checked

                    if result.divisor is not None:
                        p = result.divisor
                        q = n // p
                        self.log.info(
                            "Factor found in chunk %s: p=%s, q=%s", chunk.chunk_id, p, q
                        )
                        for leftover in running_refs:
                            ray.cancel(leftover, force=True)
                        pending.clear()
                        break

                if p is None:
                    pending = {ref: pending[ref] for ref in running_refs if ref in pending}

        finally:
            elapsed = perf_counter() - start_time

        status = FactorizationStatus.FOUND if p is not None else FactorizationStatus.NOT_FOUND
        message = None
        if status is FactorizationStatus.NOT_FOUND:
            message = "No divisor found in search space"

        result_summary = FactorizationResult(
            task_id=task.task_id,
            status=status,
            p=p,
            q=q,
            elapsed_seconds=elapsed,
            checked_chunks=len(results),
            checked_candidates=checked_candidates,
            message=message,
        )

        if status is FactorizationStatus.FOUND:
            self.log.info(
                "Task %s completed: p=%s, q=%s, elapsed=%.3fs",
                task.task_id,
                p,
                q,
                elapsed,
            )
        else:
            self.log.info(
                "Task %s completed without factor, checked %s candidates in %.3fs",
                task.task_id,
                checked_candidates,
                elapsed,
            )

        return result_summary

    def _build_task(self, n: int) -> FactorizationTask:
        return FactorizationTask(
            n=n,
            chunk_size=self.chunk_size,
            search_limit=calculate_search_limit(n),
            task_id=str(uuid4()),
            created_at=datetime.utcnow(),
            status=FactorizationStatus.RUNNING,
        )
