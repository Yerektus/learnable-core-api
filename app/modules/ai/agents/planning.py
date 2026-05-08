import json
import uuid
from typing import AsyncIterator
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.mongodb import MongoDBSaver
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from app.modules.ai.llm import get_llm
from app.modules.ai.graph import queries as gq
from app.modules.ai.graph.client import get_graph
from motor.motor_asyncio import AsyncIOMotorClient

PLANNING_SYSTEM = """You are an AI assistant that helps build and edit learning graphs.
You can add nodes, remove nodes, create connections between nodes, and generate tasks.
Always think step by step. After each operation, verify the graph state.
When done, summarize what changes you made."""

# Tools for graph editing
def make_graph_tools(graph_id: str, user_id: str):

    @tool
    def add_node(title: str, description: str) -> str:
        """Add a new topic node to the graph."""
        from app.modules.ai.graph.embeddings import embed
        node_id = str(uuid.uuid4())
        emb = embed(f"{title} {description}")
        gq.create_node(node_id, graph_id, title, description, emb)
        return f"Created node '{title}' with id {node_id}"

    @tool
    def remove_node(node_id: str) -> str:
        """Remove a node from the graph by ID."""
        g = get_graph()
        g.query("MATCH (n:Node {id: $id}) DETACH DELETE n", {"id": node_id})
        return f"Removed node {node_id}"

    @tool
    def connect_nodes(from_node_id: str, to_node_id: str) -> str:
        """Create a PRECEDES relationship between two nodes."""
        gq.create_precedes(from_node_id, to_node_id)
        return f"Connected {from_node_id} → {to_node_id}"

    @tool
    def get_graph_state() -> str:
        """Read current graph structure."""
        snapshot = gq.snapshot_graph_state(graph_id)
        return json.dumps(snapshot, indent=2)

    return [add_node, remove_node, connect_nodes, get_graph_state]


async def stream_planning(
    graph_id: str,
    user_id: str,
    message: str,
    mongodb_client: AsyncIOMotorClient,
) -> AsyncIterator[str]:

    # Snapshot before agent starts
    snapshot = gq.snapshot_graph_state(graph_id)

    tools = make_graph_tools(graph_id, user_id)
    llm = get_llm().bind_tools(tools)

    messages = [
        SystemMessage(content=PLANNING_SYSTEM),
        HumanMessage(content=message)
    ]

    try:
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content
            # Handle tool calls
            if chunk.tool_calls:
                for tc in chunk.tool_calls:
                    tool_name = tc["name"]
                    tool_args = tc["args"]
                    yield f"\n[Running: {tool_name}...]\n"
                    # Find and execute tool
                    for t in tools:
                        if t.name == tool_name:
                            result = t.invoke(tool_args)
                            yield f"[Done: {result}]\n"
                            break
    except Exception as e:
        # Restore snapshot on failure
        gq.restore_graph_state(graph_id, snapshot)
        yield f"\n[Error occurred, changes reverted: {str(e)}]\n"
