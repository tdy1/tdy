from fastapi.testclient import TestClient

from techa.api import app


client = TestClient(app)


def _case(case_id: str) -> dict:
    return {
        "case_id": case_id,
        "name": "Workspace Test Case",
        "base_currency": "ETB",
        "assumptions": [
            {"key": "units_sold", "value": "100", "unit": "units", "evidence_class": "MARKET_ASSUMPTION"},
            {"key": "selling_price", "value": "50", "unit": "ETB/unit", "evidence_class": "MARKET_ASSUMPTION"},
            {"key": "direct_cogs", "value": "3000", "unit": "ETB", "evidence_class": "COST_ENGINEERING_ESTIMATE"},
            {"key": "reserve_rate", "value": "0.20", "unit": "ratio", "evidence_class": "MARKET_ASSUMPTION"},
            {"key": "operating_expenses", "value": "1000", "unit": "ETB", "evidence_class": "COST_ENGINEERING_ESTIMATE"},
            {"key": "tax_rate", "value": "0.30", "unit": "ratio", "evidence_class": "VERIFIED_FACT"},
        ],
    }


def test_workspace_creates_and_loads_business_case():
    case_id = "WORKSPACE-API-001"
    created = client.post("/v1/business-cases", json=_case(case_id))
    assert created.status_code == 200
    body = created.json()
    assert body["case_id"] == case_id
    assert body["assumptions"]["units_sold"]["evidence_class"] == "MARKET_ASSUMPTION"

    loaded = client.get(f"/v1/business-cases/{case_id}")
    assert loaded.status_code == 200
    assert loaded.json()["name"] == "Workspace Test Case"


def test_workspace_runs_base_and_scenario_simulations():
    case_id = "WORKSPACE-API-002"
    created = client.post("/v1/business-cases", json=_case(case_id))
    assert created.status_code == 200

    base = client.post(
        f"/v1/business-cases/{case_id}/simulate",
        json={"scenario_id": "BASE", "scenario_name": "Base Case", "overrides": {}},
    )
    assert base.status_code == 200
    assert base.json()["financial"]["net_profit"] == "280.00"
    assert base.json()["audit_digest"]

    scenario = client.post(
        f"/v1/business-cases/{case_id}/simulate",
        json={
            "scenario_id": "LOW-PRICE",
            "scenario_name": "Low Price",
            "overrides": {"selling_price": "40"},
        },
    )
    assert scenario.status_code == 200
    assert scenario.json()["scenario_id"] == "LOW-PRICE"
    assert scenario.json()["financial"]["revenue"] == "4000.00"
    assert scenario.json()["financial"]["net_profit"] == "-600.00"

    audit = client.get(f"/v1/business-cases/{case_id}/audit")
    assert audit.status_code == 200
    assert len(audit.json()["records"]) >= 2
