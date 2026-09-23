"""AEGIS HTTP API — wraps existing MAPE-K-V scripts; does not rewrite them."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import common, evaluation, exploit, scan, verify
from api.scope_store import LabModeDenied, PluginDenied, TargetDenied

app = FastAPI(title="AEGIS", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(LabModeDenied)
@app.exception_handler(TargetDenied)
@app.exception_handler(PluginDenied)
async def permission_denied(_request: Request, exc: PermissionError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


app.include_router(scan.router, prefix="/api")
app.include_router(exploit.router, prefix="/api")
app.include_router(verify.router, prefix="/api")
app.include_router(evaluation.router, prefix="/api")
app.include_router(common.router, prefix="/api")

# WebSocket lives at /ws/findings as specified (not under /api).
app.add_api_websocket_route("/ws/findings", common.findings_ws)


@app.get("/health")
async def health():
    return {"ok": True}
