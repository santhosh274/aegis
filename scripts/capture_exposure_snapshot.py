"""Capture an exposure snapshot for later regression comparison.

Run this BEFORE applying a remediation, so run_verification.py has a genuine
"before" state to diff against the post-remediation "after" scan. This is the
before/after pair the ReplayEngine/regression_detector need to tell "cleanly
fixed" apart from "original path blocked but a new one opened."

Usage:
    python scripts/capture_exposure_snapshot.py 192.168.232.10 before.json
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict

sys.path.insert(0, ".")

from plugins.scanners.nmap_scanner import NmapDiscoveryAdapter, NmapScanError


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python scripts/capture_exposure_snapshot.py <target-ip> <output.json>")
        return 1
    target, out_path = sys.argv[1], sys.argv[2]

    adapter = NmapDiscoveryAdapter()
    try:
        records = adapter.discover(target)
    except NmapScanError as exc:
        print(f"Scan failed: {exc}")
        return 1

    exposures = []
    for record in records:
        # record["value"] looks like "ssh/22 (OpenSSH 4.7p1 ...)" -- pull service/port
        left = record["value"].split(" ", 1)[0]
        service, _, port_str = left.partition("/")
        try:
            port = int(port_str)
        except ValueError:
            continue
        exposures.append({"target": target, "service": service, "port": port, "fingerprint": record["value"]})

    with open(out_path, "w") as f:
        json.dump(exposures, f, indent=2)

    print(f"Captured {len(exposures)} exposure(s) for {target} -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
