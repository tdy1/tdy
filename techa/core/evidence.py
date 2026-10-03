from __future__ import annotations

from dataclasses import dataclass
from techa.core.models import EvidenceClass


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    claim: str
    evidence_class: EvidenceClass
    source: str | None = None
    note: str | None = None
    requires_primary_verification: bool = False

    @property
    def executable(self) -> bool:
        return not self.requires_primary_verification and self.evidence_class not in {
            EvidenceClass.REQUIRES_PRIMARY_VERIFICATION,
            EvidenceClass.FIELD_VALIDATION_REQUIREMENTS,
        }


class EvidenceRegistry:
    def __init__(self) -> None:
        self._items: dict[str, EvidenceItem] = {}

    def add(self, item: EvidenceItem) -> None:
        if item.evidence_id in self._items:
            raise ValueError("Duplicate evidence_id")
        self._items[item.evidence_id] = item

    def get(self, evidence_id: str) -> EvidenceItem:
        return self._items[evidence_id]

    def all(self) -> tuple[EvidenceItem, ...]:
        return tuple(self._items.values())

    def blocking_items(self) -> tuple[EvidenceItem, ...]:
        return tuple(item for item in self._items.values() if not item.executable)

    def can_execute(self) -> bool:
        return not self.blocking_items()
