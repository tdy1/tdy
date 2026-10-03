from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Mapping


class EvidenceClass(str, Enum):
    VERIFIED_FACT = "VERIFIED_FACT"
    INDICATIVE_OBSERVED_DATA = "INDICATIVE_OBSERVED_DATA"
    COST_ENGINEERING_ESTIMATE = "COST_ENGINEERING_ESTIMATE"
    MARKET_ASSUMPTION = "MARKET_ASSUMPTION"
    ANALYTICAL_CONCLUSION = "ANALYTICAL_CONCLUSION"
    REQUIRES_PRIMARY_VERIFICATION = "REQUIRES_PRIMARY_VERIFICATION"
    FIELD_VALIDATION_REQUIREMENTS = "FIELD_VALIDATION_REQUIREMENTS"


@dataclass(frozen=True)
class Assumption:
    key: str
    value: Decimal
    unit: str
    evidence_class: EvidenceClass
    source: str | None = None
    editable: bool = True

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("Assumption key cannot be empty")
        if not self.unit.strip():
            raise ValueError("Assumption unit cannot be empty")


@dataclass(frozen=True)
class Currency:
    code: str
    name: str

    def __post_init__(self) -> None:
        code = self.code.upper()
        if len(code) != 3 or not code.isalpha():
            raise ValueError("Currency code must be a three-letter ISO-style code")
        object.__setattr__(self, "code", code)


@dataclass(frozen=True)
class FxRate:
    from_currency: str
    to_currency: str
    rate: Decimal
    as_of: str
    source: str

    def __post_init__(self) -> None:
        if self.rate <= 0:
            raise ValueError("FX rate must be positive")


@dataclass(frozen=True)
class BusinessCase:
    case_id: str
    name: str
    base_currency: Currency
    assumptions: Mapping[str, Assumption] = field(default_factory=dict)

    def assumption(self, key: str) -> Assumption:
        try:
            return self.assumptions[key]
        except KeyError as exc:
            raise KeyError(f"Unknown assumption: {key}") from exc
