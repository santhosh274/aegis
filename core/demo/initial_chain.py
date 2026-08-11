"""Deterministic Monitor-to-Verify chain for the first integration stage."""
from __future__ import annotations

from dataclasses import dataclass, field

from config.settings import ScopePolicy
from core.analyze.confidence_engine import ConfidenceAssessment, ConfidenceEngine
from core.analyze.utility_ranker import CandidateAction
from core.execute.devils_advocate import DevilsAdvocate
from core.execute.executor import Executor
from core.knowledge_base.ledger import KnowledgeLedger
from core.knowledge_base.models import (
    AttackStep,
    CorroborationOutcome,
    Finding,
    RemediationEvent,
    VerificationResult,
)
from core.monitor.scanner_manager import Observation, ScannerManager
from core.plan.planner import Planner
from core.verify.regression_detector import Exposure
from core.verify.replay_engine import ReplayEngine
from plugins.corroboration.rce_validation import RceCorroborator
from plugins.fixtures.deterministic import FixtureDiscoveryAdapter, FixtureValidationPlugin


@dataclass(frozen=True)
class InitialChainScenario:
    """All inputs are fixtures; no option enables network or command execution."""

    target: str = "10.0.0.5"
    discovery_records: tuple[dict[str, str], ...] = ({"kind": "service", "value": "http/8080"},)
    primary_claim_observed: bool = True
    corroboration_observed: bool | None = True
    remediation_description: str | None = "fixture remediation applied"
    replay_succeeds: bool = False
    controls_ok: bool = True
    before_exposures: frozenset[Exposure] = field(default_factory=frozenset)
    after_exposures: frozenset[Exposure] = field(default_factory=frozenset)


@dataclass(frozen=True)
class InitialChainRun:
    observations: list[Observation]
    selected_action: CandidateAction
    finding: Finding
    confidence: ConfidenceAssessment
    verification: VerificationResult | None
    ledger: KnowledgeLedger
    action_plugin_calls: int


def run_initial_chain(scenario: InitialChainScenario = InitialChainScenario()) -> InitialChainRun:
    """Run the fixture-only lifecycle and retain every produced record in a ledger."""
    discovery = FixtureDiscoveryAdapter(list(scenario.discovery_records))
    observations = ScannerManager().normalize(
        scenario.target, discovery.name, discovery.discover(scenario.target)
    )
    candidates = _candidates_from(observations)
    selected = Planner().choose_next(candidates)
    if selected is None:
        raise ValueError("fixture scenario produced no actionable observations")

    action_plugin = FixtureValidationPlugin(scenario.primary_claim_observed)
    policy = ScopePolicy(
        allowed_hosts=(scenario.target,), allowed_plugins=(action_plugin.name,), lab_mode=True
    )
    step = AttackStep(action_plugin.name, "benign_validation", scenario.target, selected.name)
    primary_evidence = Executor(policy, {action_plugin.name: action_plugin}).execute(step)
    finding = Finding(
        "Fixture validation claim",
        scenario.target,
        "A fixture predicate indicates a controlled validation condition",
        primary_evidence,
        [step],
    )
    ledger = KnowledgeLedger()
    ledger.record_finding(finding)

    corroborations = DevilsAdvocate().validate(
        finding, [RceCorroborator(scenario.corroboration_observed)]
    )
    for corroboration in corroborations:
        ledger.record_evidence(corroboration.evidence)
    confidence = ConfidenceEngine().assess_finding(finding)

    verification = None
    if scenario.remediation_description is not None:
        ledger.record_remediation(RemediationEvent(finding.id, scenario.remediation_description))
        verification = ReplayEngine().verify(
            finding,
            lambda _step: scenario.replay_succeeds,
            controls_ok=scenario.controls_ok,
            before=set(scenario.before_exposures),
            after=set(scenario.after_exposures),
        )
        ledger.record_verification(verification)

    return InitialChainRun(
        observations, selected, finding, confidence, verification, ledger, len(action_plugin.calls)
    )


def _candidates_from(observations: list[Observation]) -> list[CandidateAction]:
    """Translate supported service observations into bounded fixture actions."""
    return [
        CandidateAction(
            name=f"validate {observation.value} on {observation.target}",
            expected_gain=0.5,
            information_gain=0.8,
            cost=0.1,
            risk=0.05,
        )
        for observation in observations
        if observation.kind == "service"
    ]
