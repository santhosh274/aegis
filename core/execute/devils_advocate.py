"""Independent corroboration orchestration for a candidate finding."""
from __future__ import annotations

from typing import Protocol
from core.knowledge_base.models import Corroboration, Finding


class CorroborationPlugin(Protocol):
    name: str
    def corroborate(self, finding: Finding) -> Corroboration: ...


class DevilsAdvocate:
    def validate(self, finding: Finding, plugins: list[CorroborationPlugin]) -> list[Corroboration]:
        results = [plugin.corroborate(finding) for plugin in plugins]
        finding.corroborations.extend(results)
        return results
