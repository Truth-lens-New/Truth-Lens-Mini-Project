"""
TruthLens Backend API

FastAPI application for misinformation analysis.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.auth.auth import router as auth_router
from app.api.v1.analyze import router as analyze_router
from app.api.v1.history import router as history_router
from app.api.v3.router import router as v3_router  # V3 Phase 1


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: Initialize database
    await init_db()
    print("Database initialized")
    
    yield
    
    # Shutdown: Cleanup if needed
    print("Application shutting down")


# Create FastAPI application
app = FastAPI(
    title="TruthLens API",
    description="Misinformation analysis and claim verification API",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(analyze_router)
app.include_router(history_router)
app.include_router(v3_router)  # V3 Phase 1 routes


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "name": "TruthLens API",
        "version": "0.1.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
