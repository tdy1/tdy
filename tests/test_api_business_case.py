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
