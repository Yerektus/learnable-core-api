from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    mongodb_url: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URL")
    database_name: str = Field(default="learnable", alias="DATABASE_NAME")
    secret_key: str = Field(alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    algorithm: Literal["HS256"] = Field(default="HS256", alias="ALGORITHM")
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"])

    # FalkorDB
    falkordb_host: str = Field(default="localhost", alias="FALKORDB_HOST")
    falkordb_port: int = Field(default=6379, alias="FALKORDB_PORT")

    # LLM (OpenAI-compatible, works with Together AI and vLLM)
    llm_base_url: str = Field(default="https://api.together.xyz/v1", alias="LLM_BASE_URL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="deepseek-ai/DeepSeek-R1", alias="LLM_MODEL")
    llm_vision_model: str = Field(default="Qwen/Qwen2.5-VL-72B-Instruct", alias="LLM_VISION_MODEL")

    # Embeddings
    embed_model: str = Field(default="BAAI/bge-m3", alias="EMBED_MODEL")

    # Whisper
    whisper_model: str = Field(default="base", alias="WHISPER_MODEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
