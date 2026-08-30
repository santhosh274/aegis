"""Run live Monitor-phase discovery against a single, pre-authorized lab target.

This is the first script that touches a real target instead of a fixture. It
performs discovery ONLY -- no exploitation, no post-exploitation. It exists to
validate the real nmap_scanner.py adapter and to prove Observation objects flow
correctly from a live scan, same as they already do from the fixture adapter.

Usage:
    python scripts/run_live_discovery.py 192.168.232.10

Requirements:
    pip install python-nmap
    nmap binary installed and on PATH
    Target must be your own isolated lab VM -- see docs/architecture.md for the
    network isolation checklist before running this against anything.
"""
from __future__ import annotations

import sys

# Allow running directly via `python scripts/run_live_discovery.py`
sys.path.insert(0, ".")

from config.settings import ScopePolicy
from core.monitor.scanner_manager import ScannerManager
from core.analyze.utility_ranker import CandidateAction
from core.plan.planner import Planner
from plugins.scanners.nmap_scanner import NmapDiscoveryAdapter, NmapScanError


def _candidates_from(observations):
    return [
        CandidateAction(
            name=f"validate {obs.value} on {obs.target}",
            expected_gain=0.5,
            information_gain=0.8,
            cost=0.1,
            risk=0.05,
        )
        for obs in observations
        if obs.kind == "service"
    ]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/run_live_discovery.py <target-ip>")
        return 1
    target = sys.argv[1]

    # EDIT THIS: your one pre-declared lab host, matching the replacement gate.
    policy = ScopePolicy(
        allowed_hosts=(target,),
        allowed_plugins=("nmap_scanner",),
        lab_mode=True,
    )
    if not policy.permits_target(target):
        print(f"REJECTED: {target} is not in the allowed scope. Edit this script's ScopePolicy first.")
        return 1

    adapter = NmapDiscoveryAdapter()
    print(f"Scanning {target} (bounded port set, read-only -sV)...")
    try:
        raw_records = adapter.discover(target)
    except NmapScanError as exc:
        print(f"Scan failed: {exc}")
        return 1

    if not raw_records:
        print("No open services found in the scanned port range, or host did not respond.")
        return 0

    observations = ScannerManager().normalize(target, adapter.name, raw_records)
    print(f"\n{len(observations)} observation(s):")
    for obs in observations:
        print(f"  - {obs.kind}: {obs.value}  (source={obs.source})")

    candidates = _candidates_from(observations)
    selected = Planner().choose_next(candidates)
    print(f"\nPlanner's highest-utility next candidate: {selected.name if selected else 'none'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
