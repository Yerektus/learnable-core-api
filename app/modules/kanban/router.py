from fastapi import APIRouter, Depends, Query, Response, status

from app.modules.auth.dependencies import current_active_user
from app.modules.kanban.dependencies import get_task_service
from app.modules.kanban.schemas import TaskCreate, TaskRead, TaskUpdate
from app.modules.kanban.service import TaskService
from app.modules.users.models import User

router = APIRouter(tags=["kanban"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED, summary="Create task")
async def create_task(
    payload: TaskCreate,
    user: User = Depends(current_active_user),
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    return await service.create_task(user, payload)


@router.get("", response_model=list[TaskRead], summary="List current user's tasks")
async def list_tasks(
    user: User = Depends(current_active_user),
    service: TaskService = Depends(get_task_service),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[TaskRead]:
    return await service.list_tasks(user, skip=skip, limit=limit)


@router.get("/{task_id}", response_model=TaskRead, summary="Get task")
async def get_task(
    task_id: str,
    user: User = Depends(current_active_user),
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    return await service.get_task(user, task_id)


@router.patch("/{task_id}", response_model=TaskRead, summary="Update task")
async def update_task(
    task_id: str,
    payload: TaskUpdate,
    user: User = Depends(current_active_user),
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    return await service.update_task(user, task_id, payload)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete task")
async def delete_task(
    task_id: str,
    user: User = Depends(current_active_user),
    service: TaskService = Depends(get_task_service),
) -> Response:
    await service.delete_task(user, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)