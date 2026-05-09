from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.modules.chats.repository import ChatRepository
from app.modules.chats.schemas import ChatCreate, ChatMessageRead, ChatRead
from app.modules.users.models import User


class ChatService:

    def __init__(self, repo: ChatRepository):
        self.repo = repo

    async def create_chat(self, user: User, data: ChatCreate) -> ChatRead:
        try:
            node_id = PydanticObjectId(data.node_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid node_id")
        chat = await self.repo.create(user.id, node_id, chat_type=data.chat_type)
        return ChatRead.model_validate(chat)

    async def list_chats(self, user: User, node_id: str, skip: int = 0, limit: int = 100) -> list[ChatRead]:
        try:
            node_oid = PydanticObjectId(node_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid node_id")
        chats = await self.repo.get_all_by_owner_and_node(user.id, node_oid, skip=skip, limit=limit)
        return [ChatRead.model_validate(c) for c in chats]

    async def get_messages(self, user: User, chat_id: str) -> list[ChatMessageRead]:
        chat = await self.repo.get_by_id_and_owner(chat_id, user.id)
        if chat is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
        messages = await self.repo.get_messages(chat.id)
        return [ChatMessageRead.model_validate(m) for m in messages]

    async def delete_chat(self, user: User, chat_id: str) -> None:
        chat = await self.repo.get_by_id_and_owner(chat_id, user.id)
        if chat is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
        await self.repo.delete(chat)
