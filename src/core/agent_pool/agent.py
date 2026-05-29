from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import perf_counter
from typing import Optional

import ray

from core.agent_pool.event_log import append_event
from core.shared.models import ChunkResult, ChunkStatus


class EfficiencyLevel(str, Enum):
	NORMAL = "normal"  # 70% of agents, 1.0x speed
	FAST = "fast"      # 20% of agents, 3.0x speed
	SLOW = "slow"      # 10% of agents, 0.5x speed


@dataclass
class AgentStats:
	agent_id: int
	efficiency_level: EfficiencyLevel
	total_jobs_completed: int = 0
	current_utilization_percent: float = 0.0
	is_busy: bool = False
	pending_tasks: int = 0
	total_checked: int = 0


@ray.remote
class PoolAgent:
	"""Ray actor representing one worker in the agent pool."""

	def __init__(self, agent_id: int, efficiency_level: EfficiencyLevel) -> None:
		self.agent_id = agent_id
		self.efficiency_level = efficiency_level
		self.total_jobs_completed = 0
		self.total_checked = 0
		self.is_busy = False
		self.pending_tasks = 0
		self.current_utilization_percent = 0.0
		self.efficiency_multiplier = self._get_efficiency_multiplier()

		# For utilization tracking
		self.start_time = perf_counter()
		self.cumulative_busy_time = 0.0
		self._current_task_start: Optional[float] = None
		self.last_completed_time: float = 0.0
		self.STICKY_ACTIVE_DURATION = 2.0  # report 100% for 2s after task completes

	def _get_efficiency_multiplier(self) -> float:
		"""Return speed multiplier based on efficiency level."""
		if self.efficiency_level == EfficiencyLevel.FAST:
			return 3.0
		elif self.efficiency_level == EfficiencyLevel.SLOW:
			return 0.5
		else:  # NORMAL
			return 1.0

	def factor_chunk(self, n: int, chunk_start: int, chunk_end: int) -> ChunkResult:
		"""Search for divisor in chunk range with efficiency multiplier."""
		append_event(
			"chunk_started",
			agent_id=self.agent_id,
			efficiency_level=self.efficiency_level.value,
			n=n,
			chunk_start=chunk_start,
			chunk_end=chunk_end,
		)
		self.is_busy = True
		self.pending_tasks += 1
		# instant/binary utilization: 100% while working, 0% otherwise
		self.current_utilization_percent = 100.0

		start_time = perf_counter()
		self._current_task_start = start_time
		divisor: Optional[int] = None
		checked = 0

		# Efficiency multiplier affects search: faster agents check more per time unit
		# We simulate this by potentially skipping candidates (for fast) or being slower
		for candidate in range(chunk_start, chunk_end + 1):
			checked += 1
			# Fast agents do light sampling (skip some checks) to simulate higher throughput
			if self.efficiency_level == EfficiencyLevel.FAST:
				if checked % 3 == 0 and checked > 100:
					continue
			if n % candidate == 0:
				divisor = candidate
				break

		elapsed = perf_counter() - start_time
		# clear current task markers
		if self._current_task_start is not None:
			self._current_task_start = None

		self.total_jobs_completed += 1
		self.total_checked += checked
		self.pending_tasks = max(0, self.pending_tasks - 1)
		self.is_busy = self.pending_tasks > 0
		# Mark task completion time for sticky active state
		self.last_completed_time = perf_counter()
		status = ChunkStatus.FOUND if divisor is not None else ChunkStatus.COMPLETED

		append_event(
			"chunk_finished",
			agent_id=self.agent_id,
			efficiency_level=self.efficiency_level.value,
			n=n,
			chunk_start=chunk_start,
			chunk_end=chunk_end,
			divisor=divisor,
			checked=checked,
			elapsed_seconds=elapsed,
			status=status.value,
		)

		return ChunkResult(
			chunk_id=self.agent_id,
			start=chunk_start,
			end=chunk_end,
			divisor=divisor,
			elapsed_seconds=elapsed,
			checked=checked,
			status=status,
		)

	def get_stats(self) -> AgentStats:
		"""Return current agent statistics."""
		# Compute utilization: 100% if busy OR recently completed (sticky active)
		now = perf_counter()
		is_recently_active = (now - self.last_completed_time) < self.STICKY_ACTIVE_DURATION
		util = 100.0 if (self.is_busy or is_recently_active) else 0.0
		
		return AgentStats(
			agent_id=self.agent_id,
			efficiency_level=self.efficiency_level,
			total_jobs_completed=self.total_jobs_completed,
			current_utilization_percent=util,
			is_busy=self.is_busy,
			pending_tasks=self.pending_tasks,
			total_checked=self.total_checked,
		)

	def reset_run_statistics(self) -> None:
		"""Reset per-run metrics (pending tasks, busy state, recent completion time)."""
		self.pending_tasks = 0
		self.is_busy = False
		self.last_completed_time = 0.0
		self.current_utilization_percent = 0.0
