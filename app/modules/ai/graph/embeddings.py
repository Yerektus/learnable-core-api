from sentence_transformers import SentenceTransformer
from app.config import get_settings

_model: SentenceTransformer | None = None

def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        settings = get_settings()
        _model = SentenceTransformer(settings.embed_model)
    return _model

def embed(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text, normalize_embeddings=True).tolist()

def warmup():
    """Call at startup to pre-load model."""
    embed("warmup")
