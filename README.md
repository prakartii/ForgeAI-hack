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
│   ├── tests/                    # Backend pytest suite (22 tests)
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
    ├── run_backend.bat           # Launch backend server
    └── run_frontend.bat          # Launch frontend dev server
```

---

## 4. Phase 1 Implementation Status

✅ **Backend**: FastAPI + Pydantic v2 + SQLAlchemy + SQLite initialized.
✅ **Health Endpoint**: `GET /health` returns real application, environment, and database status.
✅ **API Namespaces**: `/api/agents`, `/api/scenarios`, `/api/runs`, `/api/traces`, `/api/failures`, `/api/prism`, `/api/abis`, `/api/mutations`, `/api/hardening`, `/api/regressions`, `/api/metrics`, `/api/gates`.
✅ **Database**: SQLite database initialized with all 17 models (`Policy`, `Claim`, `Document`, `Evidence`, `WorkflowState`, `AgentRun`, `TraceEvent`, `Scenario`, `CounterfactualPair`, `GroundTruth`, `Failure`, `BehaviorABI`, `ABIRule`, `Mutation`, `RegressionTest`, `EvaluationResult`, `ReleaseGateResult`).
✅ **Pydantic Schemas**: 17 domain schemas + complete `TraceEnvelope` complying with CLAUDE.md §9.
✅ **Architectural Boundaries**: 12 isolated subsystems under `backend/app/` with clear architectural contracts.
✅ **Frontend**: React + Tailwind CSS shell with Sidebar, Header, LifecycleStepper, live backend HealthBadge, and 10 primary views.
✅ **Live Connectivity**: Frontend fetches real status from `GET /health` and displays backend & SQLite state live.
✅ **Testing**: 22 backend automated tests covering health, database initialization, configuration, API routes, and schemas.

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

## 6. URLs
- **Backend API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)
