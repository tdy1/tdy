from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping

from techa.audit.record import AuditRecord
from techa.core.evidence import EvidenceRegistry
from techa.core.models import BusinessCase
from techa.core.scenario import Scenario
from techa.financial.engine import FinancialEngine, FinancialInputs, FinancialResult
from techa.storage.repository import SQLiteStore


@dataclass(frozen=True)
class SimulationResult:
    case_id: str
    scenario_id: str
    financial: FinancialResult
    audit: AuditRecord


class SimulationService:
    """Executable lifecycle joining stored case assumptions, scenarios, finance and audit."""

    REQUIRED_FINANCIAL_KEYS = (
        "units_sold", "selling_price", "direct_cogs",
        "reserve_rate", "operating_expenses", "tax_rate",
    )

    def __init__(self, store: SQLiteStore, engine_version: str = "0.1.0") -> None:
        self.store = store
        self.engine_version = engine_version

    def execute(
        self,
        case: BusinessCase,
        scenario: Scenario | None = None,
        evidence: EvidenceRegistry | None = None,
    ) -> SimulationResult:
        if evidence is not None and not evidence.can_execute():
            blocking = [item.evidence_id for item in evidence.blocking_items()]
            raise ValueError(f"Simulation blocked by evidence requiring verification: {blocking}")

        values = {key: case.assumption(key).value for key in self.REQUIRED_FINANCIAL_KEYS}
        scenario_id = "BASE" if scenario is None else scenario.scenario_id
        if scenario is not None:
            values = scenario.apply(values)

        unknown = set(values) - set(self.REQUIRED_FINANCIAL_KEYS)
        if unknown:
            raise ValueError(f"Unknown financial inputs: {sorted(unknown)}")
        inputs = FinancialInputs(**values)
        result = FinancialEngine.calculate(inputs)
        outputs = {key: value for key, value in result.__dict__.items()}
        audit = AuditRecord.create(
            event="simulation.execute",
            case_id=case.case_id,
            engine_version=self.engine_version,
            inputs={"scenario_id": scenario_id, **values},
            outputs=outputs,
        )
        self.store.save_audit_record(audit)
        return SimulationResult(case.case_id, scenario_id, result, audit)
