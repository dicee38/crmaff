from fastapi import APIRouter

from app.api.v1 import (
    actions,
    auth,
    dashboard,
    leaderboard,
    leads,
    redirect,
    reference,
    reports,
    tasks,
    track,
    webhooks,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(leads.router)
api_router.include_router(track.router)
api_router.include_router(webhooks.router)
api_router.include_router(redirect.router)
api_router.include_router(tasks.router)
api_router.include_router(actions.router)
api_router.include_router(dashboard.router)
api_router.include_router(reports.router)
api_router.include_router(leaderboard.router)
api_router.include_router(reference.router)
