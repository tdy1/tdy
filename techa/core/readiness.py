from __future__ import annotations

from dataclasses import dataclass
from techa.core.evidence import EvidenceRegistry


@dataclass(frozen=True)
class ExecutionReadiness:
    can_execute: bool
    blocking_items: tuple[str, ...]

    @property
    def status(self) -> str:
        return "READY" if self.can_execute else "BLOCKED"


class ExecutionReadinessService:
    """Central simulation execution gate; readiness is distinct from investment clearance."""

    @staticmethod
    def assess(evidence: EvidenceRegistry) -> ExecutionReadiness:
        blocking = tuple(item.evidence_id for item in evidence.blocking_items())
        return ExecutionReadiness(not blocking, blocking)
