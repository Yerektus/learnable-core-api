import asyncio
import json
from datetime import datetime, UTC
from typing import Optional
from app.modules.ai.graph.client import get_graph

def ensure_user_node(user_id: str):
    g = get_graph()
    g.query("MERGE (:User {id: $uid})", {"uid": user_id})

def create_graph_node(graph_id: str, user_id: str, name: str):
    """Sync MongoDB Graph with FalkorDB."""
    g = get_graph()
    g.query(
        "MERGE (u:User {id: $uid}) "
        "MERGE (gr:Graph {id: $gid}) ON CREATE SET gr.name = $name "
        "MERGE (u)-[:OWNS]->(gr)",
        {"uid": user_id, "gid": graph_id, "name": name}
    )

def create_node(node_id: str, graph_id: str, title: str, description: str, embedding: list[float]):
    g = get_graph()
    g.query(
        "MERGE (gr:Graph {id: $gid}) "
        "MERGE (n:Node {id: $nid}) "
        "SET n.title = $title, n.description = $desc, n.embedding = vecf32($emb) "
        "MERGE (gr)-[:HAS_NODE]->(n)",
        {"gid": graph_id, "nid": node_id, "title": title, "desc": description, "emb": embedding}
    )

def ensure_graph_node(graph_id: str, user_id: str):
    """Ensure Graph and User nodes exist in FalkorDB without requiring a name."""
    g = get_graph()
    g.query(
        "MERGE (u:User {id: $uid}) "
        "MERGE (gr:Graph {id: $gid}) "
        "MERGE (u)-[:OWNS]->(gr)",
        {"uid": user_id, "gid": graph_id}
    )

def update_node_embedding(node_id: str, title: str, description: str, embedding: list[float]):
    """Update title, description and embedding of an existing FalkorDB node."""
    g = get_graph()
    g.query(
        "MATCH (n:Node {id: $nid}) "
        "SET n.title = $title, n.description = $desc, n.embedding = vecf32($emb)",
        {"nid": node_id, "title": title, "desc": description, "emb": embedding}
    )

def create_precedes(from_node_id: str, to_node_id: str):
    g = get_graph()
    g.query(
        "MATCH (a:Node {id: $aid}), (b:Node {id: $bid}) MERGE (a)-[:PRECEDES]->(b)",
        {"aid": from_node_id, "bid": to_node_id}
    )

def create_deadline(deadline_id: str, graph_id: str, title: str, date: str, type: str = "assignment"):
    g = get_graph()
    g.query(
        "MATCH (gr:Graph {id: $gid}) "
        "MERGE (d:Deadline {id: $did}) "
        "SET d.title = $title, d.date = $date, d.type = $type "
        "MERGE (gr)-[:HAS_DEADLINE]->(d)",
        {"gid": graph_id, "did": deadline_id, "title": title, "date": date, "type": type}
    )

def link_deadline_to_node(deadline_id: str, node_id: str):
    g = get_graph()
    g.query(
        "MATCH (d:Deadline {id: $did}), (n:Node {id: $nid}) MERGE (d)-[:COVERS]->(n)",
        {"did": deadline_id, "nid": node_id}
    )

def get_node_context(user_id: str, node_id: str) -> dict:
    """Get node info + upcoming deadlines covering this node."""
    g = get_graph()
    result = g.query(
        "MATCH (n:Node {id: $nid}) "
        "OPTIONAL MATCH (d:Deadline)-[:COVERS]->(n) "
        "WHERE d.date IS NOT NULL AND d.date >= $today "
        "RETURN n.title, n.description, collect({id: d.id, title: d.title, date: d.date}) as deadlines",
        {"nid": node_id, "today": datetime.now(UTC).strftime("%Y-%m-%d")}
    )
    if not result.result_set:
        return {}
    row = result.result_set[0]
    return {
        "node_title": row[0],
        "node_description": row[1],
        "upcoming_deadlines": [d for d in row[2] if d.get("id")]
    }

def search_similar_errors(question_embedding: list[float], user_id: str, node_id: str, threshold: float = 0.82) -> list[str]:
    """Find errors similar to current question using vector search."""
    try:
        g = get_graph()
        max_dist = 1.0 - threshold
        result = g.query(
            "CALL db.idx.vector.queryNodes('Error', 'embedding', 10, $emb) YIELD node AS e, score "
            "WHERE score <= $max_dist "
            "WITH e, score "
            "MATCH (u:User {id: $uid})-[:MADE_ERROR]->(e)-[:IN_NODE]->(n:Node {id: $nid}) "
            "RETURN e.description ORDER BY score ASC LIMIT 5",
            {"uid": user_id, "nid": node_id, "emb": question_embedding, "max_dist": max_dist}
        )
        return [row[0] for row in result.result_set]
    except Exception:
        return []

def record_error(error_id: str, user_id: str, node_id: str, description: str,
                 embedding: list[float], source: str = "chat"):
    """Synchronously record an error."""
    g = get_graph()
    g.query(
        "MATCH (u:User {id: $uid}), (n:Node {id: $nid}) "
        "CREATE (e:Error {id: $eid, description: $desc, embedding: vecf32($emb), "
        "source: $source, created_at: $ts}) "
        "CREATE (u)-[:MADE_ERROR]->(e) "
        "CREATE (e)-[:IN_NODE]->(n)",
        {"uid": user_id, "nid": node_id, "eid": error_id,
         "desc": description, "emb": embedding,
         "source": source, "ts": datetime.now(UTC).isoformat()}
    )

def find_and_link_similar_errors(error_id: str, threshold: float = 0.85):
    """Async background task — find similar errors and create SIMILAR_TO edges."""
    g = get_graph()
    result = g.query(
        "MATCH (e:Error {id: $eid}) RETURN e.embedding", {"eid": error_id}
    )
    if not result.result_set:
        return
    emb = result.result_set[0][0]
    max_dist = 1.0 - threshold
    similar = g.query(
        "CALL db.idx.vector.queryNodes('Error', 'embedding', 20, vecf32($emb)) YIELD node AS other, score "
        "WHERE score <= $max_dist AND other.id <> $eid "
        "RETURN other.id",
        {"eid": error_id, "emb": emb, "max_dist": max_dist}
    )
    for row in similar.result_set:
        g.query(
            "MATCH (a:Error {id: $aid}), (b:Error {id: $bid}) MERGE (a)-[:SIMILAR_TO]->(b)",
            {"aid": error_id, "bid": row[0]}
        )

def get_deadline_prep_context(user_id: str, deadline_id: str) -> dict:
    """Get all errors across all nodes covered by deadline — for prep mode."""
    g = get_graph()
    result = g.query(
        "MATCH (d:Deadline {id: $did})-[:COVERS]->(n:Node) "
        "OPTIONAL MATCH (u:User {id: $uid})-[:MADE_ERROR]->(e:Error)-[:IN_NODE]->(n) "
        "RETURN d.title, d.date, n.title, collect(e.description) as errors",
        {"did": deadline_id, "uid": user_id}
    )
    nodes_data = []
    deadline_title = ""
    deadline_date = ""
    for row in result.result_set:
        deadline_title = row[0]
        deadline_date = row[1]
        nodes_data.append({"node": row[2], "errors": row[3]})
    return {
        "deadline_title": deadline_title,
        "deadline_date": deadline_date,
        "nodes": nodes_data
    }

def get_graph_deadlines(graph_id: str, user_id: str) -> list[dict]:
    """Return all deadlines for a graph. Ownership verified via User→OWNS→Graph chain."""
    g = get_graph()
    result = g.query(
        "MATCH (:User {id: $uid})-[:OWNS]->(gr:Graph {id: $gid})-[:HAS_DEADLINE]->(d:Deadline) "
        "OPTIONAL MATCH (d)-[:COVERS]->(n:Node) "
        "RETURN d.id, d.title, d.date, d.type, collect(n.id) as node_ids",
        {"uid": user_id, "gid": graph_id}
    )
    return [
        {"id": row[0], "title": row[1], "date": row[2], "type": row[3] or "assignment", "node_ids": row[4]}
        for row in result.result_set
    ]

def get_node_deadlines(node_id: str, user_id: str) -> list[dict]:
    """Return all deadlines covering a specific node. Ownership verified via User→OWNS→Graph→HAS_NODE→Node chain."""
    g = get_graph()
    result = g.query(
        "MATCH (:User {id: $uid})-[:OWNS]->(:Graph)-[:HAS_NODE]->(n:Node {id: $nid})"
        "<-[:COVERS]-(d:Deadline) "
        "RETURN d.id, d.title, d.date, d.type",
        {"uid": user_id, "nid": node_id}
    )
    return [
        {"id": row[0], "title": row[1], "date": row[2], "type": row[3] or "assignment"}
        for row in result.result_set
    ]

def snapshot_graph_state(graph_id: str) -> dict:
    """Serialize full graph state for rollback."""
    g = get_graph()
    nodes = g.query(
        "MATCH (gr:Graph {id: $gid})-[:HAS_NODE]->(n:Node) "
        "RETURN n.id, n.title, n.description",
        {"gid": graph_id},
    )
    edges = g.query("MATCH (gr:Graph {id: $gid})-[:HAS_NODE]->(a:Node)-[:PRECEDES]->(b:Node) RETURN a.id, b.id", {"gid": graph_id})
    deadlines = g.query("MATCH (gr:Graph {id: $gid})-[:HAS_DEADLINE]->(d:Deadline) RETURN d.id, d.title, d.date, d.type", {"gid": graph_id})
    covers = g.query("MATCH (gr:Graph {id: $gid})-[:HAS_DEADLINE]->(d:Deadline)-[:COVERS]->(n:Node) RETURN d.id, n.id", {"gid": graph_id})
    return {
        "nodes": [{"id": r[0], "title": r[1], "description": r[2]} for r in nodes.result_set],
        "edges": [{"from": r[0], "to": r[1]} for r in edges.result_set],
        "deadlines": [{"id": r[0], "title": r[1], "date": r[2], "type": r[3] or "assignment"} for r in deadlines.result_set],
        "covers": [{"deadline_id": r[0], "node_id": r[1]} for r in covers.result_set],
    }

def restore_graph_state(graph_id: str, snapshot: dict):
    """Delete current graph nodes and restore from snapshot, preserving embeddings."""
    g = get_graph()
    # Guard: ensure Graph node exists so all subsequent MATCHes succeed
    g.query("MERGE (:Graph {id: $gid})", {"gid": graph_id})
    g.query("MATCH (gr:Graph {id: $gid})-[:HAS_NODE]->(n:Node) DETACH DELETE n", {"gid": graph_id})
    g.query("MATCH (gr:Graph {id: $gid})-[:HAS_DEADLINE]->(d:Deadline) DETACH DELETE d", {"gid": graph_id})
    for n in snapshot["nodes"]:
        emb = n.get("embedding")
        if emb:
            g.query(
                "MATCH (gr:Graph {id: $gid}) "
                "CREATE (nd:Node {id: $id, title: $t, description: $d, embedding: vecf32($emb)}) "
                "CREATE (gr)-[:HAS_NODE]->(nd)",
                {"gid": graph_id, "id": n["id"], "t": n["title"], "d": n["description"], "emb": emb},
            )
        else:
            g.query(
                "MATCH (gr:Graph {id: $gid}) "
                "CREATE (nd:Node {id: $id, title: $t, description: $d}) "
                "CREATE (gr)-[:HAS_NODE]->(nd)",
                {"gid": graph_id, "id": n["id"], "t": n["title"], "d": n["description"]},
            )
    for e in snapshot["edges"]:
        g.query("MATCH (a:Node {id: $aid}), (b:Node {id: $bid}) CREATE (a)-[:PRECEDES]->(b)",
                {"aid": e["from"], "bid": e["to"]})
    for d in snapshot["deadlines"]:
        g.query(
            "MATCH (gr:Graph {id: $gid}) "
            "CREATE (dl:Deadline {id: $id, title: $t, date: $date, type: $type}) "
            "CREATE (gr)-[:HAS_DEADLINE]->(dl)",
            {"gid": graph_id, "id": d["id"], "t": d["title"], "date": d["date"], "type": d.get("type", "assignment")},
        )
    for c in snapshot["covers"]:
        g.query("MATCH (d:Deadline {id: $did}), (n:Node {id: $nid}) CREATE (d)-[:COVERS]->(n)",
                {"did": c["deadline_id"], "nid": c["node_id"]})
