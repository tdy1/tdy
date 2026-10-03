from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BusinessLifecycle(str, Enum):
    UNIVERSE = "UNIVERSE"
    CANDIDATE = "CANDIDATE"
    INGESTED = "INGESTED"
    GOVERNANCE_HOLD = "GOVERNANCE_HOLD"
    SIMULATION_READY = "SIMULATION_READY"
    SIMULATED = "SIMULATED"
    REVIEW = "REVIEW"
    CLEARED = "CLEARED"
    NOT_CLEARED = "NOT_CLEARED"


@dataclass(frozen=True)
class BusinessUniverseItem:
    business_id: str
    name: str
    sector: str
    geography: str
    lifecycle_status: BusinessLifecycle = BusinessLifecycle.UNIVERSE
    active_case_id: str | None = None

    def __post_init__(self) -> None:
        for value, label in ((self.business_id, "business_id"), (self.name, "name"),
                             (self.sector, "sector"), (self.geography, "geography")):
            if not value.strip():
                raise ValueError(f"{label} cannot be empty")
        if self.active_case_id is not None and not self.active_case_id.strip():
            raise ValueError("active_case_id cannot be empty when provided")


ALLOWED_LIFECYCLE_TRANSITIONS: dict[BusinessLifecycle, frozenset[BusinessLifecycle]] = {
    BusinessLifecycle.UNIVERSE: frozenset({BusinessLifecycle.CANDIDATE}),
    BusinessLifecycle.CANDIDATE: frozenset({BusinessLifecycle.INGESTED}),
    BusinessLifecycle.INGESTED: frozenset({BusinessLifecycle.GOVERNANCE_HOLD, BusinessLifecycle.SIMULATION_READY}),
    BusinessLifecycle.GOVERNANCE_HOLD: frozenset({BusinessLifecycle.SIMULATION_READY, BusinessLifecycle.NOT_CLEARED}),
    BusinessLifecycle.SIMULATION_READY: frozenset({BusinessLifecycle.SIMULATED, BusinessLifecycle.GOVERNANCE_HOLD}),
    BusinessLifecycle.SIMULATED: frozenset({BusinessLifecycle.REVIEW, BusinessLifecycle.GOVERNANCE_HOLD}),
    BusinessLifecycle.REVIEW: frozenset({BusinessLifecycle.CLEARED, BusinessLifecycle.NOT_CLEARED, BusinessLifecycle.GOVERNANCE_HOLD}),
    BusinessLifecycle.CLEARED: frozenset(),
    BusinessLifecycle.NOT_CLEARED: frozenset({BusinessLifecycle.REVIEW, BusinessLifecycle.CANDIDATE}),
}


def validate_lifecycle_transition(current: BusinessLifecycle, target: BusinessLifecycle) -> None:
    if current == target:
        return
    if target not in ALLOWED_LIFECYCLE_TRANSITIONS[current]:
        raise ValueError(f"Invalid lifecycle transition: {current.value} -> {target.value}")
