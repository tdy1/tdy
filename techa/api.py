from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from techa.core.models import Assumption, BusinessCase, Currency, EvidenceClass, FxRate
from techa.core.scenario import Scenario
from techa.core.serialization import jsonable
from techa.core.simulation import SimulationService
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


class SensitivityRequest(BaseModel):
    variable: str = Field(min_length=1)
    values: list[Decimal] = Field(min_length=1, max_length=100)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return (Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "engine": "techa"}


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
