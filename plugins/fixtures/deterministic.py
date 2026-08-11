"""Fixture adapters that exercise orchestration without network activity."""
from __future__ import annotations

from core.knowledge_base.models import AttackStep, Evidence


class FixtureDiscoveryAdapter:
    """Returns declared records only; it never contacts a target."""

    name = "fixture_discovery"

    def __init__(self, records: list[dict[str, str]]):
        self.records = records

    def discover(self, target: str) -> list[dict[str, str]]:
        return list(self.records)


class FixtureValidationPlugin:
    """Produces deterministic primary evidence for a benign validation predicate."""

    name = "fixture_validation"

    def __init__(self, claim_observed: bool = True):
        self.claim_observed = claim_observed
        self.calls: list[AttackStep] = []

    def run(self, step: AttackStep) -> Evidence:
        self.calls.append(step)
        summary = (
            "fixture validation predicate observed"
            if self.claim_observed
            else "fixture validation predicate was not observed"
        )
        return Evidence("primary_claim", summary, self.name)
