import pytest

from src.generate_pilot_scenarios import write_outputs


@pytest.fixture(scope="session")
def generated_scenarios():
    return write_outputs()
