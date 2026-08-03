"""Append-only in-memory ledger; replace its backing store with PostgreSQL later."""
from __future__ import annotations

from dataclasses import dataclass, field
from .models import Evidence, Finding, RemediationEvent, VerificationResult


@dataclass
class KnowledgeLedger:
    findings: dict[str, Finding] = field(default_factory=dict)
    evidence: dict[str, Evidence] = field(default_factory=dict)
    remediations: list[RemediationEvent] = field(default_factory=list)
    verifications: list[VerificationResult] = field(default_factory=list)

    def record_finding(self, finding: Finding) -> Finding:
        self.findings[finding.id] = finding
        self.record_evidence(finding.primary_evidence)
        return finding

    def record_evidence(self, item: Evidence) -> None:
        # Never overwrite an existing evidence object with a different object.
        existing = self.evidence.get(item.id)
        if existing is not None and existing != item:
            raise ValueError("evidence identifiers are immutable")
        self.evidence[item.id] = item

    def record_remediation(self, event: RemediationEvent) -> None:
        if event.finding_id not in self.findings:
            raise KeyError("unknown finding")
        self.remediations.append(event)

    def record_verification(self, result: VerificationResult) -> None:
        if result.finding_id not in self.findings:
            raise KeyError("unknown finding")
        self.record_evidence(result.evidence)
        self.verifications.append(result)
