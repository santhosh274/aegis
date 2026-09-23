"""Load and persist operator scope settings (config/scope.json)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config.settings import ScopePolicy
from plugins.scanners.nmap_scanner import DEFAULT_PORTS

ROOT = Path(__file__).resolve().parent.parent
SCOPE_PATH = ROOT / "config" / "scope.json"

DEFAULT_SCOPE: dict[str, Any] = {
    "allowed_hosts": ["192.168.52.139"],
    "allowed_plugins": ["nmap_scanner", "vsftpd_backdoor", "rce_validation"],
    "lab_mode": True,
    "ports": DEFAULT_PORTS,
    "listener_port": 6200,
    "timeouts": {"connect": 5, "listen": 8, "replay_wait": 5},
}


def load_scope() -> dict[str, Any]:
    if not SCOPE_PATH.exists():
        save_scope(DEFAULT_SCOPE)
        return dict(DEFAULT_SCOPE)
    data = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    merged = {**DEFAULT_SCOPE, **data}
    merged["timeouts"] = {**DEFAULT_SCOPE["timeouts"], **(data.get("timeouts") or {})}
    return merged


def save_scope(data: dict[str, Any]) -> dict[str, Any]:
    merged = {**DEFAULT_SCOPE, **data}
    if "timeouts" in data:
        merged["timeouts"] = {**DEFAULT_SCOPE["timeouts"], **data["timeouts"]}
    SCOPE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCOPE_PATH.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged


def policy_from_scope(scope: dict[str, Any] | None = None) -> ScopePolicy:
    data = scope or load_scope()
    return ScopePolicy(
        allowed_hosts=tuple(data.get("allowed_hosts") or ()),
        allowed_plugins=tuple(data.get("allowed_plugins") or ()),
        lab_mode=bool(data.get("lab_mode", False)),
    )


def require_lab(action: str) -> dict[str, Any]:
    scope = load_scope()
    if not scope.get("lab_mode"):
        raise LabModeDenied(action)
    return scope


def require_target(target: str, *, plugin: str | None = None) -> dict[str, Any]:
    scope = load_scope()
    policy = policy_from_scope(scope)
    if not policy.permits_target(target):
        raise TargetDenied(target)
    if plugin and not policy.permits_plugin(plugin):
        raise PluginDenied(plugin)
    return scope


class LabModeDenied(PermissionError):
    def __init__(self, action: str) -> None:
        super().__init__(
            f"{action} is blocked while Lab Mode is off. Enable Lab Mode in Settings."
        )


class TargetDenied(PermissionError):
    def __init__(self, target: str) -> None:
        super().__init__(f"Target {target} is outside the authorized host allowlist.")


class PluginDenied(PermissionError):
    def __init__(self, plugin: str) -> None:
        super().__init__(f"Plugin {plugin} is not in the allowed plugin set.")
