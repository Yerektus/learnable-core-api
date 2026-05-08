import asyncio
import json
import logging
import uuid
from typing import AsyncIterator

logger = logging.getLogger(__name__)
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
    chat_history: list[dict],
) -> AsyncIterator[str]:

    loop = asyncio.get_running_loop()
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

    history = chat_history[-20:]

    messages = [SystemMessage(content=system)]
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=message))

    llm = get_llm(streaming=True).bind_tools([record_error_tool])

    pending_error_descriptions: list[str] = []
    tool_call_accumulator: dict[int, dict] = {}

    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content

        # Accumulate streamed tool_call deltas
        if chunk.tool_call_chunks:
            for delta in chunk.tool_call_chunks:
                idx = delta.get("index", 0)
                if idx not in tool_call_accumulator:
                    tool_call_accumulator[idx] = {"name": "", "args": ""}
                if delta.get("name"):
                    tool_call_accumulator[idx]["name"] += delta["name"]
                if delta.get("args"):
                    tool_call_accumulator[idx]["args"] += delta["args"]

    # After stream: process completed tool calls
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


async def _link_similar_bg(error_id: str) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, find_and_link_similar_errors, error_id)

def _log_task_exception(task: asyncio.Task) -> None:
    if not task.cancelled() and task.exception() is not None:
        logger.error("Background task %s failed", task.get_name(), exc_info=task.exception())
