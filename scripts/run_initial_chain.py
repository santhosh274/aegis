"""Run the first deterministic, fixture-only MAPE-K-V integration chain."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.demo.initial_chain import run_initial_chain
from reporting.generator import render_finding


if __name__ == "__main__":
    run = run_initial_chain()
    print(render_finding(run.finding, run.verification))
