"""Read/write findings using json_store plus evaluation/results/ on disk."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.knowledge_base.json_store import save_finding
from core.knowledge_base.models import Finding, FindingStatus

from api.runtime import runtime
from api.serialize import finding_dict

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "evaluation" / "results"
LIVE_FINDING = ROOT / "finding.json"
HISTORY_PATH = RESULTS_DIR / "verification_history.json"


def _is_finding_file(path: Path) -> bool:
    if path.suffix != ".json":
        return False
    if path.name in {"metrics.json", "verification_history.json"}:
        return False
    return True


def list_finding_files() -> list[Path]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    files = [p for p in sorted(RESULTS_DIR.glob("*.json")) if _is_finding_file(p)]
    if LIVE_FINDING.exists():
        files.append(LIVE_FINDING)
    return files


def load_raw_findings() -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for path in list_finding_files():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or "id" not in data:
            continue
        data["_path"] = str(path.relative_to(ROOT))
        key = data["id"]
        if key in seen:
            continue
        seen.add(key)
        out.append(data)
    out.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return out


def get_finding(finding_id: str) -> dict[str, Any] | None:
    for item in load_raw_findings():
        if item.get("id") == finding_id:
            return item
    return None


def finding_path_for(finding_id: str) -> Path | None:
    item = get_finding(finding_id)
    if not item:
        return None
    rel = item.get("_path")
    if not rel:
        return None
    return ROOT / rel


def persist_finding(finding: Finding, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    live = str(LIVE_FINDING)
    save_finding(finding, live)
    payload = finding_dict(finding)
    if extra:
        payload.update(extra)
        LIVE_FINDING.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    dest = RESULTS_DIR / f"{finding.id}.json"
    dest.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    payload["_path"] = str(dest.relative_to(ROOT))
    return payload


def update_finding_file(path: Path, mutator: Any) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    mutator(data)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    if path != LIVE_FINDING and data.get("id"):
        # keep live copy in sync when it is the same finding
        if LIVE_FINDING.exists():
            try:
                live = json.loads(LIVE_FINDING.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                live = {}
            if live.get("id") == data.get("id"):
                LIVE_FINDING.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    data["_path"] = str(path.relative_to(ROOT))
    return data


def mark_remediated(finding_id: str) -> dict[str, Any] | None:
    path = finding_path_for(finding_id)
    if path is None or not path.exists():
        return None

    def _mutate(data: dict[str, Any]) -> None:
        data["status"] = FindingStatus.REMEDIATED.value

    return update_finding_file(path, _mutate)


def append_verification_history(entry: dict[str, Any]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    history: list[dict[str, Any]] = []
    if HISTORY_PATH.exists():
        try:
            loaded = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                history = loaded
        except json.JSONDecodeError:
            history = []
    history.insert(0, entry)
    HISTORY_PATH.write_text(json.dumps(history, indent=2, default=str), encoding="utf-8")


def load_verification_history() -> list[dict[str, Any]]:
    if not HISTORY_PATH.exists():
        return []
    try:
        data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


async def notify_finding(payload: dict[str, Any]) -> None:
    await runtime.broadcast_finding(payload)
