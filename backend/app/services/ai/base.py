from abc import ABC, abstractmethod
from typing import Any


class AIProviderError(RuntimeError):
    pass


class AIProvider(ABC):
    @abstractmethod
    async def chat_json(self, messages: list[dict[str, str]], schema_hint: dict[str, Any]) -> dict[str, Any]:
        """Return a JSON object from a model response."""
