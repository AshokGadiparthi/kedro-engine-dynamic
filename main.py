"""
FastAPI Main Application
Complete API with all endpoints
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import all routers
from app.api import (
    auth,
    projects,
    datasets,
    datasources,
    models,
    activities,
    eda,
    pipelines,
    jobs,
    health
)

# Create FastAPI app
app = FastAPI(
    title="ML Platform with EDA",
    description="Complete ML Platform with Exploratory Data Analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets"])
app.include_router(datasources.router, prefix="/api/datasources", tags=["Datasources"])
app.include_router(models.router, prefix="/api/models", tags=["Models"])
app.include_router(activities.router, prefix="/api/activities", tags=["Activities"])
app.include_router(eda.router, prefix="/api/eda", tags=["EDA"])
app.include_router(pipelines.router, prefix="/api/v1/pipelines", tags=["Pipelines"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])

@app.on_event("startup")
async def startup_event():
    logger.info("✅ FastAPI application started")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("⛔ FastAPI application shutdown")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
