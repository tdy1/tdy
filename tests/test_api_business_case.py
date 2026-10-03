from fastapi.testclient import TestClient
from techa.api import app
client=TestClient(app)

def test_create_and_get_business_case():
    r=client.post("/v1/business-cases",json={
        "case_id":"API-001","name":"API Test","base_currency":"ETB",
        "currency_name":"Ethiopian Birr","assumptions":[{
            "key":"price","value":"380","unit":"ETB/kg",
            "evidence_class":"MARKET_ASSUMPTION","editable":True}]})
    assert r.status_code==200 and r.json()["case_id"]=="API-001"
    r=client.get("/v1/business-cases/API-001")
    assert r.status_code==200 and r.json()["assumptions"]["price"]["value"]=="380"


def test_simulate_business_case_endpoint():
    assumptions = [
        {"key": "units_sold", "value": "100", "unit": "units", "evidence_class": "MARKET_ASSUMPTION"},
        {"key": "selling_price", "value": "50", "unit": "ETB/unit", "evidence_class": "MARKET_ASSUMPTION"},
        {"key": "direct_cogs", "value": "3000", "unit": "ETB", "evidence_class": "COST_ENGINEERING_ESTIMATE"},
        {"key": "reserve_rate", "value": "0.20", "unit": "ratio", "evidence_class": "MARKET_ASSUMPTION"},
        {"key": "operating_expenses", "value": "1000", "unit": "ETB", "evidence_class": "COST_ENGINEERING_ESTIMATE"},
        {"key": "tax_rate", "value": "0.30", "unit": "ratio", "evidence_class": "VERIFIED_FACT"},
    ]
    r = client.post("/v1/business-cases", json={
        "case_id": "API-SIM-001", "name": "API Simulation", "base_currency": "ETB",
        "assumptions": assumptions,
    })
    assert r.status_code == 200
    r = client.post("/v1/business-cases/API-SIM-001/simulate", json={
        "scenario_id": "LOW", "scenario_name": "Low price", "overrides": {"selling_price": "40"}
    })
    assert r.status_code == 200
    assert r.json()["financial"]["net_profit"] == "-600.00"
    assert r.json()["audit_digest"]
