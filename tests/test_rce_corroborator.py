from core.knowledge_base.models import (
    ConfidenceGrade,
    CorroborationOutcome,
    Evidence,
    Finding,
)
from plugins.corroboration.rce_validation import LiveRceCorroborator


def make_finding(target="192.168.232.10"):
    return Finding(
        title="vsftpd backdoor",
        target=target,
        claim="root shell listener reachable",
        primary_evidence=Evidence("shell_access", "listener observed", "vsftpd_backdoor"),
    )


class RespondingSocket:
    def __init__(self):
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def settimeout(self, value):
        pass

    def sendall(self, data: bytes):
        self.sent.append(data)

    def recv(self, n):
        # Echo back whatever nonce was sent, simulating a real shell round-trip
        sent_text = b"".join(self.sent).decode()
        nonce = sent_text.strip().removeprefix("echo ")
        return nonce.encode()


class SilentSocket(RespondingSocket):
    def recv(self, n):
        return b""


def test_corroborate_supports_when_nonce_echoed_back():
    def connector(address, timeout):
        return RespondingSocket()

    probe = LiveRceCorroborator(connector=connector)
    result = probe.corroborate(make_finding())

    assert result.outcome is CorroborationOutcome.SUPPORTS
    assert result.independent is True
    assert result.probe == "rce_validation"


def test_corroborate_contradicts_when_nonce_not_echoed():
    def connector(address, timeout):
        return SilentSocket()

    probe = LiveRceCorroborator(connector=connector)
    result = probe.corroborate(make_finding())

    assert result.outcome is CorroborationOutcome.CONTRADICTS


def test_corroborate_ambiguous_when_session_cannot_be_established():
    def connector(address, timeout):
        raise ConnectionRefusedError("refused")

    probe = LiveRceCorroborator(connector=connector)
    result = probe.corroborate(make_finding())

    assert result.outcome is CorroborationOutcome.AMBIGUOUS
    assert "could not establish independent session" in result.evidence.summary


def test_corroborate_uses_a_fresh_nonce_each_call():
    seen_payloads = []

    class RecordingSocket(RespondingSocket):
        def sendall(self, data: bytes):
            seen_payloads.append(data)
            super().sendall(data)

    def connector(address, timeout):
        return RecordingSocket()

    probe = LiveRceCorroborator(connector=connector)
    probe.corroborate(make_finding())
    probe.corroborate(make_finding())

    assert seen_payloads[0] != seen_payloads[1]  # nonce must not repeat
