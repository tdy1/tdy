from decimal import Decimal
from techa.core.models import Assumption, BusinessCase, Currency, EvidenceClass, FxRate
from techa.storage.repository import SQLiteStore

def test_business_case_round_trip(tmp_path):
    store=SQLiteStore(tmp_path/"techa.db"); store.initialize("techa/storage/schema.sql")
    case=BusinessCase("B001","Test Case",Currency("ETB","Ethiopian Birr"),{
        "price":Assumption("price",Decimal("380"),"ETB/kg",EvidenceClass.MARKET_ASSUMPTION)
    })
    store.save_business_case(case); loaded=store.get_business_case("B001")
    assert loaded is not None and loaded.name=="Test Case"
    assert loaded.base_currency.code=="ETB"
    assert loaded.assumption("price").value==Decimal("380")
    store.close()

def test_fx_rate_persistence(tmp_path):
    store=SQLiteStore(tmp_path/"techa.db"); store.initialize("techa/storage/schema.sql")
    store.save_fx_rate(FxRate("ETB","USD",Decimal("163.35"),"2026-10-03","reference"))
    assert store.db.execute("SELECT rate FROM fx_rate").fetchone()[0]=="163.35"
    store.close()


def test_fx_rate_exact_as_of_lookup(tmp_path):
    store=SQLiteStore(tmp_path/"techa.db"); store.initialize("techa/storage/schema.sql")
    store.save_fx_rate(FxRate("ETB","USD",Decimal("163.35"),"2026-10-03","reference"))
    assert store.get_fx_rate("etb","usd","2026-10-03").rate==Decimal("163.35")
    assert store.get_fx_rate("ETB","USD","2026-10-02") is None
    store.close()
