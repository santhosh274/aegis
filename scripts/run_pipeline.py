"""Safe deterministic demonstration of the MAPE-K-V lifecycle.

This does not contact a network or execute an exploit. It is a fixture for the
research workflow and a starting point for lab-only integrations.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.analyze.confidence_engine import ConfidenceEngine
from core.execute.devils_advocate import DevilsAdvocate
from core.knowledge_base.models import AttackStep, Evidence, Finding
from core.verify.replay_engine import ReplayEngine
from plugins.corroboration.rce_validation import RceCorroborator
from reporting.generator import render_finding


def run_demo() -> str:
    finding = Finding(
        "Lab RCE claim", "10.0.0.5", "A controlled lab predicate indicates code execution",
        Evidence("primary_claim", "fixture tool reported success", "demo"),
        [AttackStep("fixture", "benign_nonce", "10.0.0.5", "nonce observed")],
    )
    DevilsAdvocate().validate(finding, [RceCorroborator(True)])
    ConfidenceEngine().assess_finding(finding)
    verification = ReplayEngine().verify(finding, lambda _step: False, controls_ok=True)
    return render_finding(finding, verification)


if __name__ == "__main__":
    print(run_demo())
