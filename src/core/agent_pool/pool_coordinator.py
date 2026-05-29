from __future__ import annotations

from collections import deque
from datetime import datetime
from time import perf_counter
from typing import Dict, List, Optional
from uuid import uuid4

import ray

from core.agent_pool.pool import AgentPool
from core.agent_pool.event_log import append_event
from core.factorization.chunking import build_chunks, calculate_search_limit
from core.shared.models import (
	Chunk,
	ChunkResult,
	ChunkStatus,
	FactorizationResult,
	FactorizationStatus,
	FactorizationTask,
)
from utils.logger import get_logger


class AgentPoolFactorizationCoordinator:
	"""Coordinates factorization using persistent agent pool."""

	def __init__(
		self,
		agent_pool: Optional[AgentPool] = None,
		chunk_size: int = 10_000,
		log_level: str = "INFO",
	) -> None:
		if chunk_size <= 0:
			raise ValueError("chunk_size must be positive")

		self.chunk_size = chunk_size
		self.agent_pool = agent_pool or AgentPool()
		self.log = get_logger(self.__class__.__name__, level=log_level)

	def factor(self, n: int) -> FactorizationResult:
		"""Factor n using the persistent agent pool."""
		if n <= 3:
			raise ValueError("n must be greater than 3")

		task = self._build_task(n)
		chunks = build_chunks(n, self.chunk_size)

		self.log.info(
			"Task %s started with %s chunks using agent pool (%s agents)",
			task.task_id,
			len(chunks),
			len(self.agent_pool.get_all_agents()),
		)
		append_event(
			"task_started",
			task_id=task.task_id,
			n=n,
			chunk_size=self.chunk_size,
			chunks=len(chunks),
			agents=len(self.agent_pool.get_all_agents()),
		)

		chunk_queue = deque(chunks)
		# Build weighted agent list based on efficiency so faster agents receive more chunks
		agent_refs = self.agent_pool.get_all_agents()
		agent_stats = self.agent_pool.get_agent_stats()
		# map efficiency level to multiplier (keep in sync with agent._get_efficiency_multiplier)
		def multiplier_from_level(level):
			if level == "FAST" or level == "fast":
				return 3.0
			if level == "SLOW" or level == "slow":
				return 0.5
			return 1.0

		multipliers = [multipler_val if (multipler_val := multiplier_from_level(getattr(s.efficiency_level, 'value', str(s.efficiency_level)))) is not None else 1.0 for s in agent_stats]
		min_mul = min(multipliers) if multipliers else 1.0
		scale = max(1, int(round(1.0 / min_mul)))
		weighted_agents = []
		for ref, mul in zip(agent_refs, multipliers):
			weight = max(1, int(round(mul * scale)))
			for _ in range(weight):
				weighted_agents.append(ref)

		# prioritized list: fast agents first, then normal, then slow
		agents_by_eff = {"fast": [], "normal": [], "slow": []}
		for ref, s in zip(agent_refs, agent_stats):
			lvl = getattr(s.efficiency_level, 'value', str(s.efficiency_level))
			agents_by_eff.get(lvl, agents_by_eff["normal"]).append(ref)
		prioritized_agents = agents_by_eff["fast"] + agents_by_eff["normal"] + agents_by_eff["slow"]

		agents = agent_refs
		pending: Dict[ray.ObjectRef, Chunk] = {}
		agent_cycle = 0

		# Start initial batch (use weighted cycle for fair distribution)
		# Only prioritize fast agents if total chunks is extremely small (rare case)
		use_prioritized = len(chunks) <= 5
		while chunk_queue and len(pending) < len(agents):
			chunk = chunk_queue.popleft()
			if use_prioritized:
				agent = prioritized_agents[agent_cycle % len(prioritized_agents)]
			else:
				agent = weighted_agents[agent_cycle % len(weighted_agents)]
			pending[agent.factor_chunk.remote(n, chunk.start, chunk.end)] = chunk
			agent_cycle += 1

		results: List[ChunkResult] = []
		p: Optional[int] = None
		q: Optional[int] = None
		checked_candidates = 0
		peak_pool_utilization_percent = 0.0
		start_time = perf_counter()

		try:
			while pending:
				current_utilization = (len(pending) / len(agents)) * 100 if agents else 0.0
				peak_pool_utilization_percent = max(peak_pool_utilization_percent, current_utilization)
				done_refs, running_refs = ray.wait(
					list(pending.keys()), num_returns=1, timeout=None
				)

				for ref in done_refs:
					chunk = pending.pop(ref, None)
					if chunk is None:
						continue

					try:
						result: ChunkResult = ray.get(ref)
					except Exception as exc:
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
							"Factor found: p=%s, q=%s",
							p,
							q,
						)
						append_event(
							"factor_found",
							task_id=task.task_id,
							n=n,
							p=p,
							q=q,
							checked_candidates=checked_candidates,
						)
						for leftover in running_refs:
							# actor tasks do not support force cancellation; perform best-effort cancel
							try:
								ray.cancel(leftover)
							except Exception:
								pass
						pending.clear()
						break

				if p is None:
					pending = {ref: pending[ref] for ref in running_refs if ref in pending}
					while chunk_queue and len(pending) < len(agents):
						chunk = chunk_queue.popleft()
						# switch to prioritized mode ONLY at the very end (last 5 chunks)
						remaining = len(chunk_queue)
						if remaining <= 5:
							agent = prioritized_agents[agent_cycle % len(prioritized_agents)]
						else:
							agent = weighted_agents[agent_cycle % len(weighted_agents)]
						pending[agent.factor_chunk.remote(n, chunk.start, chunk.end)] = chunk
						agent_cycle += 1

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
			peak_pool_utilization_percent=peak_pool_utilization_percent,
			message=message,
		)

		pool_stats = self.agent_pool.get_pool_summary()
		self.log.info(
			"Task %s completed: jobs_completed=%s, avg_util=%.1f%%, elapsed=%.3fs",
			task.task_id,
			pool_stats["total_jobs_completed"],
			pool_stats["average_utilization_percent"],
			elapsed,
		)
		append_event(
			"task_completed",
			task_id=task.task_id,
			n=n,
			status=status.value,
			p=p,
			q=q,
			elapsed_seconds=elapsed,
			checked_chunks=len(results),
			checked_candidates=checked_candidates,
			pool_total_jobs=pool_stats["total_jobs_completed"],
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
