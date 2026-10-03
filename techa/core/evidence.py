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

class EvidenceRegistry:
    def __init__(self) -> None: self._items={}
    def add(self,item:EvidenceItem)->None:
        if item.evidence_id in self._items: raise ValueError("Duplicate evidence_id")
        self._items[item.evidence_id]=item
    def get(self,evidence_id:str)->EvidenceItem: return self._items[evidence_id]
    def all(self)->tuple[EvidenceItem,...]: return tuple(self._items.values())
