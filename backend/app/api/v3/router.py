"""
TruthLens V3 API Router

Routes for the Phase 1+ claim analysis pipeline.
"""

from fastapi import APIRouter
from .endpoints.analyze import router as analyze_router

router = APIRouter(prefix="/api/v3", tags=["v3"])
router.include_router(analyze_router)
