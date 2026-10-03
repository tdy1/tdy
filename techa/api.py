from __future__ import annotations
from decimal import Decimal
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from techa.financial.engine import FinancialEngine, FinancialInputs

app=FastAPI(title="TECHA Engine", version="0.1.0")

class FinancialRequest(BaseModel):
    units_sold: Decimal = Field(ge=0)
    selling_price: Decimal = Field(ge=0)
    direct_cogs: Decimal = Field(ge=0)
    reserve_rate: Decimal = Field(ge=0, le=1)
    operating_expenses: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)

@app.get("/", response_class=HTMLResponse)
def home()->str:
    return (Path(__file__).parent/"web"/"index.html").read_text(encoding="utf-8")

@app.get("/health")
def health()->dict[str,str]:
    return {"status":"ok","engine":"techa"}

@app.post("/v1/financial/calculate")
def calculate(req:FinancialRequest)->dict[str,str]:
    try:
        r=FinancialEngine.calculate(FinancialInputs(**req.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=422,detail=str(exc)) from exc
    return {k:str(v) for k,v in r.__dict__.items()}
