import socket

import pytest

from core.knowledge_base.models import AttackStep
from plugins.exploits.vsftpd_backdoor import (
    BACKDOOR_PORT,
    VsftpdBackdoorAdapter,
    VsftpdBackdoorError,
)


class FakeSocket:
    def __init__(self, recv_data: bytes = b"220 ready\r\n", raise_on_connect: bool = False):
        self.recv_data = recv_data
        self.raise_on_connect = raise_on_connect
        self.sent: list[bytes] = []
        self._timeout = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def settimeout(self, value):
        self._timeout = value

    def recv(self, n):
        return self.recv_data

    def sendall(self, data: bytes):
        self.sent.append(data)


def make_connector(ftp_socket: FakeSocket, backdoor_reachable: bool):
    calls = []

    def connector(address, timeout):
        calls.append(address)
        host, port = address
        if port == 21:
            return ftp_socket
        if port == BACKDOOR_PORT:
            if backdoor_reachable:
                return FakeSocket()
            raise ConnectionRefusedError("connection refused")
        raise AssertionError(f"unexpected port {port}")

    connector.calls = calls
    return connector


def test_run_returns_evidence_when_listener_appears():
    ftp_sock = FakeSocket()
    connector = make_connector(ftp_sock, backdoor_reachable=True)
    adapter = VsftpdBackdoorAdapter(connector=connector, listener_wait_seconds=0)
    step = AttackStep(plugin="vsftpd_backdoor", action="trigger", target="192.168.232.10", expected_predicate="listener_open")

    evidence = adapter.run(step)

    assert evidence.kind == "shell_access"
    assert "192.168.232.10" in evidence.summary
    assert evidence.source == "vsftpd_backdoor"
    assert any(b"USER aegis:)" in sent for sent in ftp_sock.sent)


def test_run_raises_when_listener_never_appears():
    ftp_sock = FakeSocket()
    connector = make_connector(ftp_sock, backdoor_reachable=False)
    adapter = VsftpdBackdoorAdapter(connector=connector, listener_wait_seconds=0)
    step = AttackStep(plugin="vsftpd_backdoor", action="trigger", target="192.168.232.10", expected_predicate="listener_open")

    with pytest.raises(VsftpdBackdoorError):
        adapter.run(step)


def test_run_raises_when_ftp_service_unreachable():
    def connector(address, timeout):
        raise ConnectionRefusedError("no route")

    adapter = VsftpdBackdoorAdapter(connector=connector, listener_wait_seconds=0)
    step = AttackStep(plugin="vsftpd_backdoor", action="trigger", target="10.0.0.1", expected_predicate="listener_open")

    with pytest.raises(VsftpdBackdoorError):
        adapter.run(step)
