"""Import existing adapters/scripts; do not reimplement exploit logic here."""
from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

from core.analyze.confidence_engine import ConfidenceEngine
from core.analyze.utility_ranker import CandidateAction
from core.execute.devils_advocate import DevilsAdvocate
from core.execute.executor import Executor
from core.knowledge_base.json_store import load_finding
from core.knowledge_base.models import AttackStep, Finding, RemediationEvent
from core.monitor.scanner_manager import ScannerManager
from core.plan.planner import Planner
from core.verify.regression_detector import Exposure
from core.verify.replay_engine import ReplayEngine
from plugins.corroboration.rce_validation import LiveRceCorroborator
from plugins.exploits.vsftpd_backdoor import VsftpdBackdoorAdapter, VsftpdBackdoorError
from plugins.scanners.nmap_scanner import NmapDiscoveryAdapter

from api.scope_store import policy_from_scope
from api.serialize import finding_dict, observation_dict

ROOT = Path(__file__).resolve().parent.parent


def discover_target(target: str, ports: str, timeout_seconds: int) -> dict[str, Any]:
    adapter = NmapDiscoveryAdapter(ports=ports, timeout_seconds=timeout_seconds)
    raw_records = adapter.discover(target)
    observations = ScannerManager().normalize(target, adapter.name, raw_records)
    candidates = [
        CandidateAction(
            name=f"validate {obs.value} on {obs.target}",
            expected_gain=0.5,
            information_gain=0.8,
            cost=0.1,
            risk=0.05,
        )
        for obs in observations
        if obs.kind == "service"
    ]
    selected = Planner().choose_next(candidates)
    return {
        "observations": [observation_dict(obs) for obs in observations],
        "planner_selection": selected.name if selected else "none",
        "raw_records": raw_records,
    }


def trigger_exploit(target: str) -> Finding:
    policy = policy_from_scope()
    executor = Executor(policy=policy, plugins={"vsftpd_backdoor": VsftpdBackdoorAdapter()})
    step = AttackStep(
        plugin="vsftpd_backdoor",
        action="trigger_backdoor",
        target=target,
        expected_predicate="listener_open_on_6200",
    )
    primary_evidence = executor.execute(step)
    return Finding(
        title="vsftpd 2.3.4 backdoor (CVE-2011-2523)",
        target=target,
        claim="Backdoored vsftpd spawns a root shell listener on port 6200 when triggered",
        primary_evidence=primary_evidence,
        attack_chain=[step],
    )


def corroborate_finding(finding: Finding) -> Finding:
    DevilsAdvocate().validate(finding, [LiveRceCorroborator()])
    return finding


def grade_finding(finding: Finding) -> Finding:
    ConfidenceEngine().assess_finding(finding)
    return finding


def capture_exposures(target: str, ports: str, timeout_seconds: int) -> list[dict[str, Any]]:
    adapter = NmapDiscoveryAdapter(ports=ports, timeout_seconds=timeout_seconds)
    records = adapter.discover(target)
    exposures: list[dict[str, Any]] = []
    for record in records:
        left = record["value"].split(" ", 1)[0]
        service, _, port_str = left.partition("/")
        try:
            port = int(port_str)
        except ValueError:
            continue
        exposures.append(
            {
                "target": target,
                "service": service,
                "port": port,
                "fingerprint": record["value"],
            }
        )
    return exposures


def snapshot_path(target: str, label: str) -> Path:
    safe = target.replace(".", "_")
    return ROOT / f"{label}_{safe}.json"


def check_controls(target: str, connect_timeout: int = 5) -> bool:
    for port in (80, 23, 21):
        try:
            with socket.create_connection((target, port), timeout=connect_timeout):
                return True
        except OSError:
            continue
    return False


def load_before_exposures(path: Path) -> set[Exposure]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        Exposure(
            target=e["target"],
            service=e["service"],
            port=e["port"],
            fingerprint=e.get("fingerprint", ""),
        )
        for e in data
    }


def exposures_from_dicts(rows: list[dict[str, Any]]) -> set[Exposure]:
    return {
        Exposure(
            target=e["target"],
            service=e["service"],
            port=int(e["port"]),
            fingerprint=e.get("fingerprint", ""),
        )
        for e in rows
    }


def resolve_repo_path(path: str) -> Path:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = ROOT / resolved
    return resolved


def replay_finding(
    target: str,
    finding_path: Path,
    before_path: Path,
    ports: str,
    timeout_seconds: int,
    connect_timeout: int,
) -> dict[str, Any]:
    finding = load_finding(finding_path)
    controls_ok = check_controls(target, connect_timeout)
    before_set = load_before_exposures(before_path)
    after_rows = capture_exposures(target, ports, timeout_seconds)
    after_set = exposures_from_dicts(after_rows)

    adapter = VsftpdBackdoorAdapter()

    def execute_step(step) -> bool:
        try:
            adapter.run(step)
            return True
        except VsftpdBackdoorError:
            return False

    result = ReplayEngine().verify(
        finding,
        execute_step,
        controls_ok=controls_ok,
        before=before_set,
        after=after_set,
    )
    RemediationEvent(finding_id=finding.id, description="reported fix, verified via live replay")

    data = json.loads(finding_path.read_text(encoding="utf-8"))
    data["verification_verdict"] = result.verdict.value
    data["status"] = finding.status.value
    finding_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    return {
        "verification": {
            "finding_id": result.finding_id,
            "verdict": result.verdict.value,
            "evidence": {
                "kind": result.evidence.kind,
                "summary": result.evidence.summary,
                "source": result.evidence.source,
                "collected_at": result.evidence.collected_at.isoformat(),
                "digest": result.evidence.digest,
                "id": result.evidence.id,
            },
            "failed_step_id": result.failed_step_id,
            "regression_summary": result.regression_summary,
            "completed_at": result.completed_at.isoformat(),
        },
        "finding": finding_dict(finding),
        "controls_ok": controls_ok,
        "before_count": len(before_set),
        "after_count": len(after_set),
        "after_exposures": after_rows,
    }
