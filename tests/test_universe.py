from techa.core.universe import BusinessLifecycle, BusinessUniverseItem, validate_lifecycle_transition
from techa.storage.repository import SQLiteStore


def test_universe_item_validates_identity():
    item = BusinessUniverseItem("100", "Example", "Agriculture", "Ethiopia")
    assert item.lifecycle_status is BusinessLifecycle.UNIVERSE
    assert item.active_case_id is None


def test_universe_registry_round_trip(tmp_path):
    store = SQLiteStore(tmp_path / "techa.db")
    store.initialize("techa/storage/schema.sql")
    item = BusinessUniverseItem("548", "Dehydrated Vegetable Production", "Agriculture & Agribusiness", "Ethiopia")
    store.save_universe_item(item)
    loaded = store.get_universe_item("548")
    assert loaded == item
    store.close()


def test_universe_lifecycle_and_case_link(tmp_path):
    store = SQLiteStore(tmp_path / "techa.db")
    store.initialize("techa/storage/schema.sql")
    item = BusinessUniverseItem("548", "Dehydrated Vegetable Production", "Agriculture & Agribusiness", "Ethiopia")
    store.save_universe_item(item)
    updated = BusinessUniverseItem("548", item.name, item.sector, item.geography,
                                   BusinessLifecycle.INGESTED, "548-case-v1")
    store.save_universe_item(updated)
    assert store.get_universe_item("548") == updated
    store.close()


def test_lifecycle_transition_rules():
    item = BusinessUniverseItem("548", "Dehydrated Vegetable Production", "Agriculture", "Ethiopia")
    validate_lifecycle_transition(item.lifecycle_status, BusinessLifecycle.CANDIDATE)
    with pytest.raises(ValueError, match="Invalid lifecycle transition"):
        validate_lifecycle_transition(BusinessLifecycle.UNIVERSE, BusinessLifecycle.CLEARED)
