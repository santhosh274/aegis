# AEGIS Workbench — Design Ideation

**Status:** editable spec. Implementation has not started.  
**Constraint:** this file is the only design source of truth for a later GUI. Existing `dashboard/` is a discarded prototype.  
**Audience:** operator / researcher exercising the lab-scoped MAPE-K-V core without living in the terminal.

Edit the **Open knobs** section (and any token) rather than inventing a second style. Locked decisions from the planning pass are marked **LOCKED**.

---

## 1. Purpose and non-goals

### Purpose

Give AEGIS a **routed workbench** so a human can:

- declare engagement scope (`ScopePolicy`)
- walk **Monitor → Analyze → Plan → Execute → (Devil’s Advocate) → Knowledge → Remediate → Verify**
- inspect typed ledger objects, not log soup
- run fixture-backed (and later lab-adapter) actions
- export the same Markdown report the Python reporter already produces

The GUI is a **client of the research core**, not a parallel pentest product.

### Non-goals

- Not a generic vulnerability scanner or CVSS dashboard.
- Not a Metasploit / Hydra / Nmap front-end. Live adapters stay behind `ScopePolicy` and registered plugins.
- Not a SOC wall: no world maps, no CPU/RAM gauges, no “cyber grid,” no fake packet counters.
- Not merging **utility**, **confidence**, and **verification** into one score or one badge.
- Not treating a tool success or a reported patch as ground truth.
- Not shipping exploit payloads through the UI. Attack steps remain declarative (`plugin`, `action`, `target`, `expected_predicate`, `parameters`).

---

## 2. System map (crux of the current repo)

### Loop

```
Monitor → Analyze → Plan → Execute → Devil’s Advocate
    → Knowledge → Report → Remediate → Verify → Knowledge → Monitor
```

AEGIS extends MAPE-K with **V (Verify)** and an evidence-backed **confidence grade**. Research name: **MAPE-K-V**.

### Three scores (never merge)

| Score | Question | When | Core | Output |
|---|---|---|---|---|
| **Utility** | What should the loop try next? | Before execute | `core/analyze/utility_ranker.py` `CandidateAction.utility()` | Ranked candidates |
| **Confidence** | How well is this claim supported? | After corroboration | `core/analyze/confidence_engine.py` | `confirmed` / `suspected` / `needs_human_review` |
| **Verification** | Did the recorded chain close after remediation? | After replay | `core/verify/replay_engine.py` | `verified_closed` / `reopened` / `regression_detected` / `inconclusive` |

Confidence rubric (v1, independent corroboration only):

- any `contradicts` → `needs_human_review`
- ≥1 independent `supports` and no `ambiguous` → `confirmed`
- otherwise → `suspected`

Verify rules:

- controls/prerequisites fail → `inconclusive`
- recorded chain reproduces → `reopened`
- decisive step fails, controls OK, no new exposure → `verified_closed`
- original path blocked but new exposure vs baseline snapshot → `regression_detected` (finding status `needs_human_review`, not a false all-clear)

### Domain objects the UI must speak

From `core/knowledge_base/models.py` and neighbors:

| Type | Role in UI |
|---|---|
| `ScopePolicy` | Lab mode, CIDR/host allowlist, approved plugin names |
| `Observation` | Normalized monitor records (target, kind, value, source, time) |
| `CandidateAction` | Utility ranking inputs (gain, info, cost, risk) |
| `Evidence` | Immutable, content-addressed claim support (`kind`, `summary`, `source`, `digest`, `id`) |
| `AttackStep` | Replayable declarative step — never a stored shell command |
| `Finding` | Claim + target + chain + confidence + lifecycle status |
| `Corroboration` | Independent probe: `supports` / `contradicts` / `ambiguous` |
| `RemediationEvent` | Claimed fix + optional `target_snapshot` |
| `VerificationResult` | Verdict, evidence, optional `failed_step_id`, `regression_summary` |
| `Exposure` | Snapshot item for regression (`service`/`port` comparison) |
| `EvaluationScenario` | Labeled lab cases in `evaluation/scripts/run_evaluation.py` |

Finding lifecycle (`FindingStatus`): `open` → `confirmed` / `needs_human_review` → `remediated` → `verified_closed` | `reopened` | `needs_human_review`.

### Persistence today

- `KnowledgeLedger`: in-memory, append-only (`findings`, `evidence`, `remediations`, `verifications`). Evidence IDs cannot be reused for different content.
- `json_store.save_finding` / `load_finding`: single-finding JSON round-trip between scripts.
- `reporting/generator.py` `render_finding`: canonical Markdown.
- PostgreSQL / `FindingRepository` is a future seam — the GUI should not assume SQL in v1.

### Operator scripts the workbench replaces (as buttons / jobs)

| Script | Meaning in the UI |
|---|---|
| `scripts/run_pipeline.py` | Deterministic fixture lifecycle → report |
| `scripts/run_initial_chain.py` | First integration chain |
| `scripts/run_first_exploit.py` | Produce a finding JSON |
| `scripts/run_verification.py` | Load finding, replay, persist verdict |
| `scripts/capture_exposure_snapshot.py` | Before/after exposure sets |
| `scripts/run_live_discovery.py` | Live monitor — **gated**, lab-only |
| `evaluation/scripts/run_evaluation.py` | Scenario matrix |
| `evaluation/scripts/collect_metrics.py` | Label accuracy / false all-clear |

### Safety

`Executor.execute` refuses unless:

1. `policy.lab_mode` is true
2. `permits_target(step.target)`
3. `permits_plugin(step.plugin)`
4. plugin is registered

The chrome always shows **LAB** vs **DENIED**. Out-of-scope targets never look “almost allowed.”

### Discarded prototype (`dashboard/`)

Do not copy: name “CYBERPIPE”, CSS grid overlay, mock CVSS severity, `ResourceGauges`, `LiveConsole` as decoration, scanner→exploit→post-ex pipeline as the primary model, Lucide-everywhere, tracking-widest ops chrome. Keep the **Vite + React + Tailwind** folder only as a later implementation host if convenient.

---

## 3. User jobs

1. **Open an engagement** — set allowed hosts/CIDRs, plugins, lab flag, run id.
2. **Ingest monitor data** — paste/import adapter records; see normalized `Observation` table.
3. **Analyze** — architecture/candidates on one side; **utility list** physically separate from **confidence rubric**.
4. **Plan + execute** — pick highest-utility permitted action; run registered plugin; store `Evidence`.
5. **Challenge** — run corroboration plugins (`weak_credentials`, `rce_validation`, `privilege_escalation`, `data_exposure`); attach outcomes.
6. **Read a finding as a dossier** — claim, primary evidence, chain, corroboration ledger, grade rationale (`rubric_version`).
7. **Register remediation** — description + snapshot; status becomes a *claimed* fix, not closed.
8. **Verify** — controls check, step-by-step replay, verdict, regression diff.
9. **Export** — Markdown from `render_finding`; optional JSON dump of the finding.
10. **Evaluation** — load named scenarios (`unpatched`, `ambiguous_signal`, `correct_patch`, `ineffective_patch`, `partial_patch`) and compare expected vs actual verdict.

---

## 4. Information architecture

**LOCKED:** routed workbench (not a single infinite scroll of widgets).

### Routes

| Path | Phase | Primary action |
|---|---|---|
| `/engagement` | Prepare | Save `ScopePolicy` + run metadata |
| `/monitor` | Monitor | Normalize / list observations |
| `/analyze` | Analyze | Rank utility **and** (separately) show confidence of selected finding |
| `/plan-execute` | Plan + Execute + Devil’s Advocate | Choose next action, execute, corroborate |
| `/verify` | Remediate + Verify | Register fix, replay, regression |
| `/findings/:id` | Knowledge dossier | Read-only-first document of one finding |
| `/report/:id` | Reporting | Preview + copy/download Markdown |
| `/evaluation` | Research harness | Scenario picker + expected/actual |

Redirect `/` → last route of the current run, default `/engagement`.

### Persistent chrome (every route)

Horizontal **instrument strip**, not a fat sidebar app shell:

1. **Mark** — wordmark `AEGIS` (Newsreader italic) + run id (Plex Mono).
2. **ScopeStrip** — lab flag, allowlist summary, plugin count. Click → `/engagement`.
3. **PhaseTimeline** — M · A · P · E · V as a hairline sequence; current phase is the only filled mark. Knowledge is implied (ledger always live), not a sixth cartoon node.
4. **RunState** — `idle` | `running` | `blocked` (scope deny) | `needs_review`. One verb-sized primary control on the right: context-sensitive (`Normalize`, `Choose next`, `Execute`, `Corroborate`, `Replay`).
5. **ModeBadge** — `FIXTURE` vs `LIVE` (live requires lab + allowlist).

No hamburger. No icon rail. Findings access: a **thin left column only on `/findings/:id` and `/verify`**, otherwise a text link `Findings n` in the strip.

### Dossier as the unit of design

A finding is a **document**, not a card in a masonry grid. Route `/findings/:id` is a typeset page: title, claim paragraph, metadata table, evidence, chain, corroboration, verification appendix.

---

## 5. Component inventory

Map name → Python type → notes. Implement later as React; names stay stable.

### Chrome

| Component | Binds to | Notes |
|---|---|---|
| `Wordmark` | — | `AEGIS` + subtitle `MAPE-K-V` in muted small caps, not a shield icon |
| `ScopeStrip` | `ScopePolicy` | Hosts/CIDRs as mono chips; empty allowlist = explicit `NO TARGETS` |
| `PhaseTimeline` | current phase + optional stage duration | Timeline, **not** a flowchart or chevrons |
| `RunState` | job status | Text + 4px square, not a pulsing neon orb |
| `ModeBadge` | fixture/live | Live is quieter, not more decorated |
| `PrimaryAction` | route verb | One per view. Secondary actions are text links |

### Engagement (`/engagement`)

| Component | Binds to | Notes |
|---|---|---|
| `RunMeta` | run id, lab id, time window | Plain fields, hairline under labels |
| `AllowlistEditor` | `allowed_hosts`, `allowed_networks` | One host/CIDR per line |
| `PluginPermitList` | `allowed_plugins` | Check against known plugin names; unauthorized stay visible but unselectable at execute time |
| `LabGate` | `lab_mode` | If false, entire execute/verify surface is inert with reason |

### Monitor (`/monitor`)

| Component | Binds to | Notes |
|---|---|---|
| `ObservationTable` | `list[Observation]` | Columns: time, source, target, kind, value. Sort/filter; no row chrome |
| `RecordIngest` | raw `list[dict]` → `ScannerManager.normalize` | Paste JSON or load fixture |
| `SourceLegend` | distinct `source` | Typographic, not colored pills for every vendor |

### Analyze (`/analyze`)

| Component | Binds to | Notes |
|---|---|---|
| `UtilityRankList` | `rank(candidates)` | Columns: name, U, E[gain], I, cost, risk. Weights shown as a footnote (`0.45 / 0.35 / 0.15 / 0.05`) |
| `ConfidenceRubric` | `ConfidenceAssessment` | Grade, numeric score, rationale, `rubric_version`. **Visually opposite** the utility list (split pane, vertical rule) |
| `FindingPicker` | `ledger.findings` | Mono ids + title; selected finding feeds the rubric |

Utility and confidence **must not share a color scale**. Utility is numeric/neutral. Confidence uses the single accent only for `confirmed`; `suspected` is body text; `needs_human_review` is inverted (canvas text on accent or a 1px reverse rule — pick one, see knobs).

### Plan + Execute (`/plan-execute`)

| Component | Binds to | Notes |
|---|---|---|
| `NextAction` | `Planner.choose_next` | Large type: action name; small type: utility breakdown |
| `AttackChainSteps` | `Finding.attack_chain` | Ordered list: plugin · action · target · predicate |
| `ExecuteGate` | `Executor.execute` | Shows which of the four gates passed/failed |
| `EvidenceLine` | returned `Evidence` | Summary + source + digest; write-once |
| `CorroborationLedger` | `DevilsAdvocate.validate` | Probe, outcome, independence, rationale, evidence summary |
| `PluginRoster` | registered `ActionPlugin` / `CorroborationPlugin` | Name only; no vendor logos |

### Dossier (`/findings/:id`)

| Component | Binds to | Notes |
|---|---|---|
| `ClaimHead` | `title`, `claim`, `target` | Serif title, claim as body paragraph |
| `MetaTable` | id, created_at, confidence, status | Two-column definition list |
| `PrimaryEvidence` | `primary_evidence` | — |
| `AttackChainSteps` | reuse | — |
| `CorroborationLedger` | reuse | — |
| `LifecycleMark` | `FindingStatus` | Word, not a traffic light |

### Verify (`/verify`)

| Component | Binds to | Notes |
|---|---|---|
| `RemediationForm` | `RemediationEvent` | Description + snapshot id/path |
| `ControlsCheck` | `controls_ok` | Explicit boolean the operator (or fixture) sets |
| `ReplayTrace` | per-step success/fail | Align with `AttackStep.id`; mark `failed_step_id` |
| `VerdictBlock` | `VerificationResult` | Verdict word + evidence summary |
| `RegressionDiff` | `detect_regressions(before, after)` | New `service/port` lines only |
| `SnapshotPair` | `set[Exposure]` | Before | After tables |

### Report + evaluation

| Component | Binds to | Notes |
|---|---|---|
| `ReportPane` | `render_finding` | Preview of Markdown; download `.md` |
| `JsonPeek` | `asdict(Finding)` | Collapsed by default |
| `ScenarioMatrix` | `SCENARIOS` | Name, ground truth, expected verdict, purpose |
| `MetricsLine` | `collect_metrics` | Accuracy / confusion / false all-clear — numbers, not charts in v1 |

### Anti-components (do not add)

- Hex/grid backgrounds, scanlines, glow, gradients, glassmorphism
- Lucide (or any) icon grid; if an icon is unavoidable, one 16px stroke mark for lab-gate only
- CPU/GPU/network gauges, sparklines of nothing, “packets/s”
- Generic vulnerability cards with red/orange/yellow/green severity
- World map, attack-origin animation
- Chat-style copilot dock
- Multi-card Bento dashboard on `/`
- Flowchart nodes with drop shadows for MAPE
- Terminal emulator as the hero (a small **job log** under RunState is allowed: timestamp + message, Plex Mono 12px, no fake prompt)

---

## 6. Visual tokens

**LOCKED language:** editorial print + instrument. Warm charcoal canvas, hairline rules, Newsreader titles, IBM Plex Mono for IDs/verdicts, MAPE as timeline, tabular evidence, almost no motion.

Dark is the **only** mode.

### Color (default palette — oxidised green accent)

| Token | Value | Use |
|---|---|---|
| `--canvas` | `#161411` | Page |
| `--inset` | `#1c1916` | Recessed tables, ingest areas |
| `--rule` | `#2e2a26` | 1px hairlines |
| `--rule-strong` | `#4a433c` | Active timeline segment, focused field |
| `--text` | `#e8e0d5` | Body |
| `--text-dim` | `#9a9186` | Labels, secondary |
| `--text-faint` | `#6b645c` | Unused phases, placeholders |
| `--accent` | `#7a8f62` | Confirmed, primary button fill, live “on” |
| `--accent-ink` | `#161411` | Text on accent fill |
| `--invert` | `#e8e0d5` | Primary ghost invert for `needs_human_review` mark (optional) |

**Do not use:** `#000000`, `#00ff00`, `#00ffff`, `#7c3aed`, Tailwind default indigo, red/amber/green traffic lights.

Alternate accent (knob): ochre `--accent-alt: #c4a35a`.

Surfaces are the canvas plus rules. **No cards-on-cards.** A “panel” is a region under a label with a top hairline, not a rounded elevated box. Radius: **0** everywhere (instrument). If a control needs a hit target, pad; do not round.

### Type

| Role | Family | Size / leading | Weight |
|---|---|---|---|
| Page / finding title | Newsreader | 28–36 / 1.15 | 400 italic for wordmark; 500 roman for finding title |
| Section label | IBM Plex Mono | 11 / 1.3 | 500, tracking `0.08em`, sentence case not scream-case (e.g. `Confidence`, not `CONFIDENCE GRADE`) |
| Body / claim | Newsreader | 16–18 / 1.5 | 400 |
| Tables, IDs, verdicts, JSON | IBM Plex Mono | 12–13 / 1.45 | 400 |
| Utility numbers | IBM Plex Mono | 13 tabular | 400 |
| Chrome strip | IBM Plex Mono | 12 | 400 |

Load from a self-hosted or Google Fonts import **only these two families**. No Inter, no JetBrains as UI (Plex covers mono). No Geist.

### Density

- Page margin: 32–48px.
- Strip height: ~48px.
- Table cell padding: 8px 12px.
- Generous vertical space on the dossier; tighter on `/monitor` and `/analyze` tables.
- Max content width for dossier/report: **720px**. Workbench tables can use full width.

### Motion

Almost none. Allowed:

- Timeline mark fill: 150ms opacity
- Running state: static `running` word + optional 1Hz blink of a 4px square (step-end, not ease)

No page-load stagger, no Framer-motion hero, no layout spring.

### Verdict / grade typography (no color semantics besides accent)

| Value | Treatment |
|---|---|
| `confirmed` | Accent word, mono |
| `suspected` | Dim text, mono |
| `needs_human_review` | Body text + 1px bottom rule in `--rule-strong` |
| `verified_closed` | Accent |
| `reopened` | Body, same weight as closed (do not “alarm red”) |
| `regression_detected` | Body + `RegressionDiff` revealed |
| `inconclusive` | Dim + controls reason |

Severity CVSS colors are **out**. Impact is not a finding field in the core model.

---

## 7. Interaction principles

1. **One primary action per route.** Everything else is a text button or a row click.
2. **Scope is a hard gate.** Failed `ExecuteGate` explains which check failed; never retry-spam.
3. **Fixture vs live** is always visible. Fixture jobs may run without a network; live requires lab + allowlist.
4. **Evidence is write-once.** UI never offers “edit evidence.” New probes append corroboration.
5. **Remediation ≠ closed.** After `RemediationForm` submit, CTA becomes `Replay`, not `Mark closed`.
6. **Utility ≠ confidence.** Cannot sort findings by utility; cannot show a combined “score.”
7. **Empty states are instructional** one sentence (“No observations. Ingest records or run a fixture.”) plus the primary action. No illustrations.
8. **Errors** are a single line under the strip (`PermissionError: target is outside authorized scope: …`).
9. **Keyboard:** `/` focuses finding search when the list is open; `Enter` fires primary action if the form is valid.
10. **No modal theater.** Confirm replay on-page (`Replay` then `Confirm replay` as a two-step in the same `VerdictBlock` area).

---

## 8. API sketch (spec only — FastAPI does not exist yet)

**LOCKED intent:** thin FastAPI over `KnowledgeLedger` + existing engines/scripts. Process-local ledger for v1 (restart clears unless JSON load). CORS for the Vite app.

Base: `/api/v1`

### Scope and run

```
GET  /run
PUT  /run/scope          body: ScopePolicy fields
POST /run/jobs           body: { "kind": "pipeline" | "initial_chain" | "evaluation", "scenario"?: string }
GET  /run/jobs/:id       status + log lines
```

### Monitor / analyze / plan

```
POST /observations/normalize   body: { target, source, records: [{kind, value}] }
GET  /observations
GET  /candidates               → ranked CandidateAction + utility
POST /plan/next                → chosen CandidateAction | null
```

### Findings and execute

```
GET    /findings
GET    /findings/:id
POST   /findings               create from fixture or ingest
POST   /findings/:id/execute   body: AttackStep; 403 on scope fail
POST   /findings/:id/corroborate  body: { plugins: string[] }
GET    /findings/:id/report    text/markdown
GET    /findings/:id/json
POST   /findings/:id/import    multipart or path to json_store file
```

### Remediate / verify

```
POST /findings/:id/remediate   body: { description, target_snapshot? }
POST /findings/:id/verify      body: { controls_ok, before?: Exposure[], after?: Exposure[], fixture_step_success?: bool[] }
GET  /findings/:id/verifications
GET  /findings/:id/remediations
```

Verify v1 may use a **fixture step executor** (boolean per step or “all fail/succeed”) matching `ReplayEngine.verify(..., execute_step, ...)`. Live step execution later uses the same `Executor` gates.

### Evaluation

```
GET  /evaluation/scenarios
POST /evaluation/run           body: { name }
GET  /evaluation/metrics       body/query: labels vs predictions
```

### Error shape

```json
{ "error": "permission", "detail": "target is outside authorized scope: 8.8.8.8" }
```

Map `PermissionError` → 403, `KeyError` unknown finding → 404, evidence mutation → 409.

The UI must display `detail` verbatim (instrument, not toast carnival).

---

## 9. v1 vs later

### v1 (GUI worth building first)

- Routed shell + tokens as above
- Fixture pipeline / initial chain as jobs
- Ledger inspection (findings, evidence, corroboration, verification)
- Scope editor + execute gate visualization
- Utility list vs confidence rubric split
- Remediation + fixture replay + regression tables
- Markdown report pane
- Evaluation scenario matrix
- JSON save/load via `json_store` semantics

### Explicitly later

- PostgreSQL `FindingRepository`
- Live Nmap / exploit adapters in-process
- PDF (ReportLab) wrapping Markdown
- Concurrent managed-tool scheduling (ADAPT-style)
- Graph view of architecture (`networkx`) — optional **later** dossier appendix, still print-like (nodes as type, not neon)
- Auth / multi-user
- Replacing the in-memory ledger across restarts except explicit JSON

### Implementation host (when coding starts)

Prefer rewrite inside `dashboard/` (Vite, React, Tailwind v4) using **this** token set, not the current CSS. Add a sibling Python FastAPI module (e.g. `api/`) that only imports core — **not specified as work now.**

---

## 10. Open knobs (edit these)

Change values here; keep section structure.

| Knob | Current | Alternatives |
|---|---|---|
| Accent | oxidised green `#7a8f62` | ochre `#c4a35a` |
| Timeline placement | top strip, after scope | under strip as a full-width hairline |
| Dossier | own route `/findings/:id` | split: table left / document right on `/verify` only |
| `needs_human_review` | strong rule under word | invert chip (text on `--text`, fill `--inset`, 1px `--rule-strong`) |
| Primary button | accent fill, square | hairline button, accent only on the label |
| Job log | 3 lines under strip | hidden unless `running` |
| Finding list | count link in strip | always-on 240px rail |
| Font loading | Newsreader + IBM Plex (Google) | self-host files in `dashboard/public/fonts` |
| Default landing | `/engagement` | `/monitor` if a run already has observations |
| Evaluation charts | none in v1 | later: one small confusion table, still no pie charts |
| Prototype code | discard visuals; maybe reuse folder | empty `dashboard/src` on first implementation PR |

---

## 11. Copy (tone)

- Product name in UI: **AEGIS**, subtitle **MAPE-K-V**.
- Prefer verbs from the core: *normalize*, *rank*, *choose next*, *execute*, *corroborate*, *remediate*, *replay*.
- Do not say *hack*, *pwn*, *critical vuln* unless it is a finding title from data.
- Scope failures quote the Python exception class in mono, then the message.
- Footer one line, faint: `Lab-scoped research workbench · claims require corroboration · closure requires replay`

---

## 12. Layout sketches (text)

### Engagement

```
[ AEGIS  run_04c1 ] [ LAB  10.0.0.5  10.0.0.0/24  3 plugins ] [ M A P E V ] [ idle ]  [ Save scope ]

Run
  id                lab
  ────────────────────────────────
Allowlist
  hosts             networks
  ────────────────────────────────
Plugins permitted
  fixture  nmap_scanner  …
  ────────────────────────────────
lab_mode  yes
```

### Analyze (split)

```
Utility (next action)                 |  Confidence (selected finding)
name        U    Eg   I    c    r     |  suspected
scan_smb    0.71 …                    |  score  0    rubric 1.0
exploit_x   0.64 …                    |  insufficient independent corroboration
                                      |  finding  Lab RCE claim
Footnote: U = 0.45Eg + 0.35I − 0.15c − 0.05r
```

### Dossier (narrow column)

```
Lab RCE claim

A controlled lab predicate indicates code execution.

target          10.0.0.5
confidence      confirmed
status          confirmed
id              8f2c…

Primary evidence
  fixture tool reported success    demo

Attack chain
  1  fixture  benign_nonce  10.0.0.5  nonce observed

Corroboration
  rce_validation  supports  independent  …

Verification
  (none | verdict block)
```

### Verify

```
Remediation
  description  [ ................................ ]
  snapshot     [ before.json ]
  [ Register remediation ]

Controls  ok

Replay
  1  benign_nonce  fail
Verdict  verified_closed
Regression  —
[ Confirm replay ]
```

---

## 13. Iteration log

| Date | Decision |
|---|---|
| 2026-09-22 | Hybrid look locked: editorial print + instrument |
| 2026-09-22 | Full MAPE-K-V workbench, not inspector-only |
| 2026-09-22 | Routed FastAPI workbench; replace mock dashboard later |
| 2026-09-22 | Default accent oxidised green; ochre as knob |
| 2026-09-22 | This file created; no other repo files changed |

Add a row whenever Darksyde27 edits a knob or rejects a component.
