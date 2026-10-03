from decimal import Decimal
from techa.financial.debt import DebtEngine, DebtTerms

def test_debt_amortizes():
    rows=DebtEngine.schedule(DebtTerms(Decimal("1200"),Decimal("0.12"),12))
    assert rows[-1].closing_balance==Decimal("0.00")
    assert sum((r.interest for r in rows),Decimal())>0
