from fastapi import APIRouter

from app.api.v1 import (
    auth,
    bom,
    bom_imports,
    documents,
    eco,
    eco_records,
    graph,
    health,
    intelligence,
    jobs,
    reports,
    uploads,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(health.router, tags=["health"])
api_router.include_router(uploads.router)
api_router.include_router(bom.router)
api_router.include_router(bom_imports.router)
api_router.include_router(documents.router)
api_router.include_router(graph.router)
api_router.include_router(eco.router)
api_router.include_router(eco_records.router)
api_router.include_router(intelligence.router)
api_router.include_router(reports.router)
api_router.include_router(jobs.router)
