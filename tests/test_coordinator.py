from __future__ import annotations

from core.coordinator import FactorizationCoordinator
from core.models import FactorizationStatus


def test_coordinator_finds_factor(ray_session):
    coordinator = FactorizationCoordinator(chunk_size=3)
    result = coordinator.factor(91)  # 7 * 13
    assert result.status is FactorizationStatus.FOUND
    assert {result.p, result.q} == {7, 13}
    assert result.checked_chunks >= 1
    assert result.checked_candidates >= 1


def test_coordinator_reports_not_found(ray_session):
    coordinator = FactorizationCoordinator(chunk_size=4)
    result = coordinator.factor(97)  # prime
    assert result.status is FactorizationStatus.NOT_FOUND
    assert result.p is None and result.q is None
    assert result.checked_chunks >= 1
    assert result.checked_candidates >= 1
