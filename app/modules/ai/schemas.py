from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel


# ── Syllabus ──────────────────────────────────────────────────
class GeneratedNode(BaseModel):
    title: str
    description: str
    order: int

class GeneratedDeadline(BaseModel):
    title: str
    date: date  # validated YYYY-MM-DD; Pydantic rejects bad format and invalid calendar dates
    node_indices: list[int]
    type: Literal["exam", "quiz", "assignment"] = "assignment"

class GeneratedGraph(BaseModel):
    nodes: list[GeneratedNode]
    edges: list[tuple[int, int]]  # (from_order, to_order) PRECEDES
    deadlines: list[GeneratedDeadline]

class GenerateGraphResponse(BaseModel):
    graph_id: str
    nodes_created: int
    deadlines_created: int


# ── Chat ──────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    chat_type: Literal["theory", "task"]
    thread_id: str


# ── Materials ─────────────────────────────────────────────────
class GenerateMaterialsRequest(BaseModel):
    node_id: str
    material_type: Literal["cards", "notes", "both"] = "both"

class Flashcard(BaseModel):
    front: str
    back: str

class CardsOutput(BaseModel):
    cards: list[Flashcard]

class GeneratedMaterials(BaseModel):
    node_id: str = ""
    cards: list[Flashcard] = []
    notes: str = ""


# ── Planning Panel ────────────────────────────────────────────
class PlanningRequest(BaseModel):
    message: str
    history: list[dict] = []


# ── Deadline Prep ─────────────────────────────────────────────
class DeadlinePrepRequest(BaseModel):
    deadline_id: str


# ── Canvas (v1 stubs — frontend can build against these now) ──
class CanvasInput(BaseModel):
    svg_region: str
    task_id: str
    node_id: str

class CanvasResponse(BaseModel):
    type: Literal["latex", "mermaid", "text", "highlight"]
    content: str
    position: Literal["ai_zone", "inline", "below_last"]

class CanvasError(BaseModel):
    description: str
    region: dict  # {x, y, w, h}
    # source="canvas" → same MADE_ERROR pipeline when implemented


# ── Stats ─────────────────────────────────────────────────────
class AIStats(BaseModel):
    model: str
    vision_model: str
    llm_base_url: str
