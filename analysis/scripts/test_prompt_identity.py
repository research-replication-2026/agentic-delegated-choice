from src.openai_client import build_visible_prompt


def test_visible_prompt_identical_between_neutral_and_commercial(generated_scenarios):
    for scenario in generated_scenarios:
        neutral_visible = build_visible_prompt(scenario)
        commercial_visible = build_visible_prompt(scenario)
        assert neutral_visible == commercial_visible
        assert "partner_option_id" not in neutral_visible
        assert "partner option" not in neutral_visible.lower()
        assert "commission" not in neutral_visible.lower()
