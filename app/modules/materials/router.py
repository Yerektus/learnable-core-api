from fastapi import APIRouter, Depends, HTTPException, Response, status
from beanie import PydanticObjectId

from app.modules.auth.dependencies import current_active_user
from app.modules.materials.repository import MaterialRepository
from app.modules.materials.schemas import MaterialDetail, MaterialListItem
from app.modules.users.models import User

router = APIRouter(tags=["materials"])

_repo = MaterialRepository()


def _parse_oid(value: str, field: str) -> PydanticObjectId:
    try:
        return PydanticObjectId(value)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid {field}",
        )


@router.get("/nodes/{node_id}/materials", response_model=list[MaterialListItem])
async def list_materials(
    node_id: str,
    user: User = Depends(current_active_user),
) -> list[MaterialListItem]:
    node_oid = _parse_oid(node_id, "node_id")
    materials = await _repo.list_by_node(user.id, node_oid)
    return [MaterialListItem.model_validate(m) for m in materials]


@router.get("/nodes/{node_id}/materials/{material_id}", response_model=MaterialDetail)
async def get_material(
    node_id: str,
    material_id: str,
    user: User = Depends(current_active_user),
) -> MaterialDetail:
    node_oid = _parse_oid(node_id, "node_id")
    material = await _repo.get_by_id_and_owner(material_id, user.id, node_oid)
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    return MaterialDetail.model_validate(material)


@router.delete(
    "/nodes/{node_id}/materials/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_material(
    node_id: str,
    material_id: str,
    user: User = Depends(current_active_user),
) -> Response:
    node_oid = _parse_oid(node_id, "node_id")
    material = await _repo.get_by_id_and_owner(material_id, user.id, node_oid)
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    await _repo.delete(material)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
