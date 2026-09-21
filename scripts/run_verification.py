"""
Run live remediation verification against a real target.

Loads the Finding saved by run_first_exploit.py, re-attempts the EXACT original
exploit chain against the (hopefully now patched) target, checks independent
reachability as "controls", diffs a before/after exposure snapshot for
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
from pathlib import Path

sys.path.insert(0, ".")

from core.knowledge_base.json_store import load_finding
from core.knowledge_base.models import RemediationEvent
from core.verify.regression_detector import Exposure
from core.verify.replay_engine import ReplayEngine
from plugins.exploits.vsftpd_backdoor import (
    VsftpdBackdoorAdapter,
    VsftpdBackdoorError,
)
from plugins.scanners.nmap_scanner import (
    NmapDiscoveryAdapter,
    NmapScanError,
)
from reporting.generator import render_finding


def check_controls(target: str) -> bool:
    """
    Use known Metasploitable2 services as independent reachability controls.

    Returns True if at least one expected service is reachable.
    """
    for port in (80, 23, 21):
        try:
            with socket.create_connection((target, port), timeout=5):
                return True
        except OSError:
            continue

    return False


def capture_after_exposures(target: str) -> set[Exposure]:
    """Capture the post-remediation exposure snapshot."""
    adapter = NmapDiscoveryAdapter()

    try:
        records = adapter.discover(target)
    except NmapScanError:
        return set()

    exposures = set()

    for record in records:
        value = record.get("value", "")

        left = value.split(" ", 1)[0]
        service, _, port_str = left.partition("/")

        try:
            port = int(port_str)
        except ValueError:
            continue

        exposures.add(
            Exposure(
                target=target,
                service=service,
                port=port,
                fingerprint=value,
            )
        )

    return exposures


def load_before_exposures(path: str) -> set[Exposure]:
    """Load the pre-remediation exposure snapshot."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        Exposure(
            target=e["target"],
            service=e["service"],
            port=e["port"],
            fingerprint=e.get("fingerprint", ""),
        )
        for e in data
    }


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "usage: python scripts/run_verification.py "
            "<target-ip> <finding.json> <before.json>"
        )
        return 1

    target, finding_path, before_path = sys.argv[1:4]

    # Load finding
    try:
        finding = load_finding(finding_path)
    except Exception as exc:
        print(f"ERROR: Could not load finding: {exc}")
        return 1

    if finding.target != target:
        print(
            f"WARNING: finding.json target ({finding.target}) "
            f"differs from given target ({target})"
        )

    # Check independent controls
    print("Checking controls (independent reachability)...")
    controls_ok = check_controls(target)
    print(f"  controls_ok = {controls_ok}")

    # Capture post-remediation exposure snapshot
    print("Capturing post-remediation exposure snapshot...")

    try:
        before = load_before_exposures(before_path)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"ERROR: Could not load before snapshot: {exc}")
        return 1

    after = capture_after_exposures(target)

    print(f"  before exposures = {len(before)}")
    print(f"  after exposures  = {len(after)}")

    # Create exploit adapter
    adapter = VsftpdBackdoorAdapter()

    def execute_step(step) -> bool:
        """
        Returns True if the original exploit chain still reproduces
        (bad -- remediation ineffective).

        Returns False if the exploit is blocked
        (good -- remediation held).
        """
        try:
            adapter.run(step)
            return True
        except VsftpdBackdoorError:
            return False

    # Replay the original exploit chain
    print("Re-attempting original exploit chain...")

    result = ReplayEngine().verify(
        finding,
        execute_step,
        controls_ok=controls_ok,
        before=before,
        after=after,
    )

    # Record remediation event for the audit trail
    RemediationEvent(
        finding_id=finding.id,
        description="reported fix, verified via live replay",
    )

    # Render verification report
    print()
    print(render_finding(finding, verification=result))

    # ---------------------------------------------------------
    # FIX: Path must be imported from pathlib
    # ---------------------------------------------------------
    finding_file = Path(finding_path)

    try:
        data = json.loads(
            finding_file.read_text(encoding="utf-8")
        )

        data["verification_verdict"] = result.verdict

        finding_file.write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8",
        )

    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: Could not update {finding_path}: {exc}")
        return 1

    print(
        f"Updated {finding_path} with verdict: "
        f"{data['verification_verdict']}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())