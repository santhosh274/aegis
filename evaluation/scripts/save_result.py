from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, ".")

def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python evaluation/scripts/save_result.py <finding.json> <scenario-name>")
        return 1
    source_path, scenario = Path(sys.argv[1]), sys.argv[2]
    if not source_path.exists():
        print(f"Error: {source_path} not found")
        return 1
    data = json.loads(source_path.read_text())
    data["scenario"] = scenario
    # pull verification verdict if present
    if "verification_verdict" not in data:
        print("WARNING: no verification_verdict found — run run_verification.py first")
    out_dir = Path("evaluation/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{scenario}.json"
    out_path.write_text(json.dumps(data, indent=2, default=str))
    print(f"Saved: {out_path} (verdict={data.get('verification_verdict', 'missing')})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())