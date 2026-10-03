from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class FinancialInputs:
    units_sold: Decimal
    selling_price: Decimal
    direct_cogs: Decimal
    reserve_rate: Decimal
    operating_expenses: Decimal
    tax_rate: Decimal = Decimal("0")


@dataclass(frozen=True)
class FinancialResult:
    revenue: Decimal
    direct_cogs: Decimal
    reserve: Decimal
    total_cogs_and_reserve: Decimal
    operating_expenses: Decimal
    operating_profit: Decimal
    tax: Decimal
    net_profit: Decimal


class FinancialEngine:
    """Deterministic base-currency financial calculation engine."""

    @staticmethod
    def calculate(inputs: FinancialInputs) -> FinancialResult:
        for name in ("units_sold", "selling_price", "direct_cogs", "reserve_rate", "operating_expenses", "tax_rate"):
            if getattr(inputs, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        if inputs.reserve_rate > 1 or inputs.tax_rate > 1:
            raise ValueError("Rates must be expressed as decimals between 0 and 1")

        revenue = money(inputs.units_sold * inputs.selling_price)
        reserve = money(inputs.direct_cogs * inputs.reserve_rate)
        total = money(inputs.direct_cogs + reserve)
        operating_profit = money(revenue - total - inputs.operating_expenses)
        tax = money(max(Decimal("0"), operating_profit) * inputs.tax_rate)
        net = money(operating_profit - tax)

        return FinancialResult(
            revenue=revenue,
            direct_cogs=money(inputs.direct_cogs),
            reserve=reserve,
            total_cogs_and_reserve=total,
            operating_expenses=money(inputs.operating_expenses),
            operating_profit=operating_profit,
            tax=tax,
            net_profit=net,
        )
