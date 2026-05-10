from beanie import PydanticObjectId

from app.modules.materials.models import NodeMaterial


class MaterialRepository:

    async def list_by_node(
        self,
        owner_id: PydanticObjectId,
        node_id: PydanticObjectId,
    ) -> list[NodeMaterial]:
        return (
            await NodeMaterial.find(
                NodeMaterial.owner_id == owner_id,
                NodeMaterial.node_id == node_id,
            )
            .sort("-created_at")
            .to_list()
        )

    async def get_by_id_and_owner(
        self,
        material_id: PydanticObjectId | str,
        owner_id: PydanticObjectId,
        node_id: PydanticObjectId,
    ) -> NodeMaterial | None:
        try:
            oid = PydanticObjectId(material_id)
        except (TypeError, ValueError):
            return None
        return await NodeMaterial.find_one(
            NodeMaterial.id == oid,
            NodeMaterial.owner_id == owner_id,
            NodeMaterial.node_id == node_id,
        )

    async def create(
        self,
        owner_id: PydanticObjectId,
        node_id: PydanticObjectId,
        material_type: str,
        title: str,
        content: str = "",
        cards: list[dict[str, str]] | None = None,
    ) -> NodeMaterial:
        material = NodeMaterial(
            owner_id=owner_id,
            node_id=node_id,
            type=material_type,
            title=title,
            content=content,
            cards=cards or [],
        )
        return await material.insert()

    async def delete(self, material: NodeMaterial) -> None:
        await material.delete()
