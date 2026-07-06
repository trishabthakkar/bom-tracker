from fastapi import APIRouter

from app.api.v1 import auth, bom, health, uploads

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(health.router, tags=["health"])
api_router.include_router(uploads.router)
api_router.include_router(bom.router)
