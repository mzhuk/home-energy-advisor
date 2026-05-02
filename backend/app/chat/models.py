from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ChatRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatSource(StrEnum):
    GLOBAL = "global"
    SOLAR = "solar"
    BATTERY = "battery"
    HEAT_PUMP = "heat_pump"
    SMART_CONTROLS = "smart_controls"
    EV_CHARGING = "ev_charging"


class ChatMessageRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Are smaller solar panels useful for my roof?",
                "source": "solar",
            }
        }
    )

    message: str = Field(min_length=1, max_length=2000)
    source: ChatSource = ChatSource.GLOBAL


class ChatMessage(BaseModel):
    id: str
    home_id: str
    role: ChatRole
    source: ChatSource
    content: str
    created_at: str


class ChatMessageResponse(BaseModel):
    user_message: ChatMessage
    assistant_message: ChatMessage

