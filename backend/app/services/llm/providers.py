from app.core.config import settings
from app.services.llm.base import BaseLLMProvider
from app.services.llm.openai_provider import OpenAILLMProvider
from app.services.llm.rule_based import RuleBasedLLMProvider


def get_llm_provider() -> BaseLLMProvider:
    provider_name = settings.llm_provider.strip().lower()

    if provider_name == "rule_based":
        return RuleBasedLLMProvider()

    if provider_name == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        return OpenAILLMProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
