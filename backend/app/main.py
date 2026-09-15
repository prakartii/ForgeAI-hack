from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config.settings import get_settings
from app.db.session import init_db
from app.api.router import api_router, health_router

settings = get_settings()

IMAGES_DIR = Path(__file__).resolve().parents[2] / "data" / "images"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    Initializes database tables on startup.
    """
    # Initialize SQLite database schema
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "FailureFoundry: Behavioral reliability and governance layer for high-stakes AI agents. "
        "Single source of truth: CLAUDE.md."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for frontend communication
origins = [
    settings.frontend_url,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount health check directly at /health and under /api
app.include_router(health_router)
app.include_router(health_router, prefix="/api")

# Mount API routers under /api
app.include_router(api_router)

# Serve the demo dataset's damage photos so the customer portal can show
# real claim evidence images, not placeholders.
if IMAGES_DIR.exists():
    app.mount("/media/images", StaticFiles(directory=str(IMAGES_DIR)), name="claim_images")


@app.get("/")
def root():
    """
    Root discovery endpoint.
    """
    return {
        "app": settings.app_name,
        "version": "0.1.0",
        "description": "Behavioral reliability and governance layer for high-stakes AI agents",
        "health": "/health",
        "api_docs": "/docs",
        "lifecycle": [
            "BUILD",
            "ATTACK",
            "PRISM OBSERVE",
            "EVALUATE",
            "DIAGNOSE",
            "COMPILE BEHAVIOR ABI",
            "ENFORCE",
            "FIX / HARDEN",
            "PRISM PROVE",
            "REGRESSION TEST",
            "RELEASE GATE",
        ],
    }
