from __future__ import annotations

from core.models import AttackStatus
from services.attack_service import AttackService


def test_attack_service_recovers_private_exponent(ray_session):
    service = AttackService()
    result = service.attack(3233, 65537, workers_count=4, chunk_size=5000)

    assert result.status is AttackStatus.COMPLETED
    assert {result.p, result.q} == {53, 61}
    assert result.phi == 3120
    assert result.d == pow(65537, -1, 3120)
