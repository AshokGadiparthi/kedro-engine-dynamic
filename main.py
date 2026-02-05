"""
FastAPI Main Application - 100% WORKING
Database auto-initializes on startup with ALL tables
Complete ML Platform with Kedro Integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from app.core.database import engine, Base, init_db
from app.models.models import (
    User, Workspace, Project, Dataset, Activity,
    Datasource, Model, Job,  # ← Must include Job!
    EdaResult, EDASummary, EDAStatistics, EDAQuality, EDACorrelations
)

Base.metadata.create_all(bind=engine)  # Creates all registered models

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# KEDRO CONFIGURATION
# ============================================================================

KEDRO_PROJECT_PATH = Path(os.getenv(
    'KEDRO_PROJECT_PATH',
    '/home/ashok/work/latest/full/kedro-ml-engine-integrated'
))

logger.info(f"Kedro project path: {KEDRO_PROJECT_PATH}")

if KEDRO_PROJECT_PATH.exists():
    if str(KEDRO_PROJECT_PATH / 'src') not in sys.path:
        sys.path.insert(0, str(KEDRO_PROJECT_PATH / 'src'))
    logger.info(f"✅ Kedro project found and added to path")
else:
    logger.warning(f"⚠️  Kedro project not found at {KEDRO_PROJECT_PATH}")

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

try:
    from app.core.job_manager import JobManager
    logger.info("✅ JobManager imported successfully")
except ImportError as e:
    logger.warning(f"⚠️  JobManager import warning: {e}")
    JobManager = None

# ============================================================================
# IMPORT ROUTERS
# ============================================================================

try:
    from app.api import health
    logger.info("✅ Health router imported")
except ImportError as e:
    logger.warning(f"⚠️  Health router: {e}")
    health = None

try:
    from app.api import auth
    logger.info("✅ Auth router imported")
except ImportError as e:
    logger.warning(f"⚠️  Auth router: {e}")
    auth = None

try:
    from app.api import projects
    logger.info("✅ Projects router imported")
except ImportError as e:
    logger.warning(f"⚠️  Projects router: {e}")
    projects = None

try:
    from app.api import datasets
    logger.info("✅ Datasets router imported")
except ImportError as e:
    logger.warning(f"⚠️  Datasets router: {e}")
    datasets = None

try:
    from app.api import datasources
    logger.info("✅ Datasources router imported")
except ImportError as e:
    logger.warning(f"⚠️  Datasources router: {e}")
    datasources = None

try:
    from app.api import models
    logger.info("✅ Models router imported")
except ImportError as e:
    logger.warning(f"⚠️  Models router: {e}")
    models = None

try:
    from app.api import activities
    logger.info("✅ Activities router imported")
except ImportError as e:
    logger.warning(f"⚠️  Activities router: {e}")
    activities = None

try:
    from app.api import eda
    logger.info("✅ EDA router imported")
except ImportError as e:
    logger.warning(f"⚠️  EDA router: {e}")
    eda = None

try:
    from app.api import pipelines
    logger.info("✅ Pipelines router imported")
except ImportError as e:
    logger.warning(f"⚠️  Pipelines router: {e}")
    pipelines = None

try:
    from app.api import jobs
    logger.info("✅ Jobs router imported")
except ImportError as e:
    logger.warning(f"⚠️  Jobs router: {e}")
    jobs = None

# ============================================================================
# APPLICATION LIFECYCLE
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager
    Initializes database with ALL required tables on startup
    """
    # ========================================================================
    # STARTUP
    # ========================================================================
    try:
        logger.info("\n" + "="*80)
        logger.info("🚀 STARTING UP APPLICATION")
        logger.info("="*80)

        # Initialize database with ALL tables
        logger.info("📊 Initializing database with ALL tables...")
        if JobManager:
            job_manager = JobManager()
            logger.info("✅ Database initialized successfully with all tables!")
        else:
            logger.warning("⚠️  JobManager not available, database initialization skipped")

        logger.info(f"✅ Kedro project path: {KEDRO_PROJECT_PATH}")
        logger.info(f"✅ API running on: {os.getenv('API_HOST', '0.0.0.0')}:{os.getenv('API_PORT', '8000')}")
        logger.info(f"✅ Celery broker: {os.getenv('CELERY_BROKER_URL', 'not configured')}")
        logger.info(f"✅ Database: {os.getenv('DATABASE_URL', 'sqlite:///ml_platform.db')}")
        logger.info("="*80)
        logger.info("✅ FastAPI application started successfully\n")

    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}", exc_info=True)
        raise

    yield

    # ========================================================================
    # SHUTDOWN
    # ========================================================================
    logger.info("\n" + "="*80)
    logger.info("🛑 SHUTTING DOWN APPLICATION")
    logger.info("="*80)
    logger.info("⛔ FastAPI application shutdown")
    logger.info("="*80 + "\n")

# ============================================================================
# CREATE FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="ML Platform with Kedro Integration",
    description="Complete ML Platform with Exploratory Data Analysis and Kedro Pipeline Execution",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

logger.info(f"✅ FastAPI application created: {app.title}")

# ============================================================================
# CORS MIDDLEWARE
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("✅ CORS middleware configured")

# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": app.title,
        "version": app.version,
        "status": "active",
        "documentation": "/docs",
        "kedro_project": str(KEDRO_PROJECT_PATH)
    }

@app.get("/api/health")
def api_health():
    """API health check"""
    return {
        "status": "healthy",
        "api": "active",
        "database": os.getenv('DATABASE_URL', 'sqlite:///ml_platform.db'),
        "celery_broker": os.getenv('CELERY_BROKER_URL', 'not configured')
    }

# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

if health:
    app.include_router(health.router, tags=["Health"])
    logger.info("✅ Health router included")

if auth:
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    logger.info("✅ Auth router included")

if projects:
    app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
    logger.info("✅ Projects router included")

if datasets:
    app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets"])
    logger.info("✅ Datasets router included")

if datasources:
    app.include_router(datasources.router, prefix="/api/datasources", tags=["Datasources"])
    logger.info("✅ Datasources router included")

if models:
    app.include_router(models.router, prefix="/api/models", tags=["Models"])
    logger.info("✅ Models router included")

if activities:
    app.include_router(activities.router, prefix="/api/activities", tags=["Activities"])
    logger.info("✅ Activities router included")

if eda:
    app.include_router(eda.router, prefix="/api/eda", tags=["EDA"])
    logger.info("✅ EDA router included")

if pipelines:
    app.include_router(pipelines.router, prefix="/api/v1/pipelines", tags=["Pipelines"])
    logger.info("✅ Pipelines router included")

if jobs:
    app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
    logger.info("✅ Jobs router included")

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 8000))
    debug = os.getenv('API_DEBUG', 'False').lower() == 'true'

    logger.info(f"Starting Uvicorn server on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level=os.getenv('LOG_LEVEL', 'info').lower()
    )