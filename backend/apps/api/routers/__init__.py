from fastapi import APIRouter

from apps.api.routers import auth, contacts, domains, health, imports, lists, sender_profiles, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(domains.router)
api_router.include_router(sender_profiles.router)
api_router.include_router(contacts.router)
api_router.include_router(lists.router)
api_router.include_router(imports.router)
