from app.modules.ai.graph.client import get_graph

def init_falkordb_schema():
    """Run once at startup to create indexes."""
    g = get_graph()

    # Vector indexes for semantic search
    try:
        g.query("CREATE VECTOR INDEX FOR (n:Node) ON (n.embedding) OPTIONS {dimension: 1024, similarityFunction: 'cosine'}")
    except Exception:
        pass
    try:
        g.query("CREATE VECTOR INDEX FOR (e:Error) ON (e.embedding) OPTIONS {dimension: 1024, similarityFunction: 'cosine'}")
    except Exception:
        pass
    try:
        g.query("CREATE INDEX FOR (u:User) ON (u.id)")
    except Exception:
        pass
    try:
        g.query("CREATE INDEX FOR (n:Node) ON (n.id)")
    except Exception:
        pass
    try:
        g.query("CREATE INDEX FOR (d:Deadline) ON (d.id)")
    except Exception:
        pass
