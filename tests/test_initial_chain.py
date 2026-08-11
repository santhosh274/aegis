from core.demo.initial_chain import InitialChainScenario, run_initial_chain
from core.knowledge_base.models import ConfidenceGrade, FindingStatus, VerificationVerdict
from core.verify.regression_detector import Exposure


def test_initial_chain_runs_the_fixture_lifecycle_and_records_audit_trail():
    run = run_initial_chain()

    assert run.observations[0].value == "http/8080"
    assert run.action_plugin_calls == 1
    assert run.confidence.grade is ConfidenceGrade.CONFIRMED
    assert run.verification is not None
    assert run.verification.verdict is VerificationVerdict.VERIFIED_CLOSED
    assert run.finding.status is FindingStatus.VERIFIED_CLOSED
    assert len(run.ledger.findings) == 1
    assert len(run.ledger.evidence) == 3
    assert len(run.ledger.remediations) == 1
    assert len(run.ledger.verifications) == 1


def test_contradictory_corroboration_needs_human_review_without_replay():
    run = run_initial_chain(
        InitialChainScenario(corroboration_observed=False, remediation_description=None)
    )

    assert run.confidence.grade is ConfidenceGrade.NEEDS_HUMAN_REVIEW
    assert run.finding.status is FindingStatus.NEEDS_HUMAN_REVIEW
    assert run.verification is None


def test_blocked_original_route_with_new_exposure_is_a_regression():
    run = run_initial_chain(
        InitialChainScenario(
            after_exposures=frozenset({Exposure("10.0.0.5", "ssh", 22)})
        )
    )

    assert run.verification is not None
    assert run.verification.verdict is VerificationVerdict.REGRESSION_DETECTED
    assert run.finding.status is FindingStatus.NEEDS_HUMAN_REVIEW
