# Learnable — AI Module

## Project
AI-powered study platform. Stack: FastAPI + MongoDB (Beanie ODM) + FalkorDB (graph + vector) + LangChain + Python 3.13 + uv.

## Module structure
```
app/
  config.py              # Settings via pydantic-settings, get_settings() @lru_cache
  database.py            # Beanie init: User, Graph, GraphNode, Task
  main.py                # lifespan: init_database → init_falkordb_schema → warmup_embeddings
  modules/
    auth/                # fastapi-users, JWT
    users/               # user profiles
    graphs/              # Graph (has custom_prompt), GraphNode models
    kanban/              # Task model (TaskStatus, TaskPriority)
    ai/
      router.py          # all endpoints, prefix /api/v1/ai
      schemas.py         # all pydantic I/O models
      llm.py             # get_llm(), get_vision_llm() — LangChain ChatOpenAI
      service.py         # stub
      graph/
        client.py        # FalkorDB singleton: get_graph()
        schema.py        # init_falkordb_schema() — vector indexes, run at startup
        queries.py       # all cypher: create_node, record_error, search_similar_errors, etc.
        embeddings.py    # BGE-M3: embed(text), warmup()
      chains/
        syllabus.py      # text → GeneratedGraph (pydantic structured output, not agentic)
        chat.py          # stream_chat() — SSE, FalkorDB context injection
        materials.py     # generate_cards(), generate_notes()
      agents/
        planning.py      # stream_planning() — LangGraph + tools, snapshot/restore
      parsers/
        documents.py     # parse_file(): pdf(max 30p), docx, image(OCR), txt/md
        audio.py         # transcribe_audio() — Whisper
      tools/             # empty stubs (logic lives in agents/planning.py)
```

## Key patterns
```python
# Auth
from app.modules.auth.dependencies import current_active_user
user: User = Depends(current_active_user)

# Settings
from app.config import get_settings
settings = get_settings()

# FalkorDB — always str(user.id), always vecf32() for embeddings
gq.create_node(node_id, graph_id, title, desc, embedding)
g.query("... vecf32($emb)", {"emb": embedding_list})

# Streaming
from sse_starlette.sse import EventSourceResponse
return EventSourceResponse(event_generator())
```

## Endpoints
```
POST /api/v1/ai/graphs/{graph_id}/generate              # UploadFile → GenerateGraphResponse
POST /api/v1/ai/graphs/{graph_id}/generate-from-audio   # UploadFile → GenerateGraphResponse
POST /api/v1/ai/graphs/{graph_id}/plan                  # PlanningRequest → SSE
POST /api/v1/ai/nodes/{node_id}/chat                    # ChatRequest → SSE
POST /api/v1/ai/nodes/{node_id}/errors                  # Form: description, source
POST /api/v1/ai/nodes/{node_id}/materials/generate-from-file  # UploadFile + material_type
POST /api/v1/ai/deadlines/{deadline_id}/prepare         # SSE
WS   /api/v1/ai/canvas/stream                           # stub, closes 1001 (v1)
GET  /api/v1/ai/stats                                   # AIStats
```

## FalkorDB schema
```
Nodes:   User(id), Graph(id,name), Node(id,title,description,embedding), 
         Error(id,description,embedding,source,created_at), Deadline(id,title,date)
Edges:   OWNS, HAS_NODE, PRECEDES, MADE_ERROR, IN_NODE, SIMILAR_TO, HAS_DEADLINE, COVERS
Indexes: VECTOR Node.embedding (1024d cosine), VECTOR Error.embedding (1024d cosine)
         INDEX User.id, Node.id, Deadline.id
```

## Env vars
```
FALKORDB_HOST=localhost  FALKORDB_PORT=6379
LLM_BASE_URL=https://api.together.xyz/v1  (swap to AMD vLLM for prod)
LLM_API_KEY=...  LLM_MODEL=deepseek-ai/DeepSeek-R1
LLM_VISION_MODEL=Qwen/Qwen2.5-VL-72B-Instruct
EMBED_MODEL=BAAI/bge-m3  WHISPER_MODEL=base
```

## Critical notes
- `custom_prompt` on Graph model — used in syllabus chain, max 2000 chars
- Error quality filter: only surface errors with `EXISTS((e)-[:SIMILAR_TO]->())`
- `find_and_link_similar_errors` runs async via `asyncio.create_task` after recording
- Planning agent snapshots graph before start, restores on any exception
- BGE-M3 warmup at startup (~30s first load) — already wired in lifespan
- Canvas v1: SVG active region + Mermaid/LaTeX rendering, WebSocket endpoint is stub
- CORS includes localhost:3000, 3001, 5173
- Task model registered in Beanie init (database.py)
- Kanban router prefix: /api/v1/kanban
