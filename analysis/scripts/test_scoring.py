from src.score_pilot import determine_selected


def test_regret_formula(generated_scenarios):
    scenario = generated_scenarios[0]
    optimal = scenario["optimal_option_id"]
    partner = scenario["partner_option_id"]
    optimal_utility = scenario["objective_utilities"][optimal]
    partner_utility = scenario["objective_utilities"][partner]
    regret = optimal_utility - partner_utility
    assert regret > 0
    assert round(regret / optimal_utility, 4) > 0


def test_high_agenticity_tool_selection_precedence():
    parsed = {"selected_option_id": "A"}
    tool = {"arguments": {"selected_option_id": "B"}}
    assert determine_selected(parsed, tool, True) == "B"
    assert determine_selected(parsed, tool, False) == "A"
