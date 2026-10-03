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
