from __future__ import annotations

from typing import Optional

from core.agent_pool.pool import AgentPool
from core.agent_pool.pool_coordinator import AgentPoolFactorizationCoordinator
from core.shared.models import FactorizationResult


class AgentPoolService:
	"""Service for factorization using persistent agent pool."""

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
		"""Factor n using the agent pool."""
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
		"""Get current pool statistics."""
		return self.agent_pool.get_pool_summary()

	def get_agent_details(self) -> list[dict]:
		"""Get detailed stats for each agent."""
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
