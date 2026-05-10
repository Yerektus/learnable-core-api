from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status

from app.modules.auth.dependencies import current_active_user
from app.modules.chats.dependencies import get_chat_service
from app.modules.chats.schemas import (
    ChatCreate,
    ChatMessageCreate,
    ChatMessageRead,
    ChatRead,
    PlanningChatRead,
)
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


@router.get(
    "/graphs/{graph_id}/planning-chat",
    response_model=PlanningChatRead,
    summary="Get or create planning chat for a graph",
)
async def get_planning_chat(
    graph_id: str,
    user: User = Depends(current_active_user),
    service: ChatService = Depends(get_chat_service),
) -> PlanningChatRead:
    return await service.get_or_create_planning_chat(user, graph_id)


@router.post(
    "/graphs/{graph_id}/planning-chat/messages",
    response_model=ChatMessageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Save a message to the planning chat",
)
async def save_planning_message(
    graph_id: str,
    data: ChatMessageCreate,
    user: User = Depends(current_active_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatMessageRead:
    return await service.save_planning_message(user, graph_id, data)
