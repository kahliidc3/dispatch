from fastapi import APIRouter

from apps.api.routers import (
    auth,
    campaigns,
    contacts,
    domains,
    health,
    imports,
    lists,
    segments,
    sender_profiles,
    suppression,
    templates,
    unsubscribe,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(campaigns.router)
api_router.include_router(domains.router)
api_router.include_router(sender_profiles.router)
api_router.include_router(contacts.router)
api_router.include_router(lists.router)
api_router.include_router(imports.router)
api_router.include_router(templates.router)
api_router.include_router(segments.router)
api_router.include_router(suppression.router)
api_router.include_router(unsubscribe.router)
