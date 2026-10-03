from decimal import Decimal
from techa.core.execution import ScenarioExecutor

def test_scenarios_execute_independently():
    e=ScenarioExecutor(lambda x: {"profit":x["price"]*x["volume"]})
    r=e.run({"price":Decimal("10"),"volume":Decimal("2")},[("base",{}),("down",{"price":Decimal("8")})])
    assert r[0].outputs["profit"]==Decimal("20")
    assert r[1].outputs["profit"]==Decimal("16")
