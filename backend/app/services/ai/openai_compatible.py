import json
from typing import Any

import httpx

from app.core.config import settings
from app.services.ai.base import AIProvider, AIProviderError


class OpenAICompatibleProvider(AIProvider):
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ai_base_url).rstrip("/")
        self.api_key = api_key or settings.ai_api_key
        self.model = model or settings.ai_model
        self.timeout_seconds = timeout_seconds or settings.ai_timeout_seconds

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        schema_hint: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_config()
        payload = {
            "model": self.model,
            "messages": [
                *messages,
                {
                    "role": "system",
                    "content": (
                        "请严格输出 JSON 对象，不要输出 Markdown、代码块或额外解释。"
                        f"JSON 字段参考：{json.dumps(schema_hint, ensure_ascii=False)}"
                    ),
                },
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise AIProviderError(f"AI 接口调用失败：{exc}") from exc

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            raise AIProviderError("AI 响应缺少 message.content")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIProviderError("AI 响应不是合法 JSON") from exc
        if not isinstance(parsed, dict):
            raise AIProviderError("AI 响应 JSON 必须是对象")
        return parsed

    def _validate_config(self) -> None:
        if not self.base_url:
            raise AIProviderError("AI_BASE_URL 未配置")
        if not self.model:
            raise AIProviderError("AI_MODEL 未配置")
        if not self.api_key or self.api_key == "YOUR_DEEPSEEK_API_KEY":
            raise AIProviderError("AI_API_KEY 未配置真实 key")
