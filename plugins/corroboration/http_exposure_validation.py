"""Independent HTTP exposure re-validation corroborator.

Establishes its own HTTP sessions to the reported target and re-fetches the
known-vulnerable web-application paths. It never reuses the primary adapter's
connection; each fetch is a fresh, bounded socket. Matches the devil's-advocate
contract: an attempt to disprove the claim that a known-vulnerable web app is
exposed on the public interface.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from core.knowledge_base.models import Corroboration, CorroborationOutcome, Evidence, Finding
from plugins.exploits.http_exposed_service import (
    DEFAULT_PATHS,
    DEFAULT_PORTS,
    _default_connector,
)


@dataclass
class HttpExposureCorroborator:
    name: str = "http_exposure_validation"
    ports: tuple[int, ...] = DEFAULT_PORTS
    paths: tuple[tuple[str, str, str], ...] = DEFAULT_PATHS
    timeout: float = 5.0

    # Injectable connector for testing/mocking.
    connector: Callable[[str, int, str, float], bytes] = field(default=_default_connector)

    def corroborate(self, finding: Finding) -> Corroboration:
        for port in self.ports:
            for path, marker, _label in self.paths:
                try:
                    body = self.connector(finding.target, port, path, self.timeout)
                except OSError:
                    continue
                if marker and marker.encode("utf-8", errors="ignore") in body:
                    return Corroboration(
                        self.name,
                        CorroborationOutcome.SUPPORTS,
                        Evidence(
                            "http_recheck",
                            f"independent fetch confirmed {marker} marker on {finding.target}:{port}",
                            self.name,
                        ),
                        True,
                        "independent HTTP fetch predicate",
                    )
                return Corroboration(
                    self.name,
                    CorroborationOutcome.CONTRADICTS,
                    Evidence(
                        "http_recheck",
                        f"endpoint reached but {marker} marker not present on {finding.target}:{port}",
                        self.name,
                    ),
                    True,
                    "independent HTTP fetch predicate",
                )
        return Corroboration(
            self.name,
            CorroborationOutcome.AMBIGUOUS,
            Evidence(
                "http_recheck",
                f"no HTTP endpoint independently reachable on {finding.target}",
                self.name,
            ),
            True,
            "independent HTTP fetch predicate",
        )