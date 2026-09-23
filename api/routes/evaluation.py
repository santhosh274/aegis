from __future__ import annotations

import json
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.findings_io import RESULTS_DIR, ROOT
from api.sse import format_sse, pipeline_event, sse_response
from evaluation.scripts.run_metrics import (
    GROUND_TRUTH,
    EvaluationReport,
    load_results_dir,
    measure_confidence_accuracy,
    measure_fp_reduction,
    measure_verification_accuracy,
)
from datetime import datetime, timezone
from dataclasses import asdict

router = APIRouter()


class SaveEvalBody(BaseModel):
    finding_path: str = Field(min_length=1)
    scenario: str = Field(min_length=1)


@router.post("/evaluation/save")
async def evaluation_save(body: SaveEvalBody):
    source = Path(body.finding_path)
    if not source.is_absolute():
        source = ROOT / source
    if not source.exists():
        raise HTTPException(status_code=404, detail=f"{body.finding_path} not found")
    data = json.loads(source.read_text(encoding="utf-8"))
    data["scenario"] = body.scenario
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{body.scenario}.json"
    out_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return {"saved_to": str(out_path.relative_to(ROOT))}


def _build_report() -> tuple[EvaluationReport, list[dict]]:
    raw = load_results_dir(RESULTS_DIR)
    findings: list[dict] = []
    for item in raw:
        scenario = item.get("scenario")
        gt = GROUND_TRUTH.get(scenario, {})
        findings.append({**item, **gt})
    total = len(findings)
    adapt_fp, aegis_fp, fp_reduction = measure_fp_reduction(findings)
    conf_acc, conf_confusion = measure_confidence_accuracy(findings)
    ver_acc, facr, ver_confusion = measure_verification_accuracy(findings)
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
    return report, findings


async def _metrics_stream() -> AsyncIterator[str]:
    report, findings = _build_report()
    if report.total_findings == 0:
        yield format_sse(
            pipeline_event("report", "failed", "No result files found in evaluation/results/")
        )
        return

    yield format_sse(
        pipeline_event(
            "report",
            "complete",
            f"Loaded {report.total_findings} finding(s) from evaluation/results/",
            {"total_findings": report.total_findings},
        )
    )
    yield format_sse(
        pipeline_event(
            "analyze",
            "complete",
            (
                f"False-positive rate — ADAPT {report.false_positive_rate_adapt_baseline:.1%} "
                f"vs AEGIS {report.false_positive_rate_aegis:.1%} "
                f"(reduction {report.fp_reduction_percent:.1f}%)"
            ),
            {
                "false_positive_rate_adapt_baseline": report.false_positive_rate_adapt_baseline,
                "false_positive_rate_aegis": report.false_positive_rate_aegis,
                "fp_reduction_percent": report.fp_reduction_percent,
            },
        )
    )
    yield format_sse(
        pipeline_event(
            "analyze",
            "complete",
            f"Confidence-grading accuracy vs ground truth: {report.confidence_accuracy:.1%}",
            {
                "confidence_accuracy": report.confidence_accuracy,
                "confidence_confusion": report.confidence_confusion,
            },
        )
    )
    yield format_sse(
        pipeline_event(
            "verify",
            "complete",
            (
                f"Remediation-verification accuracy: {report.verification_accuracy:.1%} "
                f"(false all-clear {report.false_all_clear_rate:.1%})"
            ),
            {
                "verification_accuracy": report.verification_accuracy,
                "false_all_clear_rate": report.false_all_clear_rate,
                "verification_confusion": report.verification_confusion,
            },
        )
    )
    metrics_path = RESULTS_DIR / "metrics.json"
    metrics_path.write_text(json.dumps(asdict(report), indent=2, default=str), encoding="utf-8")
    yield format_sse(
        pipeline_event(
            "report",
            "complete",
            f"Full report written to {metrics_path.relative_to(ROOT)}",
            {"report": asdict(report), "scenarios": findings},
        )
    )


@router.post("/evaluation/metrics")
async def evaluation_metrics():
    return sse_response(_metrics_stream())


@router.get("/evaluation/report")
async def evaluation_report():
    path = RESULTS_DIR / "metrics.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="metrics.json not found — run evaluation first")
    return json.loads(path.read_text(encoding="utf-8"))
