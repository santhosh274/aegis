"""Bounded comparison of pre/post-remediation exposure snapshots."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Exposure:
    target: str
    service: str
    port: int
    fingerprint: str = ""


def detect_regressions(before: set[Exposure], after: set[Exposure]) -> list[Exposure]:
    """Returns new or materially changed exposures; does not scan by itself."""
    return sorted(after - before, key=lambda item: (item.target, item.port, item.service))
