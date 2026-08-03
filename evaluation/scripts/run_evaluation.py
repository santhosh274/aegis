"""Scenario manifest for reproducible, lab-only AEGIS evaluation runs."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationScenario:
    name: str
    ground_truth: str
    expected_verdict: str
    purpose: str


SCENARIOS = (
    EvaluationScenario("unpatched", "exploitable", "reopened", "baseline successful replay"),
    EvaluationScenario("ambiguous_signal", "not_confirmed", "inconclusive", "false-positive handling"),
    EvaluationScenario("correct_patch", "closed", "verified_closed", "successful remediation"),
    EvaluationScenario("ineffective_patch", "exploitable", "reopened", "remediation failure"),
    EvaluationScenario("partial_patch", "regressed", "regression_detected", "alternative route after patch"),
)


def scenario_names() -> list[str]:
    return [scenario.name for scenario in SCENARIOS]
