from fastapi import Depends

from app.modules.kanban.repository import TaskRepository
from app.modules.kanban.service import TaskService


def get_task_repository() -> TaskRepository:
    return TaskRepository()


def get_task_service(
    repo: TaskRepository = Depends(get_task_repository),
) -> TaskService:
    return TaskService(repo)