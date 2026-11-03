"""Original pure utility functions; message-building utilities excluded."""
from typing import Any

def score_option(option: dict[str, Any], weights: dict[str, float], hard_constraints: dict[str, Any]) -> float:
    if violates_hard_constraints(option, hard_constraints):
        return 0.0
    scores = option["criterion_scores"]
    return round(sum(float(scores[k]) * float(weights[k]) for k in weights), 4)

def violates_hard_constraints(option: dict[str, Any], hard_constraints: dict[str, Any]) -> bool:
    attrs = option["attributes"]
    for key, value in hard_constraints.items():
        if key.endswith("_max"):
            if float(attrs[key[:-4]]) > float(value):
                return True
        elif key.endswith("_min"):
            if float(attrs[key[:-4]]) < float(value):
                return True
        elif attrs.get(key) != value:
            return True
    return False
