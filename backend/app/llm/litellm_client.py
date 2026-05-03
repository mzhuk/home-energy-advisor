from collections.abc import Sequence
from importlib.util import find_spec
from typing import Any

import litellm

from app.core.errors import (
    LLMAuthError,
    LLMBadResponseError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from app.core.settings import LLMProvider, Settings
from app.llm.client import ChatSource, LLMMessage


class LiteLLMClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate_advice(
        self, messages: Sequence[LLMMessage], response_schema: dict[str, Any]
    ) -> str:
        return self._completion_text(
            messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "home_energy_advice",
                    "schema": response_schema,
                    "strict": True,
                },
            },
        )

    def chat(self, messages: Sequence[LLMMessage], *, source: ChatSource = "global") -> str:
        return self._completion_text(messages)

    def _completion_text(
        self,
        messages: Sequence[LLMMessage],
        *,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        try:
            response = litellm.completion(
                **self._completion_kwargs(messages, response_format=response_format)
            )
        except litellm.AuthenticationError as exc:
            raise LLMAuthError() from exc
        except litellm.Timeout as exc:
            raise LLMTimeoutError() from exc
        except litellm.BadRequestError as exc:
            raise LLMBadResponseError(_provider_error_message(exc)) from exc
        except (litellm.RateLimitError, litellm.APIConnectionError, litellm.APIError) as exc:
            raise LLMUnavailableError() from exc
        except Exception as exc:
            message = _provider_error_message(exc)
            if "context length" in message.lower() or "token" in message.lower():
                raise LLMBadResponseError(
                    "The current conversation is too long for the configured local model."
                ) from exc
            if "tenacity import failed" in message.lower():
                raise LLMUnavailableError(
                    "The configured model provider retry layer is unavailable."
                ) from exc
            raise LLMUnavailableError() from exc

        content = _extract_content(response)
        if not content:
            raise LLMUnavailableError("The configured model provider returned an empty response.")
        return content

    def _completion_kwargs(
        self,
        messages: Sequence[LLMMessage],
        *,
        response_format: dict[str, Any] | None,
    ) -> dict[str, Any]:
        model, api_key, api_base = _provider_config(self._settings)
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [message.to_provider_dict() for message in messages],
            "api_key": api_key,
            "timeout": self._settings.llm_timeout_seconds,
            "num_retries": _available_retry_count(self._settings.llm_max_retries),
            "temperature": self._settings.llm_temperature,
        }
        if api_base:
            kwargs["api_base"] = api_base
        if response_format:
            kwargs["response_format"] = response_format
        return kwargs


def _provider_config(settings: Settings) -> tuple[str, str, str | None]:
    provider: LLMProvider = settings.llm_provider
    if provider == "local":
        return f"openai/{settings.llm_model}", settings.llm_api_key, settings.llm_api_base
    if provider == "openai":
        return settings.openai_model, settings.openai_api_key, None
    if provider == "anthropic":
        return f"anthropic/{settings.anthropic_model}", settings.anthropic_api_key, None
    msg = "LiteLLMClient cannot be used with the fake provider."
    raise ValueError(msg)


def _extract_content(response: Any) -> str:
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, KeyError, TypeError):
        try:
            content = response["choices"][0]["message"]["content"]
        except (IndexError, KeyError, TypeError) as exc:
            raise LLMUnavailableError(
                "The configured model provider returned an unknown shape."
            ) from exc
    return str(content).strip() if content is not None else ""


def _provider_error_message(exc: Exception) -> str:
    return str(exc)


def _available_retry_count(configured_retries: int) -> int:
    if configured_retries <= 0:
        return 0
    if find_spec("tenacity") is None:
        return 0
    return configured_retries
