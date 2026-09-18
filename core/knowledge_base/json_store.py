"""Minimal JSON persistence for a single Finding.

This is intentionally NOT the future PostgreSQL/SQLAlchemy backend described by
core/knowledge_base/database.py's FindingRepository protocol -- it's a small,
dependency-free stopgap so a Finding produced by one script (e.g.
run_first_exploit.py) can be loaded by a later, separate script (e.g.
run_verification.py) without both needing to run in the same process.

Scope: single Finding round-trip only. Not a query layer, not a real store.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from core.knowledge_base.models import (
    AttackStep,
    ConfidenceGrade,
    Corroboration,
    CorroborationOutcome,
    Evidence,
    Finding,
    FindingStatus,
)


def _default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (ConfidenceGrade, FindingStatus, CorroborationOutcome)):
        return obj.value
    raise TypeError(f"not JSON serializable: {type(obj)}")


def save_finding(finding: Finding, path: str | Path) -> None:
    Path(path).write_text(json.dumps(asdict(finding), default=_default, indent=2))


def load_finding(path: str | Path) -> Finding:
    data = json.loads(Path(path).read_text())

    primary_evidence = Evidence(
        kind=data["primary_evidence"]["kind"],
        summary=data["primary_evidence"]["summary"],
        source=data["primary_evidence"]["source"],
        collected_at=datetime.fromisoformat(data["primary_evidence"]["collected_at"]),
        digest=data["primary_evidence"].get("digest"),
        id=data["primary_evidence"]["id"],
    )

    attack_chain = [
        AttackStep(
            plugin=step["plugin"],
            action=step["action"],
            target=step["target"],
            expected_predicate=step["expected_predicate"],
            parameters=step.get("parameters", {}),
            id=step["id"],
        )
        for step in data.get("attack_chain", [])
    ]

    corroborations = [
        Corroboration(
            probe=c["probe"],
            outcome=CorroborationOutcome(c["outcome"]),
            evidence=Evidence(
                kind=c["evidence"]["kind"],
                summary=c["evidence"]["summary"],
                source=c["evidence"]["source"],
                collected_at=datetime.fromisoformat(c["evidence"]["collected_at"]),
                digest=c["evidence"].get("digest"),
                id=c["evidence"]["id"],
            ),
            independent=c.get("independent", True),
            rationale=c.get("rationale", ""),
        )
        for c in data.get("corroborations", [])
    ]

    finding = Finding(
        title=data["title"],
        target=data["target"],
        claim=data["claim"],
        primary_evidence=primary_evidence,
        attack_chain=attack_chain,
        confidence=ConfidenceGrade(data["confidence"]),
        status=FindingStatus(data["status"]),
        corroborations=corroborations,
        id=data["id"],
        created_at=datetime.fromisoformat(data["created_at"]),
    )
    return finding
