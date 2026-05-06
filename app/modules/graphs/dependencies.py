from fastapi import Depends

from app.modules.graphs.repository import GraphRepository
from app.modules.graphs.service import GraphService


def get_graph_repository() -> GraphRepository:
    return GraphRepository()


def get_graph_service(
    repo: GraphRepository = Depends(get_graph_repository),
) -> GraphService:
    return GraphService(repo)
