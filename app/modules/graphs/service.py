from fastapi import HTTPException, status

from app.modules.graphs.repository import GraphRepository
#from app.modules.graphs.schemas import GraphCreate, GraphRead, GraphUpdate
from app.modules.graphs.schemas import (
    GraphCreate,
    GraphNodeCreate,
    GraphNodeRead,
    GraphNodeUpdate,
    GraphRead,
    GraphUpdate,
)
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

    # вот тут логика нодов
    async def create_node(
        self,
        user: User,
        graph_id: str,
        data: GraphNodeCreate,
    ) -> GraphNodeRead:

        graph = await self.repo.get_by_id_and_owner(
            graph_id,
            user.id,
        )

        if graph is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Graph not found",
            )

        node = await self.repo.create_node(
            graph_id,
            user.id,
            data,
        )

        return GraphNodeRead.model_validate(node)

    async def list_nodes(
        self,
        user: User,
        graph_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[GraphNodeRead]:

        graph = await self.repo.get_by_id_and_owner(
            graph_id,
            user.id,
        )

        if graph is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Graph not found",
            )

        nodes = await self.repo.get_nodes_by_graph(
            graph_id,
            user.id,
            skip=skip,
            limit=limit,
        )

        return [
            GraphNodeRead.model_validate(node)
            for node in nodes
        ]

    async def get_node(
        self,
        user: User,
        graph_id: str,
        node_id: str,
    ) -> GraphNodeRead:

        node = await self.repo.get_node_by_id_and_graph(
            node_id,
            graph_id,
            user.id,
        )

        if node is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found",
            )

        return GraphNodeRead.model_validate(node)

    async def update_node(
        self,
        user: User,
        graph_id: str,
        node_id: str,
        data: GraphNodeUpdate,
    ) -> GraphNodeRead:

        node = await self.repo.get_node_by_id_and_graph(
            node_id,
            graph_id,
            user.id,
        )

        if node is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found",
            )

        updated_node = await self.repo.update_node(
            node,
            data,
        )

        return GraphNodeRead.model_validate(updated_node)

    async def delete_node(
        self,
        user: User,
        graph_id: str,
        node_id: str,
    ) -> None:

        node = await self.repo.get_node_by_id_and_graph(
            node_id,
            graph_id,
            user.id,
        )

        if node is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found",
            )

        await self.repo.delete_node(node)
