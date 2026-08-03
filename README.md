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
