from decimal import Decimal

import pytest

from techa.core.evidence import EvidenceRegistry
from techa.integration.gbl import GBLCaseValidationError, import_gbl_case


def payload():
    return {
        "contract_version": "1.0",
        "business": {
            "business_id": "548",
            "name": "Dehydrated Vegetable Production",
            "sector": "Agriculture & Agribusiness",
            "geography": "Ethiopia, Addis Ababa / Modjo Regional Corridor",
        },
        "governance": {
            "state": "State 0",
            "human_gate": "HOLD / NOT CLEARED",
            "steps_frozen_through": 55,
        },
        "currency": {"base_currency": "ETB"},
        "assumptions": [
            {
                "key": "selling_price",
                "value": "380",
                "unit": "ETB/kg",
                "evidence_class": "REQUIRES_PRIMARY_VERIFICATION",
                "source": "GBL #548 evidence register",
                "editable": True,
            },
            {
                "key": "reserve_rate",
                "value": "0.20",
                "unit": "ratio",
                "evidence_class": "MARKET_ASSUMPTION",
                "source": "GBL model assumption",
                "editable": True,
            },
        ],
        "scenarios": [
            {"scenario_id": "S2", "name": "Rented facility", "overrides": {"selling_price": "400"}}
        ],
        "source_results": [
            {
                "result_id": "548-S2-FINAL",
                "result_version": "1",
                "source_system": "GBL",
                "source_reference": "Business #548 completed model",
                "status": "AUTHORITATIVE_REFERENCE",
            }
        ],
    }


def test_import_preserves_business_evidence_and_source_result():
    case = import_gbl_case(payload())
    assert case.business_case.case_id == "548"
    assert case.business_case.base_currency.code == "ETB"
    assert case.business_case.assumption("selling_price").evidence_class.value == "REQUIRES_PRIMARY_VERIFICATION"
    assert case.source_results[0].status == "AUTHORITATIVE_REFERENCE"


def test_import_rejects_unknown_scenario_assumption():
    data = payload()
    data["scenarios"][0]["overrides"]["unknown"] = "1"
    with pytest.raises(GBLCaseValidationError, match="unknown assumptions"):
        import_gbl_case(data)


def test_import_rejects_invalid_evidence_class():
    data = payload()
    data["assumptions"][0]["evidence_class"] = "VERIFIED"
    with pytest.raises(GBLCaseValidationError, match="Invalid evidence class"):
        import_gbl_case(data)


def test_import_rejects_missing_fx_metadata_for_different_presentation_currency():
    data = payload()
    data["currency"] = {"base_currency": "ETB", "presentation_currency": "USD"}
    with pytest.raises(GBLCaseValidationError, match="presentation currency"):
        import_gbl_case(data)
