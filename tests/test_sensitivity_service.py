from decimal import Decimal

from techa.core.models import Assumption, BusinessCase, Currency, EvidenceClass
from techa.core.sensitivity_service import SensitivityService
from techa.core.simulation import SimulationService
from techa.storage.repository import SQLiteStore


def make_case() -> BusinessCase:
    return BusinessCase(
        "SENS-001",
        "Sensitivity Case",
        Currency("ETB", "Ethiopian Birr"),
        {
            "units_sold": Assumption("units_sold", Decimal("100"), "units", EvidenceClass.MARKET_ASSUMPTION),
            "selling_price": Assumption("selling_price", Decimal("50"), "ETB/unit", EvidenceClass.MARKET_ASSUMPTION),
            "direct_cogs": Assumption("direct_cogs", Decimal("3000"), "ETB", EvidenceClass.COST_ENGINEERING_ESTIMATE),
            "reserve_rate": Assumption("reserve_rate", Decimal("0.20"), "ratio", EvidenceClass.MARKET_ASSUMPTION),
            "operating_expenses": Assumption("operating_expenses", Decimal("1000"), "ETB", EvidenceClass.COST_ENGINEERING_ESTIMATE),
            "tax_rate": Assumption("tax_rate", Decimal("0.30"), "ratio", EvidenceClass.VERIFIED_FACT),
        },
    )


def test_sensitivity_executes_each_point_and_audits(tmp_path):
    store = SQLiteStore(tmp_path / "techa.db")
    store.initialize("techa/storage/schema.sql")
    case = make_case()
    store.save_business_case(case)
    service = SensitivityService(SimulationService(store), store)
    result = service.execute(case, "selling_price", [Decimal("40"), Decimal("50"), Decimal("60")])
    assert [p.financial.net_profit for p in result.points] == [
        Decimal("-600.00"), Decimal("280.00"), Decimal("1160.00")
    ]
    records = store.get_audit_records("SENS-001")
    assert len(records) == 4
    assert records[0]["event"] == "sensitivity.execute"
    store.close()
