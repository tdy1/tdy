from decimal import Decimal
from techa.financial.cashflow import CashFlowEngine, PeriodInputs

def test_cashflow_includes_working_capital():
    r=CashFlowEngine.calculate(PeriodInputs(
      revenue=Decimal("1000"),direct_cogs=Decimal("400"),reserve_rate=Decimal(".2"),
      operating_expenses=Decimal("200"),tax_rate=Decimal(".3"),
      accounts_receivable=Decimal("100"),inventory=Decimal("50"),accounts_payable=Decimal("25")))
    assert r.ending_working_capital==Decimal("125.00")
    assert r.net_cash_flow==r.operating_cash_flow+r.investing_cash_flow+r.financing_cash_flow
