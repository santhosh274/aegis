# AEGIS architecture

AEGIS implements MAPE-K-V: **Monitor** normalizes observations; **Analyze** maintains
the model and grades evidence; **Plan** ranks permitted next actions by utility;
**Execute** is scope-gated; a devil's-advocate pass obtains independent
corroboration; **Verify** replays a recorded declarative chain after remediation and
returns `verified_closed`, `reopened`, `regression_detected`, or `inconclusive`.

## Phase-to-component mapping

MAPE-K-V names the process phases; the following classes are the current concrete
implementation seams. They are parts of one system, not a second workflow.

| Phase | Current component(s) | Responsibility |
|---|---|---|
| Monitor | `ScannerManager` | Normalize adapter-provided records into observations. |
| Analyze | `ConfidenceEngine`, `utility_ranker` | Grade evidence and rank possible next actions; these are separate decisions. |
| Plan | `Planner` | Select the highest-utility permitted candidate action. |
| Execute | `Executor`, `DevilsAdvocate` | Scope-gate an adapter invocation, then obtain independent corroboration. |
| Verify | `ReplayEngine`, `regression_detector` | Replay the immutable chain and detect changed exposures after remediation. |
| Knowledge | `KnowledgeLedger` | Preserve findings, evidence, remediations, and verification results. |

`KnowledgeLedger` is the single append-only system of record in the current
implementation. Its evidence, confidence-related finding state, remediation, and
verification collections are logical views, not independent stores. A later
PostgreSQL implementation may project them into an Evidence Store, Confidence
Ledger, and Remediation Registry for query and retention needs, but all projections
must retain common IDs and preserve one authoritative audit trail.

Confidence is intentionally separate from utility: utility decides what to attempt,
while confidence decides how strongly to report a claim.
