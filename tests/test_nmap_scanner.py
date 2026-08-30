import pytest

from plugins.scanners.nmap_scanner import NmapDiscoveryAdapter, NmapScanError


class FakeHostData:
    """Mimics python-nmap's per-host result object closely enough for our adapter."""

    def __init__(self, ports: dict[int, dict[str, str]]):
        self._ports = ports

    def all_protocols(self) -> list[str]:
        return ["tcp"] if self._ports else []

    def __getitem__(self, proto: str) -> dict[int, dict[str, str]]:
        return self._ports


class FakePortScanner:
    """Fake python-nmap PortScanner: scripted responses, no subprocess, no network."""

    def __init__(self, hosts: dict[str, dict[int, dict[str, str]]]):
        self._hosts = hosts
        self.scan_calls: list[dict[str, object]] = []

    def scan(self, hosts: str, arguments: str, timeout: int) -> None:
        self.scan_calls.append({"hosts": hosts, "arguments": arguments, "timeout": timeout})

    def all_hosts(self) -> list[str]:
        return list(self._hosts.keys())

    def __getitem__(self, host: str) -> FakeHostData:
        return FakeHostData(self._hosts[host])


def test_discover_returns_open_services_as_records():
    fake = FakePortScanner({
        "192.168.232.10": {
            22: {"state": "open", "name": "ssh", "product": "OpenSSH", "version": "4.7p1"},
            80: {"state": "open", "name": "http", "product": "Apache httpd", "version": "2.2.8"},
            9999: {"state": "closed", "name": "unknown", "product": "", "version": ""},
        }
    })
    adapter = NmapDiscoveryAdapter(scanner_factory=lambda: fake)

    records = adapter.discover("192.168.232.10")

    assert {"kind": "service", "value": "ssh/22 (OpenSSH 4.7p1)"} in records
    assert {"kind": "service", "value": "http/80 (Apache httpd 2.2.8)"} in records
    # closed port must not appear
    assert not any("9999" in r["value"] for r in records)


def test_discover_returns_empty_list_for_unresponsive_host():
    fake = FakePortScanner({})  # target never appears in all_hosts()
    adapter = NmapDiscoveryAdapter(scanner_factory=lambda: fake)

    assert adapter.discover("192.168.232.99") == []


def test_discover_uses_bounded_scan_arguments():
    fake = FakePortScanner({"192.168.232.10": {}})
    adapter = NmapDiscoveryAdapter(scanner_factory=lambda: fake, max_rate=50, ports="22,80")

    adapter.discover("192.168.232.10")

    call = fake.scan_calls[0]
    assert call["hosts"] == "192.168.232.10"
    assert "--max-rate 50" in call["arguments"]
    assert "-p 22,80" in call["arguments"]
    assert "-sV" in call["arguments"]
    # must never include vuln/brute NSE categories
    assert "vuln" not in call["arguments"]
    assert "brute" not in call["arguments"]


@pytest.mark.parametrize("bad_target", ["", "10.0.0.1,10.0.0.2", "10.0.0.0/24", "10.0.0.1; rm -rf /"])
def test_discover_rejects_unsafe_target_strings_before_scanning(bad_target):
    fake = FakePortScanner({})
    adapter = NmapDiscoveryAdapter(scanner_factory=lambda: fake)

    with pytest.raises(NmapScanError):
        adapter.discover(bad_target)

    assert fake.scan_calls == []  # never reached the scanner


def test_scan_failure_raises_nmap_scan_error():
    class ExplodingScanner(FakePortScanner):
        def scan(self, hosts: str, arguments: str, timeout: int) -> None:
            raise RuntimeError("nmap process exited with code 1")

    adapter = NmapDiscoveryAdapter(scanner_factory=lambda: ExplodingScanner({}))

    with pytest.raises(NmapScanError):
        adapter.discover("192.168.232.10")
