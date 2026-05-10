from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.modules.chats.repository import ChatRepository
from app.modules.chats.schemas import (
    ChatCreate,
    ChatMessageCreate,
    ChatMessageRead,
    ChatRead,
    PlanningChatRead,
)
from app.modules.users.models import User


class ChatService:

    def __init__(self, repo: ChatRepository):
        self.repo = repo

    async def create_chat(self, user: User, data: ChatCreate) -> ChatRead:
        node_id = None
        graph_id = None
        if data.node_id is not None:
            try:
                node_id = PydanticObjectId(data.node_id)
            except (TypeError, ValueError):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid node_id")
        if data.graph_id is not None:
            try:
                graph_id = PydanticObjectId(data.graph_id)
            except (TypeError, ValueError):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid graph_id")
        chat = await self.repo.create(user.id, node_id=node_id, chat_type=data.chat_type, graph_id=graph_id)
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

    async def get_or_create_planning_chat(self, user: User, graph_id: str) -> PlanningChatRead:
        try:
            graph_oid = PydanticObjectId(graph_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid graph_id")
        chat = await self.repo.get_planning_chat_by_graph(user.id, graph_oid)
        if chat is None:
            chat = await self.repo.create(user.id, chat_type="planning", graph_id=graph_oid)
        messages = await self.repo.get_messages(chat.id)
        return PlanningChatRead(
            id=str(chat.id),
            messages=[ChatMessageRead.model_validate(m) for m in messages],
        )

    async def save_planning_message(
        self, user: User, graph_id: str, data: ChatMessageCreate
    ) -> ChatMessageRead:
        try:
            graph_oid = PydanticObjectId(graph_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid graph_id")
        chat = await self.repo.get_planning_chat_by_graph(user.id, graph_oid)
        if chat is None:
            chat = await self.repo.create(user.id, chat_type="planning", graph_id=graph_oid)
        msg = await self.repo.create_message(chat.id, data.role, data.content)
        return ChatMessageRead.model_validate(msg)
