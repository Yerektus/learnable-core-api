import asyncio

from fastapi import APIRouter, Depends, Query, Response, status

from app.modules.auth.dependencies import current_active_user
from app.modules.graphs.dependencies import get_graph_service

#заменил from app.modules.graphs.schemas import GraphCreate, GraphRead, GraphUpdate
from app.modules.graphs.schemas import (
    GraphCreate,
    GraphEdgeCreate,
    GraphEdgeRead,
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
    try:
        from app.modules.ai.graph import queries as gq
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, gq.delete_graph, graph_id)
    except Exception:
        pass
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
    from app.modules.ai.graph import queries as gq
    from app.modules.ai.graph.embeddings import embed
    node = await service.create_node(user, graph_id, payload)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, gq.ensure_graph_node, graph_id, str(user.id))
    node_emb = await loop.run_in_executor(None, embed, f"{payload.title} {payload.description or ''}")
    await loop.run_in_executor(None, gq.create_node, str(node.id), graph_id, payload.title, payload.description or "", node_emb)
    return node


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
    from app.modules.ai.graph import queries as gq
    from app.modules.ai.graph.embeddings import embed
    node = await service.update_node(user, graph_id, node_id, payload)
    if payload.title is not None or payload.description is not None:
        loop = asyncio.get_running_loop()
        node_emb = await loop.run_in_executor(None, embed, f"{node.title} {node.description or ''}")
        await loop.run_in_executor(None, gq.update_node_embedding, node_id, node.title, node.description or "", node_emb)
    return node


@router.get(
    "/{graph_id}/deadlines",
    summary="List deadlines for a graph",
)
async def list_graph_deadlines(
    graph_id: str,
    user: User = Depends(current_active_user),
    service: GraphService = Depends(get_graph_service),
) -> list[dict]:
    await service.get_graph(user, graph_id)  # ownership check
    from app.modules.ai.graph import queries as gq
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, gq.get_graph_deadlines, graph_id, str(user.id))


@router.get(
    "/{graph_id}/nodes/{node_id}/deadlines",
    summary="List deadlines covering a specific node",
)
async def list_node_deadlines(
    graph_id: str,
    node_id: str,
    user: User = Depends(current_active_user),
    service: GraphService = Depends(get_graph_service),
) -> list[dict]:
    await service.get_node(user, graph_id, node_id)  # ownership check
    from app.modules.ai.graph import queries as gq
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, gq.get_node_deadlines, node_id, str(user.id))


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
    try:
        from app.modules.ai.graph import queries as gq
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, gq.delete_node, node_id)
    except Exception:
        pass
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{graph_id}/edges",
    response_model=GraphEdgeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create graph edge",
)
async def create_graph_edge(
    graph_id: str,
    payload: GraphEdgeCreate,
    user: User = Depends(current_active_user),
    service: GraphService = Depends(get_graph_service),
) -> GraphEdgeRead:
    return await service.create_edge(user, graph_id, payload)


@router.get(
    "/{graph_id}/edges",
    response_model=list[GraphEdgeRead],
    summary="List graph edges",
)
async def list_graph_edges(
    graph_id: str,
    user: User = Depends(current_active_user),
    service: GraphService = Depends(get_graph_service),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[GraphEdgeRead]:
    return await service.list_edges(user, graph_id, skip=skip, limit=limit)


@router.delete(
    "/{graph_id}/edges/{edge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete graph edge",
)
async def delete_graph_edge(
    graph_id: str,
    edge_id: str,
    user: User = Depends(current_active_user),
    service: GraphService = Depends(get_graph_service),
) -> Response:
    await service.delete_edge(user, graph_id, edge_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
