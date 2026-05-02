from typing import Any, cast

from app.advice.models import AdviceResponse
from app.advice.repository import get_latest_advice
from app.chat.models import ChatMessage, ChatMessageRequest, ChatMessageResponse, ChatRole
from app.chat.repository import append_message, list_messages
from app.core.errors import NotFoundError
from app.core.settings import Settings
from app.db.connection import connect
from app.db.ids import new_id
from app.guardrails.pipeline import GuardrailPipeline
from app.homes.repository import get_home as get_home_record
from app.homes.schemas import HomeProfile
from app.llm.client import ChatSource as LLMChatSource
from app.llm.client import LLMMessage
from app.llm.prompts import PromptBuilder
from app.llm.provider import create_llm_client
from app.llm.response_validator import ResponseValidator


def _home_profile_from_record(record: dict[str, Any]) -> HomeProfile:
    return HomeProfile(
        id=str(record["id"]),
        name=str(record["name"]),
        build_period=record["build_period"],
        home_size=record["home_size"],
        residents=record["residents"],
        heating_system=record["heating_system"],
        has_ev=bool(record["has_ev"]),
        created_at=str(record["created_at"]),
        updated_at=str(record["updated_at"]),
    )


def _chat_message_from_record(record: dict[str, Any]) -> ChatMessage:
    return ChatMessage(
        id=str(record["id"]),
        home_id=str(record["home_id"]),
        role=record["role"],
        source=record["source"],
        content=str(record["content"]),
        created_at=str(record["created_at"]),
    )


def get_history(database_url: str, home_id: str) -> list[ChatMessage]:
    with connect(database_url) as connection:
        if get_home_record(connection, home_id) is None:
            raise NotFoundError("Home profile was not found.")
        records = list_messages(connection, home_id)
    return [_chat_message_from_record(record) for record in records]


def send_message(
    settings: Settings, home_id: str, request: ChatMessageRequest
) -> ChatMessageResponse:
    with connect(settings.database_url) as connection:
        home_record = get_home_record(connection, home_id)
        if home_record is None:
            raise NotFoundError("Home profile was not found.")

        home = _home_profile_from_record(home_record)
        guardrails = GuardrailPipeline(connection=connection)
        input_result = guardrails.run_input_hooks(home, request.source.value, request.message)
        history_before_user = list_messages(connection, home_id)
        user_message = append_message(
            connection,
            {
                "id": new_id("msg"),
                "home_id": home_id,
                "role": ChatRole.USER.value,
                "source": input_result.source,
                "content": input_result.original_message,
            },
        )

        raw_response = create_llm_client(settings).chat(
            _build_messages(
                home_record=home_record,
                home=home,
                history=[
                    *history_before_user,
                    user_message,
                ],
                latest_advice=_latest_advice_response(get_latest_advice(connection, home_id)),
                scrubbed_message=input_result.scrubbed_message,
                source=input_result.source,
            ),
            source=cast(LLMChatSource, input_result.source),
        )
        assistant_content = ResponseValidator().validate_chat_response(raw_response)
        assistant_content = guardrails.run_output_hooks(
            home,
            input_result.source,
            assistant_content,
        )
        assistant_message = append_message(
            connection,
            {
                "id": new_id("msg"),
                "home_id": home_id,
                "role": ChatRole.ASSISTANT.value,
                "source": input_result.source,
                "content": assistant_content,
            },
        )

    return ChatMessageResponse(
        user_message=_chat_message_from_record(user_message),
        assistant_message=_chat_message_from_record(assistant_message),
    )


def _build_messages(
    *,
    home_record: dict[str, Any],
    home: HomeProfile,
    history: list[dict[str, Any]],
    latest_advice: AdviceResponse | None,
    scrubbed_message: str,
    source: str,
) -> list[LLMMessage]:
    return PromptBuilder().build_chat_messages(
        home=home,
        ai_context=[str(item) for item in home_record["ai_context"]],
        latest_advice=latest_advice,
        history=[
            {
                "role": str(message["role"]),
                "source": str(message["source"]),
                "content": str(message["content"]),
            }
            for message in history
        ],
        current_source=cast(LLMChatSource, source),
        scrubbed_message=scrubbed_message,
    )


def _latest_advice_response(record: dict[str, Any] | None) -> AdviceResponse | None:
    if record is None:
        return None
    return AdviceResponse(
        summary=str(record["summary"]),
        areas=record["areas"],
        disclaimer=str(record["disclaimer"]),
    )
