"""AEGIS evaluation harness — collects all three project metrics.

Reads the findings and verification results produced by the live scripts,
compares them against the ground-truth scenario manifest, and writes a
metrics summary to evaluation/results/metrics.json.

Usage:
    # After running the full exploit + verify arc for each scenario:
    python evaluation/scripts/run_metrics.py

Three metrics are measured:

    1. False-positive rate reduction
       How many findings ADAPT would report as unconditional fact vs how many
       AEGIS downgrades to suspected / needs_human_review via devil's-advocate.

    2. Confidence-grading accuracy
       AEGIS confidence grade vs manually-verified ground truth per finding.

    3. Remediation-verification accuracy
       AEGIS Verify verdict vs known patch state (closed/ineffective/regressed).
       Includes the false-all-clear rate specifically.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, ".")

from evaluation.scripts.collect_metrics import (
    accuracy,
    confusion,
    false_all_clear_rate,
)


# ── Ground-truth scenario table ──────────────────────────────────────────────
# Each entry maps a scenario name to:
#   ground_truth_exploitable : was the target genuinely exploitable?
#   ground_truth_fixed        : was the patch genuine?
#   expected_confidence       : what grade should AEGIS produce?
#   expected_verdict          : what verification verdict should AEGIS produce?
GROUND_TRUTH: dict[str, dict] = {
    "vsftpd_unpatched": {
        "ground_truth_exploitable": True,
        "ground_truth_fixed": False,
        "expected_confidence": "confirmed",
        "expected_verdict": "reopened",
        "description": "vsftpd running, no fix applied",
    },
    "vsftpd_stopped": {
        "ground_truth_exploitable": True,
        "ground_truth_fixed": False,
        "expected_confidence": "confirmed",
        "expected_verdict": "regression_detected",
        "description": "vsftpd stopped — original blocked but http/8180 regression found",
    },
    "vsftpd_restarted": {
        "ground_truth_exploitable": True,
        "ground_truth_fixed": False,
        "expected_confidence": "confirmed",
        "expected_verdict": "reopened",
        "description": "vsftpd restarted after stop — ineffective fix",
    },
}


@dataclass
class MetricResult:
    name: str
    value: float
    detail: dict


@dataclass
class EvaluationReport:
    timestamp: str
    total_findings: int
    false_positive_rate_adapt_baseline: float
    false_positive_rate_aegis: float
    fp_reduction_percent: float
    confidence_accuracy: float
    confidence_confusion: dict
    verification_accuracy: float
    false_all_clear_rate: float
    verification_confusion: dict
    raw_results: list[dict]


def load_results_dir(results_dir: Path) -> list[dict]:
    """Load all finding JSON files from the results directory."""
    findings = []
    for path in sorted(results_dir.glob("*.json")):
        if path.name == "metrics.json":
            continue
        try:
            data = json.loads(path.read_text())
            findings.append(data)
        except Exception as exc:
            print(f"  warning: could not load {path.name}: {exc}")
    return findings


def measure_fp_reduction(findings: list[dict]) -> tuple[float, float, float]:
    """Compare ADAPT-style flat reporting vs AEGIS confidence grading.

    ADAPT baseline: every successful exploit = confirmed (flat, unconditional).
    AEGIS: only findings with corroboration support reach 'confirmed'.
    """
    total = len(findings)
    if total == 0:
        return 0.0, 0.0, 0.0

    adapt_fp = sum(
        1 for f in findings
        if f.get("ground_truth_exploitable") is False
    )
    aegis_fp = sum(
        1 for f in findings
        if f.get("ground_truth_exploitable") is False
        and f.get("confidence") == "confirmed"
    )

    adapt_rate = adapt_fp / total
    aegis_rate = aegis_fp / total
    reduction = ((adapt_rate - aegis_rate) / adapt_rate * 100) if adapt_rate > 0 else 100.0
    return adapt_rate, aegis_rate, reduction


def measure_confidence_accuracy(findings: list[dict]) -> tuple[float, dict]:
    """AEGIS confidence grade vs ground truth."""
    expected = [f["expected_confidence"] for f in findings if "expected_confidence" in f]
    observed = [f.get("confidence", "unknown") for f in findings if "expected_confidence" in f]
    if not expected:
        return 0.0, {}
    return accuracy(expected, observed), confusion(expected, observed)


def measure_verification_accuracy(findings: list[dict]) -> tuple[float, float, dict]:
    """AEGIS Verify verdict vs known patch state."""
    with_verdict = [f for f in findings if "verification_verdict" in f and "expected_verdict" in f]
    if not with_verdict:
        return 0.0, 0.0, {}

    expected = [f["expected_verdict"] for f in with_verdict]
    observed = [f["verification_verdict"] for f in with_verdict]
    expected_exploitable = [f.get("ground_truth_exploitable", False) for f in with_verdict]

    acc = accuracy(expected, observed)
    facr = false_all_clear_rate(expected_exploitable, observed)
    conf = confusion(expected, observed)
    conf_str = {f"{k[0]} → {k[1]}": v for k, v in conf.items()}
    return acc, facr, conf_str


def main() -> int:
    results_dir = Path("evaluation/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = results_dir / "metrics.json"

    print("AEGIS Evaluation Harness")
    print("=" * 40)

    # ── Load saved findings from results dir ──────────────────────────────
    raw = load_results_dir(results_dir)

    # ── Annotate with ground truth from the manifest ──────────────────────
    findings: list[dict] = []
    for f in raw:
        scenario = f.get("scenario")
        gt = GROUND_TRUTH.get(scenario, {})
        findings.append({**f, **gt})

    if not findings:
        print("\nNo result files found in evaluation/results/")
        print("Run the following scripts first for each scenario:")
        print("  python scripts/run_first_exploit.py <target>")
        print("  python scripts/run_verification.py <target> finding.json before.json")
        print("  Then copy the finding.json to evaluation/results/<scenario>.json")
        print("  and add a 'scenario' field matching a GROUND_TRUTH key.")
        return 1

    total = len(findings)
    print(f"\nLoaded {total} finding(s) from evaluation/results/")

    # ── Metric 1: False-positive reduction ───────────────────────────────
    adapt_fp, aegis_fp, fp_reduction = measure_fp_reduction(findings)
    print(f"\nMetric 1 — False-positive rate")
    print(f"  ADAPT baseline (flat reporting): {adapt_fp:.1%}")
    print(f"  AEGIS (confidence-graded):       {aegis_fp:.1%}")
    print(f"  Reduction:                        {fp_reduction:.1f}%")

    # ── Metric 2: Confidence-grading accuracy ────────────────────────────
    conf_acc, conf_confusion = measure_confidence_accuracy(findings)
    print(f"\nMetric 2 — Confidence-grading accuracy")
    print(f"  Accuracy vs ground truth: {conf_acc:.1%}")
    if conf_confusion:
        for pair, count in conf_confusion.items():
            print(f"  {pair}: {count}")

    # ── Metric 3: Remediation-verification accuracy ──────────────────────
    ver_acc, facr, ver_confusion = measure_verification_accuracy(findings)
    print(f"\nMetric 3 — Remediation-verification accuracy")
    print(f"  Accuracy:             {ver_acc:.1%}")
    print(f"  False all-clear rate: {facr:.1%}")
    if ver_confusion:
        for pair, count in ver_confusion.items():
            print(f"  {pair}: {count}")

    # ── Write full report ─────────────────────────────────────────────────
    report = EvaluationReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_findings=total,
        false_positive_rate_adapt_baseline=round(adapt_fp, 4),
        false_positive_rate_aegis=round(aegis_fp, 4),
        fp_reduction_percent=round(fp_reduction, 2),
        confidence_accuracy=round(conf_acc, 4),
        confidence_confusion={str(k): v for k, v in conf_confusion.items()},
        verification_accuracy=round(ver_acc, 4),
        false_all_clear_rate=round(facr, 4),
        verification_confusion=ver_confusion,
        raw_results=findings,
    )

    metrics_path.write_text(json.dumps(asdict(report), indent=2, default=str))
    print(f"\nFull report written to {metrics_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
