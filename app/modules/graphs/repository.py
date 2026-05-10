from beanie import PydanticObjectId

from app.modules.graphs.models import Graph, GraphEdge, GraphNode, NodeMaterial
from app.modules.graphs.schemas import (
    GraphCreate,
    GraphEdgeCreate,
    GraphNodeCreate,
    GraphNodeUpdate,
    GraphUpdate,
    NodeMaterialCreate,
)


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
        await NodeMaterial.find(NodeMaterial.graph_id == graph.id).delete()
        await GraphEdge.find(GraphEdge.graph_id == graph.id).delete()
        await GraphNode.find(GraphNode.graph_id == graph.id).delete()
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
        await NodeMaterial.find(NodeMaterial.node_id == node.id).delete()
        await GraphEdge.find(
            GraphEdge.graph_id == node.graph_id,
            GraphEdge.source_node_id == node.id,
        ).delete()
        await GraphEdge.find(
            GraphEdge.graph_id == node.graph_id,
            GraphEdge.target_node_id == node.id,
        ).delete()
        await node.delete()

    async def get_edges_by_graph(
        self,
        graph_id: PydanticObjectId | str,
        owner_id: PydanticObjectId,
        skip: int = 0,
        limit: int = 100,
    ) -> list[GraphEdge]:
        try:
            graph_object_id = PydanticObjectId(graph_id)
        except (TypeError, ValueError):
            return []

        return (
            await GraphEdge.find(
                GraphEdge.graph_id == graph_object_id,
                GraphEdge.owner_id == owner_id,
            )
            .sort("created_at")
            .skip(skip)
            .limit(limit)
            .to_list()
        )

    async def create_edge(
        self,
        graph_id: PydanticObjectId | str,
        owner_id: PydanticObjectId,
        data: GraphEdgeCreate,
    ) -> GraphEdge:
        graph_object_id = PydanticObjectId(graph_id)

        existing_edge = await GraphEdge.find_one(
            GraphEdge.graph_id == graph_object_id,
            GraphEdge.owner_id == owner_id,
            GraphEdge.source_node_id == data.source_node_id,
            GraphEdge.target_node_id == data.target_node_id,
        )

        if existing_edge is not None:
            return existing_edge

        edge = GraphEdge(
            graph_id=graph_object_id,
            owner_id=owner_id,
            source_node_id=data.source_node_id,
            target_node_id=data.target_node_id,
        )

        return await edge.insert()

    async def get_edge_by_id_and_graph(
        self,
        edge_id: PydanticObjectId | str,
        graph_id: PydanticObjectId | str,
        owner_id: PydanticObjectId,
    ) -> GraphEdge | None:
        try:
            edge_object_id = PydanticObjectId(edge_id)
            graph_object_id = PydanticObjectId(graph_id)
        except (TypeError, ValueError):
            return None

        return await GraphEdge.find_one(
            GraphEdge.id == edge_object_id,
            GraphEdge.graph_id == graph_object_id,
            GraphEdge.owner_id == owner_id,
        )

    async def delete_edge(self, edge: GraphEdge) -> None:
        await edge.delete()

    async def get_materials_by_node(
        self,
        graph_id: PydanticObjectId | str,
        node_id: PydanticObjectId | str,
        owner_id: PydanticObjectId,
    ) -> list[NodeMaterial]:
        try:
            graph_object_id = PydanticObjectId(graph_id)
            node_object_id = PydanticObjectId(node_id)
        except (TypeError, ValueError):
            return []
        return (
            await NodeMaterial.find(
                NodeMaterial.graph_id == graph_object_id,
                NodeMaterial.node_id == node_object_id,
                NodeMaterial.owner_id == owner_id,
            )
            .sort("-created_at")
            .to_list()
        )

    async def create_material(
        self,
        graph_id: PydanticObjectId | str,
        node_id: PydanticObjectId | str,
        owner_id: PydanticObjectId,
        data: NodeMaterialCreate,
    ) -> NodeMaterial:
        material = NodeMaterial(
            graph_id=PydanticObjectId(graph_id),
            node_id=PydanticObjectId(node_id),
            owner_id=owner_id,
            **data.model_dump(),
        )
        return await material.insert()

    async def get_material_by_id(
        self,
        graph_id: PydanticObjectId | str,
        node_id: PydanticObjectId | str,
        material_id: PydanticObjectId | str,
        owner_id: PydanticObjectId,
    ) -> NodeMaterial | None:
        try:
            graph_object_id = PydanticObjectId(graph_id)
            node_object_id = PydanticObjectId(node_id)
            material_object_id = PydanticObjectId(material_id)
        except (TypeError, ValueError):
            return None
        return await NodeMaterial.find_one(
            NodeMaterial.id == material_object_id,
            NodeMaterial.graph_id == graph_object_id,
            NodeMaterial.node_id == node_object_id,
            NodeMaterial.owner_id == owner_id,
        )

    async def delete_material(self, material: NodeMaterial) -> None:
        await material.delete()