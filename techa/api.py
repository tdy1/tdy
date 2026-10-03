from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from techa.core.models import Assumption, BusinessCase, Currency, EvidenceClass
from techa.core.scenario import Scenario
from techa.core.serialization import jsonable
from techa.core.simulation import SimulationService
from techa.core.sensitivity_service import SensitivityService
from techa.financial.engine import FinancialEngine, FinancialInputs
from techa.storage.repository import SQLiteStore

app = FastAPI(title="TECHA Engine", version="0.1.0")
_store = SQLiteStore(Path("techa.db"))
_store.initialize(Path(__file__).parent / "storage" / "schema.sql")
_simulation = SimulationService(_store)
_sensitivity = SensitivityService(_simulation, _store)


class FinancialRequest(BaseModel):
    units_sold: Decimal = Field(ge=0)
    selling_price: Decimal = Field(ge=0)
    direct_cogs: Decimal = Field(ge=0)
    reserve_rate: Decimal = Field(ge=0, le=1)
    operating_expenses: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)


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


class SensitivityRequest(BaseModel):
    variable: str = Field(min_length=1)
    values: list[Decimal] = Field(min_length=1, max_length=100)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return (Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "engine": "techa"}


@app.post("/v1/financial/calculate")
def calculate(req: FinancialRequest) -> dict[str, str]:
    try:
        result = FinancialEngine.calculate(FinancialInputs(**req.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {k: str(v) for k, v in result.__dict__.items()}


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


@app.get("/v1/business-cases/{case_id}/audit")
def get_business_case_audit(case_id: str, limit: int = 100):
    if _store.get_business_case(case_id) is None:
        raise HTTPException(status_code=404, detail="Business case not found")
    try:
        return {"case_id": case_id, "records": _store.get_audit_records(case_id, limit)}
    except ValueError as exc:
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
        result = _simulation.execute(case, scenario)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return jsonable({
        "case_id": result.case_id,
        "scenario_id": result.scenario_id,
        "financial": result.financial,
        "audit": result.audit,
        "audit_digest": result.audit.digest(),
    })
