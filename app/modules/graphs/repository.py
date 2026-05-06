from beanie import PydanticObjectId

from app.modules.graphs.models import Graph
from app.modules.graphs.schemas import GraphCreate, GraphUpdate


class GraphRepository:

    async def get_by_id(self, graph_id: PydanticObjectId | str) -> Graph | None:
        try:
            object_id = PydanticObjectId(graph_id)
        except (TypeError, ValueError):
            return None
        return await Graph.get(object_id)

    async def get_by_id_and_owner(
        self,
        graph_id: PydanticObjectId | str,
        owner_id: PydanticObjectId,
    ) -> Graph | None:
        try:
            object_id = PydanticObjectId(graph_id)
        except (TypeError, ValueError):
            return None
        return await Graph.find_one(Graph.id == object_id, Graph.owner_id == owner_id)

    async def get_all_by_owner(
        self,
        owner_id: PydanticObjectId,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Graph]:
        return (
            await Graph.find(Graph.owner_id == owner_id)
            .sort("-created_at")
            .skip(skip)
            .limit(limit)
            .to_list()
        )

    async def create(self, owner_id: PydanticObjectId, data: GraphCreate) -> Graph:
        graph = Graph(owner_id=owner_id, **data.model_dump())
        return await graph.insert()

    async def update(self, graph: Graph, data: GraphUpdate) -> Graph:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(graph, field, value)
        return await graph.save()

    async def delete(self, graph: Graph) -> None:
        await graph.delete()
