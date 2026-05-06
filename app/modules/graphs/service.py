from fastapi import HTTPException, status

from app.modules.graphs.repository import GraphRepository
from app.modules.graphs.schemas import GraphCreate, GraphRead, GraphUpdate
from app.modules.users.models import User


class GraphService:

    def __init__(self, repo: GraphRepository):
        self.repo = repo

    async def create_graph(self, user: User, data: GraphCreate) -> GraphRead:
        graph = await self.repo.create(user.id, data)
        return GraphRead.model_validate(graph)

    async def list_graphs(self, user: User, skip: int = 0, limit: int = 100) -> list[GraphRead]:
        graphs = await self.repo.get_all_by_owner(user.id, skip=skip, limit=limit)
        return [GraphRead.model_validate(graph) for graph in graphs]

    async def get_graph(self, user: User, graph_id: str) -> GraphRead:
        graph = await self.repo.get_by_id_and_owner(graph_id, user.id)
        if graph is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph not found")
        return GraphRead.model_validate(graph)

    async def update_graph(self, user: User, graph_id: str, data: GraphUpdate) -> GraphRead:
        graph = await self.repo.get_by_id_and_owner(graph_id, user.id)
        if graph is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph not found")
        updated_graph = await self.repo.update(graph, data)
        return GraphRead.model_validate(updated_graph)

    async def delete_graph(self, user: User, graph_id: str) -> None:
        graph = await self.repo.get_by_id_and_owner(graph_id, user.id)
        if graph is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph not found")
        await self.repo.delete(graph)
