from openai import OpenAI
from app.config import get_settings

_client: OpenAI | None = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    return _client

def embed(text: str) -> list[float]:
    settings = get_settings()
    response = _get_client().embeddings.create(
        model=settings.embed_model,
        input=text,
    )
    return response.data[0].embedding

def warmup():
    pass  # no warmup needed for API-based embeddings
