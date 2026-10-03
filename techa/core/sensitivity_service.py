from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from techa.audit.record import AuditRecord
from techa.core.models import BusinessCase
from techa.core.scenario import Scenario
from techa.core.simulation import SimulationService, SimulationResult
from techa.storage.repository import SQLiteStore


@dataclass(frozen=True)
class SensitivityExecutionResult:
    case_id: str
    variable: str
    points: tuple[SimulationResult, ...]
    audit: AuditRecord


class SensitivityService:
    """Runs a reproducible one-way sensitivity through the frozen financial engine."""

    def __init__(self, simulation: SimulationService, store: SQLiteStore, engine_version: str = "0.1.0") -> None:
        self.simulation = simulation
        self.store = store
        self.engine_version = engine_version

    def execute(
        self,
        case: BusinessCase,
        variable: str,
        values: list[Decimal],
    ) -> SensitivityExecutionResult:
        if variable not in SimulationService.REQUIRED_FINANCIAL_KEYS:
            raise ValueError(f"Unknown financial sensitivity variable: {variable}")
        if not values:
            raise ValueError("Sensitivity values cannot be empty")

        points = []
        for index, value in enumerate(values, start=1):
            scenario = Scenario(
                scenario_id=f"SENS-{variable}-{index}",
                name=f"Sensitivity {variable}={value}",
                overrides={variable: value},
            )
            points.append(self.simulation.execute(case, scenario))

        outputs = [
            {
                "scenario_id": point.scenario_id,
                "variable": variable,
                "value": str(values[index]),
                "net_profit": str(point.financial.net_profit),
                "operating_profit": str(point.financial.operating_profit),
            }
            for index, point in enumerate(points)
        ]
        audit = AuditRecord.create(
            event="sensitivity.execute",
            case_id=case.case_id,
            engine_version=self.engine_version,
            inputs={"variable": variable, "values": [str(v) for v in values]},
            outputs={"points": outputs},
        )
        self.store.save_audit_record(audit)
        return SensitivityExecutionResult(case.case_id, variable, tuple(points), audit)
