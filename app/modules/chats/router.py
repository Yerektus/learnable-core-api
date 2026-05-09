from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status

from app.modules.auth.dependencies import current_active_user
from app.modules.chats.dependencies import get_chat_service
from app.modules.chats.schemas import ChatCreate, ChatMessageRead, ChatRead
from app.modules.chats.service import ChatService
from app.modules.users.models import User

router = APIRouter(tags=["chats"])


@router.post("", response_model=ChatRead, status_code=status.HTTP_201_CREATED, summary="Create chat session")
async def create_chat(
    node_id: str = Query(...),
    chat_type: Literal["theory", "task"] = Query(default="theory"),
    user: User = Depends(current_active_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatRead:
    return await service.create_chat(user, ChatCreate(node_id=node_id, chat_type=chat_type))


@router.get("", response_model=list[ChatRead], summary="List chats for a node")
async def list_chats(
    node_id: str = Query(...),
    user: User = Depends(current_active_user),
    service: ChatService = Depends(get_chat_service),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[ChatRead]:
    return await service.list_chats(user, node_id, skip=skip, limit=limit)


@router.get("/{chat_id}/messages", response_model=list[ChatMessageRead], summary="Get chat message history")
async def get_chat_messages(
    chat_id: str,
    user: User = Depends(current_active_user),
    service: ChatService = Depends(get_chat_service),
) -> list[ChatMessageRead]:
    return await service.get_messages(user, chat_id)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete chat and all messages")
async def delete_chat(
    chat_id: str,
    user: User = Depends(current_active_user),
    service: ChatService = Depends(get_chat_service),
) -> Response:
    await service.delete_chat(user, chat_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
