"""Evidence-based confidence grading, deliberately separate from utility ranking."""
from __future__ import annotations

from dataclasses import dataclass
from core.knowledge_base.models import ConfidenceGrade, Corroboration, CorroborationOutcome, Finding, FindingStatus


@dataclass(frozen=True)
class ConfidenceAssessment:
    grade: ConfidenceGrade
    score: int
    rationale: str
    rubric_version: str = "1.0"


class ConfidenceEngine:
    """Small, transparent rubric suitable for calibration against lab truth."""
    def assess(self, corroborations: list[Corroboration]) -> ConfidenceAssessment:
        independent_support = sum(c.outcome is CorroborationOutcome.SUPPORTS and c.independent for c in corroborations)
        contradictions = sum(c.outcome is CorroborationOutcome.CONTRADICTS for c in corroborations)
        ambiguous = sum(c.outcome is CorroborationOutcome.AMBIGUOUS for c in corroborations)
        score = independent_support * 2 - contradictions * 3 - ambiguous
        if contradictions:
            return ConfidenceAssessment(ConfidenceGrade.NEEDS_HUMAN_REVIEW, score, "contradictory corroboration evidence")
        if independent_support >= 1 and not ambiguous:
            return ConfidenceAssessment(ConfidenceGrade.CONFIRMED, score, "independent corroboration supports the claim")
        return ConfidenceAssessment(ConfidenceGrade.SUSPECTED, score, "insufficient independent corroboration")

    def assess_finding(self, finding: Finding) -> ConfidenceAssessment:
        assessment = self.assess(finding.corroborations)
        finding.confidence = assessment.grade
        finding.status = {
            ConfidenceGrade.CONFIRMED: FindingStatus.CONFIRMED,
            ConfidenceGrade.SUSPECTED: FindingStatus.OPEN,
            ConfidenceGrade.NEEDS_HUMAN_REVIEW: FindingStatus.NEEDS_HUMAN_REVIEW,
        }[assessment.grade]
        return assessment
