"""Live nmap-based discovery adapter.

This is the first adapter permitted through the replacement gate defined in
docs/initial-tool-chaining-plan.md: discovery only, bounded to a single explicit
target and a small, explicit port set. It performs a read-only service/version
scan (-sV) -- no vulnerability scripts, no brute-forcing, no exploitation.

The nmap client library is imported lazily (inside a factory function) so this
module can be imported, and its logic unit-tested, without python-nmap or the
nmap binary being installed. ScopePolicy at the Executor layer is the actual
safety boundary; the validation here is a second, adapter-local check against
obviously malformed or unsafe target strings.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

# Well-known Metasploitable2 service footprint. Deliberately narrow and explicit
# rather than a full 1-65535 sweep, per the replacement gate's "small approved
# port set" requirement. Extend only with a documented reason per port.
DEFAULT_PORTS = (
    "21-23,25,53,80,111,139,445,512-514,1099,1524,2049,"
    "3306,3632,5432,5900,6000,6667,8009,8180,8787"
)


class NmapScanError(RuntimeError):
    """Raised when the underlying nmap invocation fails or is misconfigured."""


class PortScannerLike(Protocol):
    def scan(self, hosts: str, arguments: str, timeout: int) -> Any: ...
    def all_hosts(self) -> list[str]: ...
    def __getitem__(self, host: str) -> Any: ...


def _default_scanner_factory() -> PortScannerLike:
    """Constructs the real python-nmap scanner. Import stays inside this function
    so the module loads fine in environments/tests without the dependency."""
    try:
        import nmap  # python-nmap
    except ImportError as exc:
        raise NmapScanError(
            "python-nmap is not installed; run `pip install python-nmap` "
            "and ensure the `nmap` binary is on PATH"
        ) from exc
    return nmap.PortScanner()


@dataclass
class NmapDiscoveryAdapter:
    """Live discovery adapter. Read-only service/version detection only.

    Deliberately excludes: OS fingerprinting beyond default -sV behavior, NSE
    vuln/brute categories, and any port range beyond DEFAULT_PORTS unless
    explicitly overridden. Those are separate, later-gated capabilities.

    Matches FixtureDiscoveryAdapter's contract exactly: `.name` attribute and
    `.discover(target) -> list[dict[str, str]]` with "kind"/"value" keys, so
    ScannerManager.normalize() and everything downstream needs no changes.
    """

    name: str = "nmap_scanner"
    ports: str = DEFAULT_PORTS
    timeout_seconds: int = 120
    max_rate: int = 100  # packets/sec cap -- keeps scans bounded and polite
    scanner_factory: Callable[[], PortScannerLike] = field(default=_default_scanner_factory)

    def discover(self, target: str) -> list[dict[str, str]]:
        """Run a bounded, read-only scan and return raw records.

        Raises NmapScanError on invalid target strings or scan failure. Returns
        an empty list (not an error) if the host doesn't respond within scope --
        that's a legitimate "no observations yet" result, not a fault.
        """
        self._validate_target(target)
        scanner = self.scanner_factory()
        arguments = f"-sV --version-light --max-rate {self.max_rate} -p {self.ports}"
        try:
            scanner.scan(hosts=target, arguments=arguments, timeout=self.timeout_seconds)
        except Exception as exc:  # covers nmap.PortScannerError and subprocess errors
            raise NmapScanError(f"nmap scan failed for {target}: {exc}") from exc

        if target not in scanner.all_hosts():
            return []

        records: list[dict[str, str]] = []
        host_data = scanner[target]
        for proto in host_data.all_protocols():
            for port in sorted(host_data[proto].keys()):
                port_info = host_data[proto][port]
                if port_info.get("state") != "open":
                    continue
                service = port_info.get("name", "unknown")
                product = port_info.get("product", "")
                version = port_info.get("version", "")
                descriptor = f"{service}/{port}"
                if product:
                    descriptor += f" ({product} {version})".rstrip()
                records.append({"kind": "service", "value": descriptor})
        return records

    @staticmethod
    def _validate_target(target: str) -> None:
        """Reject anything that isn't a bare IPv4/hostname -- no CIDR ranges, no
        comma-separated lists, no shell/argument-injection characters. This is a
        defense-in-depth check; ScopePolicy at the Executor layer is the actual
        authorization boundary and must also allowlist this exact target."""
        if not target or any(c in target for c in " ,/;|&$`\n\t"):
            raise NmapScanError(f"invalid or unsafe target string: {target!r}")
