"""Plan phase: pick a bounded next action from utility-ranked candidates."""
from __future__ import annotations

from core.analyze.utility_ranker import CandidateAction, rank


class Planner:
    def choose_next(self, candidates: list[CandidateAction]) -> CandidateAction | None:
        ordered = rank(candidates)
        return ordered[0] if ordered else None
