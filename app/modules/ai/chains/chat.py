import asyncio
import json
import logging
import uuid
from typing import AsyncIterator

logger = logging.getLogger(__name__)

from beanie import PydanticObjectId
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool

from app.modules.ai.llm import get_llm
from app.modules.ai.graph.queries import (
    ensure_user_node, get_node_context, search_similar_errors,
    record_error, find_and_link_similar_errors,
)
from app.modules.ai.graph.embeddings import embed

SYSTEM_PROMPT = """You are an AI tutor helping a student learn. You have access to context about the current topic and the student's learning history.

Current topic: {node_title}
Topic description: {node_description}

{deadline_context}

{error_context}

Guidelines:
- Give clear, educational responses
- If error context is provided, use it ONLY to calibrate your explanation depth — do NOT explicitly mention the student's past errors unless asked
- If the student makes a factual mistake or shows a clear misunderstanding in their message, call record_error_tool with a concise description of the error before responding
- For task chats: help solve practical problems step by step
- For theory chats: explain concepts clearly with examples"""


@tool
def record_error_tool(description: str) -> str:
    """Record a factual mistake or misunderstanding made by the student. Call this when the student's message contains an error worth tracking."""
    return description


async def stream_chat(
    user_id: str,
    node_id: str,
    message: str,
    chat_type: str,
    thread_id: str,
    graph_id: str | None = None,
) -> AsyncIterator[str]:
    from app.modules.chats.models import Chat, ChatMessage as ChatMsg

    loop = asyncio.get_running_loop()

    # Load last 20 messages from MongoDB (ownership already verified by router)
    chat_oid = PydanticObjectId(thread_id)
    raw_messages = (
        await ChatMsg.find(ChatMsg.chat_id == chat_oid)
        .sort("-created_at")
        .limit(20)
        .to_list()
    )
    is_first_message = len(raw_messages) == 0
    chat_history = [{"role": m.role, "content": m.content} for m in reversed(raw_messages)]

    # FalkorDB context
    await loop.run_in_executor(None, ensure_user_node, user_id)
    node_ctx = await loop.run_in_executor(None, get_node_context, user_id, node_id)
    question_emb = await loop.run_in_executor(None, embed, message)
    similar_errors = await loop.run_in_executor(None, search_similar_errors, question_emb, user_id, node_id)

    deadline_context = ""
    if node_ctx.get("upcoming_deadlines"):
        deadlines_str = ", ".join(
            f"{d['title']} on {d['date']}"
            for d in node_ctx["upcoming_deadlines"]
        )
        deadline_context = f"Upcoming deadlines covering this topic: {deadlines_str}"

    error_context = ""
    if similar_errors:
        errors_str = "; ".join(similar_errors)
        error_context = f"Student context (use to calibrate explanation only, do not address directly): {errors_str}"

    system = SYSTEM_PROMPT.format(
        node_title=node_ctx.get("node_title", ""),
        node_description=node_ctx.get("node_description", ""),
        deadline_context=deadline_context,
        error_context=error_context,
    )

    messages = [SystemMessage(content=system)]
    for msg in chat_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=message))

    llm = get_llm(streaming=True).bind_tools([record_error_tool])

    full_response = ""
    pending_error_descriptions: list[str] = []
    tool_call_accumulator: dict[int, dict] = {}

    async for chunk in llm.astream(messages):
        if chunk.content:
            full_response += chunk.content
            yield chunk.content

        if chunk.tool_call_chunks:
            for delta in chunk.tool_call_chunks:
                idx = delta.get("index", 0)
                if idx not in tool_call_accumulator:
                    tool_call_accumulator[idx] = {"name": "", "args": ""}
                if delta.get("name"):
                    tool_call_accumulator[idx]["name"] += delta["name"]
                if delta.get("args"):
                    tool_call_accumulator[idx]["args"] += delta["args"]

    # Process completed tool calls
    for tc in tool_call_accumulator.values():
        if tc["name"] == "record_error_tool":
            try:
                args = json.loads(tc["args"]) if tc["args"] else {}
                description = args.get("description", "")
                if description:
                    pending_error_descriptions.append(description)
            except (json.JSONDecodeError, KeyError) as exc:
                logger.warning("Failed to parse record_error_tool call args %r: %s", tc, exc)

    # Persist errors as background tasks
    for description in pending_error_descriptions:
        error_id = str(uuid.uuid4())
        error_emb = await loop.run_in_executor(None, embed, description)
        await loop.run_in_executor(
            None, record_error, error_id, user_id, node_id, description, error_emb, "chat"
        )
        task = asyncio.create_task(_link_similar_bg(error_id))
        task.add_done_callback(_log_task_exception)

    # Save user message and assistant response to MongoDB
    await ChatMsg(chat_id=chat_oid, role="user", content=message).insert()
    if full_response:
        await ChatMsg(chat_id=chat_oid, role="assistant", content=full_response).insert()

    # Auto-generate title from first user message
    if is_first_message:
        title = message[:80].strip()
        if title:
            chat_doc = await Chat.get(chat_oid)
            if chat_doc is not None and not chat_doc.title:
                chat_doc.title = title
                await chat_doc.save()

    # Auto-create Task on first message of a task chat
    if chat_type == "task" and is_first_message and graph_id is not None:
        from app.modules.kanban.models import Task, TaskStatus
        task_title = message[:120].strip() or "Task"
        await Task(
            owner_id=PydanticObjectId(user_id),
            title=task_title,
            graph_id=graph_id,
            topic_id=node_id,
            source="chat",
            status=TaskStatus.NOT_STARTED,
        ).insert()

    # Auto-create subnode on first message of a theory chat
    if chat_type == "theory" and is_first_message and graph_id is not None:
        from app.modules.graphs.models import GraphNode as GraphNodeDoc
        from app.modules.ai.graph.queries import ensure_graph_node, create_node as falkor_create_node
        node_title = message[:120].strip() or "Topic"
        subnode = GraphNodeDoc(
            owner_id=PydanticObjectId(user_id),
            graph_id=PydanticObjectId(graph_id),
            title=node_title,
            node_type="topic",
            position_x=0.0,
            position_y=0.0,
        )
        await subnode.insert()
        node_emb = await loop.run_in_executor(None, embed, node_title)
        await loop.run_in_executor(None, ensure_graph_node, graph_id, user_id)
        await loop.run_in_executor(None, falkor_create_node, str(subnode.id), graph_id, node_title, "", node_emb)


async def _link_similar_bg(error_id: str) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, find_and_link_similar_errors, error_id)


def _log_task_exception(task: asyncio.Task) -> None:
    if not task.cancelled() and task.exception() is not None:
        logger.error("Background task %s failed", task.get_name(), exc_info=task.exception())
