import asyncio
import logging
import uuid
from typing import Annotated

logger = logging.getLogger(__name__)

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, WebSocket
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.modules.ai.schemas import (
    AIStats, ChatRequest, DeadlinePrepRequest, GenerateGraphResponse,
    GenerateMaterialsRequest, ManualDeadlineRequest, ManualDeadlineResponse,
    PlanningRequest, CanvasInput,
)
from app.modules.auth.dependencies import current_active_user
from app.modules.users.models import User
from app.modules.ai.parsers.documents import parse_file
from app.modules.ai.parsers.audio import transcribe_audio
from app.modules.ai.chains.syllabus import generate_graph_from_text
from app.modules.ai.chains.chat import stream_chat
from app.modules.ai.chains.materials import generate_cards, generate_notes
from app.modules.ai.agents.planning import stream_planning
from app.modules.ai.graph import queries as gq
from app.modules.ai.graph.embeddings import embed
from app.modules.ai.graph.schema import init_falkordb_schema
from app.config import get_settings

router = APIRouter()

_MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


async def _run_sync(func, *args):
    return await asyncio.get_running_loop().run_in_executor(None, func, *args)


async def _persist_generated_graph(
    generated,
    graph_id: str,
    user,
) -> tuple[int, int]:
    """Insert GeneratedGraph into MongoDB + FalkorDB. Returns (nodes_created, deadlines_created)."""
    from app.modules.graphs.models import GraphNode
    from beanie import PydanticObjectId

    node_ids = []
    for i, node_data in enumerate(generated.nodes):
        gn = GraphNode(
            owner_id=user.id,
            graph_id=PydanticObjectId(graph_id),
            title=node_data.title,
            description=node_data.description,
            position_x=float(i * 200),
            position_y=0.0,
        )
        await gn.insert()
        node_id = str(gn.id)
        node_ids.append(node_id)
        node_emb = await _run_sync(embed, f"{node_data.title} {node_data.description}")
        await _run_sync(gq.create_node, node_id, graph_id, node_data.title, node_data.description, node_emb)

    order_to_id = {node_data.order: node_id for node_data, node_id in zip(generated.nodes, node_ids)}
    index_to_id = {i: node_id for i, node_id in enumerate(node_ids)}
    order_to_title = {node_data.order: node_data.title for node_data in generated.nodes}
    index_to_title = {i: node_data.title for i, node_data in enumerate(generated.nodes)}

    for from_order, to_order in generated.edges:
        if from_order in order_to_id and to_order in order_to_id:
            await _run_sync(gq.create_precedes, order_to_id[from_order], order_to_id[to_order])

    for i_dl, dl in enumerate(generated.deadlines):
        dl_id = str(uuid.uuid4())
        await _run_sync(gq.create_deadline, dl_id, graph_id, dl.title, dl.date.isoformat(), dl.type)
        covered_titles = []
        for ni in dl.node_indices:
            node_id_for_dl = order_to_id.get(ni) or index_to_id.get(ni)
            if node_id_for_dl:
                await _run_sync(gq.link_deadline_to_node, dl_id, node_id_for_dl)
            title = order_to_title.get(ni) or index_to_title.get(ni)
            if title:
                covered_titles.append(title)
        if dl.type in ("quiz", "exam"):
            dl_node = GraphNode(
                owner_id=user.id,
                graph_id=PydanticObjectId(graph_id),
                title=dl.title,
                node_type="quiz",
                description=", ".join(covered_titles) if covered_titles else None,
                position_x=float(i_dl * 300),
                position_y=350.0,
                falkordb_deadline_id=dl_id,
            )
            await dl_node.insert()

    return len(node_ids), len(generated.deadlines)


# ── Graph generation ──────────────────────────────────────────
@router.post("/graphs/{graph_id}/generate", response_model=GenerateGraphResponse)
async def generate_graph(
    graph_id: str,
    file: UploadFile = File(...),
    user: User = Depends(current_active_user),
):
    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum allowed size is 50 MB.")
    try:
        text = await _run_sync(parse_file, file.filename or "file.txt", content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    from app.modules.graphs.models import Graph
    graph = await Graph.get(graph_id)
    if not graph or str(graph.owner_id) != str(user.id):
        raise HTTPException(status_code=404, detail="Graph not found")

    generated = await _run_sync(generate_graph_from_text, text, graph.custom_prompt or "")
    await _run_sync(gq.create_graph_node, graph_id, str(user.id), graph.name)
    nodes_created, deadlines_created = await _persist_generated_graph(generated, graph_id, user)

    return GenerateGraphResponse(
        graph_id=graph_id,
        nodes_created=nodes_created,
        deadlines_created=deadlines_created,
    )


# ── Audio transcription ───────────────────────────────────────
@router.post("/graphs/{graph_id}/generate-from-audio", response_model=GenerateGraphResponse)
async def generate_graph_from_audio(
    graph_id: str,
    file: UploadFile = File(...),
    user: User = Depends(current_active_user),
):
    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum allowed size is 50 MB.")
    text = await _run_sync(transcribe_audio, content, file.filename or "audio.mp3")

    from app.modules.graphs.models import Graph
    graph = await Graph.get(graph_id)
    if not graph or str(graph.owner_id) != str(user.id):
        raise HTTPException(status_code=404, detail="Graph not found")

    generated = await _run_sync(generate_graph_from_text, text, graph.custom_prompt or "")
    await _run_sync(gq.create_graph_node, graph_id, str(user.id), graph.name)
    nodes_created, deadlines_created = await _persist_generated_graph(generated, graph_id, user)

    return GenerateGraphResponse(
        graph_id=graph_id,
        nodes_created=nodes_created,
        deadlines_created=deadlines_created,
    )


# ── Chat ──────────────────────────────────────────────────────
@router.post("/nodes/{node_id}/chat")
async def chat(
    node_id: str,
    request: ChatRequest,
    user: User = Depends(current_active_user),
):
    from app.modules.chats.models import Chat as ChatDoc
    from beanie import PydanticObjectId

    try:
        chat_oid = PydanticObjectId(request.thread_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Invalid thread_id")

    chat_doc = await ChatDoc.find_one(ChatDoc.id == chat_oid, ChatDoc.user_id == user.id)
    if chat_doc is None or str(chat_doc.node_id) != node_id:
        raise HTTPException(status_code=404, detail="Chat not found")

    from app.modules.graphs.models import GraphNode
    try:
        node_oid = PydanticObjectId(node_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Invalid node_id")
    graph_node = await GraphNode.find_one(GraphNode.id == node_oid, GraphNode.owner_id == user.id)
    graph_id = str(graph_node.graph_id) if graph_node is not None else None

    async def event_generator():
        async for token in stream_chat(
            user_id=str(user.id),
            node_id=node_id,
            message=request.message,
            chat_type=request.chat_type,
            thread_id=request.thread_id,
            graph_id=graph_id,
        ):
            yield {"data": token}

    return EventSourceResponse(event_generator())


# ── Record error manually ─────────────────────────────────────
@router.post("/nodes/{node_id}/errors")
async def record_error_endpoint(
    node_id: str,
    background_tasks: BackgroundTasks,
    description: str = Form(...),
    source: str = Form(default="chat"),
    user: User = Depends(current_active_user),
):
    from app.modules.graphs.models import GraphNode
    from beanie import PydanticObjectId as _OID
    try:
        node_oid = _OID(node_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Invalid node_id")
    if not await GraphNode.find_one(GraphNode.id == node_oid, GraphNode.owner_id == user.id):
        raise HTTPException(status_code=404, detail="Node not found")

    error_id = str(uuid.uuid4())
    await _run_sync(gq.ensure_user_node, str(user.id))
    emb = await _run_sync(embed, description)
    await _run_sync(gq.record_error, error_id, str(user.id), node_id, description, emb, source)
    background_tasks.add_task(gq.find_and_link_similar_errors, error_id)
    return {"error_id": error_id}


# ── Materials ─────────────────────────────────────────────────
@router.post("/nodes/{node_id}/materials/generate-from-file")
async def generate_materials_from_file(
    node_id: str,
    file: UploadFile = File(...),
    material_type: str = Form(default="both"),
    user: User = Depends(current_active_user),
):
    from beanie import PydanticObjectId as OID
    from app.modules.materials.repository import MaterialRepository
    from app.modules.graphs.models import GraphNode

    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum allowed size is 50 MB.")
    filename = file.filename or "file.txt"
    try:
        text = await _run_sync(parse_file, filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    title = filename.rsplit(".", 1)[0] or filename

    result: dict = {"node_id": node_id, "cards": [], "notes": "", "material_ids": []}
    repo = MaterialRepository()

    try:
        node_oid = OID(node_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Invalid node_id")

    if not await GraphNode.find_one(GraphNode.id == node_oid, GraphNode.owner_id == user.id):
        raise HTTPException(status_code=404, detail="Node not found")

    if material_type in ("cards", "both"):
        result["cards"] = await _run_sync(generate_cards, text)
        saved = await repo.create(
            owner_id=user.id,
            node_id=node_oid,
            material_type="cards",
            title=title,
            cards=result["cards"],
        )
        result["material_ids"].append(str(saved.id))

    if material_type in ("notes", "both"):
        result["notes"] = await _run_sync(generate_notes, text)
        saved = await repo.create(
            owner_id=user.id,
            node_id=node_oid,
            material_type="notes",
            title=title,
            content=result["notes"],
        )
        result["material_ids"].append(str(saved.id))

    return result


# ── Planning Panel ────────────────────────────────────────────
@router.post("/graphs/{graph_id}/plan")
async def planning_panel(
    graph_id: str,
    request: PlanningRequest,
    user: User = Depends(current_active_user),
):
    from app.modules.graphs.models import Graph
    graph = await Graph.get(graph_id)
    if not graph or str(graph.owner_id) != str(user.id):
        raise HTTPException(status_code=404, detail="Graph not found")

    async def event_generator():
        async for chunk in stream_planning(
            graph_id=graph_id,
            user_id=str(user.id),
            message=request.message,
            mongodb_client=None,  # simplified for v0
            history=request.history,
        ):
            yield {"data": chunk}

    return EventSourceResponse(event_generator())


# ── Deadline preparation ──────────────────────────────────────
@router.post("/deadlines/{deadline_id}/prepare")
async def deadline_prep(
    deadline_id: str,
    user: User = Depends(current_active_user),
):
    is_owner = await _run_sync(gq.check_deadline_owner, deadline_id, str(user.id))
    if not is_owner:
        raise HTTPException(status_code=404, detail="Deadline not found")

    ctx = await _run_sync(gq.get_deadline_prep_context, str(user.id), deadline_id)

    async def event_generator():
        from app.modules.ai.llm import get_llm
        from langchain_core.messages import HumanMessage, SystemMessage

        nodes_summary = "\n".join(
            f"- {n['node']}: errors: {', '.join(n['errors']) if n['errors'] else 'none'}"
            for n in ctx["nodes"]
        )

        prompt = f"""You are preparing a student for: {ctx['deadline_title']} on {ctx['deadline_date']}.

Topics covered and student's known error patterns:
{nodes_summary}

Create a personalized study plan that:
1. Prioritizes topics where the student has repeated errors
2. Suggests specific practice exercises for weak areas
3. Provides a day-by-day schedule if the deadline allows
4. Gives targeted tips for each weak area

Be specific and actionable."""

        llm = get_llm(streaming=True)
        async for chunk in llm.astream([HumanMessage(content=prompt)]):
            if chunk.content:
                yield {"data": chunk.content}

    return EventSourceResponse(event_generator())


# ── Manual deadline creation ──────────────────────────────────
@router.post("/deadlines/manual", response_model=ManualDeadlineResponse)
async def create_manual_deadline(
    request: ManualDeadlineRequest,
    user: User = Depends(current_active_user),
):
    from app.modules.graphs.models import Graph
    graph = await Graph.get(request.graph_id)
    if not graph or str(graph.owner_id) != str(user.id):
        raise HTTPException(status_code=404, detail="Graph not found")

    deadline_id = str(uuid.uuid4())
    await _run_sync(
        gq.create_deadline,
        deadline_id, request.graph_id, request.title, request.date, request.type,
    )
    for node_id in request.node_ids:
        await _run_sync(gq.link_deadline_to_node, deadline_id, node_id)
    return ManualDeadlineResponse(deadline_id=deadline_id)


# ── Canvas stub (v1) ──────────────────────────────────────────
@router.websocket("/canvas/stream")
async def canvas_stream(websocket: WebSocket):
    """Canvas WebSocket — v1 implementation pending."""
    await websocket.close(code=1001, reason="Canvas feature coming in v1")


# ── Stats ─────────────────────────────────────────────────────
@router.get("/stats", response_model=AIStats)
async def get_stats(user: User = Depends(current_active_user)):
    settings = get_settings()
    return AIStats(
        model=settings.llm_model,
        vision_model=settings.llm_vision_model,
        llm_base_url=settings.llm_base_url,
    )
