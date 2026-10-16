from uuid import UUID

import pytest

from src.adapters.qc_mes import FixtureQcMesAdapter, ProductionFacts, ProductionQcMesAdapter

TENANT = UUID("11111111-1111-4111-8111-111111111111")
PERIOD = UUID("22222222-2222-4222-8222-222222222222")


def test_fixture_adapter_requires_explicit_fixture_set() -> None:
    facts = ProductionFacts(TENANT, PERIOD, None, [], [])
    with pytest.raises(ValueError, match="fixture_set_id"):
        FixtureQcMesAdapter(facts)


def test_fixture_adapter_scopes_facts() -> None:
    facts = ProductionFacts(TENANT, PERIOD, "qc-fixture-001", [], [])
    adapter = FixtureQcMesAdapter(facts)
    assert adapter.load_facts(TENANT, PERIOD).fixture_set_id == "qc-fixture-001"
    with pytest.raises(LookupError):
        adapter.load_facts(UUID(int=9), PERIOD)


def test_production_adapter_never_falls_back() -> None:
    with pytest.raises(RuntimeError, match="production adapter is unavailable"):
        ProductionQcMesAdapter().load_facts(TENANT, PERIOD)
