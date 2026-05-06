from fastapi import HTTPException, status

from app.modules.kanban.repository import TaskRepository
from app.modules.kanban.schemas import TaskCreate, TaskRead, TaskUpdate
from app.modules.users.models import User


class TaskService:

    def __init__(self, repo: TaskRepository):
        self.repo = repo

    async def create_task(
        self,
        user: User,
        data: TaskCreate,
    ) -> TaskRead:

        task = await self.repo.create(user.id, data)

        return TaskRead.model_validate(task)

    async def list_tasks(
        self,
        user: User,
        skip: int = 0,
        limit: int = 100,
    ) -> list[TaskRead]:

        tasks = await self.repo.get_all_by_owner(
            user.id,
            skip=skip,
            limit=limit,
        )

        return [
            TaskRead.model_validate(task)
            for task in tasks
        ]

    async def get_task(
        self,
        user: User,
        task_id: str,
    ) -> TaskRead:

        task = await self.repo.get_by_id_and_owner(
            task_id,
            user.id,
        )

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return TaskRead.model_validate(task)

    async def update_task(
        self,
        user: User,
        task_id: str,
        data: TaskUpdate,
    ) -> TaskRead:

        task = await self.repo.get_by_id_and_owner(
            task_id,
            user.id,
        )

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        updated_task = await self.repo.update(task, data)

        return TaskRead.model_validate(updated_task)

    async def delete_task(
        self,
        user: User,
        task_id: str,
    ) -> None:

        task = await self.repo.get_by_id_and_owner(
            task_id,
            user.id,
        )

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        await self.repo.delete(task)