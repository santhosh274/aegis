"""Server-Sent Event helpers shared by streaming endpoints."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Literal

from fastapi.responses import StreamingResponse

Phase = Literal["monitor", "analyze", "plan", "execute", "verify", "report"]
Status = Literal["running", "complete", "failed"]


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def pipeline_event(
    phase: Phase,
    status: Status,
    message: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "phase": phase,
        "status": status,
        "message": message,
        "timestamp": utcnow_iso(),
    }
    if data is not None:
        event["data"] = data
    return event


def format_sse(event: dict[str, Any], event_name: str = "pipeline") -> str:
    return f"event: {event_name}\ndata: {json.dumps(event, default=str)}\n\n"


def sse_response(iterator: AsyncIterator[str]) -> StreamingResponse:
    return StreamingResponse(
        iterator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
