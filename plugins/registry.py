"""Aggregate adapter registry + ATT&CK-aware exploit planning.

Single registration point for the exploit adapters that the planner surface
knows about. Each exploit carries bounded metadata: a human title/claim, the
declarative action/predicate for its AttackStep, an importance score for
selection, the service observations it applies to, and its MITRE ATT&CK
technique mapping.

The engine's "multiple-vulnerability exploit flow" works by:
    1. Discovery (nmap, nuclei) produces observation value strings.
    2. choose_exploit() scores every registered, allowlisted exploit whose
       service pattern appears in an observation and returns the highest
       importance one (or None).
    3. trigger_exploit() disables that selection to a declarative AttackStep
       and runs it through the scope-gated Executor.
    4. Corroboration probes are selected per technique, never applied blindly.
"""
from __future__ import annotations

from typing import Any, Iterable

from core.execute.executor import ActionPlugin
from core.knowledge_base.models import AttackStep
from plugins.corroboration.http_exposure_validation import HttpExposureCorroborator
from plugins.corroboration.rce_validation import LiveRceCorroborator
from plugins.corroboration.ssh_revalidation import SshCredentialCorroborator
from plugins.exploits.http_exposed_service import HttpExposedServiceAdapter
from plugins.exploits.ssh_default_creds import SshWeakCredentialsAdapter
from plugins.exploits.vsftpd_backdoor import VsftpdBackdoorAdapter


# ---------------------------------------------------------------------------
# Exploit metadata (registry of record)
# ---------------------------------------------------------------------------

EXPLOIT_META: dict[str, dict[str, Any]] = {
    "vsftpd_backdoor": {
        "title": "vsftpd 2.3.4 backdoor (CVE-2011-2523)",
        "claim": "Backdoored vsftpd spawns a root shell listener on port 6200 when triggered",
        "action": "trigger_backdoor",
        "expected_predicate": "listener_open_on_6200",
        "importance": 90,
        "services": ("ftp/21",),
        "attck": ("T1190", "Exploit Public-Facing Application"),
        "description": "Triggers the intentionally backdoored vsftpd shipped with Metasploitable2 (no command execution).",
    },
    "ssh_weak_credentials": {
        "title": "SSH default credentials accepted",
        "claim": "A default credential authenticates over SSH using a preset allowlist",
        "action": "authenticate_default_credentials",
        "expected_predicate": "authentication_accepted",
        "importance": 80,
        "services": ("ssh/22",),
        "attck": ("T1078", "Valid Accounts"),
        "description": "Attempts a small fixed set of known default SSH credentials (authentication only, no post-auth activity).",
    },
    "http_exposed_service": {
        "title": "Known-vulnerable web application exposed",
        "claim": "A known-vulnerable web application is reachable on the public interface",
        "action": "fingerprint_web_services",
        "expected_predicate": "known_application_marker_present",
        "importance": 50,
        "services": (
            "http/80",
            "http/8180",
            "phpmyadmin",
            "dvwa",
            "mutillidae",
            "tomcat",
        ),
        "attck": ("T1190", "Exploit Public-Facing Application"),
        "description": "Read-only fingerprinting of known-vulnerable web applications (phpMyAdmin, DVWA, Mutillidae, Tomcat).",
    },
}

# ---------------------------------------------------------------------------
# Adapter instances
# ---------------------------------------------------------------------------

EXPLOITS: dict[str, ActionPlugin] = {
    "vsftpd_backdoor": VsftpdBackdoorAdapter(),
    "ssh_weak_credentials": SshWeakCredentialsAdapter(),
    "http_exposed_service": HttpExposedServiceAdapter(),
}

# ---------------------------------------------------------------------------
# Technique-scoped corroboration probes
# ---------------------------------------------------------------------------

CORROBORATORS: dict[str, list[Any]] = {
    "vsftpd_backdoor": [LiveRceCorroborator()],
    "ssh_weak_credentials": [SshCredentialCorroborator()],
    "http_exposed_service": [HttpExposureCorroborator()],
}


def is_exploit(name: str) -> bool:
    return name in EXPLOITS


def exploit_meta(name: str) -> dict[str, Any] | None:
    return EXPLOIT_META.get(name)


def choose_exploit(
    observation_values: Iterable[str],
    allowed_plugins: Iterable[str],
) -> str | None:
    """Return the highest-importance allowlisted exploit whose service pattern
    appears in any observation value, or None when nothing matches."""
    allowed = {str(p) for p in allowed_plugins}
    best_score = -1
    best_name: str | None = None
    for name, meta in EXPLOIT_META.items():
        if name not in allowed:
            continue
        patterns = tuple(p.lower() for p in meta["services"])
        if any(any(pattern in obs.lower() for pattern in patterns) for obs in observation_values):
            score = int(meta["importance"])
            if score > best_score:
                best_score = score
                best_name = name
    return best_name


def reproduce(step: AttackStep) -> bool:
    """Deterministic replay of a recorded declarative step via its registered
    adapter. Any adapter-level/OS failure means 'not reproduced'."""
    adapter = EXPLOITS.get(step.plugin)
    if adapter is None:
        return False
    try:
        adapter.run(step)
    except (RuntimeError, OSError):
        return False
    return True