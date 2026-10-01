"""Live nuclei-based web vulnerability scanner adapter.

Nuclei (ProjectDiscovery) is a template-driven vulnerability scanner. This
adapter is a bounded, read-only wrapper: a single URL target, JSONL output, a
fixed polite rate limit, bounded request time, and no network update checks.
Each JSONL result is parsed into a normalized record that carries a small
ATT&CK technique mapping (derived from template tags), which the exploit
planner can use to connect web findings to initial-access techniques.

The binary is located lazily (via shutil.which) so this module can be imported
and unit-tested without nuclei installed; when the binary is absent, discover()
raises NucleiScanError with installation guidance. ScopePolicy at the Executor
layer is the actual authorization boundary; validation here is a second,
adapter-local check against malformed target strings.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Callable

# Template-tag/substring -> ATT&CK technique id for planning attribution.
# Deliberately small and conservative; unknown templates get no mapping.
TECHNIQUE_MAP: dict[str, str] = {
    "default-login": "T1078",   # Valid Accounts
    "default-logins": "T1078",
    "exposed-panel": "T1190",   # Exploit Public-Facing Application
    "exposure": "T1190",
    "panel": "T1190",
    "misconfig": "T1190",
    "misconfiguration": "T1190",
    "cve": "T1190",
    "rce": "T1190",
    "sqli": "T1190",
}

RUNNER_RESULT = Any  # duck-typed: .returncode, .stdout, .stderr


class NucleiScanError(RuntimeError):
    """Raised when the nuclei binary is missing, the target is unsafe, or the
    scan fails or times out."""


def _validate_target(target: str) -> None:
    """Reject anything but a bare IPv4/hostname (no ranges, lists, or shell
    characters) before building the nuclei URL."""
    if not target or any(c in target for c in " ,/;|&$`\n\t"):
        raise NucleiScanError(f"invalid or unsafe target string: {target!r}")


@dataclass
class NucleiScannerAdapter:
    """Live scanner adapter matching the .name + .discover(target) contract,
    producing "kind"/"value" records for ScannerManager.normalize()."""

    name: str = "nuclei"
    timeout_seconds: int = 60
    rate_limit: int = 25
    scheme: str = "http"
    # Also probe TLS on the same host: most real-world web targets are HTTPS.
    # Both runs are bounded and independent; results are merged and deduped.
    also_https: bool = True

    # Injectable binary locator and runner for testing/mocking.
    which: Callable[[str], str | None] | None = None
    run: Callable[[list[str]], RUNNER_RESULT] | None = None

    def __post_init__(self) -> None:
        if self.which is None:
            self.which = shutil.which
        if self.run is None:
            # Timeout covers the request budget plus template-startup overhead.
            self.run = lambda cmd: subprocess.run(  # type: ignore[assignment]
                cmd, capture_output=True, text=True, timeout=self.timeout_seconds + 30
            )

    def discover(self, target: str) -> list[dict[str, str]]:
        _validate_target(target)

        binary = self.which("nuclei")
        if not binary:
            raise NucleiScanError(
                "the `nuclei` binary was not found on PATH. Install it from "
                "https://github.com/projectdiscovery/nuclei (or `go install "
                "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest`) and "
                "ensure `nuclei` resolves before running this scan. Templates: "
                "`nuclei -update-templates`."
            )

        records: list[dict[str, str]] = []
        seen: set[str] = set()
        schemes = [self.scheme] + (["https"] if self.also_https and self.scheme != "https" else [])
        for scheme in schemes:
            for record in self._scan_scheme(target, scheme, binary):
                if record["value"] not in seen:
                    seen.add(record["value"])
                    records.append(record)
        return records

    def _scan_scheme(self, target: str, scheme: str, binary: str) -> list[dict[str, str]]:
        url = f"{scheme}://{target}"
        cmd = [
            binary,
            "-u",
            url,
            "-jsonl",
            "-silent",
            "-nc",
            "-disable-update-check",
            "-rl",
            str(self.rate_limit),
            "-timeout",
            str(self.timeout_seconds),
        ]
        try:
            proc = self.run(cmd)
        except Exception as exc:  # noqa: BLE001 - covers subprocess errors incl. TimeoutExpired
            raise NucleiScanError(f"nuclei scan failed for {target}: {exc}") from exc

        stdout = (proc.stdout or "") if isinstance(proc, tuple) else getattr(proc, "stdout", "") or ""
        if not stdout and getattr(proc, "returncode", 0) != 0:
            stderr = (getattr(proc, "stderr", "") or "").strip()
            raise NucleiScanError(
                f"nuclei exited with {getattr(proc, 'returncode', '?')} against {target}"
                + (f": {stderr[:400]}" if stderr else "")
            )

        records: list[dict[str, str]] = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            info = obj.get("info") or {}
            if obj.get("type") != "http" and not info:
                continue
            name = info.get("name") or obj.get("template-id") or "unmatched"
            severity = info.get("severity") or "unknown"
            matched_at = obj.get("matched-at") or url
            raw_tags = info.get("tags") or []
            if isinstance(raw_tags, str):
                raw_tags = raw_tags.split(",")
            tags = " ".join(str(t) for t in raw_tags)
            technique = self._technique_for(tags)
            value = f"[{severity}] {name} @ {matched_at}"
            if technique:
                value += f" (ATT&CK {technique})"
            records.append({"kind": "nuclei_vuln", "value": value})
        return records

    @staticmethod
    def _technique_for(tags: str) -> str:
        tags_lower = tags.lower()
        for key, technique in TECHNIQUE_MAP.items():
            if key in tags_lower:
                return technique
        return ""