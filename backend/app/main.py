"""
SentinelX - Intelligent Fraud Detection & Transaction Risk Intelligence Platform
Main FastAPI Backend Server
"""

import os
import time
import logging
from contextlib import asynccontextmanager

# Set matplotlib cache directory to temp before any imports
if "MPLCONFIGDIR" not in os.environ:
    import tempfile
    os.environ["MPLCONFIGDIR"] = os.path.join(tempfile.gettempdir(), "sentinelx_mpl")
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.database.connection import get_database, is_mock_database
from backend.app.database.indexes import create_all_indexes
from backend.app.services.fraud_service import get_fraud_service

# Import API Routers
from backend.app.routes.transactions import router as transactions_router
from backend.app.routes.predictions import router as predictions_router
from backend.app.routes.alerts import router as alerts_router
from backend.app.routes.investigations import router as investigations_router
from backend.app.routes.models import router as models_router
from backend.app.routes.graph import router as graph_router
from backend.app.routes.simulator import router as simulator_router
from backend.app.routes.auth import router as auth_router

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("sentinelx.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SentinelX Risk Engine & MongoDB connections...")
    create_all_indexes()
    get_fraud_service()
    
    if not os.environ.get("SENTINELX_SKIP_SEED"):
        from seed_data import seed_initial_records
        seed_initial_records()
        
    logger.info("SentinelX Platform is online and ready for transaction ingestion.")
    yield
    logger.info("SentinelX Backend shutting down.")

app = FastAPI(
    title="SentinelX - Transaction Risk Intelligence API",
    description="End-to-end FinTech transaction risk evaluation, explainable fraud classification, and investigation platform.",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for request timing and audit correlation
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response

# Mount Routers
app.include_router(auth_router)
app.include_router(transactions_router)
app.include_router(predictions_router)
app.include_router(alerts_router)
app.include_router(investigations_router)
app.include_router(models_router)
app.include_router(graph_router)
app.include_router(simulator_router)

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "HEALTHY",
        "timestamp": time.time(),
        "database": "CONNECTED",
        "models_loaded": get_fraud_service().xgb_model is not None
    }

# Mount React static SPA if dist directory exists
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist")
if os.path.exists(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/", tags=["System"])
    def root_endpoint():
        return {
            "platform": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "OPERATIONAL",
            "database_backend": "In-Memory PyMongo Store" if is_mock_database() else "Live MongoDB Instance",
            "documentation": "/docs"
        }
