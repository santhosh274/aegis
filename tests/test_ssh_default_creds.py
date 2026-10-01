import pytest

from core.knowledge_base.models import AttackStep
from plugins.exploits.ssh_default_creds import (
    SshWeakCredentialsAdapter,
    SshWeakCredentialsError,
)


class FakeAuthError(Exception):
    """Thrown by the fake client for rejected credentials."""


class FakeSshClient:
    def __init__(self, accepted: set[tuple[str, str]]):
        self.accepted = accepted
        self.calls: list[tuple[str, int, str]] = []
        self.closed = 0
        self.policy = None

    def set_missing_host_key_policy(self, policy):
        self.policy = policy

    def connect(
        self,
        hostname=None,
        port=None,
        username=None,
        password=None,
        timeout=None,
        allow_agent=None,
        look_for_keys=None,
    ):
        self.calls.append((hostname, port, username))
        if (username, password) not in self.accepted:
            raise FakeAuthError("Authentication failed.")

    def close(self):
        self.closed += 1


def make_client_factory(accepted: set[tuple[str, str]]):
    clients: list[FakeSshClient] = []

    def factory():
        client = FakeSshClient(accepted)
        clients.append(client)
        return client

    factory.clients = clients
    return factory


def test_run_returns_evidence_when_default_credential_accepted():
    factory = make_client_factory({("msfadmin", "msfadmin")})
    adapter = SshWeakCredentialsAdapter(client_factory=factory)
    step = AttackStep(
        plugin="ssh_weak_credentials",
        action="authenticate_default_credentials",
        target="192.168.232.10",
        expected_predicate="authentication_accepted",
    )

    evidence = adapter.run(step)

    assert evidence.kind == "authenticated_ssh"
    assert "msfadmin" in evidence.summary
    assert "192.168.232.10" in evidence.summary
    assert evidence.source == "ssh_weak_credentials"
    assert factory.clients[0].calls[0][0:2] == ("192.168.232.10", 22)
    assert factory.clients[0].closed >= 1


def test_run_raises_when_no_default_credential_accepted():
    factory = make_client_factory(set())
    adapter = SshWeakCredentialsAdapter(client_factory=factory)
    step = AttackStep(
        plugin="ssh_weak_credentials",
        action="authenticate_default_credentials",
        target="192.168.232.10",
        expected_predicate="authentication_accepted",
    )

    with pytest.raises(SshWeakCredentialsError, match="no default credential accepted"):
        adapter.run(step)


def test_run_raises_when_ssh_service_unreachable():
    def factory():
        class Unreachable(FakeSshClient):
            def connect(self, **kwargs):
                raise ConnectionRefusedError("connection refused")

        return Unreachable(set())

    adapter = SshWeakCredentialsAdapter(client_factory=factory)
    step = AttackStep(
        plugin="ssh_weak_credentials",
        action="authenticate_default_credentials",
        target="10.0.0.1",
        expected_predicate="authentication_accepted",
    )

    with pytest.raises(SshWeakCredentialsError, match="interaction against 10.0.0.1:22 failed"):
        adapter.run(step)


def test_construction_needs_no_paramiko_installed():
    # Default client_factory is lazy — constructing the adapter must not import
    # paramiko (which is not installed in this environment).
    adapter = SshWeakCredentialsAdapter()
    assert adapter.name == "ssh_weak_credentials"