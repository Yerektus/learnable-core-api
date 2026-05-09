from fastapi import Depends

from app.modules.chats.repository import ChatRepository
from app.modules.chats.service import ChatService


def get_chat_repository() -> ChatRepository:
    return ChatRepository()


def get_chat_service(
    repo: ChatRepository = Depends(get_chat_repository),
) -> ChatService:
    return ChatService(repo)
