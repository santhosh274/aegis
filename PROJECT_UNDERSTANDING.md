# AEGIS — Project Understanding and Knowledge Matrix

**Prepared:** 2026-08-01  
**Repository state reviewed:** `main` at `acefb3a` (`file structure made`)  
**Primary context:** `C:\Users\santh\Downloads\AEGIS_Project_Reference.md`

> **Implementation update (2026-08-03):** The previously empty scaffold now has a
> safe, dependency-light MAPE-K-V core: typed knowledge/evidence records, an
> append-only ledger, separate utility and confidence engines, a devil's-advocate
> orchestration boundary, scope-gated execution, controlled replay and regression
> verdicts, Markdown reporting, scenario/metric helpers, and phase-focused tests.
> Live scanners and exploit adapters remain intentionally unimplemented: they must be
> reviewed, lab-authorized integrations rather than payloads in the core repository.

## Executive understanding

AEGIS (*Autonomous Exploitation-Graded Incident-Verification System*) is an academic offensive-security research project. Its goal is **not** to produce a generic vulnerability scanner. It should autonomously run a scoped, black-box penetration-testing loop in an isolated lab, retain evidence for every claimed exploit, independently challenge that claim, and later replay the exact exploit chain after a reported fix to establish whether the finding is truly closed.

The research contribution is a proposed extension of ADAPT's MAPE-K architecture to **MAPE-K-V**:

`Monitor → Analyze → Plan → Execute → Verify → Knowledge Base → Monitor`

The two differentiators are:

1. **Confidence grading:** a successful tool invocation is a claim, not automatically ground truth. A separate corroboration pass assigns `Confirmed`, `Suspected`, or `Needs Human Review` from independently collected evidence.
2. **Closed-loop remediation verification:** a remediation event triggers a controlled replay of the recorded exploit chain. The system records `Verified Closed`, `Reopened`, or `Regression Detected`, rather than assuming that a patch worked.

All active testing must remain limited to explicit, authorized lab targets (Metasploitable 2/3 and the proposed custom network). The project should encode scope and safety controls rather than relying only on operator discipline.

## What exists today

The repository began as a **scaffold**. The MAPE-K-V core has since been implemented,
but the external-tool adapters, durable database backend, VM provisioning, and live
evaluation harness remain future integration work.

| Area | Intended responsibility inferred from path | Current state |
|---|---|---|
| `core/monitor` | Receive/manage scan results | Implemented normalization boundary; no live scanner adapter yet |
| `core/analyze` | Utility ranking and confidence scoring | Implemented; the two scores are explicitly separate |
| `core/plan` | Choose scans/attacks and form an executable plan | Implemented minimal next-action selector |
| `core/execute` | Execute actions and devil's-advocate validation | Implemented scope gate and corroboration orchestration; no live executor plugins |
| `core/verify` | Replay prior chains and detect regressions | Implemented controlled replay verdicts and snapshot comparison |
| `core/knowledge_base` | Persist pentest state, evidence, ledger, and database access | Implemented typed records and in-memory ledger; database interface only |
| `plugins/corroboration` | Independent claim checks | Implemented safe result-model adapters for four claim classes |
| Other `plugins` | Scanner, exploit, post-exploitation adapters | Reserved placeholders for reviewed lab-only integrations |
| `reporting` | Evidence-backed report generation | Implemented Markdown renderer; PDF template remains future work |
| `evaluation` | Experiment runner and metric collection | Implemented scenario manifest and pure metric helpers |
| `tests` | Phase-level behavioral tests | Implemented pytest tests; not executed here because pytest is absent |
| `docs` | Architecture/evaluation documentation | Implemented concise phase documents; lab READMEs remain placeholders |

`pytest` is declared in `requirements.txt`, but is not installed in the available Python environment; therefore the pytest suite has not yet been run. Compilation, the safe end-to-end demonstration, evaluation smoke checks, and `git diff --check` did pass.

### Implemented file-by-file map

#### Shared state and knowledge base

| File | Detailed responsibility |
|---|---|
| `core/knowledge_base/models.py` | Defines all typed core records and state enums. `Evidence` carries source/provenance; `Corroboration` links an independent probe to evidence; `AttackStep` records replayable declarative intent instead of commands; `Finding` holds the claim, chain, grade, and lifecycle; remediation and verification records preserve the closed-loop audit trail. |
| `core/knowledge_base/ledger.py` | Provides the current in-memory, append-only record store. It records findings, evidence, remediations, and verification runs; evidence IDs cannot be re-used for different evidence content. |
| `core/knowledge_base/database.py` | Defines the `FindingRepository` persistence contract. It is a seam for a later SQLAlchemy/PostgreSQL adapter, not a database implementation. |
| `config/settings.py` | Defines `ScopePolicy`, which enforces lab mode, explicit host/network allowlists, and approved plugin names. A hostname not expressly listed is denied; an IP must belong to an allowed CIDR. |

#### MAPE-K-V phase implementation

| File | Detailed responsibility |
|---|---|
| `core/monitor/scanner_manager.py` | Represents Monitor by turning adapter-provided records into timestamped, source-attributed `Observation` objects. It deliberately does not invoke Nmap or scan a host itself. |
| `core/analyze/utility_ranker.py` | Represents the existing ADAPT-style decision score. It weighs expected gain, information gain, cost, and risk to order potential actions. It does not decide whether a security claim is true. |
| `core/analyze/confidence_engine.py` | Implements the separate confidence rubric. Independent support gives `confirmed`; insufficient/ambiguous proof gives `suspected`; contradiction gives `needs_human_review`. It also updates the finding lifecycle to match the assessment. |
| `core/plan/planner.py` | Represents Plan. It chooses the highest-utility candidate action, returning `None` if no actions exist. It is intentionally minimal until prerequisites/dependencies are modelled. |
| `core/execute/executor.py` | Represents Execute. It refuses to run unless lab mode, target scope, plugin authorization, and plugin registration all pass. A registered adapter returns evidence; the core never stores arbitrary commands. |
| `core/execute/devils_advocate.py` | Runs one or more corroboration plugins and attaches their results to the finding. This makes a successful primary tool result a hypothesis that must be challenged. |
| `core/verify/replay_engine.py` | Represents Verify. It checks controls/prerequisites, calls a supplied step executor for every recorded attack step, returns a structured verdict, creates verification evidence, and updates the finding status. A full replay reopens; a decisive controlled failure closes; new exposure produces a regression; failed controls are inconclusive. |
| `core/verify/regression_detector.py` | Defines `Exposure` snapshots and returns exposures which are newly visible after remediation. It compares supplied snapshots only; it performs no network discovery. |

#### Corroboration adapters

| File | Detailed responsibility |
|---|---|
| `plugins/corroboration/weak_credentials.py` | Converts the outcome of a new, separate authentication session into supporting, contradicting, or ambiguous evidence. |
| `plugins/corroboration/rce_validation.py` | Converts an independent benign nonce predicate into RCE corroboration evidence; it does not include a payload or command execution capability. |
| `plugins/corroboration/privilege_escalation.py` | Converts a fresh effective-role/privilege check into corroboration evidence. |
| `plugins/corroboration/data_exposure.py` | Converts a minimal approved schema-check result into corroboration evidence, avoiding indiscriminate data extraction. |

#### Presentation, evaluation, and demonstration

| File | Detailed responsibility |
|---|---|
| `reporting/generator.py` | Renders a Markdown report showing the finding’s target, claim, confidence, status, primary evidence, corroboration outcomes, and optional post-remediation result. It is the canonical readable output to later feed a PDF renderer. |
| `scripts/run_pipeline.py` | Runs a deterministic local demo without network traffic: makes a fixture RCE claim, corroborates it, confirms it, simulates a blocked replay after remediation, and renders a verified-closed report. It prepends the repository root to Python’s import path so direct execution works. |
| `evaluation/scripts/run_evaluation.py` | Declares the fixed evaluation scenario matrix: unpatched, ambiguous signal, correct patch, ineffective patch, and partial-patch regression. It contains labels and expected verdicts but does not launch lab VMs. |
| `evaluation/scripts/collect_metrics.py` | Supplies pure functions for label accuracy, confusion-matrix counts, and false-all-clear rate; all reject mismatched input lengths. |
| `evaluation/results/.gitkeep` | Retains the empty output directory in version control for future experiment artifacts. |
| `evaluation/scripts/.gitkeep` | Existing directory-retention file; harmless alongside the implemented evaluation scripts. |

#### Tests and project documentation

| File | Detailed responsibility |
|---|---|
| `tests/test_monitor.py` | Verifies Monitor turns a raw record into the expected observation. |
| `tests/test_plan.py` | Verifies the planner selects the highest-utility action. |
| `tests/test_analyze.py` | Verifies independent support confirms a claim and contradiction requires human review. |
| `tests/test_execute.py` | Verifies an allowed lab target can use a fixture plugin and a public target is rejected. |
| `tests/test_verify.py` | Verifies all core Verify outcomes: reopened, closed, regression, and inconclusive. |
| `README.md` | Provides the concise system purpose, safety boundary, and entry point to this document. |
| `docs/architecture.md` | Summarizes phase boundaries and the knowledge ledger. |
| `docs/confidence-grading.md` | Documents the version-one confidence rubric and need for future calibration. |
| `docs/verify-phase.md` | Documents the closure, reopen, regression, and inconclusive decision rules. |
| `docs/evaluation-plan.md` | Documents the scenario matrix and intended metrics. |

### Reserved placeholders

The scanner, exploit, post-exploitation, lab-provisioning, PDF-template, and lab-README files are still intentionally empty. They are not missing features by accident: adding live tool execution before scope policy, evidence handling, corroboration, replay semantics, and tests would undermine the project’s central contribution and safety model. Their next implementation must be reviewed lab-only adapters that obey `ScopePolicy`.

The declared direction is nevertheless visible in the directory layout, dependency list, and `.env.example`:

- Python 3.11+ with SQLAlchemy/Psycopg suggests a relational persistence layer, likely PostgreSQL.
- `networkx` is suitable for the discovered security architecture and replayable attack-chain graph.
- `python-nmap`, a Metasploit RPC configuration, and named Hydra/Metasploit adapters establish a tool-integration direction.
- ReportLab is intended for a PDF reporting path.
- The presence of a `sqlmap` adapter conflicts with the stated scope, which explicitly excludes broad web-application testing. It should be omitted from the first demonstrator unless a narrow, justified host/service scenario requires it.

## Research foundation and intended operating model

The supplied reference is based on Skandylas and Asplund's 2025 ADAPT paper. ADAPT models penetration testing as a labeled transition system: test states contain the tester's known components, interfaces, and acquired capabilities; scans expand knowledge and attacks gain capabilities. It starts with an unknown architecture in black-box mode, continuously builds a security-informed architectural model, and uses multi-attribute utility to choose the next scan or attack. Its event-driven managed tool layer can execute independent operations concurrently. [ADAPT paper (open-access PDF)](https://www.diva-portal.org/smash/get/diva2%3A1956166/FULLTEXT01.pdf)

AEGIS should preserve that separation:

| Layer | Responsibility |
|---|---|
| Managing system | MAPE-K-V decisions, policy/scope controls, persistence, scheduling, confidence and verification logic |
| Managed system | Authorized scanner, exploit, post-exploitation, corroboration, and replay adapters |
| Environment | Isolated vulnerable VMs/network and declared remediation scenarios |

### End-to-end lifecycle

1. **Prepare an engagement:** register an allowlisted lab, explicit IP/host/service scope, time window, permitted techniques, rate/concurrency limits, goal predicates, and a run identifier.
2. **Monitor:** run permitted discovery actions; normalize raw tool output into observations with provenance and timestamps.
3. **Analyze:** update the discovered security-informed architecture; identify candidates; calculate *selection utility* separately from *finding confidence*.
4. **Plan:** select a bounded next action or prerequisite chain based on preconditions, expected capability gain, risk/cost, information gain, and current knowledge.
5. **Execute:** invoke the adapter in the lab, capture immutable action/evidence records, and never equate a tool's success exit code with proof of impact.
6. **Challenge the result:** run an independent, low-impact corroboration probe appropriate to the claim type. Aggregate evidence into a grade and persist the rationale.
7. **Report:** surface the claim, its evidence, confidence grade, attack-chain context, limitations, and recommended remediation.
8. **Register remediation:** associate a reported patch/configuration/credential change with the original finding and capture a target-state snapshot.
9. **Verify:** re-run the historical chain with controlled replay semantics. Mark the finding closed only when the decisive pathway fails and appropriate negative checks pass.
10. **Detect regression:** compare pre- and post-remediation architecture, exposed services, credentials, and alternative paths. Reopen or flag a new/changed path rather than emitting an all-clear.

## Core distinction: selection utility vs. evidential confidence

These scores answer different questions and must never be merged:

| Score | Question | Time of use | Example inputs | Output |
|---|---|---|---|---|
| Utility | “What should the autonomous loop try next?” | Before execution | goal progress, expected capability gain, likelihood, impact, cost, scope risk, information gain | ranking of scans/attacks |
| Confidence | “How well supported is this finding?” | After an exploit claim and after replay | independent probes, evidence integrity, reproducibility, consistency, freshness, contradictory evidence | Confirmed / Suspected / Needs Human Review |
| Verification status | “Did the recorded remediation close the original route?” | After remediation | replay outcome, target-state comparison, alternative-path discovery | Verified Closed / Reopened / Regression Detected / Inconclusive |

The ADAPT utility model is a weighted multi-attribute decision model. AEGIS should preserve its conceptual role for action choice, version all weights/rubrics, and empirically calibrate them against labeled lab outcomes. Confidence is an evidence-assessment model; it must be independently explainable and should be able to disagree with a high-utility action.

## Recommended domain model / knowledge base

The knowledge base is the system of record. It should maintain both an append-only audit/evidence ledger and queryable current state. A graph view is useful for chain traversal, while PostgreSQL can remain the authoritative transactional store.

| Entity | Essential fields / relations | Why it matters |
|---|---|---|
| Engagement / Scope | run ID, lab ID, CIDRs/hosts, allowed ports/actions, limits, authorization reference, start/end | Non-negotiable safety boundary and reproducibility |
| Asset / Component | identity, IP/DNS, OS, roles, properties, state snapshots | Security-informed architecture node |
| Interface / Service | asset, protocol, port, product/version, reachability, discovered-at | Attack and scan target |
| Capability | capability type, principal/context, affected component, acquisition evidence | Formal pentest-state gain (e.g., authenticated access) |
| Observation | normalized result, source plugin/version, raw-output reference, timestamp, parser version | Separates measurement from inference |
| Action / Attempt | action type, parameters fingerprint, preconditions, start/end, outcome, exit/error | Replayable, auditable execution unit |
| Attack chain / Step | ordered actions, dependencies, input bindings, expected intermediate predicates | Exact object to replay after remediation |
| Finding | vulnerability/claim, affected interface, lifecycle state, severity, confidence | User-facing security issue |
| Evidence item | content hash, immutable location, producer, collection time, interpretation | Traceability and tamper evidence |
| Corroboration | probe type, independence rationale, result, contradictions, evidence links | Devil's-advocate decision record |
| Confidence assessment | rubric version, factor values, grade, explanation, assessor timestamp | Explainable grade; supports recalibration |
| Remediation event | finding, claimed change, actor/time, baseline/post-change snapshot, evidence | Trigger and context for verification |
| Verification run | exact chain version, bindings, outcome at step, verdict, exceptions | Proves (or fails to prove) closure |
| Regression | baseline comparison, newly exposed/changed path, linked verification run | Prevents false all-clear |

Useful invariants:

- Raw evidence is write-once and content-addressed; derived interpretations may be superseded but not silently overwritten.
- A confidence grade references the exact rubric and evidence set that generated it.
- A replay references immutable chain and plugin versions, target bindings, and preconditions.
- `Verified Closed` requires an evidence-backed successful verification run, not merely a remediation event.
- A discovery observation is not a finding until an explicit claim/evidence relationship exists.

## Plugin contracts and corroboration matrix

All adapters need a common contract such as `validate_scope`, `describe`, `check_preconditions`, `execute`, `normalize_result`, and `collect_evidence`. Replay must use the same stable action specification, not shell-command history.

| Plugin family | Existing placeholder names | Intended output | Independent corroboration / safety note |
|---|---|---|---|
| Discovery | `nmap_scanner`, `service_discovery` | Hosts, services, fingerprints, reachability observations | Restrict ports, hosts, packet/rate budgets; archive raw scan output |
| Exploitation | `metasploit`, `hydra`, `sqlmap` | Claim plus candidate capability and action record | Must declare preconditions, side effects, and destructive-risk class; never store secrets in plain reports |
| Post-exploitation | `persistence`, `lateral_movement` | Capability/relationship observations | High risk; initially implement only safe, lab-specific validation checks, not persistent changes |
| Corroboration | `weak_credentials`, `rce_validation`, `privilege_escalation`, `data_exposure` | Independently gathered evidence, support/contradict/ambiguous decision | Should use a different authentication/session/probe route where feasible |
| Verification | `replay_engine`, `regression_detector` | Step-level replay trace and remediation verdict | Replay must be idempotent, bounded, and avoid actions that alter target state |

Suggested challenge logic for the four representative classes:

| Claim class | Primary claim | Independent corroboration | Strong evidence | Contradiction / uncertain case |
|---|---|---|---|---|
| Weak credentials | Credentials authenticating to a service | Fresh authenticated login through a separate client/session; verify least required authorized operation | New-session authentication and identity/role match | Original tool says success but new authentication fails or belongs to another account |
| RCE / shell | Code execution or shell obtained | New connection/session; benign nonce command; compare authenticated execution context | Nonce returned from target plus host/user/context verification | Output may be echoed, proxy-generated, stale, or session cannot be recreated |
| Privilege escalation | Higher privilege acquired | Fresh privilege check from a new session and an authorized benign privileged capability check | Independent UID/role/token plus required operation succeeds | Claimed identity and effective privileges disagree |
| Data exposure | Sensitive data accessible | Retrieve a minimal approved sample and validate schema/expected record characteristics against lab ground truth | Content identity, schema, access-control context, and sample validation align | Error page, synthetic/echoed response, or malformed/non-sensitive data |

Do not claim statistical independence merely because probes are different scripts. Record the independence rationale: separate tool/parser, separate session, separate data source, or distinct predicate. Where evidence is correlated, down-weight it.

## Verification semantics

Verification is a controlled experiment comparing the original successful chain with the post-remediation state.

| Outcome | Decision rule | Finding lifecycle effect |
|---|---|---|
| Verified Closed | A decisive original step fails for the expected remediation reason; required preconditions and target reachability are established; no material alternative path is found in the defined check | `Confirmed → Remediated → Verified Closed` |
| Reopened | Original chain succeeds again, or decisive exploit predicate is reproduced | `Remediated → Reopened` with new replay evidence |
| Regression Detected | Original path is blocked, but a materially new/changed exposure or alternate path appears after the change | Keep original remediation result explicit; create/link regression finding; no all-clear |
| Inconclusive | Lab/target is unavailable, expected preconditions cannot be established, credentials expired outside the fix, or evidence conflicts | Retain previous status; request human review; never close |

An expected failure alone is insufficient. Verification must rule out common false conclusions such as “the host is down,” “the service was disabled,” “the tester's route vanished,” or “the replay used stale credentials.” Record controls for reachability, service identity/version, scope, and replay prerequisites.

## Evaluation design

The evaluation should be a fixed, version-controlled scenario matrix—not a collection of anecdotal demos.

| Scenario | Baseline expectation | AEGIS expected result | Ground truth needed |
|---|---|---|---|
| Unpatched vulnerable service | Exploit chain succeeds | Confirmed with valid corroboration | Vulnerability and intended capability known |
| Tool false-positive / ambiguous signal | Flat report may call success | Suspected or Needs Human Review | Deliberately misleading/transient condition |
| Correctly patched service | Original chain stops | Verified Closed with controls | Exact remedial change and test snapshot |
| Ineffective remediation | Original chain still succeeds | Reopened | Patch/change fails to remove vulnerability |
| Partial patch | Original path fails but another path remains | Regression Detected | Designed alternative/new exposure |
| Non-security environmental failure | Replay cannot establish valid controls | Inconclusive, not closed | Controlled outage/routing/service absence |

Measure at least:

- **False-positive reduction:** compare flat tool-success reporting with corroborated `Confirmed` findings against ground truth.
- **Confidence-grade accuracy:** use a confusion matrix over Confirmed/Suspected/Needs Review; define how ambiguous truth is labeled before execution.
- **Remediation-verification accuracy:** correctness for closed, reopened, regression, and inconclusive verdicts.
- **False all-clear rate:** closed verdicts when an original or alternate in-scope exploitable route still exists.
- **Overhead:** wall-clock time, tool actions, and network traffic of corroboration/replay relative to the baseline.
- **Reproducibility:** scenario image/version, seed/config, tool/plugin versions, and evidence hashes for each run.

Avoid overclaiming comparisons to ADAPT. The defensible baseline is an **AEGIS ablation** that uses the same scans/exploits and reports primary tool success without corroboration or Verify. It is only a conceptual “ADAPT-style flat reporting” baseline unless the actual ADAPT tool and matched configuration are reproduced.

## Knowledge matrix and learning priorities

| Knowledge area | Why it is essential to AEGIS | Applied deliverable / evidence of mastery | Priority |
|---|---|---|---|
| ADAPT formal model | Grounds MAPE-K behavior in known components/interfaces/capabilities, LTS state transitions, and utility choice | Written mapping from ADAPT state/repertoire/strategy to code entities and test cases | Critical |
| Autonomic systems / MAPE-K | Defines phase boundaries, feedback loops, event handling, and managing-vs-managed separation | State-machine and event contracts, including Verify triggers | Critical |
| Secure ethical pentesting | Keeps automation authorized, safe, bounded, and reproducible | Scope policy, allowlist, rate limits, kill switch, audit trail; lab-only default | Critical |
| Network/service discovery | Produces reliable architecture observations and target identity controls | Nmap normalization schema and fixture-driven parser tests | Critical |
| Attack-chain planning | Represents preconditions, capability gains, dependencies, and exact replayability | Immutable action/chain model plus planner unit tests | Critical |
| Evidence engineering | Enables defensible claims and audits | Evidence schema, hashes, provenance, retention/redaction rules | Critical |
| Confidence calibration | Turns corroboration into an explainable, measurable grade instead of arbitrary labels | Versioned rubric, labeled scenarios, calibration report/confusion matrix | Critical |
| Remediation verification / regression | Implements the novel contribution without false closure | Replay controls, lifecycle state machine, regression comparison tests | Critical |
| Python async/plugin design | Makes tool orchestration robust, timeout-safe, and extensible | Adapter protocol, subprocess/RPC isolation, cancellation and retry semantics | High |
| SQLAlchemy/PostgreSQL | Persists state, relationships, evidence metadata, and immutable history | Migrations, transactional repository layer, integration tests | High |
| Graph modeling / NetworkX | Supports architecture and chain traversal/alternate-route analysis | Graph projection with deterministic replay/path queries | High |
| Metasploit RPC and tool adapters | Provides an authorized managed-system execution boundary | Mocked adapter tests before lab integration; secrets only via environment | High |
| ATT&CK / CWE / CVE vocabulary | Provides consistent technique/weakness mapping and reporting language | Optional IDs in action/finding records; do not treat a mapping as proof | Medium |
| Reporting and visualization | Makes confidence and verification understandable to assessors | Finding lifecycle, evidence, chain, and verdict rendered in PDF/Markdown | Medium |
| Experimental methodology | Supports credible final-year research claims | Preregistered scenarios, ground-truth labels, metrics, and run records | Critical |

MITRE ATT&CK is useful as a shared vocabulary for attacker behavior and defensive mapping, but it is not an attack planner or a truth source for a finding. [MITRE ATT&CK overview](https://www.mitre.org/focus-areas/cybersecurity/mitre-attack)  NIST SP 800-115 is a suitable methodological anchor for planning technical tests, analyzing findings, and mitigation work. [NIST SP 800-115](https://csrc.nist.gov/pubs/sp/800/115/final)

## Implementation sequence

1. **Establish lab governance and fixtures first.** Define scope manifests, harmless local test doubles, target snapshots, ground-truth labels, and redacted evidence handling. Do not attach real exploit tooling to an unrestricted executor.
2. **Build the core types and ledger.** Implement Pydantic/SQLAlchemy models, migrations, lifecycle transitions, evidence immutability, and test factories.
3. **Deliver a minimal MAPE-K vertical slice.** One allowlisted discovery adapter, one lab-only attack adapter/mock, normalized observations, utility ranking, action plan, and persisted trace.
4. **Implement corroboration and confidence.** Begin with weak credentials and RCE using fixture-based tests, then add privilege and data exposure. Version the rubric.
5. **Implement chain capture and Verify.** Make action specs replayable, validate prerequisite controls, and add closed/reopened/inconclusive tests before connecting a live lab.
6. **Add regression comparison.** Snapshot exposed architecture before/after remediation and evaluate alternate route predicates within explicitly bounded scope.
7. **Build reporting and evaluation harness.** Generate evidence-backed reports and run the scenario matrix repeatedly to collect metrics.
8. **Only then broaden the plugin repertoire or add concurrency.** Parallel actions need deterministic event ordering, resource limits, and clean cancellation.

## Acceptance criteria for the first credible demonstrator

- An allowlisted lab run produces normalized discovery observations and a persisted architecture snapshot.
- A successful representative attack produces a versioned chain and immutable evidence record.
- A separate corroboration probe can promote, downgrade, or flag the result with an explanation.
- A simulated remediation can cause the stored chain to be replayed and correctly yield each controlled verdict: closed, reopened, regression, and inconclusive.
- A report can show the claim, evidence, grade, chain, remediation event, replay controls, and final lifecycle status.
- Phase tests run in CI without requiring live vulnerable machines; live-lab tests are explicitly marked and opt-in.
- No plugin can target an undeclared host or run a disallowed/destructive action.

## Key decisions still required

1. Choose PostgreSQL-only versus PostgreSQL plus a graph database. PostgreSQL plus a NetworkX projection is the lowest-complexity first implementation.
2. Define the exact initial attack repertoire. A narrow four-class lab demonstrator is stronger and safer than broad tool coverage.
3. Write the confidence rubric before coding: factors, thresholds, missing-evidence behavior, and human-review routing.
4. Define what constitutes a regression and the bounded alternative-path search needed to support that label.
5. Decide whether the report is PDF-only or Markdown/JSON as canonical with PDF as a rendered artifact.
6. Obtain/prepare versioned, legally authorized VM images and remediation scripts; the repository currently has no lab configuration.

## Constraints and risks

- **Novelty risk:** confidence and replay verification are promising additions, but claims that no comparable system exists require a full literature review and careful wording.
- **Ground-truth risk:** without intentionally designed true/false/partial remediation scenarios, confidence and verification accuracy cannot be demonstrated credibly.
- **Evidence correlation risk:** multiple outputs from the same exploit/tool are not independent corroboration.
- **Replay safety risk:** historical commands are unsafe as a replay format; use typed, bounded action specifications with scope checks.
- **False-closure risk:** unreachable targets and missing preconditions must lead to `Inconclusive`, never `Verified Closed`.
- **Scope creep risk:** web attacks, broad post-exploitation, and large tool repertoires dilute the central research contribution. The initial implementation should stay host/service focused as the reference specifies.

## Sources used for this understanding

- User-provided [AEGIS project reference](C:/Users/santh/Downloads/AEGIS_Project_Reference.md).
- Skandylas & Asplund, [*Automated penetration testing: Formalization and realization*](https://www.diva-portal.org/smash/get/diva2%3A1956166/FULLTEXT01.pdf), *Computers & Security* 155 (2025), Article 104454.
- [NIST SP 800-115: Technical Guide to Information Security Testing and Assessment](https://csrc.nist.gov/pubs/sp/800/115/final).
- [MITRE ATT&CK](https://www.mitre.org/focus-areas/cybersecurity/mitre-attack).

---

This document captures the current shared understanding. It should be updated when the team settles the rubric, schema, initial repertoire, and evaluation scenarios, because those choices define the falsifiable version of AEGIS.
