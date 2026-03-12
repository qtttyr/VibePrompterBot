from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
import json

from openai import AsyncOpenAI


@dataclass(frozen=True)
class GrokResponse:
    text: str
    usage: Optional[dict[str, Any]] = None
    raw: Optional[dict[str, Any]] = None
    parsed: Optional[Any] = None


class GrokClient:
    """
    Клиент для Groq (grok.com) через OpenAI-совместимый AsyncOpenAI.
    Использует OpenAI-совместимый endpoint Groq: https://api.groq.com/openai/v1
    """

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile") -> None:
        self._model_name = model
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    async def generate_text(
        self,
        prompt: str,
        *,
        max_output_tokens: int = 900,
    ) -> GrokResponse:
        # Здесь мы просим Grok СТРОГО вернуть JSON-объект по тем же правилам,
        # что и Gemini (PromptEngine уже даёт это в тексте промпта).
        resp = await self._client.chat.completions.create(
            model=self._model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            max_tokens=max_output_tokens,
        )

        # Основной текстовый ответ
        text = (resp.choices[0].message.content or "").strip()

        # usage → обычный dict
        usage_obj = getattr(resp, "usage", None)
        usage: Optional[dict[str, Any]] = None
        if usage_obj is not None:
            if isinstance(usage_obj, dict):
                usage = usage_obj
            elif hasattr(usage_obj, "model_dump"):
                usage = usage_obj.model_dump()
            elif hasattr(usage_obj, "to_dict"):
                usage = usage_obj.to_dict()

        # Полный сырой дамп
        raw: Optional[dict[str, Any]] = None
        try:
            raw = json.loads(resp.model_dump_json())
        except Exception:
            raw = None

        # Для совместимости с интерфейсом GeminiResponse — parsed оставляем None,
        # так как structured output мы здесь не используем.
        return GrokResponse(text=str(text), usage=usage, raw=raw, parsed=None)

