"""
Shortlist — API v1 Router

Aggregates all v1 endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.jd import router as jd_router
from app.api.v1.capstone import router as capstone_router
from app.api.v1.repo import router as repo_router
from app.api.v1.scaffold import router as scaffold_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.fitness import router as fitness_router

router = APIRouter()

router.include_router(jd_router, prefix="/jd", tags=["JD Analysis"])
router.include_router(capstone_router, prefix="/capstone", tags=["Capstone Generator"])
router.include_router(repo_router, prefix="/repo", tags=["Repo Analyzer"])
router.include_router(scaffold_router, prefix="/scaffold", tags=["Scaffold Generator"])
router.include_router(portfolio_router, prefix="/portfolio", tags=["Portfolio Optimizer"])
router.include_router(fitness_router, prefix="/fitness", tags=["Resume Fitness Scorer"])
