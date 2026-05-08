import asyncio
import uuid
from typing import AsyncIterator
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from app.modules.ai.llm import get_llm
from app.modules.ai.graph.queries import (
    get_node_context, search_similar_errors, record_error, find_and_link_similar_errors
)
from app.modules.ai.graph.embeddings import embed

CONTEXT_TOKEN_LIMIT = 100000  # 80% of 128K

SYSTEM_PROMPT = """You are an AI tutor helping a student learn. You have access to context about the current topic and the student's learning history.

Current topic: {node_title}
Topic description: {node_description}

{deadline_context}

{error_context}

Guidelines:
- Give clear, educational responses
- If error context is provided, use it ONLY to calibrate your explanation depth — do NOT explicitly mention the student's past errors unless asked
- If you detect the student making a mistake in their current message, call the record_error tool
- If the student asks to generate flashcards or notes, call the generate_materials tool
- For task chats: help solve practical problems step by step
- For theory chats: explain concepts clearly with examples"""

async def stream_chat(
    user_id: str,
    node_id: str,
    message: str,
    chat_type: str,
    chat_history: list[dict],
) -> AsyncIterator[str]:

    # Get context from FalkorDB (run_in_executor — all three are sync/blocking)
    loop = asyncio.get_running_loop()
    node_ctx = await loop.run_in_executor(None, get_node_context, user_id, node_id)
    question_emb = await loop.run_in_executor(None, embed, message)
    similar_errors = await loop.run_in_executor(None, search_similar_errors, question_emb, user_id, node_id)

    # Build context strings
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

    # Context compression: keep last N messages if history too long
    history = chat_history[-20:]  # simple truncation for v0

    messages = [SystemMessage(content=system)]
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=message))

    llm = get_llm(streaming=True)
    full_response = ""

    async for chunk in llm.astream(messages):
        token = chunk.content
        if token:
            full_response += token
            yield token

    # After streaming: async background task for SIMILAR_TO
    # Error detection is done via simple heuristic for v0
    # (Full tool-calling implementation can be added in v1)
