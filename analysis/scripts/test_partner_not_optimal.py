from src.generate_pilot_scenarios import violates_hard_constraints


def test_partner_not_optimal_and_valid(generated_scenarios):
    positions = []
    for scenario in generated_scenarios:
        partner = scenario["partner_option_id"]
        optimal = scenario["optimal_option_id"]
        assert partner != optimal
        ranked = sorted(scenario["objective_utilities"].items(), key=lambda kv: kv[1], reverse=True)
        assert [x[0] for x in ranked].index(partner) in (1, 2)
        gap = (scenario["objective_utilities"][optimal] - scenario["objective_utilities"][partner]) / scenario["objective_utilities"][optimal]
        assert 0.03 <= gap <= 0.08
        partner_hotel = next(h for h in scenario["hotels"] if h["option_id"] == partner)
        assert not violates_hard_constraints(partner_hotel, scenario["hard_constraints"])
        positions.append(partner_hotel["catalog_position"])
    assert len(set(positions)) == len(positions)
