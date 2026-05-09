from app.core.config import settings
from app.services.ai.base import AIProvider, AIProviderError
from app.services.ai.openai_compatible import OpenAICompatibleProvider


def get_ai_provider() -> AIProvider:
    if settings.ai_provider in {"deepseek", "openai_compatible"}:
        return OpenAICompatibleProvider()
    raise AIProviderError(f"不支持的 AI_PROVIDER：{settings.ai_provider}")
