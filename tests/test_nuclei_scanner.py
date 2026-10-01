import json
from types import SimpleNamespace

import pytest

from plugins.scanners.nuclei_scanner import NucleiScanError, NucleiScannerAdapter


def make_runner(results: list[SimpleNamespace], **recorded):
    calls: list[list[str]] = []

    def runner(cmd):
        calls.append(cmd)
        if isinstance(results, Exception):
            raise results
        return results.pop(0) if results else SimpleNamespace(returncode=0, stdout="", stderr="")

    runner.calls = calls
    for key, value in recorded.items():
        setattr(runner, key, value)
    return runner


def jsonl_line(**fields):
    info = {
        "name": fields.get("name", "Test Template"),
        "severity": fields.get("severity", "high"),
        "tags": fields.get("tags", "cve,exposure"),
        "description": fields.get("description", ""),
    }
    payload = {
        "template-id": fields.get("template-id", "test-template"),
        "type": "http",
        "info": info,
        "matched-at": fields.get("matched-at", "http://192.168.232.10/"),
    }
    return json.dumps(payload)


def test_discover_parses_jsonl_into_records():
    sample = "\n".join(
        [
            jsonl_line(name="Drupal Admin Login", tags="cve,drupal,default-login"),
            jsonl_line(name="Nginx Version Detection", tags="nginx,tech"),
            "not json",
        ]
    )
    runner = make_runner(
        [
            SimpleNamespace(returncode=0, stdout=sample, stderr=""),
            SimpleNamespace(returncode=0, stdout="", stderr=""),  # https pass
        ]
    )
    adapter = NucleiScannerAdapter(which=lambda _: "/opt/nuclei", run=runner)

    records = adapter.discover("192.168.232.10")

    assert all(r["kind"] == "nuclei_vuln" for r in records)
    assert len(records) == 2  # the garbage line is skipped
    first = records[0]
    assert "Drupal Admin Login" in first["value"]
    assert "(ATT&CK T1078)" in first["value"]  # default-login -> Valid Accounts
    assert "ATT&CK" not in records[1]["value"]  # nginx/tech has no mapping
    # bounded, shell-free command against a single URL
    cmd = runner.calls[0]
    assert cmd[0] == "/opt/nuclei"
    assert "-u" in cmd
    assert "http://192.168.232.10" in cmd
    assert any(arg.startswith("-rl") or arg == "25" for arg in cmd)
    assert "-disable-update-check" in cmd


def test_discover_also_probes_https_and_dedupes():
    duplicate = jsonl_line(name="Same Finding", tags="cve")
    runner = make_runner(
        [
            SimpleNamespace(returncode=0, stdout=duplicate, stderr=""),
            SimpleNamespace(returncode=0, stdout=duplicate, stderr=""),
        ]
    )
    adapter = NucleiScannerAdapter(which=lambda _: "/opt/nuclei", run=runner)

    records = adapter.discover("192.168.232.10")

    assert len(records) == 1  # identical result from both schemes is deduped
    urls = [cmd[cmd.index("-u") + 1] for cmd in runner.calls]
    assert urls == ["http://192.168.232.10", "https://192.168.232.10"]


def test_discover_can_skip_https_pass():
    runner = make_runner(
        [
            SimpleNamespace(returncode=0, stdout="", stderr=""),
        ]
    )
    adapter = NucleiScannerAdapter(which=lambda _: "/opt/nuclei", run=runner, also_https=False)

    assert adapter.discover("192.168.232.10") == []
    assert len(runner.calls) == 1


@pytest.mark.parametrize("bad_target", ["", "10.0.0.1,10.0.0.2", "10.0.0.0/24", "10.0.0.1; rm -rf /"])
def test_discover_rejects_unsafe_target_strings_before_running(bad_target):
    runner = make_runner([])
    adapter = NucleiScannerAdapter(which=lambda _: "/opt/nuclei", run=runner)

    with pytest.raises(NucleiScanError):
        adapter.discover(bad_target)

    assert runner.calls == []  # never produced a command


def test_default_scan_port_set_covers_https():
    """Regression guard: a public HTTPS-only site must be discoverable."""
    from plugins.scanners.nmap_scanner import DEFAULT_PORTS

    ports = set(DEFAULT_PORTS.replace(" ", "").split(","))
    assert "443" in ports
    assert {"80", "8080", "8443"} <= ports


def test_discover_raises_helpful_error_when_binary_missing():
    runner = make_runner([])
    adapter = NucleiScannerAdapter(which=lambda _: None, run=runner)

    with pytest.raises(NucleiScanError, match=r"nuclei.*github.com/projectdiscovery/nuclei") as exc_info:
        adapter.discover("192.168.232.10")

    assert "PATH" in str(exc_info.value)
    assert runner.calls == []


def test_scan_failure_raises_nuclei_scan_error():
    runner = make_runner([])
    adapter = NucleiScannerAdapter(which=lambda _: "/opt/nuclei", run=runner)

    def failing(cmd):
        raise RuntimeError("nuclei process crashed")

    adapter.run = failing  # type: ignore[assignment]
    with pytest.raises(NucleiScanError, match="nuclei scan failed"):
        adapter.discover("192.168.232.10")


def test_nonzero_exit_without_output_raises():
    runner = make_runner(
        [SimpleNamespace(returncode=2, stdout="", stderr="templates missing")]
    )
    adapter = NucleiScannerAdapter(which=lambda _: "/opt/nuclei", run=runner)

    with pytest.raises(NucleiScanError, match="nuclei exited with 2"):
        adapter.discover("192.168.232.10")