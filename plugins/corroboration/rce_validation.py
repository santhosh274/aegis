from __future__ import annotations

import socket
from typing import Callable
from uuid import uuid4

from core.knowledge_base.models import Corroboration, CorroborationOutcome, Evidence, Finding


class RceCorroborator:
    """Fixture-style corroborator: outcome is supplied externally.

    Kept for deterministic tests (see test_initial_chain.py / test_verify.py),
    which script known-good/known-bad/ambiguous scenarios without needing a
    live target.
    """

    name = "rce_validation"

    def __init__(self, nonce_observed: bool | None):
        self.nonce_observed = nonce_observed

    def corroborate(self, finding: Finding) -> Corroboration:
        outcome = CorroborationOutcome.AMBIGUOUS if self.nonce_observed is None else (CorroborationOutcome.SUPPORTS if self.nonce_observed else CorroborationOutcome.CONTRADICTS)
        summary = "benign nonce result was indeterminate" if self.nonce_observed is None else ("benign nonce observed in independent session" if self.nonce_observed else "benign nonce was not observed")
        return Corroboration(self.name, outcome, Evidence("rce_check", summary, self.name), True, "separate session and nonce predicate")


class LiveRceCorroborator:
    """Genuine independent corroboration: opens a SEPARATE session to the
    reported shell listener and validates a fresh, single-use nonce round-trip.

    This does not reuse the exploit adapter's connection or trust its report --
    it establishes its own socket, sends its own nonce, and only trusts what it
    independently observes. Matches the devil's-advocate contract: an attempt
    to disprove the primary claim, not to rubber-stamp it.
    """

    name = "rce_validation"

    def __init__(
        self,
        port: int = 6200,
        timeout: float = 5.0,
        connector: Callable[[tuple[str, int], float], socket.socket] = socket.create_connection,
    ):
        self.port = port
        self.timeout = timeout
        self.connector = connector

    def corroborate(self, finding: Finding) -> Corroboration:
        import time
    
        nonce = f"AEGIS-{uuid4().hex[:8]}"
    
        # Wait for the shell to spawn after the primary adapter's trigger
        time.sleep(4.0)
    
        # First and only connection to port 6200 — shell is still alive
        try:
            with self.connector((finding.target, self.port), self.timeout) as sock:
                sock.settimeout(self.timeout)
                try:
                    sock.recv(4096)   # drain any prompt
                except socket.timeout:
                    pass
                sock.sendall(f"echo {nonce}\n".encode())
                time.sleep(1.0)
                try:
                    output = sock.recv(4096)
                except socket.timeout:
                    output = b""
        except OSError as exc:
            return Corroboration(
                self.name,
                CorroborationOutcome.AMBIGUOUS,
                Evidence("rce_check", f"shell not reachable on port 6200: {exc}", self.name),
                True,
                "independent nonce predicate on shell listener",
            )
    
        observed = nonce.encode() in output
        outcome = CorroborationOutcome.SUPPORTS if observed else CorroborationOutcome.CONTRADICTS
        summary = (
            "benign nonce observed in independent shell session"
            if observed
            else "nonce not observed in shell session"
        )
        return Corroboration(
            self.name, outcome,
            Evidence("rce_check", summary, self.name),
            True,
            "independent nonce predicate on shell listener",
        )   