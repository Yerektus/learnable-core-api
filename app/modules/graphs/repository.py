from beanie import PydanticObjectId

from app.modules.graphs.models import Graph, GraphNode
from app.modules.graphs.schemas import GraphCreate, GraphNodeCreate, GraphNodeUpdate, GraphUpdate


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
    
    
    async def get_node_by_id_and_graph(
        self,
        node_id: PydanticObjectId | str,
        graph_id: PydanticObjectId | str,
        owner_id: PydanticObjectId,
    ) -> GraphNode | None:
        try:
            node_object_id = PydanticObjectId(node_id)
            graph_object_id = PydanticObjectId(graph_id)
        except (TypeError, ValueError):
            return None

        return await GraphNode.find_one(
            GraphNode.id == node_object_id,
            GraphNode.graph_id == graph_object_id,
            GraphNode.owner_id == owner_id,
        )

    async def get_nodes_by_graph(
        self,
        graph_id: PydanticObjectId | str,
        owner_id: PydanticObjectId,
        skip: int = 0,
        limit: int = 100,
    ) -> list[GraphNode]:
        try:
            graph_object_id = PydanticObjectId(graph_id)
        except (TypeError, ValueError):
            return []

        return (
            await GraphNode.find(
                GraphNode.graph_id == graph_object_id,
                GraphNode.owner_id == owner_id,
            )
            .sort("-created_at")
            .skip(skip)
            .limit(limit)
            .to_list()
        )

    async def create_node(
        self,
        graph_id: PydanticObjectId | str,
        owner_id: PydanticObjectId,
        data: GraphNodeCreate,
    ) -> GraphNode:
        graph_object_id = PydanticObjectId(graph_id)

        node = GraphNode(
            graph_id=graph_object_id,
            owner_id=owner_id,
            **data.model_dump(),
        )

        return await node.insert()

    async def update_node(
        self,
        node: GraphNode,
        data: GraphNodeUpdate,
    ) -> GraphNode:
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(node, field, value)

        return await node.save()

    async def delete_node(self, node: GraphNode) -> None:
        await node.delete()
