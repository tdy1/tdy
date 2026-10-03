from decimal import Decimal

import pytest

from techa.core.scenario import Scenario, one_way_sensitivity


def test_scenario_overrides_only_declared_values() -> None:
    base = {"price": Decimal("100"), "volume": Decimal("10")}
    scenario = Scenario("downside", "Downside", {"price": Decimal("80")})
    assert scenario.apply(base) == {"price": Decimal("80"), "volume": Decimal("10")}


def test_unknown_sensitivity_variable_is_rejected() -> None:
    with pytest.raises(KeyError):
        one_way_sensitivity({"price": Decimal("100")}, "volume", [Decimal("80")])
