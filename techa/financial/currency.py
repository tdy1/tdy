from __future__ import annotations

from decimal import Decimal
from typing import Mapping

from techa.core.models import FxRate


class CurrencyConverter:
    """Explicit FX conversion; no implicit currency mixing."""

    def __init__(self, rates: Mapping[tuple[str, str], FxRate] | None = None) -> None:
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
