from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol

LLMRole = Literal["system", "user", "assistant"]
ChatSource = Literal["global", "solar", "battery", "heat_pump", "smart_controls", "ev_charging"]


@dataclass(frozen=True)
class LLMMessage:
    role: LLMRole
    content: str

    def to_provider_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class LLMClient(Protocol):
    def generate_advice(
        self, messages: Sequence[LLMMessage], response_schema: dict[str, Any]
    ) -> str:
        raise NotImplementedError

    def chat(self, messages: Sequence[LLMMessage], *, source: ChatSource = "global") -> str:
        raise NotImplementedError
