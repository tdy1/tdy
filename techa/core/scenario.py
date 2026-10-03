from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    name: str
    overrides: Mapping[str, Decimal]

    def apply(self, base: Mapping[str, Decimal]) -> dict[str, Decimal]:
        result = dict(base)
        for key, value in self.overrides.items():
            result[key] = value
        return result


@dataclass(frozen=True)
class SensitivityPoint:
    variable: str
    value: Decimal


def one_way_sensitivity(
    base: Mapping[str, Decimal],
    variable: str,
    values: list[Decimal],
) -> list[SensitivityPoint]:
    if variable not in base:
        raise KeyError(f"Unknown sensitivity variable: {variable}")
    return [SensitivityPoint(variable=variable, value=value) for value in values]
