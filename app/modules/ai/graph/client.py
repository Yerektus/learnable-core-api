from falkordb import FalkorDB
from app.config import get_settings

_client: FalkorDB | None = None
_graph = None

def get_falkor_client() -> FalkorDB:
    global _client
    if _client is None:
        settings = get_settings()
        _client = FalkorDB.from_url(settings.redis_url)
    return _client

def get_graph():
    global _graph
    if _graph is None:
        _graph = get_falkor_client().select_graph("learnable")
    return _graph
# force rebuild