# Initial tool-chaining implementation plan

## Purpose and boundary

This first implementation stage proves that AEGIS can pass structured information
through the MAPE-K-V loop without contacting a network or executing exploit
payloads. It uses deterministic fixture adapters over the existing skeleton.
Only after this chain is tested should an individual fixture be replaced by a
reviewed, lab-authorized adapter.

The chain is deliberately evidence-led:

`observation -> candidate action -> scoped action -> primary evidence -> independent corroboration -> confidence -> remediation replay -> report`

Every action must be represented by an `AttackStep` (declarative intent), not a
shell command. `ScopePolicy` must approve both its target and plugin before the
executor invokes any adapter. A primary tool success is a hypothesis; it must
never directly produce a confirmed finding or a closure verdict.

## Stage 1 outcome

Deliver one deterministic runner and tests which exercise the following sequence:

1. A fixture discovery adapter supplies service records for an allowlisted lab
   target. `ScannerManager.normalize()` creates source-attributed observations.
2. The analyzer turns only supported observations into `CandidateAction` values.
   `Planner.choose_next()` selects one bounded next action by utility.
3. The runner creates an `AttackStep`, then calls `Executor.execute()`. Scope,
   lab mode, adapter authorization, and adapter registration are checked first.
4. The fixture action adapter returns a typed primary `Evidence` item. The runner
   creates a `Finding` with that evidence and the recorded attack step.
5. `DevilsAdvocate.validate()` runs the applicable corroboration adapter(s) in a
   separate fixture session. `ConfidenceEngine.assess_finding()` then assigns the
   grade; this does not use the planning utility score.
6. The report renderer exposes the claim, primary evidence, corroboration
   outcome, confidence, and current status.
7. After a modeled remediation event, `ReplayEngine.verify()` replays the same
   declarative step through a controlled fixture executor and records the verdict.

The existing `scripts/run_pipeline.py` already demonstrates steps 4--7. Stage 1
extends that pattern backward through monitor, planning, and the scope-gated
executor, then tests every decision branch below.

## Tool use and chaining contract

| Component / tool family | Use it when | Input from prior stage | Required output for next stage | Do not use it when |
|---|---|---|---|---|
| Discovery adapter (`nmap_scanner` / `service_discovery`, initially fixture) | An allowlisted target needs bounded host/service facts | Engagement scope, target, port/rate budget | Raw records with tool/version/time provenance | Scope is absent, target is not allowed, or a previous observation is still fresh enough |
| `ScannerManager` | Adapter records need a stable core representation | Raw adapter records | `Observation` records | It must not invoke a scanner itself |
| Analysis + `utility_ranker` | Observations expose a permitted possible next step | Observations, known capabilities, action cost/risk | Ranked `CandidateAction` list | As evidence of an exploit claim |
| `Planner` | More than one permitted candidate exists | Ranked candidates | One bounded candidate or `None` | A candidate lacks a recorded precondition or exceeds an engagement limit |
| `Executor` + action adapter (initially fixture) | A selected action is within engagement scope | `AttackStep`, `ScopePolicy`, registered plugin | Typed primary `Evidence` | Lab mode is off; target/plugin is not allowlisted; adapter is unreviewed |
| Corroboration adapter | A primary action reports a security-relevant claim | Finding and independent probe context | `Corroboration` with supports, contradicts, or ambiguous | The only available check reuses the same session/parser/predicate without documenting correlation |
| `ConfidenceEngine` | At least primary evidence is available, and again after corroboration | Finding plus corroborations | Confidence grade and lifecycle state | Selecting which action to run next |
| `ReplayEngine` + regression detector | A remediation event was recorded | Immutable attack chain, controls, before/after exposure snapshots | Verification result and finding status | Controls cannot establish target reachability, identity, and replay prerequisites |
| Report generator | A finding or verification result must be reviewed | Finding, optional verification result | Markdown report artifact | A replacement for immutable ledger evidence |

## Scenario-driven chain decisions

| Scenario | Discovery / plan decision | Execute and corroborate | Expected confidence | Replay behavior after remediation | Expected result |
|---|---|---|---|---|---|
| Unpatched vulnerable lab service | Discover expected service; choose the highest-utility, low-impact validation | Fixture claim succeeds; independent predicate succeeds | Confirmed | Recorded predicate succeeds again | Reopened |
| Ambiguous or tool false-positive signal | Record the observation, but favor a low-cost confirming action over a higher-risk action | Primary reports success; independent predicate is indeterminate | Suspected | Do not schedule closure replay until a remediation/finding workflow exists | Needs human review or suspected, never confirmed |
| Contradicted primary claim | Record the same bounded claim for audit | Primary reports success; independent session fails the predicate | Needs human review | No closure conclusion based on the original claim | Human triage required |
| Correct remediation | Re-establish reachability and service identity before replay | Do not rerun discovery broadly; replay only the immutable original chain | Retain prior grade as history | Decisive original step fails; controls pass; no new exposures | Verified closed |
| Ineffective remediation | Controls pass and the original route remains in scope | Replay reproduces the predicate | Retain/refresh evidence | All recorded steps succeed | Reopened |
| Partial remediation / alternate exposure | Compare bounded before/after snapshots after original route is blocked | No new exploitation is required in this stage | No all-clear | Original step fails, but new/changed exposure exists | Regression detected; human review |
| Environmental failure | Stop before any claim verdict | Target/service identity/prerequisites cannot be established | Unchanged | Set `controls_ok=False` | Inconclusive, never closed |
| Scope violation | Do not construct an executable plan | `Executor` rejects target or plugin before adapter invocation | No finding | No replay | Permission error/auditable rejected attempt |

## Ordered implementation work

1. Add a fixture discovery plugin and a fixture validation-action plugin under a
   test-only or clearly named demo module. They return static records/evidence and
   make no subprocess or network calls.
2. Add an orchestration function (for example, `run_initial_chain`) that wires
   Monitor -> Analyze -> Plan -> Executor -> corroboration -> confidence -> report.
   Keep `run_pipeline.py` as the smaller current demo or refactor it to call this
   function once the behavior is covered by tests.
3. Persist each generated evidence and finding in the existing in-memory `KnowledgeLedger`
   during the run. This validates provenance hand-off before a database backend is
   introduced.
4. Add tests for the happy path and the seven scenario branches above. Assert that
   rejected actions do not call their adapter, and that a primary success alone
   cannot yield `confirmed` or `verified_closed`.
5. Run the deterministic runner, the test suite, and static syntax checks. Record
   the scenario, plugin names, policy, and result in the report output.

## Replacement gate for real lab adapters

A fixture may be replaced only when its adapter has: explicit lab target and
plugin allowlisting; bounded rate/time/port parameters; precondition checks;
structured normalized output; immutable raw-evidence reference; declared side
effects; a separate corroboration route; and replay-safe, idempotent semantics.

The first live candidate should be service discovery only, limited to one
pre-declared lab host and a small approved port set. Exploitation, credential
guessing, persistence, lateral movement, and broad web testing stay out of this
stage. In particular, the existing `sqlmap` placeholder is not part of the first
demonstrator.

## Acceptance criteria

- A deterministic, no-network run produces an observation, selected action,
  scope-approved evidence, corroboration, confidence grade, verification verdict,
  and Markdown report.
- The scenario matrix produces the expected status/verdict in every row.
- Scope-denied target/plugin paths prove that the adapter was not invoked.
- Tests establish that utility is used only for selection and confidence only for
  evidence assessment.
- No live command strings, credentials, payloads, or unrestricted target input
  are stored in an `AttackStep` or report.
