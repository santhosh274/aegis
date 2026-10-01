"""Independent SSH credential re-validation corroborator.

Opens a SEPARATE SSH session to the reported target and re-attempts the
documented default-credential claim. It never trusts the primary adapter's
connection and performs no post-authentication activity. Matches the
devil's-advocate contract: a fresh session is used to try to disprove the
claim that a default credential authenticates.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from core.knowledge_base.models import Corroboration, CorroborationOutcome, Evidence, Finding
from plugins.exploits.ssh_default_creds import DEFAULT_CREDENTIALS


@dataclass
class SshCredentialCorroborator:
    name: str = "ssh_revalidation"
    port: int = 22
    timeout: float = 8.0
    credentials: tuple[tuple[str, str], ...] = DEFAULT_CREDENTIALS

    # Injectable client factory for testing/mocking.
    client_factory: Callable[[], Any] | None = field(default=None)

    def __post_init__(self) -> None:
        if self.client_factory is None:
            def _lazy_factory() -> Any:
                try:
                    import paramiko
                except ImportError as exc:
                    raise RuntimeError(
                        "paramiko is not installed; run `pip install paramiko` "
                        "to use ssh_revalidation"
                    ) from exc
                return paramiko.SSHClient()

            self.client_factory = _lazy_factory

    def corroborate(self, finding: Finding) -> Corroboration:
        try:
            from paramiko import AutoAddPolicy
        except ImportError:
            AutoAddPolicy = None

        for username, password in self.credentials:
            client = self.client_factory()
            try:
                if AutoAddPolicy is not None and hasattr(client, "set_missing_host_key_policy"):
                    client.set_missing_host_key_policy(AutoAddPolicy())
                client.connect(
                    hostname=finding.target,
                    port=self.port,
                    username=username,
                    password=password,
                    timeout=self.timeout,
                    allow_agent=False,
                    look_for_keys=False,
                )
            except OSError as exc:
                return Corroboration(
                    self.name,
                    CorroborationOutcome.AMBIGUOUS,
                    Evidence(
                        "ssh_recheck",
                        f"SSH service on {finding.target}:{self.port} not independently reachable: {exc}",
                        self.name,
                    ),
                    True,
                    "independent re-login predicate with fresh session",
                )
            except Exception as exc:  # noqa: BLE001 - classify by exception shape
                if self._is_auth_failure(exc):
                    continue
                return Corroboration(
                    self.name,
                    CorroborationOutcome.AMBIGUOUS,
                    Evidence(
                        "ssh_recheck",
                        f"independent SSH session failed: {exc}",
                        self.name,
                    ),
                    True,
                    "independent re-login predicate with fresh session",
                )
            finally:
                try:
                    client.close()
                except Exception:  # pragma: no cover - defensive
                    pass

            return Corroboration(
                self.name,
                CorroborationOutcome.SUPPORTS,
                Evidence(
                    "ssh_recheck",
                    f"default credential {username} accepted in independent SSH session",
                    self.name,
                ),
                True,
                "independent re-login predicate with fresh session",
            )

        return Corroboration(
            self.name,
            CorroborationOutcome.CONTRADICTS,
            Evidence(
                "ssh_recheck",
                "default credential rejected in independent SSH session",
                self.name,
            ),
            True,
            "independent re-login predicate with fresh session",
        )

    @staticmethod
    def _is_auth_failure(exc: BaseException) -> bool:
        name = type(exc).__name__.lower()
        message = str(exc).lower()
        return "authentication" in name or "auth" in name or "authentication" in message