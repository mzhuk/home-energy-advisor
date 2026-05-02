from fastapi import APIRouter, Request, status

from app.chat.models import ChatMessage, ChatMessageRequest, ChatMessageResponse
from app.chat.service import get_history, send_message
from app.core.settings import Settings

router = APIRouter(prefix="/homes/{home_id}/chat", tags=["chat"])


def _settings(request: Request) -> Settings:
    return request.app.state.settings


@router.get("", response_model=list[ChatMessage])
def get_home_chat(request: Request, home_id: str) -> list[ChatMessage]:
    return get_history(_settings(request).database_url, home_id)


@router.post("", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
def send_home_chat_message(
    request: Request, home_id: str, payload: ChatMessageRequest
) -> ChatMessageResponse:
    return send_message(_settings(request), home_id, payload)

