"""Save a finding.json into evaluation/results/ with a scenario label.

Run this after each scenario run to build up the evaluation dataset.

Usage:
    python evaluation/scripts/save_result.py finding.json vsftpd_unpatched
    python evaluation/scripts/save_result.py finding.json vsftpd_stopped
    python evaluation/scripts/save_result.py finding.json vsftpd_restarted

Scenario names must match keys in run_metrics.py's GROUND_TRUTH table.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, ".")


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python evaluation/scripts/save_result.py <finding.json> <scenario-name>")
        print("\nAvailable scenario names:")
        print("  vsftpd_unpatched   — vsftpd running, no fix applied")
        print("  vsftpd_stopped     — vsftpd stopped (genuine fix)")
        print("  vsftpd_restarted   — vsftpd restarted after stop (ineffective fix)")
        return 1

    source_path = Path(sys.argv[1])
    scenario = sys.argv[2]

    if not source_path.exists():
        print(f"Error: {source_path} not found")
        return 1

    data = json.loads(source_path.read_text())
    data["scenario"] = scenario

    out_dir = Path("evaluation/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{scenario}.json"
    out_path.write_text(json.dumps(data, indent=2, default=str))
    print(f"Saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
