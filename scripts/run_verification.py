"""Run live remediation verification against a real target.

Loads the Finding saved by run_first_exploit.py, re-attempts the EXACT original
exploit chain against the (hopefully now patched) target, checks independent
reachability as "controls," diffs a before/after exposure snapshot for
regression detection, and produces the verdict: Verified Closed, Reopened, or
Regression Detected.

Usage:
    # 1. Before applying any fix:
    python scripts/capture_exposure_snapshot.py 192.168.232.10 before.json

    # 2. Apply your remediation on the VM, e.g.:
    #      sudo service vsftpd stop

    # 3. Then:
    python scripts/run_verification.py 192.168.232.10 finding.json before.json
"""
from __future__ import annotations

import json
import socket
import sys

sys.path.insert(0, ".")

from core.knowledge_base.json_store import load_finding
from core.knowledge_base.models import RemediationEvent
from core.verify.regression_detector import Exposure
from core.verify.replay_engine import ReplayEngine
from plugins.exploits.vsftpd_backdoor import VsftpdBackdoorAdapter, VsftpdBackdoorError
from plugins.scanners.nmap_scanner import NmapDiscoveryAdapter, NmapScanError
from reporting.generator import render_finding


def check_controls(target: str) -> bool:
    """Independent reachability check -- deliberately NOT tied to the
    vulnerability being verified (uses SSH, not FTP), so a positive result
    here can't be explained by the same fix that (we hope) closed the finding."""
    try:
        with socket.create_connection((target, 22), timeout=5):
            return True
    except OSError:
        return False


def capture_after_exposures(target: str) -> set[Exposure]:
    adapter = NmapDiscoveryAdapter()
    try:
        records = adapter.discover(target)
    except NmapScanError:
        return set()
    exposures = set()
    for record in records:
        left = record["value"].split(" ", 1)[0]
        service, _, port_str = left.partition("/")
        try:
            port = int(port_str)
        except ValueError:
            continue
        exposures.add(Exposure(target=target, service=service, port=port, fingerprint=record["value"]))
    return exposures


def load_before_exposures(path: str) -> set[Exposure]:
    with open(path) as f:
        data = json.load(f)
    return {Exposure(target=e["target"], service=e["service"], port=e["port"], fingerprint=e.get("fingerprint", "")) for e in data}


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: python scripts/run_verification.py <target-ip> <finding.json> <before.json>")
        return 1
    target, finding_path, before_path = sys.argv[1], sys.argv[2], sys.argv[3]

    finding = load_finding(finding_path)
    if finding.target != target:
        print(f"WARNING: finding.json target ({finding.target}) differs from given target ({target})")

    print("Checking controls (independent reachability, SSH)...")
    controls_ok = check_controls(target)
    print(f"  controls_ok = {controls_ok}")

    print("Capturing post-remediation exposure snapshot...")
    before = load_before_exposures(before_path)
    after = capture_after_exposures(target)

    adapter = VsftpdBackdoorAdapter()

    def execute_step(step) -> bool:
        """Returns True if the original exploit chain still reproduces (bad --
        fix ineffective), False if it's now blocked (good -- fix held)."""
        try:
            adapter.run(step)
            return True
        except VsftpdBackdoorError:
            return False

    print("Re-attempting original exploit chain...")
    result = ReplayEngine().verify(
        finding,
        execute_step,
        controls_ok=controls_ok,
        before=before,
        after=after,
    )

    # Record the remediation event we're verifying against, for the audit trail.
    RemediationEvent(finding_id=finding.id, description="reported fix, verified via live replay")

    print()
    print(render_finding(finding, verification=result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
