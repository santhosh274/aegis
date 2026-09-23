"""Process-local run flags and WebSocket finding fan-out."""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket


class RuntimeState:
    def __init__(self) -> None:
        self.active_scan = False
        self.active_exploit = False
        self.active_verify = False
        self._sockets: list[WebSocket] = []
        self._lock = asyncio.Lock()

    def snapshot(self) -> dict[str, bool]:
        return {
            "active_scan": self.active_scan,
            "active_exploit": self.active_exploit,
            "active_verify": self.active_verify,
        }

    async def register(self, ws: WebSocket) -> None:
        async with self._lock:
            self._sockets.append(ws)

    async def unregister(self, ws: WebSocket) -> None:
        async with self._lock:
            if ws in self._sockets:
                self._sockets.remove(ws)

    async def broadcast_finding(self, finding: dict[str, Any]) -> None:
        payload = {"type": "finding", "finding": finding}
        async with self._lock:
            sockets = list(self._sockets)
        stale: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                stale.append(ws)
        if stale:
            async with self._lock:
                for ws in stale:
                    if ws in self._sockets:
                        self._sockets.remove(ws)


runtime = RuntimeState()
