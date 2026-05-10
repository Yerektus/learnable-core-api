from langchain_openai import ChatOpenAI
from app.config import get_settings

def get_llm(streaming: bool = False) -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        streaming=streaming,
        temperature=0.7,
        max_tokens=32000,
    )

def get_vision_llm(streaming: bool = False) -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_vision_model,
        streaming=streaming,
        temperature=0.7,
        max_tokens=32000,
    )
