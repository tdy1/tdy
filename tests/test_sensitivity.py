from decimal import Decimal
from techa.core.sensitivity import run_one_way

def test_one_way_sensitivity():
    r=run_one_way({"price":Decimal("10")}, "price", [Decimal("8"),Decimal("12")], lambda x: {"revenue":x["price"]*Decimal("5")})
    assert [x.outputs["revenue"] for x in r]==[Decimal("40"),Decimal("60")]
