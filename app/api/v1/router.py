from fastapi import APIRouter

from app.api.v1 import auth, leads, redirect, track, webhooks

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(leads.router)
api_router.include_router(track.router)
api_router.include_router(webhooks.router)
api_router.include_router(redirect.router)
