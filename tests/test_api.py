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
