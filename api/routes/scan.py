from __future__ import annotations

from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.pipeline import discover_target
from api.runtime import runtime
from api.scope_store import LabModeDenied, PluginDenied, TargetDenied, require_target
from api.sse import format_sse, pipeline_event, sse_response

router = APIRouter()


class DiscoverBody(BaseModel):
    target: str = Field(min_length=1)


async def _discover_stream(target: str) -> AsyncIterator[str]:
    runtime.active_scan = True
    try:
        yield format_sse(
            pipeline_event("monitor", "running", f"Scanning {target} (bounded port set, read-only -sV)...")
        )
        try:
            scope = require_target(target, plugin="nmap_scanner")
        except (TargetDenied, PluginDenied, LabModeDenied) as exc:
            yield format_sse(pipeline_event("monitor", "failed", str(exc)))
            return

        ports = scope.get("ports") or "21-23,80"
        timeout = int(scope.get("timeouts", {}).get("connect", 5))
        nmap_timeout = max(30, timeout * 12)

        try:
            result = discover_target(target, ports, nmap_timeout)
        except Exception as exc:
            yield format_sse(pipeline_event("monitor", "failed", f"Scan failed: {exc}"))
            return

        observations = result["observations"]
        if not observations:
            yield format_sse(
                pipeline_event(
                    "monitor",
                    "complete",
                    "No open services found in the scanned port range, or host did not respond.",
                    {"observations": []},
                )
            )
        else:
            yield format_sse(
                pipeline_event("monitor", "complete", f"{len(observations)} observation(s) collected")
            )
            for obs in observations:
                yield format_sse(
                    pipeline_event(
                        "monitor",
                        "complete",
                        f"{obs['kind']}: {obs['value']}  (source={obs['source']})",
                        {"observation": obs},
                    )
                )

        yield format_sse(pipeline_event("analyze", "running", "Ranking discovery candidates..."))
        yield format_sse(pipeline_event("analyze", "complete", "Utility ranking complete"))
        selection = result["planner_selection"]
        yield format_sse(
            pipeline_event(
                "plan",
                "complete",
                f"Planner's highest-utility next candidate: {selection}",
                {"planner_selection": selection},
            )
        )
        yield format_sse(
            pipeline_event(
                "report",
                "complete",
                "Discovery finished",
                {
                    "observations": observations,
                    "planner_selection": selection,
                },
            )
        )
    finally:
        runtime.active_scan = False


@router.post("/scan/discover")
async def scan_discover(body: DiscoverBody):
    try:
        require_target(body.target.strip(), plugin="nmap_scanner")
    except (TargetDenied, PluginDenied, LabModeDenied) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return sse_response(_discover_stream(body.target.strip()))
