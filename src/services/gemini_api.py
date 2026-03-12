from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
import json

from google import genai


@dataclass(frozen=True)
class GeminiResponse:
    text: str
    usage: Optional[dict[str, Any]] = None
    raw: Optional[dict[str, Any]] = None
    parsed: Optional[Any] = None


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._api_key = api_key
        self._model_name = model

        self._client = genai.Client(api_key=self._api_key)

    async def generate_text(
        self,
        prompt: str,
        *,
        max_output_tokens: int = 900,
        response_schema: Optional[dict[str, Any]] = None,
    ) -> GeminiResponse:
        config: dict[str, Any] = {
            "max_output_tokens": max_output_tokens,
            "temperature": 0.7,
            "top_p": 0.9,
        }
        if response_schema is not None:
            # Включаем структурированный вывод
            config["response_mime_type"] = "application/json"
            config["response_schema"] = response_schema

        result = await self._client.aio.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=config,
        )

        parsed: Optional[Any] = getattr(result, "parsed", None)

        # Текст: если есть parsed, то это валидный JSON‑объект
        if parsed is not None:
            text: str = json.dumps(parsed, ensure_ascii=False)
        else:
            text = getattr(result, "text", "") or ""

        # usage → словарь
        usage_meta = getattr(result, "usage_metadata", None)
        usage: Optional[dict[str, Any]] = None
        if usage_meta is not None:
            if isinstance(usage_meta, dict):
                usage = usage_meta
            elif hasattr(usage_meta, "model_dump"):
                usage = usage_meta.model_dump()
            elif hasattr(usage_meta, "to_dict"):
                usage = usage_meta.to_dict()
            else:
                usage = {
                    "prompt_token_count": getattr(usage_meta, "prompt_token_count", None),
                    "candidates_token_count": getattr(usage_meta, "candidates_token_count", None),
                    "total_token_count": getattr(usage_meta, "total_token_count", None),
                }

        # Полный сырой дамп
        raw: Optional[dict[str, Any]] = None
        try:
            raw = json.loads(result.model_dump_json())
        except Exception:
            raw = None

        if not text and raw is not None:
            text = raw.get("text") or ""
            if not text:
                text = json.dumps(raw, ensure_ascii=False)

        return GeminiResponse(text=str(text), usage=usage, raw=raw, parsed=parsed)
