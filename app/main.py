"""
Integration Engine - Main Application
Third-party integration system for the Autonomous Company OS
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
from loguru import logger
import os

from app.config import settings
from app.database import init_db
from app.routers import integrations, webhooks, sync, templates
from app.middleware.tenant import tenant_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Integration Engine...")
    
    # Initialize database
    await init_db()
    
    logger.info("Integration Engine started successfully")
    yield
    
    logger.info("Shutting down Integration Engine...")


# Create FastAPI application
app = FastAPI(
    title="Integration Engine",
    description="Third-party integration system for the Autonomous Company OS",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant middleware for multi-tenancy support
app.middleware("http")(tenant_middleware)

# Include routers
app.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(sync.router, prefix="/sync", tags=["sync"])
app.include_router(templates.router, prefix="/templates", tags=["templates"])


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Integration Engine",
        "version": "1.0.0",
        "status": "operational",
        "description": "Third-party integration system",
        "features": [
            "API integration hub",
            "Webhook management",
            "Data synchronization",
            "Authentication management",
            "Rate limiting",
            "Error handling",
            "Integration templates",
            "Monitoring"
        ],
        "endpoints": {
            "integrations": "/integrations",
            "webhooks": "/webhooks",
            "sync": "/sync",
            "templates": "/templates"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "integration-engine",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8044,
        reload=True
    )
