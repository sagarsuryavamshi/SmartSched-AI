import os
import sys
from pathlib import Path

# Add project root to sys.path so 'src' and 'backend' imports resolve seamlessly
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.api.v1.router import api_router
from backend.app.api.v1.endpoints.auth import bootstrap_admin_from_env
from src.database.db_manager import ensure_runtime_tables, init_db
from src.data_management.loader import seed_synthetic_data

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="REST API for SmartSched AI — University Timetable Generation using Constraint-Based Search and Genetic Algorithms.",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.on_event("startup")
def startup_event():
    """Ensure database schema, runtime auth/job tables, and baseline data exist upon server boot."""
    db_file = str(settings.DB_PATH)
    if not os.getenv("DATABASE_URL", "").startswith("postgresql"):
        init_db(db_file)
        seed_synthetic_data(db_file, overwrite=False)
    else:
        ensure_runtime_tables(db_file)
    bootstrap_admin_from_env(db_file)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "Welcome to SmartSched AI REST API",
        "documentation": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
