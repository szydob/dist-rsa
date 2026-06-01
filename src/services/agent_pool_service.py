from __future__ import annotations

from typing import Optional

from core.agent_pool.pool import AgentPool
from core.agent_pool.pool_coordinator import AgentPoolFactorizationCoordinator
from core.shared.models import FactorizationResult


class AgentPoolService:
	"""Service facade for factorization using the persistent agent pool."""

	def __init__(
		self,
		agent_pool: Optional[AgentPool] = None,
		coordinator: Optional[AgentPoolFactorizationCoordinator] = None,
	) -> None:
		self.agent_pool = agent_pool or AgentPool()
		self.coordinator = coordinator or AgentPoolFactorizationCoordinator(
			agent_pool=self.agent_pool
		)

	def factor(
		self,
		n: int,
		*,
		chunk_size: Optional[int] = None,
	) -> FactorizationResult:
		"""Factor n using the persistent agent pool.

		Args:
			n: Integer to factor.
			chunk_size: Optional chunk-size override for this run.

		Returns:
			The completed factorization result.
		"""
		# Reset per-run statistics before starting new factorization
		self.agent_pool.reset_all_run_statistics()

		if chunk_size is not None and chunk_size <= 0:
			raise ValueError("chunk_size must be positive")

		if chunk_size is None:
			return self.coordinator.factor(n)

		temp_coordinator = AgentPoolFactorizationCoordinator(
			agent_pool=self.agent_pool,
			chunk_size=chunk_size,
		)
		return temp_coordinator.factor(n)

	def get_pool_stats(self) -> dict:
		"""Return the current pool statistics snapshot."""
		return self.agent_pool.get_pool_summary()

	def get_agent_details(self) -> list[dict]:
		"""Return detailed statistics for each agent in the pool."""
		stats = self.agent_pool.get_agent_stats()
		return [
			{
				"agent_id": s.agent_id,
				"efficiency_level": s.efficiency_level.value,
				"total_jobs_completed": s.total_jobs_completed,
				"utilization_percent": round(s.current_utilization_percent, 1),
				"is_busy": s.is_busy,
				"pending_tasks": s.pending_tasks,
				"total_checked": s.total_checked,
			}
			for s in stats
		]
