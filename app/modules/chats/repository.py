from beanie import PydanticObjectId

from app.modules.chats.models import Chat, ChatMessage


class ChatRepository:

    async def get_by_id_and_owner(
        self,
        chat_id: PydanticObjectId | str,
        user_id: PydanticObjectId,
    ) -> Chat | None:
        try:
            object_id = PydanticObjectId(chat_id)
        except (TypeError, ValueError):
            return None
        return await Chat.find_one(Chat.id == object_id, Chat.user_id == user_id)

    async def get_all_by_owner_and_node(
        self,
        user_id: PydanticObjectId,
        node_id: PydanticObjectId,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Chat]:
        return (
            await Chat.find(Chat.user_id == user_id, Chat.node_id == node_id)
            .sort("-created_at")
            .skip(skip)
            .limit(limit)
            .to_list()
        )

    async def get_planning_chat_by_graph(
        self,
        user_id: PydanticObjectId,
        graph_id: PydanticObjectId,
    ) -> Chat | None:
        return await Chat.find_one(
            Chat.user_id == user_id,
            Chat.graph_id == graph_id,
            Chat.chat_type == "planning",
        )

    async def create(
        self,
        user_id: PydanticObjectId,
        node_id: PydanticObjectId | None = None,
        chat_type: str = "theory",
        graph_id: PydanticObjectId | None = None,
    ) -> Chat:
        chat = Chat(user_id=user_id, node_id=node_id, graph_id=graph_id, chat_type=chat_type)
        return await chat.insert()

    async def create_message(
        self,
        chat_id: PydanticObjectId,
        role: str,
        content: str,
    ) -> ChatMessage:
        msg = ChatMessage(chat_id=chat_id, role=role, content=content)
        return await msg.insert()

    async def delete(self, chat: Chat) -> None:
        await ChatMessage.find(ChatMessage.chat_id == chat.id).delete()
        await chat.delete()

    async def get_messages(self, chat_id: PydanticObjectId) -> list[ChatMessage]:
        return (
            await ChatMessage.find(ChatMessage.chat_id == chat_id)
            .sort("created_at")
            .to_list()
        )
