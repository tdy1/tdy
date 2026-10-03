from fastapi.testclient import TestClient
from techa.api import app

client=TestClient(app)

def test_health():
    assert client.get("/health").json()["status"]=="ok"

def test_financial_endpoint():
    r=client.post("/v1/financial/calculate",json={
      "units_sold":"10","selling_price":"100","direct_cogs":"400",
      "reserve_rate":"0.2","operating_expenses":"200","tax_rate":"0.3"})
    assert r.status_code==200
    assert r.json()["revenue"]=="1000.00"


def test_financial_endpoint_with_presentation_currency():
    client.post("/v1/fx-rates",json={
      "from_currency":"ETB","to_currency":"USD","rate":"0.006",
      "as_of":"2026-10-03","source":"test"
    })
    r=client.post("/v1/financial/calculate",json={
      "units_sold":"100","selling_price":"50","direct_cogs":"3000",
      "reserve_rate":"0.2","operating_expenses":"1000","tax_rate":"0.3",
      "base_currency":"ETB","presentation_currency":"USD","fx_as_of":"2026-10-03"
    })
    assert r.status_code==200
    body=r.json()
    assert body["financial"]["net_profit"]=="280.00"
    assert body["presentation"]["net_profit"]=="1.6800"
    assert body["fx"]["source"]=="test"
    assert body["audit_digest"]


def test_financial_endpoint_requires_exact_fx_rate_for_presentation():
    r=client.post("/v1/financial/calculate",json={
      "units_sold":"10","selling_price":"100","direct_cogs":"400",
      "reserve_rate":"0.2","operating_expenses":"200","tax_rate":"0.3",
      "base_currency":"ETB","presentation_currency":"USD","fx_as_of":"2099-01-01"
    })
    assert r.status_code==422
