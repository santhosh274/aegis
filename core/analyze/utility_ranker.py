"""Selection utility only; it must not be used as a finding confidence score."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateAction:
    name: str
    expected_gain: float
    information_gain: float
    cost: float
    risk: float

    def utility(self) -> float:
        return 0.45 * self.expected_gain + 0.35 * self.information_gain - 0.15 * self.cost - 0.05 * self.risk


def rank(candidates: list[CandidateAction]) -> list[CandidateAction]:
    return sorted(candidates, key=lambda item: item.utility(), reverse=True)
