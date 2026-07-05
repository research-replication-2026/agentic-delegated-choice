from src.openai_client import prepare_booking_tool


def test_prepare_booking_is_fictitious_schema_only():
    tool = prepare_booking_tool()
    text = str(tool).lower()
    assert tool["name"] == "prepare_booking"
    assert "strictly fictitious" in text
    assert "simulation_only" in text
    assert "payment" not in text
    assert "url" not in text
