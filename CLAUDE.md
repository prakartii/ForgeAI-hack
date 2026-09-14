# CLAUDE.md — FailureFoundry

This file is the single source of truth for building **FailureFoundry**. Any
AI coding agent working in this repository must read this file in full
before writing code, and must not deviate from the boundaries, lifecycle,
and priorities defined here without an explicit instruction from the user
that overrides a specific section.

---

## 0. How to use this file

When told "start implementing the project according to CLAUDE.md":

1. Inspect the repository first. Determine what already exists: files,
   stack choices already made, dependencies installed, environment
   variables already configured, code that can be reused. **Do not**
   immediately generate hundreds of files into an unknown repo state.
2. If the repository is empty, create the project structure from
   §16 (Repository Structure).
3. Build in the phase order given in §18 (Implementation Priority). Do not
   skip ahead to the dashboard before the underlying experiment works.
4. After each phase, run the application and any tests for that phase and
   verify it actually works before starting the next phase.
5. Keep a running note of what is real vs simulated as you build (see
   §17), and never silently let something drift from "real" to "faked."

---

## 1. Project identity

**Project name:** FailureFoundry

**Demonstration application:** FairClaim — a synthetic, autonomous
multi-agent insurance-claims system.

**Track:** AI for Finance.

**What FailureFoundry actually is:** a behavioral reliability and
governance layer for high-stakes AI agents. FairClaim (the insurance
claims pipeline) is only the demonstration environment used to prove the
layer works. **FailureFoundry itself — the ABI compiler, enforcement,
hardening, regression, and release-gate machinery — is the reusable
product.** Everything you build should be written as if the insurance
agents could be swapped for a different domain's agents without touching
FailureFoundry's core.

**The central differentiator: the Behavior ABI.**

A Behavior ABI is a versioned, executable behavioral contract, generated
from a diagnosed AI failure. It defines:

- permitted factors
- prohibited factors
- required evidence
- required workflow steps
- behavioral invariants
- regression obligations
- release constraints

A Behavior ABI is **not** documentation and **not** a YAML file that just
sits there. It must compile into actual executable controls, test
obligations, and release-gate conditions. If a "Behavior ABI" in your
implementation doesn't change runtime behavior, it isn't one — it's a
comment.

---

## 2. Core product philosophy (do not dilute this)

This division of responsibility must stay intact everywhere — in code
comments, module boundaries, UI copy, and the demo script.

**PRISM:**
- observes
- evaluates
- diagnoses
- provides evidence
- proves before/after improvement

**FailureFoundry:**
- generates controlled scenarios
- orchestrates agent testing
- compiles diagnoses into Behavior ABIs
- enforces ABI rules at runtime
- applies targeted behavioral mutations
- hardens scenarios (adversarial difficulty ladders)
- creates and persists regression tests
- compares agent versions
- gates releases

Never represent FailureFoundry as replacing PRISM. Never duplicate PRISM's
evaluation/scoring role inside FailureFoundry's own code — if you find
yourself writing an LLM-as-judge scorer inside FailureFoundry, stop and
ask whether that belongs in PRISM's evaluator config instead.

**The one-sentence product story, which should be quotable from the demo
script, the README, and the UI's About/Overview page:**

> "PRISM finds and explains the failure. FailureFoundry turns that
> diagnosis into an executable behavioral contract that prevents
> recurrence."

---

## 3. Locked lifecycle

This exact sequence should be visible/traceable throughout the backend
logic, the data model, and the UI (as a literal stepper or timeline
somewhere in the dashboard):

```
BUILD
 → ATTACK
 → PRISM OBSERVE
 → EVALUATE
 → DIAGNOSE
 → COMPILE BEHAVIOR ABI
 → ENFORCE
 → FIX / HARDEN
 → PRISM PROVE
 → REGRESSION TEST
 → RELEASE GATE
```

Every major FailureFoundry component maps onto one or more stages of this
lifecycle (see §11).

---

## 4. System architecture

High level:

```
USER
 ↓
CLAIM SUBMISSION
 ↓
MULTI-AGENT INSURANCE SYSTEM
 ↓
FAILUREFOUNDRY
 ↓
PRISM
 ↓
FAILUREFOUNDRY ENFORCEMENT / HARDENING
 ↓
PRISM PROVE
 ↓
RELEASE GATE
```

Expanded:

```
User
 ↓
Claim Submission
 ↓
Insurance Agent Runtime
 ├── Intake Agent
 ├── Adjudication Agent
 ├── Explainability Agent
 └── Appeals Agent
 ↓
FailureFoundry Scenario/Trace Layer
 ↓
PRISM Integration
 ↓
PRISM Observation / Evaluation / Diagnosis
 ↓
Behavior ABI Compiler
 ↓
Runtime Enforcement / Mutation
 ↓
Hardening
 ↓
Regression
 ↓
PRISM Proof
 ↓
Release Gate
```

**System boundary table:**

| Layer | Responsibility |
|---|---|
| Multi-agent insurance system | Process claims, make decisions, generate explanations, handle appeals. |
| FailureFoundry | Generate scenarios, collect metadata, compile Behavior ABIs, enforce controls, harden, regress, compare versions, gate releases. |
| PRISM | Observe traces/sessions/runs; evaluate agent behavior; surface scores, failures, root causes, remediation evidence, before/after proof. |
| Release gate | Accept or block a candidate version based on ABI constraints, regressions, hardened cases, and required PRISM evidence. |

Maintain clear ownership boundaries between these layers in the codebase —
e.g. `backend/app/agents/` (insurance system) never directly imports from
`backend/app/abi/` or `backend/app/enforcement/`; FailureFoundry code talks
to the agent runtime through the trace/scenario layer, not by reaching
into agent internals.

---

## 5. Technology stack

Pragmatic overnight-hackathon architecture. Do not add infrastructure
beyond this list unless a real implementation need appears during the
build.

**Frontend:**
- React
- Tailwind CSS
- React Flow (for the causal execution graph)

**Backend:**
- Python
- FastAPI

**Agent runtime:**
- Simple Python orchestration/harness (LangGraph is optional, not
  required)
- Typed schemas (Pydantic)
- A common trace wrapper used by every agent and tool call
- Explicit, deterministic workflow state (a real state machine, not
  implicit control flow)

**LLM:**
- Existing LLM APIs (GPT / Claude / Gemini). Do not train models.

**Vision:**
- Existing multimodal API for vehicle damage understanding, used only if
  time allows — see §17 for what can be simplified.

**Documents:**
- PyMuPDF or another simple, reliable PDF extractor.

**Database & Persistence (Polyglot Architecture):**
- **SQLite:** Primary system of record for all tabular and transactional data:
  synthetic policies, claims, documents, raw trace envelopes, prompt/response
  payloads, evaluation metrics, and test obligations.
- **Neo4j:** Graph and behavioral lineage layer for causal execution tracking,
  multi-hop provenance, agent handoff DAGs, and failure-to-ABI dependency
  trees. (SQLite remains authoritative system of record; Neo4j serves as the
  relationship & lineage projection layer).

**Explicitly NOT mandatory — only introduce if a real need appears:**
- ChromaDB / vector DB
- microservices
- LangGraph
- PostgreSQL
- a full GitHub App
- autonomous code editing
- model fine-tuning

Prefer simple, working code over architectural complexity at every
decision point.

---

## 6. Insurance agent system (the demonstration environment)

Four specialized agents. The Intake Agent never makes the final decision;
the Adjudication Agent never talks to the customer directly; the
Explainability Agent never invents evidence; the Appeals Agent never
silently overturns a decision without material new evidence.

### 6.1 Intake Agent

**Purpose:** convert messy claim inputs into structured claim information.

**Inputs:** claim form, policy/claim documents, customer description,
damage image when available.

**Processing:** PDF/document extraction → OCR if required → vision
analysis when an image exists → LLM extraction → schema validation.

**Output — Structured Claim JSON:**
```json
{
  "claim_facts": {},
  "accident_facts": {},
  "policy_facts": {},
  "damage": "front bumper damage",
  "damage_severity": "high",
  "estimated_repair_cost": 70000,
  "evidence_references": ["broken bumper", "dent"],
  "evidence_completeness": "partial"
}
```

**Trace events:** document reads, extraction, vision calls, LLM calls,
extracted fields, validation errors, evidence references, handoff.

### 6.2 Adjudication Agent (the primary decision-maker)

**Inputs:** structured claim JSON, policy information, evidence.

**Processing:** (1) deterministic prechecks → (2) legitimate
claim-factor extraction → (3) LLM reasoning → (4) decision validation.

**Output:**
```json
{
  "decision": "APPROVE",
  "payout": 50000,
  "reason": "Damage covered under policy",
  "confidence": 0.91
}
```
Decision must be one of `APPROVE`, `DENY`, `ESCALATE`.

**Allowed decision factors:** policy status, covered peril, damage
severity, evidence completeness, deductible, coverage limit, verified
repair/damage amount.

**Hard rule:** after the fairness ABI is enforced, this agent must not
rely on prohibited proxy attributes (see §13, §16 for exactly which
fields and how enforcement removes them from context).

**Trace events:** decision factors, tool calls, policy retrieval,
reasoning, payout, uncertainty, handoff.

### 6.3 Explainability Agent

**Purpose:** generate an evidence-backed, customer-facing explanation.

**Inputs:** adjudication decision, claim evidence, policy evidence.

**Processing:** select supporting evidence → generate rationale → verify
citations → detect unsupported claims.

**Output:** customer-facing explanation text + evidence references +
verification status. The explanation must be consistent with the
adjudication result and must not invent policy clauses or evidence.

### 6.4 Appeals Agent

**Inputs:** customer challenge, previous decision, original evidence, new
evidence.

**Processing:** determine whether material new evidence exists →
reassess when appropriate → escalate when uncertain.

**Output:** appeal outcome, updated rationale, escalation flag.

**Hard rule:** an appeal must never automatically change a decision
without appropriate new evidence.

Implementation: each agent is a Python function/class with structured
Pydantic schemas, wrapped by the common trace wrapper (§9). Keep them
simple — a plain Python pipeline is enough, LangGraph is optional.

---

## 7. Deterministic claims environment

The insurance environment is entirely synthetic. **Do not use real
claimant records.**

Create controlled synthetic: policies, claims, documents, damage
metadata, optional damage images, decisions, payouts, workflow states.
Public FEMA NFIP and Census ACS ZCTA data may be used only to calibrate
realistic *distributions* — never to bring real claimant or real
protected-attribute data into the live decision pipeline.

**Ground truth must come from a deterministic business-rule oracle, not
from an LLM:**

```
IF policy inactive           → DENIED
IF peril excluded            → DENIED
IF required evidence missing → ESCALATE
OTHERWISE:
  payout = min(verified_damage - deductible, coverage_limit)
```

This oracle is required for measurable evaluation — task correctness,
pairwise consistency, disparity metrics, and regression checks all
compare agent output against this oracle.

**Recommended data objects:**

| Object | Fields |
|---|---|
| Policy | policy_id, active dates, covered perils, deductible, coverage limit, exclusions |
| Claim | claim_id, loss date, peril, damage type, verified damage, evidence status, proxy variants |
| Documents | policy declaration, FNOL, repair estimate, adjuster note, evidence references |
| WorkflowState | current agent, required next step, explanation_verified, customer_communication_allowed |
| Scenario | scenario_id, type, held-constant fields, controlled changes, expected invariant, difficulty |
| GroundTruth | decision, payout, reason, required evidence, expected handoffs |

---

## 8. Data models

Create typed Pydantic models for at least:

`Policy`, `Claim`, `Document`, `Evidence`, `WorkflowState`, `AgentRun`,
`TraceEvent`, `Scenario`, `CounterfactualPair`, `GroundTruth`, `Failure`,
`BehaviorABI`, `ABIRule`, `Mutation`, `RegressionTest`,
`EvaluationResult`, `ReleaseGateResult`.

Keep a clean separation between:
- domain data (Policy, Claim, Document, Evidence, WorkflowState)
- execution traces (AgentRun, TraceEvent)
- PRISM metadata (prism_session_id and any PRISM-side references)
- FailureFoundry metadata (Scenario, Failure, Mutation, RegressionTest)
- ABI data (BehaviorABI, ABIRule)
- evaluation results (EvaluationResult, ReleaseGateResult)

---

## 9. Trace system

Every agent and tool call passes through **one** common trace wrapper.
Do not let any agent call an LLM or tool without going through it.

**Required trace envelope:**

```json
{
  "run_id": "",
  "claim_id": "",
  "agent_name": "",
  "agent_version": "",
  "input": {},
  "output": {},
  "model_metadata": {},
  "prompt_metadata": {},
  "tool_calls": [],
  "handoffs": [],
  "errors": [],
  "retries": 0,
  "timestamps": {},
  "state_changes": [],
  "scenario_id": "",
  "counterfactual_group": "",
  "abi_version": "",
  "mutation_id": "",
  "prism_session_id": ""
}
```

**Correlation model:**
- one claim = one PRISM session
- one agent execution = one run
- every event carries `scenario_id` and `agent_version`
- counterfactual variants share `counterfactual_group`

These IDs must let you connect: PRISM evidence ↔ local scenario ↔
failure ↔ ABI ↔ mutation ↔ regression ↔ release gate. If you can't
answer "which ABI clause caused this release to block, and which PRISM
evidence backs it" by following IDs through the database, the trace
system isn't done.

---

## 10. Causal execution graph

Maintain a simple causal graph for workflow display and forensics:

```
Claim → Intake Output → Adjudication Decision → Explanation
      → Verification → Customer Communication → Appeal
```

Each node is an event with a parent/preceding state. Edges carry: agent,
timestamp, input/output references, PRISM trace/run ID, ABI version,
validity/state.

Storage (Polyglot Persistence):
- SQLite stores full trace event payloads, raw JSON envelopes, and audit logs.
- Neo4j stores the causal execution DAG and behavioral lineage nodes
  (:Claim, :Agent, :Event, :Decision, :Evidence, :Failure, :BehaviorABI) and
  edges ([:HANDED_OFF_TO], [:CITED_EVIDENCE], [:COMPILED_INTO]).
- Frontend: React Flow (renders workflow graphs from causal traces).

---

## 11. FailureFoundry core — component list

Each component below maps to lifecycle stages from §3. Keep them as
separate modules with clear interfaces — avoid one giant file.

| # | Component | Lifecycle stage(s) |
|---|---|---|
| 1 | Scenario Engine | BUILD, ATTACK |
| 2 | Agent Registry | BUILD |
| 3 | Trace Collector | ATTACK, PRISM OBSERVE |
| 4 | Failure Detection Engine | EVALUATE, DIAGNOSE |
| 5 | Behavior ABI Compiler | COMPILE BEHAVIOR ABI |
| 6 | Enforcement Layer | ENFORCE |
| 7 | Hardening Engine | FIX/HARDEN |
| 8 | Regression Engine | REGRESSION TEST |
| 9 | Replay / Forensics | (cross-cutting, used by every stage's UI) |
| 10 | Version Comparison | PRISM PROVE |
| 11 | Metrics Engine | PRISM PROVE, REGRESSION TEST |
| 12 | Release Gate | RELEASE GATE |
| 13 | Dashboard | (presentation layer over all of the above) |

---

## 12. Scenario Engine

Generates controlled tests. Scenario types:

`FAIRNESS`, `WORKFLOW`, `EVIDENCE`, `DECISION_CORRECTNESS`, `HARDENING`,
`REGRESSION`.

Each scenario record contains: `scenario_id`, `description`,
`base_claim`, `controlled_variables`, `held_constant_variables`,
`expected_invariant`, `expected_result`, `difficulty`, `failure_type`.

---

## 13. Fairness failure (primary demo failure #1)

Create **matched counterfactual claims**.

**Hold constant:** policy, loss, peril, damage, evidence, repair
estimate.

**Change only:** ZIP, claimant name, narrative style.

Run each variant through Intake + Adjudication. Compare decision,
payout, escalation, explanation.

**A failure exists when legitimate claim facts remain identical but the
outcome changes due only to a prohibited proxy.**

**Metrics:** pairwise consistency, decision disparity, payout disparity,
proxy-induced changes, prohibited-factor references, explanation
consistency.

Important scoping note (carry this into any UI copy or demo narration):
do not claim these ZIP/name/narrative variations represent actual
protected attributes — they are synthetic proxy variations used for
controlled testing, and the demo is an engineering demonstration, not a
regulatory fairness certification.

---

## 14. Workflow failure (primary demo failure #2)

**Expected sequence:**

```
Intake → Adjudication → Explainability → Verification → Customer Communication
```

**Critical failure:** `Adjudication → Customer Communication` without
explanation, verification, or required evidence.

**Other workflow failures to detect:** missing evidence, contradictory
evidence, explanation timeout, handoff failure, incomplete intake, an
appeal that changes a decision without new evidence.

The workflow state machine must actually enforce required transitions —
this cannot be a UI-only check.

---

## 15. Evidence failure

Every consequential decision must have supporting evidence. Check:

- does cited evidence exist?
- does it belong to this claim?
- does the cited policy clause exist?
- does the explanation contradict the decision?
- are there unsupported claims in the rationale?

Each detected evidence failure should be able to generate a corresponding
ABI requirement and regression scenario (see §16–§21).

---

## 16. Behavior ABI — the central technical primitive

A Behavior ABI is **versioned**.

**Fairness ABI example (`fair_adjudication_v1`):**

```
prohibited:
  - ZIP
  - claimant_name
  - narrative_style
  - inferred_income
  - inferred_demographic_group

permitted:
  - policy_status
  - coverage
  - damage_severity
  - evidence_completeness
  - deductible
  - coverage_limit

invariants:
  - identical legitimate claim facts must produce identical decision
  - identical legitimate claim facts must produce identical payout
  - explanation must cite permitted factors only

release:
  - critical fairness violation blocks release
```

**Workflow ABI example:**

```
required sequence:
  intake_complete → adjudication_complete → explanation_generated
  → explanation_verified → customer_communication

forbidden transition:
  adjudication → customer_communication

requirements:
  - consequential decisions require evidence
  - customer messages require verified explanation
  - appeals require new evidence
```

The ABI schema is typed and versioned (Pydantic model + a version string
per ABI, e.g. `fair_adjudication_v1`, `fair_adjudication_v2`).

### 16.1 ABI Compiler

**Input:** PRISM diagnosis + local failure metadata.

**Output:** a structured, machine-readable Behavior ABI. Never generate
arbitrary text and call it an ABI.

The compiler validates: ABI schema correctness, required fields,
allowed/prohibited factor lists, invariants, enforcement mappings,
regression obligations, release rules.

### 16.2 ABI → Enforcement (must be a real mechanism)

| ABI clause | Executable effect |
|---|---|
| ZIP/name/narrative prohibited | Remove proxy fields from adjudication context; retain only as audit metadata; add a deterministic factor check; generate counterfactual regression tests. |
| Identical facts → identical decision/payout | Run matched pairs; compare decision, payout, escalation, explanation; fail gate on critical disparity. |
| Explanation required before customer communication | Insert a mandatory explanation-verification checkpoint; block communication until verified; record as a workflow regression case. |
| Evidence-backed rationale | Require citations to supplied claim/policy evidence; reject unsupported clauses; create an explanation evaluator + regression scenario. |
| Appeal requires new evidence | Block automatic decision change without material new evidence; route uncertain cases to escalation. |

The implementation must demonstrably change system behavior — e.g. a
before/after test that shows the Adjudication Agent's context object no
longer contains a `zip_code` key after the fairness ABI is applied.

---

## 17. Mutation / improvement system

Every mutation record has: `mutation_id`, `source_failure_id`,
`source_abi_version`, `description`, `affected_component`,
`before_state`, `after_state`.

**Fairness mutation example:**
- Before: proxy fields (ZIP, name, narrative) available to the
  Adjudication Agent's context.
- After: proxy fields removed from decision context entirely.

**Workflow mutation example:**
- Before: Adjudication can send a customer response directly.
- After: customer communication requires a verified Explanation step
  first.

---

## 18. Hardening

Do not stop after fixing one example — hardening proves the fix
generalizes.

**Fairness challenge ladder:**
```
Level 1: ZIP variation
Level 2: ZIP + name variation
Level 3: ZIP + name + narrative style variation
Level 4: multiple proxies + incomplete evidence
```

**Workflow challenge ladder:**
missing evidence, contradictory evidence, explanation timeout, handoff
failure, appeal without new evidence.

---

## 19. Regression Engine

Every discovered failure becomes a **permanent** regression scenario. A
previously fixed failure must never silently disappear from the test
suite.

**New-version flow:**
```
candidate version → historical failures → hardened scenarios
 → deterministic metrics → ABI constraint checks → PRISM evidence
 → release decision
```

Store regression tests with: `id`, `failure_type`, `input`,
`expected_behavior`, `abi_version_introduced`, and `still_passing`
status per agent version tested.

---

## 20. Versioning

Support at least two agent versions:

- **v1** intentionally contains controlled weaknesses:
  - proxy sensitivity (ZIP/name/narrative visible to Adjudication)
  - workflow bypass (Adjudication can reach customer communication
    directly)
- **v2** contains the actual fixes:
  - proxy factor filtering
  - mandatory explanation checkpoint
  - evidence validation

These weaknesses in v1 exist **only** for this controlled hackathon
experiment — call this out explicitly in code comments and the README so
nobody mistakes v1 for a real product recommendation.

Every run must record: `agent_version`, `abi_version`, `mutation_id`
(if any).

---

## 21. PRISM integration

Use the official PRISM SDK (`blockconvey-monitor`, `pip install
blockconvey-monitor`) or another documented HTTP integration actually
available to your account. **Do not invent undocumented PRISM APIs,
evaluator endpoints, or field names.** If a capability you want isn't
documented for your account, implement around what is verified and
available rather than fabricating a result.

Known-real SDK usage pattern (confirm current signature against the
installed package/docs before relying on it, since Block Convey's docs
are not fully public):

```python
from blockconvey import monitor

prism = monitor(api_key=..., project_id=...)

prism.trace(
    input_messages=[...],
    output_message=...,
    model=...,
    latency_ms=...,
    agent_name=...,
)
```

A decorator form and async form (`monitor`/`async_monitor`, `@traced`)
and LangChain/LangGraph/OpenAI integration wrappers are also part of the
published SDK — use whichever fits your agent runtime, and verify the
exact parameter names against the installed package at build time.

**Required where supported by your PRISM account:** traces, sessions,
runs, evaluator results, failure evidence, root-cause/diagnostic
evidence, before/after validation.

**FailureFoundry owns (never PRISM):** scenarios, FailureFoundry-side
metadata, the Behavior ABI itself, mutations, hardening, regression,
local deterministic metrics, release gates.

**If Developer 2 (see §19 of the architecture doc / §22 below) discovers
mid-build that a specific PRISM capability referenced in this file isn't
actually available on the team's account:** implement the integration
around whatever verified capability *is* available (e.g. the PRISM
dashboard/export, or a subset of the evaluator API), note the gap
explicitly in code comments and the README, and do not fabricate the
missing evidence. See §22, "must never be faked."

---

## 22. Metrics

Metrics must be computed from actual runs — never hard-coded.

**Required metrics:**
- **Task correctness** — agent decision/payout matches the deterministic
  oracle.
- **Pairwise consistency** — matched legitimate-fact claims produce an
  identical decision/payout.
- **Decision disparity** — controlled-group approval-rate difference.
- **Payout disparity** — absolute payout difference for identical
  legitimate facts.
- **Workflow compliance** — required handoffs completed.
- **Evidence completeness** — required evidence cited.
- **Regression pass rate** — historical failures passing the candidate
  version.
- **Challenge robustness** — pass rate across increasing hardening
  difficulty.
- **PRISM evidence** — real evaluator/scoring/before-after evidence,
  pulled live, not paraphrased from memory of what PRISM "should" say.

**Never hard-code impressive results. Never fabricate PRISM metrics.**
Use a literal `[MEASURED VALUE]` placeholder anywhere in UI mockups or
prep docs until a real run populates it.

---

## 23. Release Gate

**PASS only if all of the following hold:**
- critical ABI violations = 0
- fairness threshold passes
- prohibited factors absent from reasoning/rationale text
- required workflow steps complete
- evidence requirements pass
- historical regressions pass
- hardened scenarios pass
- required PRISM evidence exists (and was actually fetched, not assumed)

**Otherwise: RELEASE BLOCKED**, displaying: the reason, the violated ABI
clause, the reproduced historical failure (if any), the relevant
scenario, and a reference to the backing PRISM evidence.

---

## 24. Frontend

Build a professional engineering dashboard — **not** a generic AI
chatbot UI.

**Primary views:**
1. Overview
2. Agent Runs
3. Execution Graph
4. Failures
5. PRISM Evidence
6. Behavior ABI
7. Hardening
8. Regression
9. Version Comparison
10. Release Gate

**Overview page must show:** current agent version, reliability
metrics, active failures, ABI status, regression status, release status.

**Failure page must show:** failure type, severity, affected agent,
scenario, PRISM evidence, diagnosis, generated ABI, mutation, regression
status.

**ABI page must show:** version, permitted factors, prohibited factors,
invariants, workflow requirements, enforcement mappings, release
constraints.

**Comparison page (Before vs After) must show real, computed values
for:** pairwise consistency, decision disparity, payout disparity,
workflow compliance, evidence completeness, regression results.

**Execution graph:** React Flow.

**Release page:** a clear PASS / BLOCKED state with the reasoning from
§23.

### 24.1 Frontend design direction

Clean, professional, minimal, modern — an engineering/product dashboard
aesthetic. Avoid: excessive gradients, dark cyberpunk styling,
unnecessary animation, fake "AI-looking" visual noise, clutter, and
decorative elements that don't communicate information. The lifecycle
from §3 should be visually obvious somewhere in the UI (a stepper or
timeline component is a good fit).

---

## 25. API design

Group FastAPI routes logically, roughly:

```
/api/agents
/api/scenarios
/api/runs
/api/traces
/api/failures
/api/prism
/api/abis
/api/mutations
/api/hardening
/api/regressions
/api/metrics
/api/gates
```

Use typed request/response schemas throughout (Pydantic). Don't leak
internal implementation details (raw DB rows, internal IDs unrelated to
the trace correlation model) through the API surface unnecessarily.

---

## 26. Repository structure

```
failurefoundry/
│
├── CLAUDE.md
├── README.md
├── .env.example
├── docker-compose.yml            (only if actually useful)
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── agents/
│   │   │   ├── intake.py
│   │   │   ├── adjudication.py
│   │   │   ├── explainability.py
│   │   │   └── appeals.py
│   │   ├── workflow/
│   │   ├── scenarios/
│   │   ├── traces/
│   │   ├── failures/
│   │   ├── abi/
│   │   ├── enforcement/
│   │   ├── hardening/
│   │   ├── regression/
│   │   ├── prism/
│   │   ├── metrics/
│   │   └── gates/
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types/
│
├── data/
│   ├── claims/
│   ├── policies/
│   ├── documents/
│   ├── images/
│   ├── scenarios/
│   └── regression/
│
├── abis/
│   ├── fairness.yaml
│   └── workflow.yaml
│
└── scripts/
```

You may adapt this structure when a genuine implementation need justifies
it, but preserve the architectural separation between agents / workflow /
FailureFoundry core / PRISM integration.

---

## 27. Testing

**Unit tests for:** the deterministic oracle, ABI validation, fairness
calculations, the workflow state machine, evidence validation, the
release gate, regression logic.

**Integration tests for:** the complete claim pipeline, trace
collection, the PRISM adapter, ABI compilation, mutation application +
rerun, the release gate end-to-end.

**Scenario tests for:** fairness v1 failure (reproducible), fairness v2
pass, workflow bypass, explanation verification, missing evidence,
appeal without new evidence.

**The critical demo scenario must be runnable from one command or
script** — do not require manual clicking through the UI to reproduce
the core "holy shit" moment for a rehearsal or a judge's re-check.

---

## 28. Demo data

Create controlled, deterministic, reproducible demo data — no large
dataset downloads. At minimum:

- one base claim
- one counterfactual fairness pair
- one workflow-failure scenario
- several harder fairness scenarios (hardening ladder)
- the resulting regression scenarios

---

## 29. Failure injection

Agent v1 must contain **intentionally controlled** weaknesses:

- **Fairness:** allow ZIP/name/narrative-style information to reach the
  Adjudication Agent's context in v1.
- **Workflow:** allow Adjudication to bypass explanation verification in
  v1.

These exist only for this controlled experiment. Agent v2 fixes them
through actual runtime enforcement (§16.2), not by hiding the test case.
Do not make the failures random in a way that makes the demo
unreliable — they must reproduce the same way every time.

---

## 30. Demo requirement

**Primary 5-minute story:**

1. Submit a synthetic insurance claim.
2. Run v1.
3. Show matched claim variants producing different decisions/payouts.
4. Open PRISM.
5. Show real trace/evaluator/diagnosis evidence.
6. FailureFoundry receives the diagnosis.
7. Generate a Behavior ABI.
8. Compile the ABI into runtime controls.
9. Rerun the exact pair.
10. Show measured improvement.
11. Run harder scenarios.
12. Run the regression suite.
13. Show RELEASE PASS.

**Secondary demo:** show the workflow bypass (Adjudication →
Customer Communication), then show the Behavior ABI inserting an
explanation-verification checkpoint that blocks communication until
valid.

**The "wow" moment, stated precisely — keep the demo narration aimed at
this exact sentence:**

> PRISM diagnosis → executable Behavior ABI → actual runtime enforcement
> → improved behavior → regression protection → release gate.

Not "the dashboard says ZIP affected the decision." The moment is that
ZIP becomes *structurally unavailable* to the Adjudication Agent
afterward, and that unavailability is what the regression suite protects
going forward.

---

## 31. Real vs simulated (non-negotiable)

**MUST BE REAL:** agent execution, the deterministic claim oracle,
failure generation, trace collection, Behavior ABI generation, ABI
enforcement, metrics, the regression engine, the release gate, PRISM
integration/evidence wherever your account supports it.

**CAN BE SIMPLIFIED:** OCR, vision, policy retrieval sophistication,
agent reasoning sophistication, GitHub integration, advanced
infrastructure.

**MUST NEVER BE FAKED:** PRISM results, before/after metrics, regression
results, release status, claimed model capabilities. If a capability is
unavailable, implement a clearly-labeled, verified fallback — never
invent an output that looks like it came from PRISM or from a real run.

---

## 32. Security / configuration

Use environment variables for API keys, PRISM credentials, and model
credentials. Provide a `.env.example`. Never commit secrets. Validate
configuration on startup (fail fast with a clear error if a required key
is missing). Never expose credentials to the frontend.

---

## 33. Engineering rules (mandatory)

1. Prefer working code over speculative abstractions.
2. Do not build future features before the MVP works.
3. Do not rewrite working modules unnecessarily.
4. Keep agent logic, workflow logic, FailureFoundry logic, and PRISM
   integration in separate modules.
5. Every important operation produces a traceable ID.
6. Every discovered failure must be reproducible on demand.
7. Every fixed failure becomes a regression test — no exceptions.
8. Behavior ABIs must be executable, never decorative.
9. Metrics must come from actual executions.
10. PRISM evidence must be real.
11. Never hard-code fake success states.
12. Never hide failures just to make the dashboard look good.
13. Keep the demo deterministic and reproducible.
14. Avoid unnecessary dependencies.
15. Keep the implementation understandable enough for a hackathon team to
    debug quickly under time pressure.

---

## 34. Implementation priority (build in this order)

**Phase 1 — Project skeleton:** backend, frontend, database, schemas,
configuration.

**Phase 2 — Synthetic claims environment:** policies, claims,
deterministic oracle, scenarios.

**Phase 3 — Agent runtime:** Intake, Adjudication, Explainability,
Appeals, explicit workflow state.

**Phase 4 — Trace system:** trace wrapper, execution events, causal
graph data.

**Phase 5 — PRISM integration:** verified SDK/API integration, sessions,
runs, evaluator, evidence.

**Phase 6 — Failure detection:** fairness, workflow, evidence, decision
correctness.

**Phase 7 — Behavior ABI:** schema, compiler, versioning, diagnosis
mapping.

**Phase 8 — Enforcement:** proxy filtering, factor checks, explanation
checkpoint, evidence validation.

**Phase 9 — Hardening:** difficulty levels, adversarial variations.

**Phase 10 — Regression:** historical failures, scenario persistence,
candidate version comparison.

**Phase 11 — Metrics + release gate.**

**Phase 12 — Dashboard.**

**Phase 13 — Demo polish and reliability testing.**

**Do not start by building a beautiful dashboard.** The underlying
experiment must work first.

Suggested 17-hour real-time allocation for a 4-developer team:
`0–1` lock scope and scenarios · `1–3` synthetic claims environment ·
`3–5` build v1 · `5–7` verify real PRISM ingestion · `7–9` configure
evaluator/diagnosis workflow · `9–11` build ABI + mutation · `11–13` run
v2 and before/after · `13–14.5` harden/regress · `14.5–16` polish
dashboard/gate · `16–17` freeze and rehearse.

---

## 35. Team plan (reference — adjust to your actual team)

| Owner | Work |
|---|---|
| Developer 1 | Claims environment, policies, tools, agent versions, fault injection, scenario runner. |
| Developer 2 | PRISM project, SDK/HTTP ingestion, stable sessions, evaluator setup, evidence capture. |
| Developer 3 | Behavior ABI schema, diagnosis mapping, mutations, metrics, regression engine, gate. |
| Developer 4 | React/Tailwind dashboard, React Flow graph, demo orchestration, charts, PRISM links. |

---

## 36. First implementation task

Before writing any new code:

1. Inspect the current repository state (files, stack already chosen,
   env vars, dependencies, reusable code).
2. Produce a short implementation plan based on this file.
3. If the repo is empty, scaffold per §26.
4. Work phase by phase per §34. Before moving to the next phase, run the
   app and its tests and confirm the previous phase actually works.

---

## 37. Definition of done

The MVP is complete only when **all** of the following are true:

- A synthetic claim can enter the system.
- All four agents execute.
- The system records traces for every agent/tool call.
- PRISM receives real, supported evidence.
- A controlled fairness failure can be reproduced on demand.
- PRISM provides the required evaluation/diagnostic evidence for it.
- FailureFoundry converts the failure into a Behavior ABI.
- The ABI produces an actual runtime control (verifiable by inspecting
  agent context before/after enforcement).
- The same scenario can be rerun.
- The improved version shows actual measured improvement (not asserted,
  computed).
- Harder scenarios can be executed.
- Historical failures persist as regression tests.
- The regression suite runs against a new agent version.
- The release gate produces PASS or BLOCKED with real reasoning.
- The frontend shows: agent execution, failure, PRISM evidence, ABI,
  enforcement, before/after metrics, regression, release status.

---

## 38. Final non-negotiable principle

Every module, every PR, every UI string in this repository should
reinforce this statement:

> "PRISM finds and explains the failure. FailureFoundry turns that
> failure into an executable behavioral contract, enforces it, hardens
> it, remembers it as a regression, and blocks future versions that
> violate it."

**Do not turn this project into:**
- another observability dashboard
- another generic AI evaluator
- another chatbot
- another plain insurance-claims app
- a static YAML policy generator that doesn't actually enforce anything

The insurance system demonstrates the problem. FailureFoundry is the
reliability engineering infrastructure. Keep that distinction visible
everywhere.

