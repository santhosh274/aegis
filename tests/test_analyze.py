from core.analyze.confidence_engine import ConfidenceEngine
from core.knowledge_base.models import Corroboration, CorroborationOutcome, Evidence, ConfidenceGrade


def test_confidence_requires_independent_support():
    result = ConfidenceEngine().assess([
        Corroboration("probe", CorroborationOutcome.SUPPORTS, Evidence("test", "ok", "test"), independent=True)
    ])
    assert result.grade is ConfidenceGrade.CONFIRMED


def test_contradiction_routes_to_human_review():
    result = ConfidenceEngine().assess([
        Corroboration("probe", CorroborationOutcome.CONTRADICTS, Evidence("test", "no", "test"))
    ])
    assert result.grade is ConfidenceGrade.NEEDS_HUMAN_REVIEW
