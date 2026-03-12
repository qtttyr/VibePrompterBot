import json
from html import escape
import re
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from google.genai import errors as genai_errors

from src.config import load_settings
from src.keyboards.inline import generate_kb
from src.services.gemini_api import GeminiClient
from src.services.grok_api import GrokClient
from src.services.prompt_engine import prompt_engine
from src.utils.db import db
from src.utils.states import PromptGen


router = Router()


logger = logging.getLogger(__name__)


TELEGRAM_TEXT_LIMIT = 4096

def _split_text(text: str, limit: int) -> list[str]:
    if limit <= 0:
        return [text]
    if len(text) <= limit:
        return [text]

    parts: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= limit:
            parts.append(remaining)
            break

        cut = remaining.rfind("\n", 0, limit)
        if cut <= 0:
            cut = limit
        parts.append(remaining[:cut])
        remaining = remaining[cut:]
        if remaining.startswith("\n"):
            remaining = remaining[1:]

    return parts


async def _send_pre_block(
    message: Message,
    title_html: str,
    content: str,
    *,
    limit: int = TELEGRAM_TEXT_LIMIT,
) -> None:
    title = f"{title_html}\n" if title_html else ""
    wrapper_overhead = len(title) + len("<pre></pre>")
    safe_payload_limit = max(1, limit - wrapper_overhead)

    escaped = escape(str(content))
    chunks = _split_text(escaped, safe_payload_limit)
    total = len(chunks)
    for idx, chunk in enumerate(chunks, 1):
        prefix = title
        if total > 1:
            prefix = f"{title_html} <b>({idx}/{total})</b>\n"
        await message.answer(f"{prefix}<pre>{chunk}</pre>")


def _render_light_md_to_html(text: str) -> str:
    s = escape(str(text))

    s = re.sub(r"^\*\s+", "• ", s, flags=re.MULTILINE)
    s = re.sub(r"^\-\s+", "• ", s, flags=re.MULTILINE)

    # code first
    s = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", s)

    # bold / italic (simple, non-nested)
    s = re.sub(r"\*\*([^*\n]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\*([^*\n]+)\*", r"<i>\1</i>", s)

    return s


def _validate_result(result: dict, *, editor: str) -> tuple[bool, str]:
    required = ["system_prompt", "cursorrules", "windsurfrules", "notes"]
    for k in required:
        if k not in result:
            return False, f"missing_key:{k}"
        # notes can be a list — coerce it to a string
        if k == "notes" and isinstance(result[k], list):
            result[k] = "\n".join(f"• {item}" for item in result[k])
        if not isinstance(result[k], str):
            return False, f"non_string:{k}"

    system_prompt = (result.get("system_prompt") or "").strip()
    if len(system_prompt) < 40:
        return False, "system_prompt_too_short"
    if system_prompt.lower().startswith("you are a helpful assistant"):
        return False, "generic_system_prompt"

    # We no longer reject if non-selected editor fields are non-empty;
    # we simply ignore them during rendering (see generate handler below).
    return True, "ok"


def _extract_json_object(text: str) -> str:
    raw = (text or "").strip()
    if "```" in raw:
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw.strip())

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1].strip()
    return raw


def _try_parse_json(text: str) -> dict:
    candidate = _extract_json_object(text)
    return json.loads(candidate)


def _attempt_simple_json_repair(text: str) -> str:
    s = _extract_json_object(text)
    # Common Gemini issue: smart quotes
    s = s.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    # Remove trailing commas before } or ]
    s = re.sub(r",\s*([}\]])", r"\1", s)
    # Try to fix unterminated strings by escaping internal quotes (basic heuristic)
    lines = s.splitlines()
    fixed_lines = []
    for line in lines:
        # Simple heuristic: if a line contains an odd number of unescaped double quotes, escape the last one
        # This is crude but helps with common Gemini truncation issues
        if line.count('"') % 2 == 1:
            # Escape the last quote to terminate the string
            line = line.rsplit('"', 1)[0] + r'\"'
        fixed_lines.append(line)
    s = "\n".join(fixed_lines)
    return s



@router.message(PromptGen.idea)
async def capture_idea(message: Message, state: FSMContext) -> None:
    idea = (message.text or "").strip()
    if not idea:
        await message.answer("Пожалуйста, опиши задачу текстом 📝")
        return

    await state.update_data(idea=idea)
    data = await state.get_data()

    # Экранируем для вывода в Telegram
    editor = escape(str(data.get("editor", "")))
    stack = escape(str(data.get("stack", "")))
    model = escape(str(data.get("model", "")))
    idea_escaped = escape(idea)
    project_info = escape(str(data.get("project_info", "")))

    await message.answer(
        "✨ <b>Все данные собраны!</b> ✨\n\n"
        f"📝 <b>Проект:</b> {project_info}\n"
        f"🚀 <b>Редактор:</b> {editor}\n"
        f"⚛️ <b>Стек:</b> {stack}\n"
        f"🤖 <b>Модель:</b> {model}\n"
        f"💡 <b>Идея:</b> {idea_escaped}\n\n"
        "Нажми <b>Generate</b>, чтобы я сотворил магию! ✨",
        reply_markup=generate_kb(),
    )


@router.callback_query(F.data == "action:generate")
async def generate(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    
    # ── Daily limit check ──────────────────────────────────────────────────
    can_generate = await db.check_limit(user_id)
    if not can_generate:
        await callback.answer("❌ Лимит исчерпан", show_alert=True)
        usage_count = await db.get_user_usage(user_id)
        await callback.message.answer(
            "🚫 <b>Дневной лимит исчерпан.</b>\n\n"
            f"📊 Использовано сегодня: <b>{usage_count}/2</b> генераций\n\n"
            "⏰ Лимит сбрасывается в <b>00:00</b> по UTC.\n"
            "💡 <i>В бесплатной версии доступно 2 генерации в день.</i>\n\n"
            "Возвращайся завтра — буду ждать! 🙌"
        )
        return
    # ──────────────────────────────────────────────────────────────────────

    await callback.answer("⏳ Генерирую промпты... Это займет 10-20 секунд.")
    await callback.message.answer("🤖 <b>Модель приступила к работе...</b>")

    data = await state.get_data()
    settings = load_settings()
    
    model_name = str(data.get("model") or "gemini-2.5-flash")
    GROK_MODELS = {"llama-3.3-70b-versatile"}
    is_grok = model_name in GROK_MODELS

    if is_grok:
        if not settings.grok_api_key:
            await callback.message.answer("❌ GROK_API_KEY не настроен!")
            return
    else:
        if not settings.gemini_api_key:
            await callback.message.answer("❌ GEMINI_API_KEY не настроен!")
            return
    
    # Собираем промпт через PromptEngine (Special Prompts + Project Info + Idea)
    full_prompt = await prompt_engine.build_prompt(data)

    response_schema = {
        "type": "object",
        "properties": {
            "system_prompt": {"type": "string"},
            "cursorrules": {"type": "string"},
            "windsurfrules": {"type": "string"},
            "notes": {"type": "string"},
        },
        "required": ["system_prompt", "cursorrules", "windsurfrules", "notes"],
    }
    
    try:
        await callback.message.answer("🧩 <b>Проверяю формат ответа...</b>")

        # 1) Основной вызов модели: либо Gemini, либо Groq
        if is_grok:
            client_grok = GrokClient(api_key=settings.grok_api_key or "", model=model_name)
            response = await client_grok.generate_text(
                full_prompt,
                max_output_tokens=4000,
            )
        else:
            client = GeminiClient(api_key=settings.gemini_api_key or "", model=model_name)
            try:
                response = await client.generate_text(
                    full_prompt,
                    max_output_tokens=4000,
                    response_schema=response_schema,
                )
            except genai_errors.ServerError as exc:
                # Fallback: если Gemini перегружен, а Groq настроен — пробуем Groq
                logger.warning("Gemini ServerError, trying Groq (Groq.com) fallback: %s", exc)
                if settings.grok_api_key:
                    await callback.message.answer(
                        "⚠️ <b>Gemini сейчас перегружен.</b>\n"
                        "Переключаюсь на Groq (Llama 3.3 70B на groq.com)..."
                    )
                    client_grok = GrokClient(api_key=settings.grok_api_key, model="llama-3.3-70b-versatile")
                    response = await client_grok.generate_text(
                        full_prompt,
                        max_output_tokens=4000,
                    )
                    is_grok = True
                else:
                    raise

        raw_text = (response.text or "").strip()
        if raw_text:
            logger.warning(
                "%s raw_text prefix: %s",
                "Groq" if is_grok else "Gemini",
                raw_text[:400].replace("\n", "\\n"),
            )
        else:
            logger.warning(
                "%s returned empty text. raw keys=%s",
                "Groq" if is_grok else "Gemini",
                list((response.raw or {}).keys()),
            )
            await callback.message.answer(
                "❌ <b>Модель вернула пустой ответ.</b>\n"
                "Это похоже на временный сбой/лимит/блокировку. Попробуй ещё раз через 30-60 секунд."
            )
            return

        # 1) Пытаемся взять уже распарсенный ответ от клиента Gemini
        if response.parsed is not None:
            # SDK с response_schema гарантирует структуру object → dict
            result = response.parsed  # type: ignore[assignment]
            if not isinstance(result, dict):
                # На всякий случай приводим к словарю через JSON
                result = json.loads(json.dumps(result, ensure_ascii=False))
        else:
            # 2) Фолбек: парсим текст как JSON (со старым аккуратным ремонтом)
            try:
                result = _try_parse_json(raw_text)
            except json.JSONDecodeError:
                try:
                    result = _try_parse_json(_attempt_simple_json_repair(raw_text))
                except json.JSONDecodeError:
                    await callback.message.answer("🔁 <b>Перегенерирую ответ (1/1) — предыдущий был некорректным...</b>")
                    regen_prompt = (
                        full_prompt
                        + "\n\nIMPORTANT: Return ONLY valid JSON. Do not include markdown fences. "
                        + "system_prompt must be specific to the project and task (never generic). "
                        + "All string values must be properly terminated and escaped."
                    )
                    regen = await client.generate_text(
                        regen_prompt,
                        max_output_tokens=4000,
                        response_schema=response_schema,
                    )
                    # При перегенерации тоже в приоритете используем structured output
                    if regen.parsed is not None:
                        result = regen.parsed  # type: ignore[assignment]
                        if not isinstance(result, dict):
                            result = json.loads(json.dumps(result, ensure_ascii=False))
                    else:
                        regen_text = (regen.text or "").strip()
                        if regen_text:
                            logger.warning(
                                "Gemini regen prefix: %s",
                                regen_text[:400].replace("\n", "\\n"),
                            )
                        try:
                            # ещё одна попытка распарсить как JSON
                            result = _try_parse_json(regen_text)
                        except json.JSONDecodeError:
                            try:
                                result = _try_parse_json(
                                    _attempt_simple_json_repair(regen_text)
                                )
                            except json.JSONDecodeError:
                                logger.exception("Second regeneration JSON parse failed")
                                await callback.message.answer(
                                    "❌ <b>Модель дважды вернула некорректный JSON.</b>\n"
                                    "Попробуй ещё раз через минуту или сократи описание проекта/идеи."
                                )
                                return

                    ok2, _ = _validate_result(result, editor=str(data.get("editor") or ""))
                    if not ok2:
                        await callback.message.answer(
                            "❌ <b>Модель вернула некорректный результат.</b>\n"
                            "Попробуй ещё раз через минуту или сократи описание проекта/идеи."
                        )
                        return
        
        ok, _ = _validate_result(result, editor=str(data.get("editor") or ""))
        await callback.message.answer("✅ <b>Готово! Твои инструменты:</b>")
        
        if result.get("system_prompt"):
            await _send_pre_block(
                callback.message,
                "📜 <b>System Prompt:</b>",
                str(result["system_prompt"]),
            )
            
        if result.get("cursorrules") and data.get("editor") == "cursor":
            await _send_pre_block(
                callback.message,
                "🛠 <b>.cursorrules:</b>",
                str(result["cursorrules"]),
            )

        if result.get("windsurfrules") and data.get("editor") == "windsurf":
            await _send_pre_block(
                callback.message,
                "🛠 <b>.windsurfrules:</b>",
                str(result["windsurfrules"]),
            )
            
        if result.get("notes"):
            notes_html = _render_light_md_to_html(str(result["notes"]))
            await callback.message.answer(f"📝 <b>Notes:</b>\n{notes_html}")

        usage = response.usage
        prompt_tokens = None
        output_tokens = None
        total_tokens = None
        if isinstance(usage, dict):
            prompt_tokens = usage.get("prompt_token_count")
            output_tokens = usage.get("candidates_token_count")
            total_tokens = usage.get("total_token_count")

        if total_tokens is None:
            approx_total = max(1, (len(full_prompt) + len(response.text)) // 4)
            usage_line = f"📊 <b>Токены:</b> ~{approx_total} (оценка)"
        else:
            parts = []
            if prompt_tokens is not None:
                parts.append(f"in {prompt_tokens}")
            if output_tokens is not None:
                parts.append(f"out {output_tokens}")
            parts.append(f"total {total_tokens}")
            usage_line = "📊 <b>Токены:</b> " + " | ".join(parts)
        await callback.message.answer(usage_line)

        # 3. Cleanup and finish
        await db.save_generation(user_id, data)
        await db.increment_usage(user_id)
        await state.clear()

    except Exception:
        logger.exception("Generation failed")
        await callback.message.answer(
            "❌ <b>Ошибка генерации.</b>\n"
            "Это похоже на временный сбой API или неожиданный формат ответа. Попробуй ещё раз через 30-60 секунд."
        )
