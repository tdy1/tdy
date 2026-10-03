from decimal import Decimal

from techa.core.models import Assumption, BusinessCase, Currency, EvidenceClass
from techa.core.scenario import Scenario
from techa.core.simulation import SimulationService
from techa.storage.repository import SQLiteStore


def make_case() -> BusinessCase:
    return BusinessCase(
        "SIM-001",
        "Simulation Case",
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


def test_simulation_executes_and_persists_audit(tmp_path):
    store = SQLiteStore(tmp_path / "techa.db")
    store.initialize("techa/storage/schema.sql")
    case = make_case()
    store.save_business_case(case)
    result = SimulationService(store).execute(case)
    assert result.scenario_id == "BASE"
    assert result.financial.revenue == Decimal("5000.00")
    assert result.financial.net_profit == Decimal("280.00")
    row = store.db.execute("SELECT event,case_id FROM audit_record").fetchone()
    assert row == ("simulation.execute", "SIM-001")
    store.close()


def test_simulation_applies_scenario_override(tmp_path):
    store = SQLiteStore(tmp_path / "techa.db")
    store.initialize("techa/storage/schema.sql")
    case = make_case()
    store.save_business_case(case)
    scenario = Scenario("LOW-PRICE", "Low price", {"selling_price": Decimal("40")})
    result = SimulationService(store).execute(case, scenario)
    assert result.scenario_id == "LOW-PRICE"
    assert result.financial.revenue == Decimal("4000.00")
    assert result.financial.net_profit == Decimal("-600.00")
    store.close()
