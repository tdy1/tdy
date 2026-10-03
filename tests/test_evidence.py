from techa.core.evidence import EvidenceItem, EvidenceRegistry
from techa.core.models import EvidenceClass

def test_evidence_is_retained():
    r=EvidenceRegistry(); r.add(EvidenceItem("E1","price",EvidenceClass.MARKET_ASSUMPTION))
    assert r.get("E1").evidence_class is EvidenceClass.MARKET_ASSUMPTION
