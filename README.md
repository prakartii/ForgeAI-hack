# FailureFoundry

> **"PRISM finds and explains the failure. FailureFoundry turns that diagnosis into an executable behavioral contract that prevents recurrence."**

**FailureFoundry** is a behavioral reliability and governance layer for high-stakes AI agents.

The repository includes **FairClaim** — a synthetic, autonomous multi-agent insurance-claims system — as the demonstration environment used to prove the layer works. FailureFoundry itself — the ABI compiler, enforcement, hardening, regression engine, and release-gate machinery — is the reusable product.

---

## 1. Core Architecture & Division of Responsibility

This boundary remains strictly preserved across all modules and tests:

| System | Responsibility |
|---|---|
| **PRISM** | **Observes** traces/sessions/runs, **evaluates** agent behavior, **surfaces** root causes, **provides** remediation evidence, **proves** before/after improvement. |
| **FailureFoundry** | **Generates** scenarios, **collects** trace metadata, **compiles** diagnoses into Behavior ABIs, **enforces** runtime controls, **hardens** challenge ladders, **persists** regression suites, **compares** agent versions, and **gates** releases. |
| **FairClaim** | Demonstration environment: Intake Agent, Adjudication Agent, Explainability Agent, Appeals Agent. |

---

## 2. Locked Lifecycle

FailureFoundry traces every agent through this exact sequence:

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

---

## 3. Project Structure

```
failurefoundry/
├── CLAUDE.md                     # Single source of truth
├── README.md                     # Documentation and setup guide
├── .gitignore                    # Git ignore configurations
├── .env.example                  # Environment template
│
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI application entry point
│   │   ├── config/               # Settings & env loading (pydantic-settings)
│   │   ├── db/                   # SQLite engine, session & declarative base
│   │   ├── api/                  # API routers (/api/... & /health)
│   │   ├── models/               # SQLAlchemy models (17 entities)
│   │   ├── schemas/              # Typed Pydantic schemas (17 entities + envelope)
│   │   ├── agents/               # Insurance demo agents (isolated)
│   │   ├── workflow/             # Workflow state machine (isolated)
│   │   ├── scenarios/            # Controlled scenario generator (isolated)
│   │   ├── traces/               # Common trace wrapper (isolated)
│   │   ├── failures/             # Failure detection engine (isolated)
│   │   ├── abi/                  # Behavior ABI compiler & registry (isolated)
│   │   ├── enforcement/          # Runtime enforcement & context sanitization (isolated)
│   │   ├── hardening/            # Adversarial challenge ladders (isolated)
│   │   ├── regression/           # Permanent regression test suite (isolated)
│   │   ├── prism/                # PRISM SDK integration client (isolated)
│   │   ├── metrics/              # Ground-truth deterministic metrics (isolated)
│   │   └── gates/                # Binary PASS/BLOCKED release gate (isolated)
│   ├── tests/                    # Backend pytest suite (90 tests)
│   ├── requirements.txt          # Python dependencies
│   └── pyproject.toml            # Project build metadata
│
├── frontend/
│   ├── src/
│   │   ├── components/           # Shell, Layout, Sidebar, Header, LifecycleStepper, HealthBadge
│   │   ├── pages/                # 10 platform views per CLAUDE.md §24
│   │   ├── services/             # API client (fetches /health and /api routes)
│   │   ├── hooks/                # React hooks (useHealth)
│   │   ├── types/                # Types & lifecycle definitions
│   │   ├── App.jsx               # View router & state container
│   │   ├── main.jsx              # React DOM root
│   │   └── index.css             # Tailwind styling
│   ├── package.json              # Frontend npm dependencies
│   ├── vite.config.js            # Vite build & backend proxy config
│   ├── tailwind.config.js        # Minimal engineering theme
│   └── postcss.config.js         # PostCSS plugins
│
├── data/
│   ├── claims/                   # Synthetic claims
│   ├── policies/                 # Synthetic policies
│   ├── documents/                # Claim documents
│   ├── images/                   # Damage photos
│   ├── scenarios/                # Scenarios
│   └── regression/               # Regression records
│
├── abis/
│   ├── fairness.yaml             # fair_adjudication_v1 Behavior ABI
│   └── workflow.yaml             # fair_workflow_v1 Behavior ABI
│
└── scripts/
    ├── run_backend.bat           # Launch backend server (Windows)
    ├── run_frontend.bat          # Launch frontend dev server (Windows)
    ├── load_demo_data.py         # Load the FairClaim India dataset + oracle check
    └── run_demo.py               # One-command, full-lifecycle demo (§27/§30)
```

---

## 4. Implementation Status — all 13 phases complete

| Phase | Status | Notes |
|---|---|---|
| 1. Project skeleton | ✅ | FastAPI + Pydantic v2 + SQLAlchemy + SQLite + Neo4j driver, 17 models/schemas |
| 2. Synthetic claims environment | ✅ | 2,500-claim India multimodal dataset + 1,512 images loaded; deterministic oracle validated, 0 mismatches |
| 3+4. Agent runtime & traces | ✅ | Intake/Adjudication/Explainability/Appeals, common `TraceRecorder`, real `WorkflowStateMachine` |
| 5. PRISM integration | ✅ | Real `prismtrace` SDK (`blockconvey-monitor`); honestly reports `not_configured` without credentials |
| 6. Failure detection | ✅ | Fairness / workflow / evidence / decision-correctness detectors over real agent output |
| 7+8. Behavior ABI + enforcement | ✅ | Compiles `abis/*.yaml` into executable `ABIRule` rows; proven before/after context-inspection test |
| 9+10. Hardening + regression | ✅ | L1-L4 challenge ladder over all 25 fairness groups; regression suite catches recurrence both ways |
| 11. Metrics + release gate | ✅ | 8-clause gate, PASS/BLOCKED from real computed metrics — never asserted |
| 12. Dashboard | ✅ | All 10 views wired to live backend actions (load data, scan, compile, harden, regress, gate) |
| 13. Demo script | ✅ | `scripts/run_demo.py` — one command, no server needed |

Backend test suite: **90 passing** (`pytest backend/tests`). No PRISM account is configured in this
environment, so the release gate legitimately reports `BLOCKED` on the `prism_evidence` clause
(and, over the full dataset, a genuine ~2% `evidence_completeness` gap from the Explainability
agent's injected citation failures) — per CLAUDE.md §31, this is never faked into a PASS.

---

## 5. Local Setup & Running

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### Backend Setup
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate      # Windows
   # source .venv/bin/activate   # Linux/macOS
   ```
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Copy configuration template:
   ```bash
   cp .env.example .env
   ```
4. Run tests:
   ```bash
   pytest backend/tests
   ```
5. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
   ```
   Or run:
   ```bash
   .\scripts\run_backend.bat
   ```

### Frontend Setup
1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Build verification:
   ```bash
   npm run build
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
   Or run:
   ```bash
   .\scripts\run_frontend.bat
   ```

---

## 6. One-command demo

Reproduces the full BUILD → ATTACK → PRISM OBSERVE → EVALUATE → DIAGNOSE →
COMPILE BEHAVIOR ABI → ENFORCE → FIX/HARDEN → PRISM PROVE → REGRESSION TEST
→ RELEASE GATE lifecycle end to end, with no server or browser required:

```bash
cd backend && python ../scripts/run_demo.py
```

It prints the v1 fairness-bug reproduction on a real counterfactual group,
the exact before/after Adjudication context diff once the fairness ABI is
enforced, the hardening ladder's per-level pass rate, real v1-vs-v2
metrics, the regression suite result, and the release gate's PASS/BLOCKED
verdict with every clause's real value.

## 7. URLs
- **Backend API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)
