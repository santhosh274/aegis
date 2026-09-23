# AEGIS

Autonomous Exploitation-Graded Incident-Verification System.

AEGIS extends a MAPE-K penetration-testing architecture with an evidence-based
confidence grade and a post-remediation **Verify** phase. This repository provides
the safe, lab-scoped core for that research: typed findings/evidence, independent
corroboration, replay verdicts, regression comparison, reporting, and tests.

It intentionally does **not** ship live exploit payloads or unrestricted scanning.
All tool adapters must be explicitly authorized and constrained to an isolated lab.

See [PROJECT_UNDERSTANDING.md](PROJECT_UNDERSTANDING.md) for the architecture,
knowledge matrix, scenario plan, and delivery sequence.

For the first deterministic integration slice, see
[the initial tool-chaining plan](docs/initial-tool-chaining-plan.md).

## Dashboard (web UI)

The full-stack dashboard wraps the existing MAPE-K-V script logic behind a FastAPI
backend and streams pipeline output to a React UI.

```bash
# 1. Backend API (imports the existing core adapters; never rewrites them)
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn api.main:app --reload --port 8000

# 2. Frontend (Vite dev server proxies /api and /ws to :8000)
cd dashboard
npm install
npm run dev            # http://localhost:5173
```

That's it: the frontend only talks to `api/main.py` (SSE + WebSocket at
`/ws/findings`) — it never invokes Python scripts directly. Scope policy lives in
`config/scope.json` (editable from the Settings screen); exploit/verify endpoints
return `403` when `lab_mode` is off or the target/plugin is out of scope.
