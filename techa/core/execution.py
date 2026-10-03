from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Mapping

@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    outputs: Mapping[str, Decimal]

class ScenarioExecutor:
    def __init__(self, calculator: Callable[[Mapping[str,Decimal]], Mapping[str,Decimal]]) -> None:
        self.calculator=calculator
    def run(self, base: Mapping[str,Decimal], scenarios: list[tuple[str,Mapping[str,Decimal]]]) -> list[ScenarioResult]:
        results=[]
        for scenario_id,overrides in scenarios:
            values=dict(base); values.update(overrides)
            results.append(ScenarioResult(scenario_id,self.calculator(values)))
        return results
