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


def test_workspace_evidence_status_and_explicit_reclassification_are_audited():
    case_id = "WORKSPACE-API-003"
    created = client.post("/v1/business-cases", json=_case(case_id))
    assert created.status_code == 200

    status = client.get(f"/v1/business-cases/{case_id}/evidence")
    assert status.status_code == 200
    body = status.json()
    assert body["can_execute"] is True
    units = next(item for item in body["items"] if item["key"] == "units_sold")
    assert units["evidence_class"] == "MARKET_ASSUMPTION"
    assert units["blocking"] is False

    changed = client.patch(
        f"/v1/business-cases/{case_id}/assumptions/units_sold/evidence",
        json={"evidence_class": "VERIFIED_FACT", "source": "Primary verification record"},
    )
    assert changed.status_code == 200
    result = changed.json()
    assert result["business_case"]["assumptions"]["units_sold"]["evidence_class"] == "VERIFIED_FACT"
    assert result["business_case"]["assumptions"]["units_sold"]["source"] == "Primary verification record"
    assert result["audit_digest"]

    status = client.get(f"/v1/business-cases/{case_id}/evidence")
    assert status.json()["can_execute"] is True

    audit = client.get(f"/v1/business-cases/{case_id}/audit")
    records = audit.json()["records"]
    assert any(
        r["event"] == "evidence.reclassified"
        and r["digest"] == result["audit_digest"]
        for r in records
    )


def test_workspace_evidence_reclassification_can_make_case_blocked():
    case_id = "WORKSPACE-API-004"
    created = client.post("/v1/business-cases", json=_case(case_id))
    assert created.status_code == 200

    changed = client.patch(
        f"/v1/business-cases/{case_id}/assumptions/units_sold/evidence",
        json={"evidence_class": "REQUIRES_PRIMARY_VERIFICATION", "source": "Pending primary evidence"},
    )
    assert changed.status_code == 200

    status = client.get(f"/v1/business-cases/{case_id}/evidence")
    body = status.json()
    assert body["can_execute"] is False
    blocked = next(item for item in body["items"] if item["key"] == "units_sold")
    assert blocked["blocking"] is True
    assert blocked["evidence_class"] == "REQUIRES_PRIMARY_VERIFICATION"


def test_workspace_simulation_supports_presentation_currency_and_audit():
    case_id = "WORKSPACE-API-005"
    created = client.post("/v1/business-cases", json=_case(case_id))
    assert created.status_code == 200
    fx = client.post("/v1/fx-rates", json={
        "from_currency": "ETB", "to_currency": "USD", "rate": "0.006",
        "as_of": "2026-10-05", "source": "workspace-test",
    })
    assert fx.status_code == 200

    simulated = client.post(
        f"/v1/business-cases/{case_id}/simulate",
        json={
            "scenario_id": "BASE",
            "scenario_name": "Base Case",
            "overrides": {},
            "presentation_currency": "USD",
            "fx_as_of": "2026-10-05",
        },
    )
    assert simulated.status_code == 200
    body = simulated.json()
    assert body["financial"]["net_profit"] == "280.00"
    assert body["presentation"]["net_profit"] == "1.68000"
    assert body["fx_direction"] == "direct"
    assert body["fx"]["source"] == "workspace-test"
    assert body["presentation_audit_digest"]

    audit = client.get(f"/v1/business-cases/{case_id}/audit")
    assert audit.status_code == 200
    assert any(r["event"] == "currency.present" for r in audit.json()["records"])


def test_workspace_blocked_evidence_prevents_simulation():
    case_id = "WORKSPACE-API-006"
    created = client.post("/v1/business-cases", json=_case(case_id))
    assert created.status_code == 200

    changed = client.patch(
        f"/v1/business-cases/{case_id}/assumptions/selling_price/evidence",
        json={"evidence_class": "REQUIRES_PRIMARY_VERIFICATION", "source": "Pending verification"},
    )
    assert changed.status_code == 200

    simulated = client.post(
        f"/v1/business-cases/{case_id}/simulate",
        json={"scenario_id": "BASE", "scenario_name": "Base Case", "overrides": {}},
    )
    assert simulated.status_code == 422
    assert "Simulation blocked by evidence requiring verification" in simulated.json()["detail"]


def test_workspace_sensitivity_is_executable_and_audited():
    case_id = "WORKSPACE-API-007"
    created = client.post("/v1/business-cases", json=_case(case_id))
    assert created.status_code == 200

    result = client.post(
        f"/v1/business-cases/{case_id}/sensitivity",
        json={"variable": "selling_price", "values": ["40", "50", "60"]},
    )
    assert result.status_code == 200
    body = result.json()
    assert [p["financial"]["net_profit"] for p in body["points"]] == ["-600.00", "280.00", "980.00"]
    assert body["audit_digest"]
