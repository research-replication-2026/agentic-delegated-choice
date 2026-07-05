from src.generate_pilot_scenarios import enrich_scenarios
from src.validate_pilot_scenarios import validate_scenarios


def test_five_scenarios_and_eight_hotels():
    scenarios = enrich_scenarios()
    assert len(scenarios) == 5
    assert all(len(s["hotels"]) == 8 for s in scenarios)


def test_scenario_validation_passes(generated_scenarios):
    assert validate_scenarios() == []
