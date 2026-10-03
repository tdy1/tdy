from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from techa.financial.engine import money

@dataclass(frozen=True)
class PeriodInputs:
    revenue: Decimal
    direct_cogs: Decimal
    reserve_rate: Decimal
    operating_expenses: Decimal
    tax_rate: Decimal = Decimal("0")
    capex: Decimal = Decimal("0")
    depreciation: Decimal = Decimal("0")
    accounts_receivable: Decimal = Decimal("0")
    inventory: Decimal = Decimal("0")
    accounts_payable: Decimal = Decimal("0")
    debt_draw: Decimal = Decimal("0")
    debt_principal: Decimal = Decimal("0")
    interest: Decimal = Decimal("0")
    equity_injection: Decimal = Decimal("0")

@dataclass(frozen=True)
class PeriodResult:
    revenue: Decimal
    reserve: Decimal
    ebitda: Decimal
    depreciation: Decimal
    ebit: Decimal
    interest: Decimal
    profit_before_tax: Decimal
    tax: Decimal
    net_income: Decimal
    operating_cash_flow: Decimal
    investing_cash_flow: Decimal
    financing_cash_flow: Decimal
    net_cash_flow: Decimal
    ending_working_capital: Decimal

class CashFlowEngine:
    @staticmethod
    def calculate(i: PeriodInputs, opening_working_capital: Decimal = Decimal("0")) -> PeriodResult:
        reserve=money(i.direct_cogs*i.reserve_rate)
        ebitda=money(i.revenue-i.direct_cogs-reserve-i.operating_expenses)
        ebit=money(ebitda-i.depreciation)
        pbt=money(ebit-i.interest)
        tax=money(max(Decimal("0"),pbt)*i.tax_rate)
        net=money(pbt-tax)
        nwc=money(i.accounts_receivable+i.inventory-i.accounts_payable)
        delta_nwc=money(nwc-opening_working_capital)
        ocf=money(net+i.depreciation-delta_nwc)
        icf=money(-i.capex)
        fcf=money(i.debt_draw-i.debt_principal+i.equity_injection-i.interest)
        return PeriodResult(i.revenue,reserve,ebitda,i.depreciation,ebit,i.interest,pbt,tax,net,ocf,icf,fcf,money(ocf+icf+fcf),nwc)
