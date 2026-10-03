from techa.core.evidence import EvidenceItem, EvidenceRegistry
from techa.core.models import EvidenceClass


def test_evidence_registry_detects_duplicate_and_blocks_unverified():
    registry = EvidenceRegistry()
    registry.add(EvidenceItem("E1", "Observed", EvidenceClass.INDICATIVE_OBSERVED_DATA))
    registry.add(EvidenceItem("E2", "Verify", EvidenceClass.REQUIRES_PRIMARY_VERIFICATION, requires_primary_verification=True))
    assert len(registry.all()) == 2
    assert registry.can_execute() is False
    assert registry.blocking_items()[0].evidence_id == "E2"


def test_verified_evidence_is_executable():
    registry = EvidenceRegistry()
    registry.add(EvidenceItem("E1", "Verified", EvidenceClass.VERIFIED_FACT))
    assert registry.can_execute() is True
