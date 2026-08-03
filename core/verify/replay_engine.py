"""Controlled replay decisions for previously recorded declarative attack chains."""
from __future__ import annotations

from typing import Callable
from core.knowledge_base.models import AttackStep, Evidence, Finding, FindingStatus, VerificationResult, VerificationVerdict
from core.verify.regression_detector import Exposure, detect_regressions


class ReplayEngine:
    def verify(
        self,
        finding: Finding,
        execute_step: Callable[[AttackStep], bool],
        *,
        controls_ok: bool,
        before: set[Exposure] | None = None,
        after: set[Exposure] | None = None,
    ) -> VerificationResult:
        if not controls_ok:
            return self._apply(finding, self._result(finding, VerificationVerdict.INCONCLUSIVE, "verification controls or prerequisites failed"))
        for step in finding.attack_chain:
            if not execute_step(step):
                regressions = detect_regressions(before or set(), after or set())
                if regressions:
                    summary = ", ".join(f"{item.service}/{item.port}" for item in regressions)
                    return self._apply(finding, self._result(finding, VerificationVerdict.REGRESSION_DETECTED, "original chain blocked but new exposure observed", step.id, summary))
                return self._apply(finding, self._result(finding, VerificationVerdict.VERIFIED_CLOSED, "decisive replay step failed after controls passed", step.id))
        return self._apply(finding, self._result(finding, VerificationVerdict.REOPENED, "recorded exploit chain reproduced"))

    def _apply(self, finding: Finding, result: VerificationResult) -> VerificationResult:
        if result.verdict is VerificationVerdict.VERIFIED_CLOSED:
            finding.status = FindingStatus.VERIFIED_CLOSED
        elif result.verdict is VerificationVerdict.REOPENED:
            finding.status = FindingStatus.REOPENED
        # A regression needs triage: do not falsely close the original finding.
        elif result.verdict is VerificationVerdict.REGRESSION_DETECTED:
            finding.status = FindingStatus.NEEDS_HUMAN_REVIEW
        return result

    def _result(self, finding: Finding, verdict: VerificationVerdict, summary: str, failed_step_id: str | None = None, regression_summary: str | None = None) -> VerificationResult:
        evidence = Evidence(kind="verification", summary=summary, source="replay_engine")
        return VerificationResult(finding.id, verdict, evidence, failed_step_id, regression_summary)
