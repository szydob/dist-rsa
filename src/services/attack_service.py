from __future__ import annotations

from datetime import datetime
from time import perf_counter
from uuid import uuid4

from core.shared.models import AttackResult, AttackStatus, FactorizationStatus
from services.factorization_service import FactorizationService


class AttackService:
    """Simulate an RSA attack by factoring n and recovering d."""

    def __init__(self, factorization_service: FactorizationService | None = None) -> None:
        self.factorization_service = factorization_service or FactorizationService()

    def attack(
        self,
        n: int,
        e: int,
        *,
        workers_count: int | None = None,
        chunk_size: int | None = None,
    ) -> AttackResult:
        """Run factorization and derive the private exponent from the result.

        Args:
            n: RSA modulus to attack.
            e: Public exponent.
            workers_count: Optional override for the distributed factorizer.
            chunk_size: Optional override for divisor-search chunk size.

        Returns:
            The completed attack result with recovered RSA parameters.

        Raises:
            ValueError: If the provided inputs are invalid.
        """
        if n <= 3:
            raise ValueError("n must be greater than 3")
        if e <= 1:
            raise ValueError("e must be greater than 1")

        task_id = str(uuid4())
        start_time = perf_counter()
        factorization_result = self.factorization_service.factor(
            n,
            workers_count=workers_count,
            chunk_size=chunk_size,
        )
        factorization_elapsed = factorization_result.elapsed_seconds

        if factorization_result.status is not FactorizationStatus.FOUND:
            total_elapsed = perf_counter() - start_time
            return AttackResult(
                task_id=task_id,
                status=AttackStatus.FAILED,
                n=n,
                e=e,
                p=None,
                q=None,
                phi=None,
                d=None,
                factorization_elapsed_seconds=factorization_elapsed,
                total_elapsed_seconds=total_elapsed,
                message=factorization_result.message or "Factorization failed",
            )

        assert factorization_result.p is not None
        assert factorization_result.q is not None
        phi = (factorization_result.p - 1) * (factorization_result.q - 1)
        d = pow(e, -1, phi)
        total_elapsed = perf_counter() - start_time

        return AttackResult(
            task_id=task_id,
            status=AttackStatus.COMPLETED,
            n=n,
            e=e,
            p=factorization_result.p,
            q=factorization_result.q,
            phi=phi,
            d=d,
            factorization_elapsed_seconds=factorization_elapsed,
            total_elapsed_seconds=total_elapsed,
            message="Recovered private exponent d from the factored modulus",
        )
