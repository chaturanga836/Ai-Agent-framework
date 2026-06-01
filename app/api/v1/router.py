from fastapi import APIRouter

from app.api.v1 import health, jobs, workflows

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
