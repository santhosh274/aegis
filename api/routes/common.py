from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from api.findings_io import (
    delete_finding,
    get_finding,
    load_raw_findings,
    mark_remediated,
    notify_finding,
)
from api.runtime import runtime
from api.scope_store import load_scope, save_scope
from plugins.scanners.nmap_scanner import DEFAULT_PORTS

router = APIRouter()


class ScopeBody(BaseModel):
    allowed_hosts: list[str] = Field(default_factory=list)
    allowed_plugins: list[str] = Field(default_factory=list)
    lab_mode: bool = True
    ports: str = DEFAULT_PORTS
    listener_port: int = 6200
    timeouts: dict[str, int] = Field(default_factory=lambda: {"connect": 5, "listen": 8, "replay_wait": 5})


@router.get("/findings")
async def list_findings():
    return load_raw_findings()


@router.get("/findings/{finding_id}")
async def finding_detail(finding_id: str):
    item = get_finding(finding_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return item


@router.post("/findings/{finding_id}/remediate")
async def finding_remediate(finding_id: str):
    updated = mark_remediated(finding_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    await notify_finding(updated)
    return updated


@router.delete("/findings/{finding_id}")
async def finding_delete(finding_id: str):
    if not delete_finding(finding_id):
        raise HTTPException(status_code=404, detail="Finding not found")
    return {"deleted": finding_id}


@router.get("/status")
async def status():
    return runtime.snapshot()


@router.get("/settings")
async def get_settings():
    return load_scope()


@router.post("/settings")
async def post_settings(body: ScopeBody):
    return save_scope(body.model_dump())


# Idle-connection keepalive. Sends a JSON "ping" every HEARTBEAT_SECONDS so
# intermediaries don't time out quiet sockets and a dead peer is detected fast.
HEARTBEAT_SECONDS = 20


async def findings_ws(ws: WebSocket):
    await ws.accept()
    await runtime.register(ws)
    try:
        await ws.send_json({"type": "hello", "findings": load_raw_findings()})
        while True:
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=HEARTBEAT_SECONDS)
            except asyncio.TimeoutError:
                try:
                    await ws.send_json({"type": "ping"})
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        await runtime.unregister(ws)
