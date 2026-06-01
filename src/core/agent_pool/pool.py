from __future__ import annotations

import os
import time

import ray

from core.agent_pool.event_log import append_event
from core.agent_pool.agent import EfficiencyLevel, AgentStats, PoolAgent


class AgentPool:
	"""Manages a pool of Ray agents with different efficiency levels.

	Reduced default size to 50 to avoid OOM in constrained Docker environments.
	"""

	POOL_SIZE = 20
	FAST_COUNT = 4  # 20% of 20
	SLOW_COUNT = 2  # 10% of 20
	NORMAL_COUNT = POOL_SIZE - FAST_COUNT - SLOW_COUNT  # 14 normal
	AGENT_NAMESPACE = "dist-rsa"
	AGENT_NAME_PREFIX = "dist-rsa-agent"

	def __init__(self) -> None:
		"""Initialize the agent pool (idempotent with Ray)."""
		self._ensure_ray()
		self.agents: list[ray.ObjectRef] = []
		self._agent_refs_map: dict[int, ray.ObjectRef] = {}
		self._initialize_agents()

	def _ensure_ray(self) -> None:
		"""Initialize Ray if not already running."""
		if not ray.is_initialized():
			ray_address = os.environ.get("RAY_ADDRESS")
			init_kwargs = {
				"include_dashboard": False,
				"ignore_reinit_error": True,
				"namespace": "dist-rsa",
				"log_to_driver": False,
			}

			if ray_address:
				ray.init(address=ray_address, **init_kwargs)
				return

			try:
				ray.init(address="auto", **init_kwargs)
				return
			except Exception:
				ray.init(address="local", **init_kwargs)

	def _initialize_agents(self) -> None:
		"""Create the agent pool in small batches to reduce scheduling pressure."""
		agent_id = 0
		batch_size = 4
		created_in_batch = 0
		append_event(
			"pool_initializing",
			pool_size=self.POOL_SIZE,
			normal_count=self.NORMAL_COUNT,
			fast_count=self.FAST_COUNT,
			slow_count=self.SLOW_COUNT,
		)

		for count, efficiency_level in (
			(self.NORMAL_COUNT, EfficiencyLevel.NORMAL),
			(self.FAST_COUNT, EfficiencyLevel.FAST),
			(self.SLOW_COUNT, EfficiencyLevel.SLOW),
		):
			for _ in range(count):
				agent_name = f"{self.AGENT_NAME_PREFIX}-{agent_id}"
				agent_ref = self._get_or_create_agent(agent_id, efficiency_level, agent_name)
				self.agents.append(agent_ref)
				self._agent_refs_map[agent_id] = agent_ref
				agent_id += 1
				created_in_batch += 1

				if created_in_batch >= batch_size:
					time.sleep(0.1)
					created_in_batch = 0

	def _get_or_create_agent(
		self,
		agent_id: int,
		efficiency_level: EfficiencyLevel,
		agent_name: str,
	):
		try:
			return ray.get_actor(agent_name, namespace=self.AGENT_NAMESPACE)
		except ValueError:
			append_event(
				"agent_created",
				agent_id=agent_id,
				efficiency_level=efficiency_level.value,
				agent_name=agent_name,
			)
			return PoolAgent.options(
				name=agent_name,
				namespace=self.AGENT_NAMESPACE,
				lifetime="detached",
			).remote(agent_id, efficiency_level)

	def get_idle_agent(self) -> ray.ObjectRef:
		"""Return a deterministic fallback agent reference.

		The pool currently exposes the first available agent when a dedicated
		load-balancing decision is not needed.
		"""
		if not self.agents:
			raise RuntimeError("No agents in pool")
		return self.agents[len(self.agents) % len(self.agents)]

	def get_all_agents(self) -> list[ray.ObjectRef]:
		"""Return all agent refs."""
		return self.agents.copy()

	def get_agent_stats(self) -> list[AgentStats]:
		"""Get stats from all agents."""
		stats_refs = [agent.get_stats.remote() for agent in self.agents]
		return ray.get(stats_refs)

	def get_pool_summary(self) -> dict:
		"""Summary of pool utilization."""
		stats = self.get_agent_stats()
		total_jobs = sum(s.total_jobs_completed for s in stats)
		avg_util = sum(s.current_utilization_percent for s in stats) / len(stats) if stats else 0.0
		busy_count = sum(1 for s in stats if s.is_busy)

		return {
			"pool_size": len(self.agents),
			"busy_agents": busy_count,
			"idle_agents": len(self.agents) - busy_count,
			"total_jobs_completed": total_jobs,
			"average_utilization_percent": avg_util,
			"agent_stats": stats,
		}

	def reset_all_run_statistics(self) -> None:
		"""Reset per-run statistics for all agents (pending tasks, busy state, utilization)."""
		reset_refs = [agent.reset_run_statistics.remote() for agent in self.agents]
		ray.wait(reset_refs)
