from typing import Optional

from beanie import PydanticObjectId

from app.modules.kanban.models import Task
from app.modules.kanban.schemas import TaskCreate, TaskUpdate


class TaskRepository:

    async def get_by_id(self, task_id: PydanticObjectId | str) -> Task | None:
        try:
            object_id = PydanticObjectId(task_id)
        except (TypeError, ValueError):
            return None

        return await Task.get(object_id)

    async def get_by_id_and_owner(
        self,
        task_id: PydanticObjectId | str,
        owner_id: PydanticObjectId,
    ) -> Task | None:
        try:
            object_id = PydanticObjectId(task_id)
        except (TypeError, ValueError):
            return None

        return await Task.find_one(
            Task.id == object_id,
            Task.owner_id == owner_id,
        )

    async def get_all_by_owner(
        self,
        owner_id: PydanticObjectId,
        skip: int = 0,
        limit: int = 100,
        graph_id: Optional[str] = None,
    ) -> list[Task]:

        conditions = [Task.owner_id == owner_id]
        if graph_id is not None:
            conditions.append(Task.graph_id == graph_id)

        return (
            await Task.find(*conditions)
            .sort("-created_at")
            .skip(skip)
            .limit(limit)
            .to_list()
        )

    async def create(
        self,
        owner_id: PydanticObjectId,
        data: TaskCreate,
    ) -> Task:

        task = Task(
            owner_id=owner_id,
            **data.model_dump(),
        )

        return await task.insert()

    async def update(
        self,
        task: Task,
        data: TaskUpdate,
    ) -> Task:

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(task, field, value)

        return await task.save()

    async def delete(self, task: Task) -> None:
        await task.delete()