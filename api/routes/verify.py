from __future__ import annotations

from typing import AsyncIterator, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.findings_io import (
    append_verification_history,
    load_verification_history,
    notify_finding,
)
import json

from api.findings_io import ROOT
from api.pipeline import capture_exposures, replay_finding, resolve_repo_path, snapshot_path
from api.runtime import runtime
from api.scope_store import LabModeDenied, PluginDenied, TargetDenied, load_scope, require_lab, require_target
from api.sse import format_sse, pipeline_event, sse_response

router = APIRouter()


class SnapshotBody(BaseModel):
    target: str = Field(min_length=1)
    label: Literal["before", "after"]


class VerifyBody(BaseModel):
    target: str = Field(min_length=1)
    finding_path: str = Field(min_length=1)
    before_path: str = Field(min_length=1)


@router.post("/snapshot/capture")
async def snapshot_capture(body: SnapshotBody):
    try:
        require_lab("Snapshot capture")
        scope = require_target(body.target, plugin="nmap_scanner")
    except (LabModeDenied, TargetDenied, PluginDenied) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    ports = scope.get("ports") or "21-23,80"
    timeout = max(30, int(scope.get("timeouts", {}).get("connect", 5)) * 12)
    try:
        exposures = capture_exposures(body.target.strip(), ports, timeout)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Scan failed: {exc}") from exc

    dest = snapshot_path(body.target.strip(), body.label)
    dest.write_text(json.dumps(exposures, indent=2), encoding="utf-8")
    # also keep a conventional before.json for the CLI/UI default
    if body.label == "before":
        (ROOT / "before.json").write_text(json.dumps(exposures, indent=2), encoding="utf-8")
    return {"exposures": exposures, "saved_to": str(dest.relative_to(ROOT))}


@router.get("/snapshot/before")
async def snapshot_before(target: str):
    dest = snapshot_path(target, "before")
    generic = ROOT / "before.json"
    if dest.exists():
        return {"saved_to": str(dest.relative_to(ROOT)), "exists": True}
    if generic.exists():
        return {"saved_to": "before.json", "exists": True}
    return {"saved_to": None, "exists": False}


async def _verify_stream(body: VerifyBody) -> AsyncIterator[str]:
    runtime.active_verify = True
    try:
        try:
            require_lab("Verification")
            require_target(body.target, plugin="vsftpd_backdoor")
        except (LabModeDenied, TargetDenied, PluginDenied) as exc:
            yield format_sse(pipeline_event("verify", "failed", str(exc)))
            return

        scope = load_scope()
        ports = scope.get("ports") or "21-23,80"
        connect = int(scope.get("timeouts", {}).get("connect", 5))
        timeout = max(30, connect * 12)

        yield format_sse(pipeline_event("verify", "running", "Checking controls (independent reachability)..."))
        try:
            packed = replay_finding(
                body.target.strip(),
                resolve_repo_path(body.finding_path),
                resolve_repo_path(body.before_path),
                ports,
                timeout,
                connect,
            )
        except Exception as exc:
            yield format_sse(pipeline_event("verify", "failed", str(exc)))
            return

        yield format_sse(
            pipeline_event(
                "verify",
                "complete",
                f"controls_ok = {packed['controls_ok']}",
                {"controls_ok": packed["controls_ok"]},
            )
        )
        yield format_sse(pipeline_event("monitor", "complete", "Capturing post-remediation exposure snapshot..."))
        yield format_sse(
            pipeline_event(
                "monitor",
                "complete",
                f"before exposures = {packed['before_count']}; after exposures = {packed['after_count']}",
            )
        )
        yield format_sse(pipeline_event("execute", "running", "Re-attempting original exploit chain..."))
        verification = packed["verification"]
        yield format_sse(
            pipeline_event(
                "execute",
                "complete",
                f"Replay finished with verdict {verification['verdict']}",
            )
        )
        yield format_sse(
            pipeline_event(
                "report",
                "complete",
                f"Verdict: {verification['verdict']} — {verification['evidence']['summary']}",
                {"verification": verification, "finding": packed["finding"]},
            )
        )
        history_entry = {
            "finding_id": verification["finding_id"],
            "finding_title": packed["finding"].get("title"),
            "target": body.target,
            "verdict": verification["verdict"],
            "timestamp": verification["completed_at"],
            "target_state": packed["finding"].get("status"),
            "evidence": verification["evidence"]["summary"],
        }
        append_verification_history(history_entry)
        await notify_finding(packed["finding"])
    finally:
        runtime.active_verify = False


@router.post("/verify/run")
async def verify_run(body: VerifyBody):
    try:
        require_lab("Verification")
        require_target(body.target.strip(), plugin="vsftpd_backdoor")
    except (LabModeDenied, TargetDenied, PluginDenied) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return sse_response(_verify_stream(body))


@router.get("/verify/history")
async def verify_history():
    return load_verification_history()
