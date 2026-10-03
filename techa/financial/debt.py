from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from techa.financial.engine import money

@dataclass(frozen=True)
class DebtTerms:
    principal: Decimal
    annual_rate: Decimal
    periods: int
    frequency_per_year: int = 12
    interest_only_periods: int = 0

@dataclass(frozen=True)
class DebtPeriod:
    period: int
    opening_balance: Decimal
    payment: Decimal
    interest: Decimal
    principal: Decimal
    closing_balance: Decimal

class DebtEngine:
    @staticmethod
    def schedule(t: DebtTerms) -> list[DebtPeriod]:
        if t.principal < 0 or t.annual_rate < 0 or t.periods <= 0 or t.frequency_per_year <= 0:
            raise ValueError("Invalid debt terms")
        r=t.annual_rate/Decimal(t.frequency_per_year)
        payment=t.principal/Decimal(t.periods) if r==0 else t.principal*r/(Decimal(1)-(Decimal(1)+r)**Decimal(-t.periods))
        balance=money(t.principal); rows=[]
        for n in range(1,t.periods+1):
            interest=money(balance*r)
            principal=money(Decimal("0") if n<=t.interest_only_periods else min(balance,max(Decimal("0"),payment-interest)))
            pmt=money(interest if n<=t.interest_only_periods else principal+interest)
            closing=money(max(Decimal("0"),balance-principal))
            rows.append(DebtPeriod(n,balance,pmt,interest,principal,closing)); balance=closing
        return rows
