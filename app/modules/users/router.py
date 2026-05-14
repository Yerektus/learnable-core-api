from typing import Any

from fastapi import APIRouter, Depends, Query

from app.modules.auth.dependencies import current_active_user, current_admin_user
from app.modules.users.dependencies import get_user_service
from app.modules.users.schemas import PublicUserRead, UserRead, UserUpdate
from app.modules.users.service import UserService

router = APIRouter(tags=["users"])
admin_router = APIRouter(prefix="/admin/users", tags=["admin"])


@router.get("/me", response_model=UserRead, summary="Get current user")
async def get_me(
    user: Any = Depends(current_active_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.get_current_profile(user)


@router.patch("/me", response_model=UserRead, summary="Update current user profile")
async def update_me(
    payload: UserUpdate,
    user: Any = Depends(current_active_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.update_profile(user, payload)


@router.get("/{username}", response_model=PublicUserRead, summary="Get public user profile")
async def get_public_profile(
    username: str,
    service: UserService = Depends(get_user_service),
) -> PublicUserRead:
    return await service.get_profile(username)


@admin_router.get("", response_model=list[UserRead], summary="List all users")
async def list_users(
    _: Any = Depends(current_admin_user),
    service: UserService = Depends(get_user_service),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[UserRead]:
    return await service.get_all_users(skip=skip, limit=limit)
