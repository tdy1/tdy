from decimal import Decimal

from techa.financial.engine import FinancialEngine, FinancialInputs


def test_financial_engine_includes_reserve_and_tax() -> None:
    result = FinancialEngine.calculate(
        FinancialInputs(
            units_sold=Decimal("100"),
            selling_price=Decimal("50"),
            direct_cogs=Decimal("3000"),
            reserve_rate=Decimal("0.20"),
            operating_expenses=Decimal("1000"),
            tax_rate=Decimal("0.30"),
        )
    )

    assert result.revenue == Decimal("5000.00")
    assert result.reserve == Decimal("600.00")
    assert result.total_cogs_and_reserve == Decimal("3600.00")
    assert result.operating_profit == Decimal("400.00")
    assert result.tax == Decimal("120.00")
    assert result.net_profit == Decimal("280.00")


def test_no_tax_on_operating_loss() -> None:
    result = FinancialEngine.calculate(
        FinancialInputs(
            units_sold=Decimal("10"),
            selling_price=Decimal("10"),
            direct_cogs=Decimal("200"),
            reserve_rate=Decimal("0"),
            operating_expenses=Decimal("100"),
            tax_rate=Decimal("0.30"),
        )
    )
    assert result.operating_profit == Decimal("-200.00")
    assert result.tax == Decimal("0.00")
