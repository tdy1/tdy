from decimal import Decimal

from techa.core.models import FxRate
from techa.financial.currency import CurrencyConverter


def test_currency_conversion_requires_explicit_rate() -> None:
    converter = CurrencyConverter()
    converter.add_rate(
        FxRate(
            from_currency="ETB",
            to_currency="USD",
            rate=Decimal("0.006"),
            as_of="2026-10-03",
            source="test",
        )
    )

    assert converter.convert(Decimal("1000"), "ETB", "USD") == Decimal("6.000")


def test_inverse_rate_is_supported() -> None:
    converter = CurrencyConverter()
    converter.add_rate(
        FxRate(
            from_currency="USD",
            to_currency="ETB",
            rate=Decimal("160"),
            as_of="2026-10-03",
            source="test",
        )
    )

    assert converter.convert(Decimal("160"), "ETB", "USD") == Decimal("1")


def test_financial_result_can_be_presented_in_explicit_currency():
    converter = CurrencyConverter()
    converter.add_rate(FxRate("ETB", "USD", Decimal("0.006"), "2026-10-03", "test"))
    from techa.financial.engine import FinancialEngine, FinancialInputs
    result = FinancialEngine.calculate(FinancialInputs(
        units_sold=Decimal("100"), selling_price=Decimal("50"),
        direct_cogs=Decimal("3000"), reserve_rate=Decimal("0.20"),
        operating_expenses=Decimal("1000"), tax_rate=Decimal("0.30"),
    ))
    presented = converter.present_financial_result(result, "ETB", "USD")
    assert presented.currency == "USD"
    assert presented.revenue == Decimal("30.0000")
    assert presented.net_profit == Decimal("1.6800")
