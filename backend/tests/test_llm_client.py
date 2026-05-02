from types import SimpleNamespace
from typing import Any

import litellm
import pytest
from pytest_mock import MockerFixture

from app.advice.deterministic import build_deterministic_advice
from app.advice.models import AdviceResponse
from app.core.errors import LLMAuthError, LLMTimeoutError, LLMUnavailableError
from app.core.settings import Settings
from app.homes.schemas import BuildPeriod, HeatingSystem, HomeProfile, HomeSize, Residents
from app.llm.client import LLMMessage
from app.llm.fake_provider import DEMO_NOTE, FakeLLMClient, fake_advice_as_dict
from app.llm.litellm_client import LiteLLMClient
from app.llm.provider import create_llm_client


def home_profile(*, has_ev: bool = True) -> HomeProfile:
    return HomeProfile(
        id="home_test",
        name="Test home",
        build_period=BuildPeriod.PRE_1978,
        home_size=HomeSize.Y100_200,
        residents=Residents.THREE_FOUR,
        heating_system=HeatingSystem.GAS,
        has_ev=has_ev,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )


def litellm_response(content: str) -> Any:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
    )


def test_fake_provider_returns_schema_valid_profile_specific_advice() -> None:
    deterministic = build_deterministic_advice(home_profile(has_ev=True), ai_context=["context"])

    raw = FakeLLMClient().generate_advice(
        [LLMMessage(role="user", content=deterministic.model_dump_json())],
        AdviceResponse.model_json_schema(),
    )

    advice = AdviceResponse.model_validate_json(raw)
    assert "ev_charging" in [area.area_id for area in advice.areas]
    assert DEMO_NOTE in advice.disclaimer


def test_fake_provider_default_advice_is_schema_valid() -> None:
    advice = AdviceResponse.model_validate(fake_advice_as_dict())

    assert advice.summary
    assert len(advice.areas) == 4
    assert DEMO_NOTE in advice.disclaimer


def test_fake_provider_chat_is_deterministic_per_source() -> None:
    first = FakeLLMClient().chat([], source="solar")
    second = FakeLLMClient().chat([], source="solar")

    assert first == second
    assert "For solar" in first
    assert DEMO_NOTE in first


def test_provider_factory_uses_fake_client_for_fake_provider() -> None:
    client = create_llm_client(Settings(llm_provider="fake"))

    assert isinstance(client, FakeLLMClient)


def test_litellm_local_provider_uses_openai_compatible_api_base(
    mocker: MockerFixture,
) -> None:
    completion = mocker.patch(
        "app.llm.litellm_client.litellm.completion",
        return_value=litellm_response("ok"),
    )
    settings = Settings(
        llm_provider="local",
        llm_model="local-demo",
        llm_api_base="http://localhost:1234/v1",
        llm_api_key="local-key",
        llm_timeout_seconds=12,
        llm_max_retries=2,
        llm_temperature=0.1,
    )

    response = LiteLLMClient(settings).chat([LLMMessage(role="user", content="Hello")])

    assert response == "ok"
    completion.assert_called_once()
    kwargs = completion.call_args.kwargs
    assert kwargs["model"] == "openai/local-demo"
    assert kwargs["api_base"] == "http://localhost:1234/v1"
    assert kwargs["api_key"] == "local-key"
    assert kwargs["timeout"] == 12
    assert kwargs["num_retries"] == 2
    assert kwargs["temperature"] == 0.1
    assert kwargs["messages"] == [{"role": "user", "content": "Hello"}]


def test_litellm_openai_provider_uses_openai_model(mocker: MockerFixture) -> None:
    completion = mocker.patch(
        "app.llm.litellm_client.litellm.completion",
        return_value={"choices": [{"message": {"content": "ok"}}]},
    )
    settings = Settings(llm_provider="openai", openai_api_key="openai-key")

    response = LiteLLMClient(settings).chat([LLMMessage(role="user", content="Hello")])

    assert response == "ok"
    kwargs = completion.call_args.kwargs
    assert kwargs["model"] == settings.openai_model
    assert kwargs["api_key"] == "openai-key"
    assert "api_base" not in kwargs


def test_litellm_anthropic_provider_prefixes_model(mocker: MockerFixture) -> None:
    completion = mocker.patch(
        "app.llm.litellm_client.litellm.completion",
        return_value=litellm_response("ok"),
    )
    settings = Settings(llm_provider="anthropic", anthropic_api_key="anthropic-key")

    response = LiteLLMClient(settings).chat([LLMMessage(role="user", content="Hello")])

    assert response == "ok"
    kwargs = completion.call_args.kwargs
    assert kwargs["model"] == f"anthropic/{settings.anthropic_model}"
    assert kwargs["api_key"] == "anthropic-key"


def test_litellm_advice_calls_include_json_schema(mocker: MockerFixture) -> None:
    completion = mocker.patch(
        "app.llm.litellm_client.litellm.completion",
        return_value=litellm_response('{"summary":"ok","areas":[],"disclaimer":"ok"}'),
    )

    LiteLLMClient(Settings()).generate_advice(
        [LLMMessage(role="user", content="Advice")],
        AdviceResponse.model_json_schema(),
    )

    response_format = completion.call_args.kwargs["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["name"] == "home_energy_advice"
    assert response_format["json_schema"]["schema"]["title"] == "AdviceResponse"


@pytest.mark.parametrize(
    ("provider_error", "app_error"),
    [
        (
            litellm.AuthenticationError("auth", "openai", "model"),
            LLMAuthError,
        ),
        (
            litellm.Timeout("timeout", "model", "openai"),
            LLMTimeoutError,
        ),
        (
            litellm.APIConnectionError("unavailable", "openai", "model"),
            LLMUnavailableError,
        ),
        (
            litellm.APIError(500, "unavailable", "openai", "model"),
            LLMUnavailableError,
        ),
        (
            litellm.RateLimitError("rate", "openai", "model"),
            LLMUnavailableError,
        ),
    ],
)
def test_litellm_errors_are_normalized(
    mocker: MockerFixture,
    provider_error: Exception,
    app_error: type[Exception],
) -> None:
    mocker.patch("app.llm.litellm_client.litellm.completion", side_effect=provider_error)

    with pytest.raises(app_error):
        LiteLLMClient(Settings()).chat([LLMMessage(role="user", content="Hello")])
