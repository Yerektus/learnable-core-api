from fastapi import APIRouter, Depends, Query, Response, status

from app.modules.auth.dependencies import current_active_user
from app.modules.graphs.dependencies import get_graph_service

#заменил from app.modules.graphs.schemas import GraphCreate, GraphRead, GraphUpdate
from app.modules.graphs.schemas import (
    GraphCreate,
    GraphNodeCreate,
    GraphNodeRead,
    GraphNodeUpdate,
    GraphRead,
    GraphUpdate,
)

from app.modules.graphs.service import GraphService
from app.modules.users.models import User

router = APIRouter(tags=["graphs"])


@router.post("", response_model=GraphRead, status_code=status.HTTP_201_CREATED, summary="Create graph")
async def create_graph(
    payload: GraphCreate,
    user: User = Depends(current_active_user),
    service: GraphService = Depends(get_graph_service),
) -> GraphRead:
    return await service.create_graph(user, payload)


@router.get("", response_model=list[GraphRead], summary="List current user's graphs")
async def list_graphs(
    user: User = Depends(current_active_user),
    service: GraphService = Depends(get_graph_service),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[GraphRead]:
    return await service.list_graphs(user, skip=skip, limit=limit)


@router.get("/{graph_id}", response_model=GraphRead, summary="Get graph")
async def get_graph(
    graph_id: str,
    user: User = Depends(current_active_user),
    service: GraphService = Depends(get_graph_service),
) -> GraphRead:
    return await service.get_graph(user, graph_id)


@router.patch("/{graph_id}", response_model=GraphRead, summary="Update graph")
async def update_graph(
    graph_id: str,
    payload: GraphUpdate,
    user: User = Depends(current_active_user),
    service: GraphService = Depends(get_graph_service),
) -> GraphRead:
    return await service.update_graph(user, graph_id, payload)


@router.delete("/{graph_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete graph")
async def delete_graph(
    graph_id: str,
    user: User = Depends(current_active_user),
    service: GraphService = Depends(get_graph_service),
) -> Response:
    await service.delete_graph(user, graph_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

#ендпойнты для нод графа
@router.post(
    "/{graph_id}/nodes",
    response_model=GraphNodeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create graph node",
)
async def create_graph_node(
    graph_id: str,
    payload: GraphNodeCreate,
    user: User = Depends(current_active_user),
    service: GraphService = Depends(get_graph_service),
) -> GraphNodeRead:
    return await service.create_node(user, graph_id, payload)


@router.get(
    "/{graph_id}/nodes",
    response_model=list[GraphNodeRead],
    summary="List graph nodes",
)
async def list_graph_nodes(
    graph_id: str,
    user: User = Depends(current_active_user),
    service: GraphService = Depends(get_graph_service),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[GraphNodeRead]:
    return await service.list_nodes(user, graph_id, skip=skip, limit=limit)


@router.get(
    "/{graph_id}/nodes/{node_id}",
    response_model=GraphNodeRead,
    summary="Get graph node",
)
async def get_graph_node(
    graph_id: str,
    node_id: str,
    user: User = Depends(current_active_user),
    service: GraphService = Depends(get_graph_service),
) -> GraphNodeRead:
    return await service.get_node(user, graph_id, node_id)


@router.patch(
    "/{graph_id}/nodes/{node_id}",
    response_model=GraphNodeRead,
    summary="Update graph node",
)
async def update_graph_node(
    graph_id: str,
    node_id: str,
    payload: GraphNodeUpdate,
    user: User = Depends(current_active_user),
    service: GraphService = Depends(get_graph_service),
) -> GraphNodeRead:
    return await service.update_node(user, graph_id, node_id, payload)


@router.delete(
    "/{graph_id}/nodes/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete graph node",
)
async def delete_graph_node(
    graph_id: str,
    node_id: str,
    user: User = Depends(current_active_user),
    service: GraphService = Depends(get_graph_service),
) -> Response:
    await service.delete_node(user, graph_id, node_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
