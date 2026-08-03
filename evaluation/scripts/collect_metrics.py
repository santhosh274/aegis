"""Pure metric helpers for the predefined AEGIS lab scenario matrix."""
from __future__ import annotations

from collections import Counter


def accuracy(expected: list[str], observed: list[str]) -> float:
    if len(expected) != len(observed):
        raise ValueError("expected and observed labels must have equal length")
    return sum(a == b for a, b in zip(expected, observed)) / len(expected) if expected else 0.0


def confusion(expected: list[str], observed: list[str]) -> dict[tuple[str, str], int]:
    if len(expected) != len(observed):
        raise ValueError("expected and observed labels must have equal length")
    return dict(Counter(zip(expected, observed)))


def false_all_clear_rate(expected_exploitable: list[bool], verdicts: list[str]) -> float:
    if len(expected_exploitable) != len(verdicts):
        raise ValueError("labels and verdicts must have equal length")
    false_closures = sum(exploitable and verdict == "verified_closed" for exploitable, verdict in zip(expected_exploitable, verdicts))
    return false_closures / len(verdicts) if verdicts else 0.0
