from core.knowledge_base.models import AttackStep, Evidence, Finding, VerificationVerdict
from core.verify.regression_detector import Exposure
from core.verify.replay_engine import ReplayEngine


def finding():
    return Finding("RCE", "10.0.0.5", "code execution", Evidence("claim", "tool success", "fixture"), [AttackStep("fixture", "check", "10.0.0.5", "nonce")])


def test_successful_replay_reopens_finding():
    result = ReplayEngine().verify(finding(), lambda step: True, controls_ok=True)
    assert result.verdict is VerificationVerdict.REOPENED


def test_failed_replay_with_controls_closes_finding():
    result = ReplayEngine().verify(finding(), lambda step: False, controls_ok=True)
    assert result.verdict is VerificationVerdict.VERIFIED_CLOSED


def test_failed_original_path_with_new_exposure_is_regression():
    before = {Exposure("10.0.0.5", "ssh", 22)}
    after = before | {Exposure("10.0.0.5", "telnet", 23)}
    result = ReplayEngine().verify(finding(), lambda step: False, controls_ok=True, before=before, after=after)
    assert result.verdict is VerificationVerdict.REGRESSION_DETECTED


def test_missing_controls_cannot_close_finding():
    result = ReplayEngine().verify(finding(), lambda step: False, controls_ok=False)
    assert result.verdict is VerificationVerdict.INCONCLUSIVE
