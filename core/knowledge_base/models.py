"""Typed domain records shared by the MAPE-K-V phases.

These records intentionally describe claims and evidence rather than raw shell
commands.  A tool adapter is responsible for any lab-authorised interaction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ConfidenceGrade(str, Enum):
    CONFIRMED = "confirmed"
    SUSPECTED = "suspected"
    NEEDS_HUMAN_REVIEW = "needs_human_review"


class FindingStatus(str, Enum):
    OPEN = "open"
    CONFIRMED = "confirmed"
    REMEDIATED = "remediated"
    VERIFIED_CLOSED = "verified_closed"
    REOPENED = "reopened"
    NEEDS_HUMAN_REVIEW = "needs_human_review"


class CorroborationOutcome(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    AMBIGUOUS = "ambiguous"


class VerificationVerdict(str, Enum):
    VERIFIED_CLOSED = "verified_closed"
    REOPENED = "reopened"
    REGRESSION_DETECTED = "regression_detected"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class Evidence:
    kind: str
    summary: str
    source: str
    collected_at: datetime = field(default_factory=utcnow)
    digest: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True)
class Corroboration:
    probe: str
    outcome: CorroborationOutcome
    evidence: Evidence
    independent: bool = True
    rationale: str = ""


@dataclass(frozen=True)
class AttackStep:
    """A replayable, declarative action; never a stored arbitrary command."""
    plugin: str
    action: str
    target: str
    expected_predicate: str
    parameters: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class Finding:
    title: str
    target: str
    claim: str
    primary_evidence: Evidence
    attack_chain: list[AttackStep] = field(default_factory=list)
    confidence: ConfidenceGrade = ConfidenceGrade.SUSPECTED
    status: FindingStatus = FindingStatus.OPEN
    corroborations: list[Corroboration] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class RemediationEvent:
    finding_id: str
    description: str
    reported_at: datetime = field(default_factory=utcnow)
    target_snapshot: str | None = None


@dataclass(frozen=True)
class VerificationResult:
    finding_id: str
    verdict: VerificationVerdict
    evidence: Evidence
    failed_step_id: str | None = None
    regression_summary: str | None = None
    completed_at: datetime = field(default_factory=utcnow)
