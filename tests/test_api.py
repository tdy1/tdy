from fastapi.testclient import TestClient
from techa.api import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_financial_endpoint():
    r = client.post("/v1/financial/calculate", json={
        "units_sold": "10", "selling_price": "100", "direct_cogs": "400",
        "reserve_rate": "0.2", "operating_expenses": "200", "tax_rate": "0.3"
    })
    assert r.status_code == 200
    assert r.json()["revenue"] == "1000.00"


def test_financial_endpoint_with_presentation_currency():
    client.post("/v1/fx-rates", json={
        "from_currency": "ETB", "to_currency": "USD", "rate": "0.006",
        "as_of": "2026-10-03", "source": "test"
    })
    r = client.post("/v1/financial/calculate", json={
        "units_sold": "100", "selling_price": "50", "direct_cogs": "3000",
        "reserve_rate": "0.2", "operating_expenses": "1000", "tax_rate": "0.3",
        "base_currency": "ETB", "presentation_currency": "USD", "fx_as_of": "2026-10-03"
    })
    assert r.status_code == 200
    body = r.json()
    assert body["financial"]["net_profit"] == "280.00"
    assert body["presentation"]["net_profit"] == "1.68000"
    assert body["fx"]["source"] == "test"
    assert body["fx_direction"] == "direct"
    assert body["audit_digest"]


def test_financial_endpoint_supports_inverse_stored_fx():
    client.post("/v1/fx-rates", json={
        "from_currency": "USD", "to_currency": "ETB", "rate": "160",
        "as_of": "2026-10-04", "source": "inverse-test"
    })
    r = client.post("/v1/financial/calculate", json={
        "units_sold": "100", "selling_price": "50", "direct_cogs": "3000",
        "reserve_rate": "0.2", "operating_expenses": "1000", "tax_rate": "0.3",
        "base_currency": "ETB", "presentation_currency": "USD", "fx_as_of": "2026-10-04"
    })
    assert r.status_code == 200
    body = r.json()
    assert body["presentation"]["net_profit"] == "1.75"
    assert body["fx_direction"] == "inverse"
    assert body["fx"]["source"] == "inverse-test"


def test_financial_endpoint_requires_exact_fx_rate_for_presentation():
    r = client.post("/v1/financial/calculate", json={
        "units_sold": "10", "selling_price": "100", "direct_cogs": "400",
        "reserve_rate": "0.2", "operating_expenses": "200", "tax_rate": "0.3",
        "base_currency": "ETB", "presentation_currency": "USD", "fx_as_of": "2099-01-01"
    })
    assert r.status_code == 422


def test_gbl_business_universe_lifecycle_api():
    payload = {
        "business_id": "548",
        "name": "Dehydrated Vegetable Production",
        "sector": "Agriculture & Agribusiness",
        "geography": "Ethiopia",
    }
    created = client.post("/v1/gbl/universe", json=payload)
    assert created.status_code == 200
    assert created.json()["lifecycle_status"] == "UNIVERSE"

    candidate = client.patch("/v1/gbl/universe/548/lifecycle", json={
        "lifecycle_status": "CANDIDATE"
    })
    assert candidate.status_code == 200
    assert candidate.json()["lifecycle_status"] == "CANDIDATE"

    changed = client.patch("/v1/gbl/universe/548/lifecycle", json={
        "lifecycle_status": "INGESTED"
    })
    assert changed.status_code == 200
    assert changed.json()["lifecycle_status"] == "INGESTED"

    listed = client.get("/v1/gbl/universe?lifecycle_status=INGESTED")
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1
    assert any(item["business_id"] == "548" for item in listed.json()["items"])

    fetched = client.get("/v1/gbl/universe/548")
    assert fetched.status_code == 200
    assert fetched.json()["active_case_id"] is None


def test_gbl_universe_instantiates_existing_case():
    universe = client.post("/v1/gbl/universe", json={
        "business_id": "550",
        "name": "Dehydrated Vegetable Production",
        "sector": "Agriculture & Agribusiness",
        "geography": "Ethiopia",
    })
    assert universe.status_code == 200

    case = client.post("/v1/business-cases", json={
        "case_id": "548-case-v1",
        "name": "Dehydrated Vegetable Production",
        "base_currency": "ETB",
    })
    assert case.status_code == 200

    linked = client.post("/v1/gbl/universe/550/instantiate", json={
        "case_id": "548-case-v1",
    })
    assert linked.status_code == 200
    assert linked.json()["lifecycle_status"] == "INGESTED"
    assert linked.json()["active_case_id"] == "548-case-v1"


def test_gbl_universe_rejects_different_active_case():
    client.post("/v1/gbl/universe", json={
        "business_id": "549",
        "name": "Business 549",
        "sector": "Agriculture",
        "geography": "Ethiopia",
    })
    client.post("/v1/business-cases", json={
        "case_id": "549-case-v1",
        "name": "Business 549",
        "base_currency": "ETB",
    })
    client.post("/v1/business-cases", json={
        "case_id": "549-case-v2",
        "name": "Business 549",
        "base_currency": "ETB",
    })
    assert client.post("/v1/gbl/universe/549/instantiate", json={"case_id": "549-case-v1"}).status_code == 200
    assert client.post("/v1/gbl/universe/549/instantiate", json={"case_id": "549-case-v2"}).status_code == 409


def test_gbl_business_intake_creates_case_and_advances_lifecycle():
    created = client.post("/v1/gbl/universe", json={
        "business_id": "560",
        "name": "Intake Test Business",
        "sector": "Agriculture",
        "geography": "Ethiopia",
    })
    assert created.status_code == 200
    intake = client.post("/v1/gbl/universe/560/intake", json={
        "case_id": "560-case-v1",
        "base_currency": "ETB",
    })
    assert intake.status_code == 200
    body = intake.json()
    assert body["business"]["lifecycle_status"] == "INGESTED"
    assert body["business"]["active_case_id"] == "560-case-v1"
    assert body["case"]["case_id"] == "560-case-v1"
    fetched = client.get("/v1/business-cases/560-case-v1")
    assert fetched.status_code == 200
    audit = client.get("/v1/business-cases/560-case-v1/audit")
    assert audit.status_code == 200
    assert any(record["event"] == "gbl.business.intake" for record in audit.json()["records"])


def test_gbl_business_intake_rejects_duplicate_case():
    client.post("/v1/gbl/universe", json={
        "business_id": "561",
        "name": "Duplicate Intake Test",
        "sector": "Agriculture",
        "geography": "Ethiopia",
    })
    first = client.post("/v1/gbl/universe/561/intake", json={
        "case_id": "561-case-v1",
        "base_currency": "ETB",
    })
    assert first.status_code == 200
    second = client.post("/v1/gbl/universe/561/intake", json={
        "case_id": "561-case-v2",
        "base_currency": "ETB",
    })
    assert second.status_code == 409


def test_gbl_case_summary_preserves_governance_readiness_and_counts():
    client = TestClient(app)
    data = {
        "contract_version": "1.0",
        "business": {"business_id": "548-SUMMARY", "name": "Dehydrated Vegetable Production", "sector": "Agriculture & Agribusiness", "geography": "Ethiopia"},
        "governance": {"state": "State 0", "human_gate": "HOLD / NOT CLEARED", "steps_frozen_through": 55},
        "currency": {"base_currency": "ETB"},
        "assumptions": [
            {"key": "selling_price", "value": "380", "unit": "ETB/kg", "evidence_class": "REQUIRES_PRIMARY_VERIFICATION", "source": "GBL #548 evidence register", "editable": True}
        ],
        "scenarios": [{"scenario_id": "S2", "name": "Rented facility", "overrides": {}}],
        "source_results": [{"result_id": "548-S2-FINAL", "result_version": "1", "source_system": "GBL", "source_reference": "GBL #548", "status": "AUTHORITATIVE_REFERENCE"}],
    }
    imported = client.post("/v1/gbl/import", json=data)
    assert imported.status_code == 200
    summary = client.get("/v1/gbl/cases/548-SUMMARY/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["business"] == data["business"]
    assert body["governance"] == data["governance"]
    assert body["currency"]["base_currency"] == "ETB"
    assert body["counts"]["scenarios"] == 1
    assert body["counts"]["source_results"] == 1
    assert body["execution_readiness"]["status"] == "BLOCKED"
    assert body["execution_readiness"]["investment_clearance"] is False


def test_gbl_active_case_navigation_lists_linked_cases():
    client = TestClient(app)
    data = {
        "contract_version": "1.0",
        "business": {"business_id": "548-NAV", "name": "Navigation Test Business", "sector": "Agriculture", "geography": "Ethiopia"},
        "governance": {"state": "State 0", "human_gate": "HOLD / NOT CLEARED", "steps_frozen_through": 55},
        "currency": {"base_currency": "ETB"},
        "assumptions": [],
        "scenarios": [],
        "source_results": [],
    }
    imported = client.post("/v1/gbl/import", json=data)
    assert imported.status_code == 200
    client.post("/v1/gbl/universe", json=data["business"])
    linked = client.post("/v1/gbl/universe/548-NAV/instantiate", json={"case_id": "548-NAV"})
    assert linked.status_code == 200
    response = client.get("/v1/gbl/cases")
    assert response.status_code == 200
    match = next(x for x in response.json()["cases"] if x["business_id"] == "548-NAV")
    assert match["case_id"] == "548-NAV"
    assert match["lifecycle_status"] == "INGESTED"


def test_gbl_case_summary_includes_linked_universe_identity():
    client = TestClient(app)
    business = {"business_id": "548-IDENTITY", "name": "Identity Test", "sector": "Agriculture", "geography": "Ethiopia"}
    created = client.post("/v1/gbl/universe", json=business)
    assert created.status_code == 200
    intake = client.post("/v1/gbl/universe/548-IDENTITY/intake", json={"case_id": "548-IDENTITY", "base_currency": "ETB"})
    assert intake.status_code == 200
    summary = client.get("/v1/gbl/cases/548-IDENTITY/summary")
    assert summary.status_code == 200
    universe = summary.json()["universe"]
    assert universe["business_id"] == "548-IDENTITY"
    assert universe["active_case_id"] == "548-IDENTITY"
    assert universe["lifecycle_status"] == "INGESTED"
