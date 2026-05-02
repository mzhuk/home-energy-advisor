from app.core.settings import Settings
from app.llm.client import LLMClient
from app.llm.fake_provider import FakeLLMClient
from app.llm.litellm_client import LiteLLMClient


def create_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_provider == "fake":
        return FakeLLMClient()
    return LiteLLMClient(settings)

