from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from techa.core.models import FxRate
from techa.financial.engine import FinancialResult


@dataclass(frozen=True)
class PresentedFinancialResult:
    currency: str
    revenue: Decimal
    direct_cogs: Decimal
    reserve: Decimal
    total_cogs_and_reserve: Decimal
    operating_expenses: Decimal
    operating_profit: Decimal
    tax: Decimal
    net_profit: Decimal


class CurrencyConverter:
    """Explicit FX conversion; no implicit currency mixing."""

    def __init__(self, rates: dict[tuple[str, str], FxRate] | None = None) -> None:
        self._rates = dict(rates or {})

    def add_rate(self, rate: FxRate) -> None:
        self._rates[(rate.from_currency.upper(), rate.to_currency.upper())] = rate

    def convert(self, amount: Decimal, from_code: str, to_code: str) -> Decimal:
        source = from_code.upper()
        target = to_code.upper()
        if source == target:
            return amount
        direct = self._rates.get((source, target))
        if direct is not None:
            return amount * direct.rate
        inverse = self._rates.get((target, source))
        if inverse is not None:
            return amount / inverse.rate
        raise ValueError(f"No explicit FX rate available for {source}->{target}")

    def present_financial_result(
        self,
        result: FinancialResult,
        base_currency: str,
        presentation_currency: str,
    ) -> PresentedFinancialResult:
        fields = (
            "revenue", "direct_cogs", "reserve", "total_cogs_and_reserve",
            "operating_expenses", "operating_profit", "tax", "net_profit",
        )
        converted = {
            field: self.convert(getattr(result, field), base_currency, presentation_currency)
            for field in fields
        }
        return PresentedFinancialResult(currency=presentation_currency.upper(), **converted)
