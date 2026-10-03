from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from techa.core.models import Assumption, BusinessCase, Currency, EvidenceClass, FxRate
from techa.core.universe import BusinessLifecycle, BusinessLifecycleService, BusinessUniverseItem
from techa.core.evidence import EvidenceItem, EvidenceRegistry
from techa.core.scenario import Scenario
from techa.core.serialization import jsonable
from techa.core.simulation import SimulationService
from techa.core.readiness import ExecutionReadinessService
from techa.core.sensitivity_service import SensitivityService
from techa.audit.record import AuditRecord
from techa.financial.currency import CurrencyConverter
from techa.financial.engine import FinancialEngine, FinancialInputs
from techa.storage.repository import SQLiteStore

app = FastAPI(title="TECHA Engine", version="0.1.0")
_store = SQLiteStore(Path("techa.db"))
_store.initialize(Path(__file__).parent / "storage" / "schema.sql")
_simulation = SimulationService(_store)
_sensitivity = SensitivityService(_simulation, _store)


class UniverseItemRequest(BaseModel):
    business_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    sector: str = Field(min_length=1)
    geography: str = Field(min_length=1)


class BusinessIntakeRequest(BaseModel):
    case_id: str = Field(min_length=1)
    base_currency: str = Field(min_length=3, max_length=3, default="ETB")


class UniverseStatusRequest(BaseModel):
    lifecycle_status: BusinessLifecycle


class UniverseCaseLinkRequest(BaseModel):
    case_id: str = Field(min_length=1)


class FinancialRequest(BaseModel):
    units_sold: Decimal = Field(ge=0)
    selling_price: Decimal = Field(ge=0)
    direct_cogs: Decimal = Field(ge=0)
    reserve_rate: Decimal = Field(ge=0, le=1)
    operating_expenses: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    base_currency: str = Field(default="ETB", min_length=3, max_length=3)
    presentation_currency: str | None = Field(default=None, min_length=3, max_length=3)
    fx_as_of: str | None = Field(default=None, min_length=1)


class FxRateRequest(BaseModel):
    from_currency: str = Field(min_length=3, max_length=3)
    to_currency: str = Field(min_length=3, max_length=3)
    rate: Decimal = Field(gt=0)
    as_of: str = Field(min_length=1)
    source: str = Field(min_length=1)


class AssumptionRequest(BaseModel):
    key: str = Field(min_length=1)
    value: Decimal
    unit: str = Field(min_length=1)
    evidence_class: EvidenceClass
    source: str | None = None
    editable: bool = True


class BusinessCaseRequest(BaseModel):
    case_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    base_currency: str = Field(min_length=3, max_length=3)
    currency_name: str = "Currency"
    assumptions: list[AssumptionRequest] = Field(default_factory=list)


class SimulationRequest(BaseModel):
    scenario_id: str | None = Field(default=None, min_length=1)
    scenario_name: str = "Scenario"
    overrides: dict[str, Decimal] = Field(default_factory=dict)
    presentation_currency: str | None = Field(default=None, min_length=3, max_length=3)
    fx_as_of: str | None = Field(default=None, min_length=1)


class SensitivityRequest(BaseModel):
    variable: str = Field(min_length=1)
    values: list[Decimal] = Field(min_length=1, max_length=100)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return (Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "engine": "techa"}


@app.post("/v1/gbl/universe")
def save_universe_item(req: UniverseItemRequest):
    try:
        if _store.get_universe_item(req.business_id) is not None:
            raise HTTPException(status_code=409, detail="Business universe item already exists")
        item = BusinessUniverseItem(
            business_id=req.business_id, name=req.name, sector=req.sector,
            geography=req.geography,
        )
        _store.save_universe_item(item)
        return jsonable(item)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/v1/gbl/universe")
def list_universe_items(lifecycle_status: BusinessLifecycle | None = None):
    items = _store.list_universe_items(lifecycle_status.value if lifecycle_status else None)
    return {"count": len(items), "items": jsonable(items)}


@app.get("/v1/gbl/universe/{business_id}")
def get_universe_item(business_id: str):
    item = _store.get_universe_item(business_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Business universe item not found")
    return jsonable(item)


@app.post("/v1/gbl/universe/{business_id}/intake")
def intake_business_case(business_id: str, req: BusinessIntakeRequest):
    item = _store.get_universe_item(business_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Business universe item not found")
    if item.lifecycle_status is not BusinessLifecycle.UNIVERSE:
        raise HTTPException(status_code=409, detail="Business must be in UNIVERSE state before intake")
    if item.active_case_id is not None:
        raise HTTPException(status_code=409, detail="Business already has an active case")
    if _store.get_business_case(req.case_id) is not None:
        raise HTTPException(status_code=409, detail="Business case already exists")
    candidate = BusinessLifecycleService.transition(item, BusinessLifecycle.CANDIDATE)
    ingested = BusinessLifecycleService.transition(candidate, BusinessLifecycle.INGESTED)
    case = BusinessCase(req.case_id, item.name, Currency(req.base_currency, req.base_currency), {})
    _store.save_business_case(case)
    linked = BusinessUniverseItem(
        business_id=ingested.business_id, name=ingested.name, sector=ingested.sector,
        geography=ingested.geography, lifecycle_status=ingested.lifecycle_status,
        active_case_id=req.case_id,
    )
    _store.save_universe_item(linked)
    _store.save_audit_record(AuditRecord.create(
        event="gbl.business.intake", case_id=req.case_id, engine_version="0.1.0",
        inputs={"business_id": business_id, "from": item.lifecycle_status.value,
                "through": [candidate.lifecycle_status.value, ingested.lifecycle_status.value],
                "base_currency": req.base_currency.upper()},
        outputs={"case_id": req.case_id, "lifecycle_status": ingested.lifecycle_status.value},
    ))
    return {"business": jsonable(linked), "case": jsonable(case)}


@app.post("/v1/gbl/universe/{business_id}/instantiate")
def instantiate_universe_case(business_id: str, req: UniverseCaseLinkRequest):
    item = _store.get_universe_item(business_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Business universe item not found")
    case = _store.get_business_case(req.case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    if item.active_case_id is not None and item.active_case_id != req.case_id:
        raise HTTPException(status_code=409, detail="Business already has a different active case")
    if case.name != item.name:
        raise HTTPException(status_code=409, detail="Business case name does not match universe item")
    updated = BusinessUniverseItem(
        business_id=item.business_id, name=item.name, sector=item.sector,
        geography=item.geography, lifecycle_status=BusinessLifecycle.INGESTED,
        active_case_id=req.case_id,
    )
    _store.save_universe_item(updated)
    return jsonable(updated)


@app.patch("/v1/gbl/universe/{business_id}/lifecycle")
def update_universe_lifecycle(business_id: str, req: UniverseStatusRequest):
    item = _store.get_universe_item(business_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Business universe item not found")
    try:
        updated = BusinessLifecycleService.transition(item, req.lifecycle_status)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _store.save_universe_item(updated)
    _store.save_audit_record(AuditRecord.create(
        event="gbl.lifecycle.transition",
        case_id=item.active_case_id or item.business_id,
        engine_version="0.1.0",
        inputs={"business_id": item.business_id, "from": item.lifecycle_status.value, "to": req.lifecycle_status.value},
        outputs={"lifecycle_status": req.lifecycle_status.value},
    ))
    return jsonable(updated)


@app.post("/v1/fx-rates")
def save_fx_rate(req: FxRateRequest):
    try:
        fx = FxRate(req.from_currency, req.to_currency, req.rate, req.as_of, req.source)
        _store.save_fx_rate(fx)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return jsonable(fx)


@app.get("/v1/fx-rates/{from_currency}/{to_currency}")
def get_fx_rate(from_currency: str, to_currency: str, as_of: str):
    fx = _store.get_fx_rate(from_currency, to_currency, as_of)
    if fx is None:
        raise HTTPException(status_code=404, detail="FX rate not found for exact currency pair and as-of date")
    return jsonable(fx)


@app.post("/v1/financial/calculate")
def calculate(req: FinancialRequest):
    try:
        result = FinancialEngine.calculate(FinancialInputs(
            units_sold=req.units_sold,
            selling_price=req.selling_price,
            direct_cogs=req.direct_cogs,
            reserve_rate=req.reserve_rate,
            operating_expenses=req.operating_expenses,
            tax_rate=req.tax_rate,
        ))
        base_currency = req.base_currency.upper()
        presentation_currency = (req.presentation_currency or base_currency).upper()
        response = {"financial": result, **{k: str(v) for k, v in result.__dict__.items()}}
        if presentation_currency != base_currency:
            if not req.fx_as_of:
                raise ValueError("fx_as_of is required when presentation currency differs from base currency")

            fx = _store.get_fx_rate(base_currency, presentation_currency, req.fx_as_of)
            fx_direction = "direct"
            if fx is None:
                fx = _store.get_fx_rate(presentation_currency, base_currency, req.fx_as_of)
                fx_direction = "inverse" if fx is not None else "unavailable"
            if fx is None:
                raise ValueError(
                    f"No stored FX rate for {base_currency}->{presentation_currency} "
                    f"(direct or inverse) as_of={req.fx_as_of}"
                )

            converter = CurrencyConverter({(fx.from_currency, fx.to_currency): fx})
            presented = converter.present_financial_result(result, base_currency, presentation_currency)
            audit = AuditRecord.create(
                event="currency.present",
                case_id="ADHOC",
                engine_version="0.1.0",
                inputs={
                    "base_currency": base_currency,
                    "presentation_currency": presentation_currency,
                    "fx_as_of": fx.as_of,
                    "fx_source": fx.source,
                    "fx_rate": fx.rate,
                    "fx_direction": fx_direction,
                },
                outputs={"financial": result, "presented": presented},
            )
            _store.save_audit_record(audit)
            response.update({
                "presentation": presented,
                "fx": fx,
                "fx_direction": fx_direction,
                "audit_digest": audit.digest(),
            })
        else:
            response["presentation"] = result
        return jsonable(response)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class EvidenceUpdateRequest(BaseModel):
    evidence_class: EvidenceClass
    source: str | None = None


@app.post("/v1/business-cases")
def create_business_case(req: BusinessCaseRequest):
    assumptions = {}
    for item in req.assumptions:
        if item.key in assumptions:
            raise HTTPException(status_code=400, detail="Duplicate assumption keys")
        assumptions[item.key] = Assumption(
            key=item.key, value=item.value, unit=item.unit,
            evidence_class=item.evidence_class, source=item.source,
            editable=item.editable,
        )
    case = BusinessCase(
        case_id=req.case_id,
        name=req.name,
        base_currency=Currency(req.base_currency, req.currency_name),
        assumptions=assumptions,
    )
    _store.save_business_case(case)
    return jsonable(case)


@app.get("/v1/business-cases/{case_id}")
def get_business_case(case_id: str):
    case = _store.get_business_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    return jsonable(case)


@app.patch("/v1/business-cases/{case_id}/assumptions/{key}/evidence")
def update_assumption_evidence(case_id: str, key: str, req: EvidenceUpdateRequest):
    case = _store.get_business_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    assumption = case.assumptions.get(key)
    if assumption is None:
        raise HTTPException(status_code=404, detail="Assumption not found")
    updated = Assumption(
        key=assumption.key,
        value=assumption.value,
        unit=assumption.unit,
        evidence_class=req.evidence_class,
        source=req.source,
        editable=assumption.editable,
    )
    assumptions = dict(case.assumptions)
    assumptions[key] = updated
    updated_case = BusinessCase(case.case_id, case.name, case.base_currency, assumptions)
    _store.save_business_case(updated_case)
    audit = AuditRecord.create(
        event="evidence.reclassified",
        case_id=case.case_id,
        engine_version="0.1.0",
        inputs={
            "assumption_key": key,
            "old_evidence_class": assumption.evidence_class.value,
            "old_source": assumption.source,
        },
        outputs={
            "new_evidence_class": updated.evidence_class.value,
            "new_source": updated.source,
        },
    )
    _store.save_audit_record(audit)
    return jsonable({"business_case": updated_case, "audit_digest": audit.digest()})


@app.get("/v1/business-cases/{case_id}/evidence")
def get_business_case_evidence(case_id: str):
    case = _store.get_business_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    items = []
    for assumption in case.assumptions.values():
        blocking = assumption.evidence_class in {
            EvidenceClass.REQUIRES_PRIMARY_VERIFICATION,
            EvidenceClass.FIELD_VALIDATION_REQUIREMENTS,
        }
        items.append({
            "key": assumption.key,
            "claim": f"{assumption.key} = {assumption.value} {assumption.unit}",
            "value": assumption.value,
            "unit": assumption.unit,
            "evidence_class": assumption.evidence_class,
            "source": assumption.source,
            "editable": assumption.editable,
            "requires_primary_verification": blocking,
            "blocking": blocking,
            "executable": not blocking,
        })
    return {
        "case_id": case_id,
        "items": items,
        "blocking_items": [item["key"] for item in items if not item["executable"]],
        "can_execute": not any(not item["executable"] for item in items),
    }


@app.get("/v1/business-cases/{case_id}/audit")
def get_business_case_audit(case_id: str, limit: int = 100):
    if _store.get_business_case(case_id) is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    try:
        return {"case_id": case_id, "records": _store.get_audit_records(case_id, limit)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/v1/business-cases/{case_id}/audit/integrity")
def verify_business_case_audit_integrity(case_id: str, limit: int = 100):
    if _store.get_business_case(case_id) is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    try:
        return _store.verify_audit_integrity(case_id, limit)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/v1/business-cases/{case_id}/sensitivity")
def run_sensitivity(case_id: str, req: SensitivityRequest):
    case = _store.get_business_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    missing = [
        key for key in SimulationService.REQUIRED_FINANCIAL_KEYS
        if key not in case.assumptions
    ]
    if missing:
        raise HTTPException(
            status_code=422,
            detail={"message": "Business case is missing financial assumptions", "missing": missing},
        )
    try:
        result = _sensitivity.execute(case, req.variable, req.values)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return jsonable({
        "case_id": result.case_id,
        "variable": result.variable,
        "points": result.points,
        "audit": result.audit,
        "audit_digest": result.audit.digest(),
    })


@app.post("/v1/business-cases/{case_id}/simulate")
def simulate_business_case(case_id: str, req: SimulationRequest):
    case = _store.get_business_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    missing = [
        key for key in SimulationService.REQUIRED_FINANCIAL_KEYS
        if key not in case.assumptions
    ]
    if missing:
        raise HTTPException(
            status_code=422,
            detail={"message": "Business case is missing financial assumptions", "missing": missing},
        )
    scenario = None
    if req.scenario_id:
        scenario = Scenario(req.scenario_id, req.scenario_name, req.overrides)
    try:
        evidence = EvidenceRegistry()
        for assumption in case.assumptions.values():
            evidence.add(EvidenceItem(
                evidence_id=assumption.key,
                claim=f"{assumption.key} = {assumption.value} {assumption.unit}",
                evidence_class=assumption.evidence_class,
                source=assumption.source,
            ))
        readiness = ExecutionReadinessService.assess(evidence)
        if not readiness.can_execute:
            raise HTTPException(status_code=409, detail={
                "message": "Simulation execution is blocked by evidence requirements",
                "status": readiness.status,
                "blocking_items": list(readiness.blocking_items),
            })
        result = _simulation.execute(case, scenario, evidence=evidence)
        response = {
            "case_id": result.case_id,
            "scenario_id": result.scenario_id,
            "financial": result.financial,
            "audit": result.audit,
            "audit_digest": result.audit.digest(),
        }
        presentation_currency = (req.presentation_currency or case.base_currency.code).upper()
        base_currency = case.base_currency.code.upper()
        if presentation_currency != base_currency:
            if not req.fx_as_of:
                raise ValueError("fx_as_of is required when presentation currency differs from base currency")
            fx = _store.get_fx_rate(base_currency, presentation_currency, req.fx_as_of)
            fx_direction = "direct"
            if fx is None:
                fx = _store.get_fx_rate(presentation_currency, base_currency, req.fx_as_of)
                fx_direction = "inverse" if fx is not None else "unavailable"
            if fx is None:
                raise ValueError(
                    f"No stored FX rate for {base_currency}->{presentation_currency} "
                    f"(direct or inverse) as_of={req.fx_as_of}"
                )
            presented = CurrencyConverter(
                {(fx.from_currency, fx.to_currency): fx}
            ).present_financial_result(result.financial, base_currency, presentation_currency)
            currency_audit = AuditRecord.create(
                event="currency.present",
                case_id=case.case_id,
                engine_version="0.1.0",
                inputs={
                    "base_currency": base_currency,
                    "presentation_currency": presentation_currency,
                    "fx_as_of": fx.as_of,
                    "fx_source": fx.source,
                    "fx_rate": fx.rate,
                    "fx_direction": fx_direction,
                    "scenario_id": result.scenario_id,
                },
                outputs={"financial": result.financial, "presented": presented},
            )
            _store.save_audit_record(currency_audit)
            response.update({
                "presentation": presented,
                "fx": fx,
                "fx_direction": fx_direction,
                "presentation_audit_digest": currency_audit.digest(),
            })
        else:
            response["presentation"] = result.financial
        return jsonable(response)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


from techa.integration.gbl import GBLCase, GBLCaseValidationError, export_gbl_case, import_gbl_case


class GBLCaseImportRequest(BaseModel):
    contract_version: str
    business: dict
    governance: dict
    currency: dict
    assumptions: list[dict]
    scenarios: list[dict]
    source_results: list[dict]


@app.post("/v1/gbl/import")
def import_gbl_case_endpoint(req: GBLCaseImportRequest):
    try:
        imported = import_gbl_case(req.model_dump())
        _store.save_business_case(imported.business_case)
        _store.save_gbl_case_metadata(
            imported.business_case.case_id,
            req.contract_version,
            dict(imported.business_metadata),
            dict(imported.governance),
            imported.presentation_currency,
            imported.fx_as_of,
            imported.fx_source,
            list(imported.scenarios),
            list(imported.source_results),
        )
        audit = AuditRecord.create(
            event="gbl.case_imported",
            case_id=imported.business_case.case_id,
            engine_version="0.1.0",
            inputs={
                "contract_version": req.contract_version,
                "governance": imported.governance,
                "presentation_currency": imported.presentation_currency,
                "source_result_ids": [r.result_id for r in imported.source_results],
            },
            outputs={
                "business_id": imported.business_case.case_id,
                "assumption_count": len(imported.business_case.assumptions),
                "scenario_count": len(imported.scenarios),
            },
        )
        _store.save_audit_record(audit)
        return jsonable({
            "case_id": imported.business_case.case_id,
            "business_case": imported.business_case,
            "governance": imported.governance,
            "presentation_currency": imported.presentation_currency,
            "fx_as_of": imported.fx_as_of,
            "fx_source": imported.fx_source,
            "scenarios": imported.scenarios,
            "source_results": imported.source_results,
            "audit_digest": audit.digest(),
        })
    except GBLCaseValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/v1/gbl/cases")
def list_gbl_cases():
    items = _store.list_universe_items()
    cases = []
    for item in items:
        if item.active_case_id:
            metadata = _store.get_gbl_case_metadata(item.active_case_id)
            cases.append({
                "business_id": item.business_id,
                "name": item.name,
                "sector": item.sector,
                "geography": item.geography,
                "lifecycle_status": item.lifecycle_status.value,
                "case_id": item.active_case_id,
                "governance": metadata["governance"] if metadata else {},
            })
    return jsonable({"cases": cases})


@app.get("/v1/gbl/cases/{case_id}/summary")
def get_gbl_case_summary(case_id: str):
    case = _store.get_business_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    metadata = _store.get_gbl_case_metadata(case_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="GBL metadata not found")

    blocking_items = [
        assumption.key
        for assumption in case.assumptions.values()
        if assumption.evidence_class in {
            EvidenceClass.REQUIRES_PRIMARY_VERIFICATION,
            EvidenceClass.FIELD_VALIDATION_REQUIREMENTS,
        }
    ]
    evidence = EvidenceRegistry()
    for assumption in case.assumptions.values():
        evidence.add(EvidenceItem(
            evidence_id=assumption.key,
            claim=f"{assumption.key} = {assumption.value} {assumption.unit}",
            evidence_class=assumption.evidence_class,
            source=assumption.source,
        ))
    readiness = ExecutionReadinessService.assess(evidence)
    scenarios = list(metadata["scenarios"])
    source_results = list(metadata["source_results"])
    governance = dict(metadata["governance"])
    return jsonable({
        "case_id": case_id,
        "business": dict(metadata["business_metadata"]),
        "governance": governance,
        "currency": {
            "base_currency": case.base_currency.code,
            "presentation_currency": metadata["presentation_currency"],
            "fx_as_of": metadata["fx_as_of"],
            "fx_source": metadata["fx_source"],
        },
        "counts": {
            "assumptions": len(case.assumptions),
            "blocking_evidence": len(blocking_items),
            "scenarios": len(scenarios),
            "source_results": len(source_results),
        },
        "execution_readiness": {
            "status": readiness.status,
            "can_execute": readiness.can_execute,
            "blocking_assumptions": list(readiness.blocking_items),
            "investment_clearance": governance.get("human_gate") != "HOLD / NOT CLEARED",
        },
        "scenarios": scenarios,
        "source_results": source_results,
    })


@app.get("/v1/gbl/cases/{case_id}/scenarios")
def get_gbl_case_scenarios(case_id: str):
    if _store.get_business_case(case_id) is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    metadata = _store.get_gbl_case_metadata(case_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="GBL metadata not found")
    return jsonable({"case_id": case_id, "scenarios": metadata["scenarios"]})


@app.get("/v1/gbl/cases/{case_id}/evidence")
def get_gbl_case_evidence(case_id: str):
    if _store.get_business_case(case_id) is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    metadata = _store.get_gbl_case_metadata(case_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="GBL metadata not found")
    case = _store.get_business_case(case_id)
    items = []
    for assumption in case.assumptions.values():
        blocking = assumption.evidence_class in {
            EvidenceClass.REQUIRES_PRIMARY_VERIFICATION,
            EvidenceClass.FIELD_VALIDATION_REQUIREMENTS,
        }
        items.append({
            "key": assumption.key,
            "value": assumption.value,
            "unit": assumption.unit,
            "evidence_class": assumption.evidence_class,
            "source": assumption.source,
            "editable": assumption.editable,
            "blocking": blocking,
            "executable": not blocking,
        })
    return jsonable({
        "case_id": case_id,
        "items": items,
        "blocking_items": [i["key"] for i in items if i["blocking"]],
        "can_execute": not any(i["blocking"] for i in items),
    })


@app.get("/v1/gbl/cases/{case_id}/results-reconciliation")
def get_gbl_results_reconciliation(case_id: str):
    if _store.get_business_case(case_id) is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    metadata = _store.get_gbl_case_metadata(case_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="GBL metadata not found")
    audits = _store.get_audit_records(case_id, 100)
    simulation_events = [r for r in audits if r.get("event") in {"simulation.execute", "gbl.case_imported"}]
    return jsonable({
        "case_id": case_id,
        "techa_calculation": {
            "available": any(r.get("event") == "simulation.execute" for r in audits),
            "audit_events": simulation_events,
        },
        "gbl_source_results": list(metadata["source_results"]),
        "reconciliation": {
            "source_result_count": len(metadata["source_results"]),
            "source_result_ids": [r["result_id"] for r in metadata["source_results"]],
            "authoritative_results_preserved": True,
            "not_silently_overwritten": True,
        },
    })


@app.get("/v1/gbl/cases/{case_id}/source-results")
def get_gbl_case_source_results(case_id: str):
    if _store.get_business_case(case_id) is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    metadata = _store.get_gbl_case_metadata(case_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="GBL metadata not found")
    return jsonable({
        "case_id": case_id,
        "source_results": metadata["source_results"],
        "reconciliation": {
            "count": len(metadata["source_results"]),
            "result_ids": [r["result_id"] for r in metadata["source_results"]],
            "authoritative_results_preserved": True,
        },
    })


@app.get("/v1/gbl/cases/{case_id}")
def get_gbl_case_metadata(case_id: str):
    if _store.get_business_case(case_id) is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    metadata = _store.get_gbl_case_metadata(case_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="GBL metadata not found")
    return jsonable({"case_id": case_id, **metadata})


@app.get("/v1/gbl/cases/{case_id}/export")
def export_gbl_case_endpoint(case_id: str):
    business_case = _store.get_business_case(case_id)
    if business_case is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    metadata = _store.get_gbl_case_metadata(case_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="GBL metadata not found")
    source_results = tuple(
        __import__("techa.integration.gbl", fromlist=["GBLSourceResult"]).GBLSourceResult(**item)
        for item in metadata["source_results"]
    )
    gbl_case = GBLCase(
        business_case=business_case,
        business_metadata=metadata["business_metadata"],
        governance=metadata["governance"],
        presentation_currency=metadata["presentation_currency"],
        fx_as_of=metadata["fx_as_of"],
        fx_source=metadata["fx_source"],
        scenarios=tuple(metadata["scenarios"]),
        source_results=source_results,
    )
    payload = export_gbl_case(gbl_case, metadata["contract_version"])
    audit = AuditRecord.create(
        event="gbl.case_exported",
        case_id=case_id,
        engine_version="0.1.0",
        inputs={"contract_version": metadata["contract_version"]},
        outputs={"source_result_ids": [r["result_id"] for r in metadata["source_results"]]},
    )
    _store.save_audit_record(audit)
    return jsonable({"contract": payload, "audit_digest": audit.digest()})
