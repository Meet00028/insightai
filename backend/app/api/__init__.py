"""
# Architect: Meet Kumar
# InsightAI - API Package
"""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.datasets import router as datasets_router
from app.api.analysis import router as analysis_router
from app.api.pipelines import router as pipelines_router
from app.api.dashboard import router as dashboard_router
from app.api.analyze_data import router as analyze_data_router
from app.api.chat import router as chat_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(datasets_router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(pipelines_router, prefix="/pipelines", tags=["Pipelines"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(chat_router, tags=["Chat"])
api_router.include_router(analyze_data_router, tags=["Analyze Data"])
