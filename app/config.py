import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    mongodb_url: str = Field(default=os.getenv("MONGODB_URL", "mongodb://localhost:27017"), alias="MONGODB_URL")
    database_name: str = Field(default="learnable", alias="DATABASE_NAME")
    secret_key: str = Field(alias="SECRET_KEY")

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters — generate one with: openssl rand -hex 32")
        return v
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    algorithm: Literal["HS256"] = Field(default="HS256", alias="ALGORITHM")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
        alias="CORS_ORIGINS",
    )
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    cookie_same_site: str = Field(default="lax", alias="COOKIE_SAME_SITE")

    # FalkorDB
    redis_url: str = Field(default=os.getenv("REDIS_URL", os.getenv("FALKORDB_URL", "redis://localhost:6379")), alias="REDIS_URL")

    # LLM (OpenAI-compatible, works with Together AI and vLLM)
    llm_base_url: str = Field(default="https://api.together.xyz/v1", alias="LLM_BASE_URL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="deepseek-ai/DeepSeek-R1", alias="LLM_MODEL")
    llm_vision_model: str = Field(default="Qwen/Qwen2.5-VL-72B-Instruct", alias="LLM_VISION_MODEL")

    # Embeddings
    embed_model: str = Field(default=os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"), alias="EMBED_MODEL")

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
