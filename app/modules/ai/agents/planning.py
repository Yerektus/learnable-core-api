import asyncio
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
When done, summarize what changes you made.
Only call tools when the user explicitly asks to modify the graph. For greetings or unclear messages — respond in plain text only, do not call get_graph_state or any other tool."""

# Tools for graph editing
def make_graph_tools(graph_id: str, user_id: str, loop: asyncio.AbstractEventLoop | None = None):

    @tool
    def add_node(title: str, description: str) -> str:
        """Add a new topic node to the graph."""
        from app.modules.ai.graph.embeddings import embed
        from app.modules.graphs.models import GraphNode
        from beanie import PydanticObjectId

        async def _insert() -> str:
            gn = GraphNode(
                owner_id=PydanticObjectId(user_id),
                graph_id=PydanticObjectId(graph_id),
                title=title,
                description=description,
                position_x=0.0,
                position_y=0.0,
            )
            await gn.insert()
            return str(gn.id)

        if loop is not None:
            future = asyncio.run_coroutine_threadsafe(_insert(), loop)
            node_id = future.result(timeout=10)
        else:
            node_id = asyncio.run(_insert())

        emb = embed(f"{title} {description}")
        gq.create_node(node_id, graph_id, title, description, emb)
        return f"Created node '{title}' with id {node_id}"

    @tool
    def remove_node(node_id: str) -> str:
        """Remove a node from the graph by ID."""
        from app.modules.graphs.models import GraphNode
        from beanie import PydanticObjectId

        g = get_graph()
        g.query("MATCH (n:Node {id: $id}) DETACH DELETE n", {"id": node_id})

        async def _delete() -> None:
            try:
                await GraphNode.find(GraphNode.id == PydanticObjectId(node_id)).delete()
            except Exception:
                pass

        if loop is not None:
            future = asyncio.run_coroutine_threadsafe(_delete(), loop)
            future.result(timeout=10)
        else:
            asyncio.run(_delete())

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
        display = {
            "nodes": [{"id": n["id"], "title": n["title"], "description": n["description"]} for n in snapshot["nodes"]],
            "edges": [{"from": e["from"], "to": e["to"]} for e in snapshot["edges"]],
            "deadlines": [{"title": d["title"], "date": d["date"]} for d in snapshot["deadlines"]],
        }
        return json.dumps(display, indent=2)

    @tool
    def create_task(title: str, description: str, node_id: str = "") -> str:
        """Create a task in the kanban board linked to the current graph and optionally to a specific node."""
        from app.modules.kanban.models import Task, TaskStatus
        from beanie import PydanticObjectId

        async def _insert() -> str:
            task = Task(
                owner_id=PydanticObjectId(user_id),
                title=title[:120].strip() or "Task",
                description=description[:1000].strip() if description else None,
                graph_id=graph_id,
                topic_id=node_id if node_id else None,
                source="planning",
                status=TaskStatus.NOT_STARTED,
            )
            await task.insert()
            return str(task.id)

        if loop is not None:
            future = asyncio.run_coroutine_threadsafe(_insert(), loop)
            task_id = future.result(timeout=10)
        else:
            task_id = asyncio.run(_insert())

        return f"Created task '{title[:120]}' with id {task_id}"

    return [add_node, remove_node, connect_nodes, get_graph_state, create_task]


async def stream_planning(
    graph_id: str,
    user_id: str,
    message: str,
    mongodb_client: AsyncIOMotorClient,
) -> AsyncIterator[str]:

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, gq.ensure_user_node, user_id)
    await loop.run_in_executor(None, gq.create_graph_node, graph_id, user_id, "")

    # Snapshot before agent starts
    snapshot = gq.snapshot_graph_state(graph_id)

    tools = make_graph_tools(graph_id, user_id, loop=loop)
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
                    # Find and execute tool (run_in_executor — tools call sync FalkorDB ops)
                    for t in tools:
                        if t.name == tool_name:
                            result = await loop.run_in_executor(None, lambda: t.invoke(tool_args))
                            yield f"[Done: {result}]\n"
                            break
    except Exception as e:
        # Restore snapshot on failure
        gq.restore_graph_state(graph_id, snapshot)
        yield f"\n[Error occurred, changes reverted: {str(e)}]\n"
