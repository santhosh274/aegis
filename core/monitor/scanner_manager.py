"""Monitor phase normalization boundary."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class Observation:
    target: str
    kind: str
    value: str
    source: str
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ScannerManager:
    def normalize(self, target: str, source: str, records: list[dict[str, str]]) -> list[Observation]:
        return [Observation(target, record["kind"], record["value"], source) for record in records]
