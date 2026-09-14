from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.agents import router as agents_router
from app.api.scenarios import router as scenarios_router
from app.api.runs import router as runs_router
from app.api.traces import router as traces_router
from app.api.failures import router as failures_router
from app.api.prism import router as prism_router
from app.api.abis import router as abis_router
from app.api.mutations import router as mutations_router
from app.api.hardening import router as hardening_router
from app.api.regressions import router as regressions_router
from app.api.metrics import router as metrics_router
from app.api.gates import router as gates_router
from app.api.graph import router as graph_router

# Master API Router mounted under /api
api_router = APIRouter(prefix="/api")

api_router.include_router(agents_router)
api_router.include_router(scenarios_router)
api_router.include_router(runs_router)
api_router.include_router(traces_router)
api_router.include_router(failures_router)
api_router.include_router(prism_router)
api_router.include_router(abis_router)
api_router.include_router(mutations_router)
api_router.include_router(hardening_router)
api_router.include_router(regressions_router)
api_router.include_router(metrics_router)
api_router.include_router(gates_router)
api_router.include_router(graph_router)

__all__ = ["api_router", "health_router"]
