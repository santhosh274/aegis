"""JSON encoding for AEGIS dataclasses without introducing a new store."""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from core.knowledge_base.models import Finding, VerificationResult
from core.monitor.scanner_manager import Observation
from core.verify.regression_detector import Exposure


def _default(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if is_dataclass(obj):
        return asdict(obj)
    raise TypeError(f"not JSON serializable: {type(obj)}")


def to_jsonable(obj: Any) -> Any:
    return json.loads(json.dumps(obj, default=_default))


def finding_dict(finding: Finding) -> dict[str, Any]:
    return to_jsonable(asdict(finding))


def observation_dict(obs: Observation) -> dict[str, Any]:
    return to_jsonable(asdict(obs))


def exposure_dict(exposure: Exposure) -> dict[str, Any]:
    return to_jsonable(asdict(exposure))


def verification_dict(result: VerificationResult) -> dict[str, Any]:
    return to_jsonable(asdict(result))
