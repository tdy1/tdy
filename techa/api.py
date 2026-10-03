from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from techa.core.models import Assumption, BusinessCase, Currency, EvidenceClass
from techa.core.serialization import jsonable
from techa.financial.engine import FinancialEngine, FinancialInputs
from techa.storage.repository import SQLiteStore

app = FastAPI(title="TECHA Engine", version="0.1.0")
_store = SQLiteStore(Path("techa.db"))
_store.initialize(Path(__file__).parent / "storage" / "schema.sql")


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
