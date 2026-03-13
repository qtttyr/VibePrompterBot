"""Folder Structure Generator — FSM handler.

Flow:
  /structure  or  🗂 Структура button
    → check daily limit (1/day)
    → show saved projects (inline KB)
  fproj:N callback  → pick existing project → show scope KB
  fproj:new callback → ask user to type project → FSM project_pick state
  text in project_pick state → save project → show scope KB
  fscope:X callback → save scope → show summary + confirm KB
  fstruct:generate callback → run AI → send tree + mkdir + notes
  fstruct:cancel callback → clear state, friendly cancel message
"""

import json
import logging
import re
from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.config import load_settings
from src.keyboards.inline import confirm_structure_kb, project_pick_kb, scope_kb
from src.services.folder_engine import folder_engine
from src.services.gemini_api import GeminiClient
from src.utils.db import db
from src.utils.i18n import _
from src.utils.states import FolderGen

router = Router()
logger = logging.getLogger(__name__)

TELEGRAM_LIMIT = 4000  # leave 96-char safety margin below the hard 4096 cap


# ─── Helpers ────────────────────────────────────────────────────────────────

def _split_text(text: str, limit: int = TELEGRAM_LIMIT) -> list[str]:
    """Split text into chunks that fit within Telegram's message size limit."""
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
        remaining = remaining[cut:].lstrip("\n")
    return parts


async def _send_pre(message: Message, title_html: str, content: str) -> None:
    """Send content in <pre> blocks, splitting if needed to stay within limits."""
    overhead = len(title_html) + len("<pre></pre>") + 2   # +2 for newlines
    safe_limit = TELEGRAM_LIMIT - overhead
    escaped = escape(str(content))
    chunks = _split_text(escaped, safe_limit)
    total = len(chunks)
    for idx, chunk in enumerate(chunks, 1):
        header = title_html if total == 1 else f"{title_html} <b>({idx}/{total})</b>"
        await message.answer(f"{header}\n<pre>{chunk}</pre>")


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


def _parse_folder_gen_fallback(text: str) -> dict:
    """Robust fallback parser for folder gen that extracts values using regex.
    Handles truncated responses and literal newlines.
    """
    result = {"tree": "", "mkdir_cmd": "", "notes": ""}
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)

    # Extract tree
    tree_match = re.search(r'"tree"\s*:\s*"(.*?)(?="\s*,\s*"[a-zA-Z_]+"|"\s*\n\s*\}|\n\s*\}|$)', raw, re.DOTALL)
    if tree_match:
        val = tree_match.group(1)
        if val.endswith('"') and not val.endswith('\\"'):
            val = val[:-1]
        result["tree"] = val.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
        
    # Extract mkdir_cmd
    mkdir_match = re.search(r'"mkdir_cmd"\s*:\s*"(.*?)"', raw)
    if mkdir_match:
        result["mkdir_cmd"] = mkdir_match.group(1).replace('\\"', '"')
        
    # Extract notes
    notes_match = re.search(r'"notes"\s*:\s*"(.*?)(?="\s*\n\s*\}|\n\s*\}|$)', raw, re.DOTALL)
    if notes_match:
        val = notes_match.group(1)
        if val.endswith('"') and not val.endswith('\\"'):
            val = val[:-1]
        result["notes"] = val.replace('\\n', '\n').replace('\\"', '"')
        
    return result


def _build_scope_label(scope: str) -> str:
    return {"backend": "🖥 Backend", "frontend": "⚛️ Frontend", "fullstack": "🌐 Fullstack"}.get(scope, scope)


# ─── Entry points ───────────────────────────────────────────────────────────

async def _start_structure_flow(message: Message, state: FSMContext) -> None:
    """Common entry: load projects, show picker."""
    user_id = message.from_user.id

    can_gen = await db.check_folder_gen_limit(user_id)
    if not can_gen:
        await message.answer(
            "🚫 <b>Лимит структуры исчерпан на сегодня.</b>\n\n"
            "📊 Доступно: <b>1 генерация в день</b>.\n"
            "⏰ Сбрасывается в <b>00:00 UTC</b>.\n\n"
            "Возвращайся завтра — сгенерируем новую структуру! 🗂"
        )
        return

    projects = await db.get_user_projects(user_id, limit=5)

    if projects:
        # Store projects list in state so callbacks can look up by index
        await state.update_data(saved_projects=[[p, s] for p, s in projects])
        await state.set_state(FolderGen.scope)   # will be overridden after project pick

        project_list_text = "\n".join(
            f"  {i + 1}. <b>{escape((p or '')[:40])}</b>"
            for i, (p, s) in enumerate(projects)
        )
        await message.answer(
            _("folder_gen_start", lang) + "\n\n" + project_list_text,
            reply_markup=project_pick_kb(projects, lang),
        )
    else:
        # No history — go straight to manual input
        await state.set_state(FolderGen.project_pick)
        no_history_text = (
            "🗂 <b>Structure Generator</b>\n\n"
            "You don't have any saved projects yet.\n\n"
            "📝 Describe your project (stack, what you are building):"
        ) if lang == "en" else (
            "🗂 <b>Генератор структуры папок</b>\n\n"
            "У тебя пока нет сохранённых проектов.\n\n"
            "📝 Опиши свой проект (стек, что строишь):"
        )
        await message.answer(no_history_text)


@router.message(Command("structure"))
async def cmd_structure(message: Message, state: FSMContext) -> None:
    await _start_structure_flow(message, state)


@router.message(F.text == "🗂 Структура")
async def quick_structure(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _start_structure_flow(message, state)


# ─── Project pick ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("fproj:"))
async def pick_project(callback: CallbackQuery, state: FSMContext) -> None:
    choice = callback.data.split(":", 1)[1]
    await callback.answer()

    if choice == "new":
        lang = await db.get_user_language(callback.from_user.id)
        await state.set_state(FolderGen.project_pick)
        prompt_text = (
            "📝 Describe your project in one message (stack, features, etc.):"
            if lang == "en" else
            "📝 Опиши свой проект одним сообщением (что строишь, стек, особенности):"
        )
        await callback.message.edit_text(prompt_text)
        return

    # Existing project by index
    user_id = callback.from_user.id
    lang = await db.get_user_language(user_id)
    data = await state.get_data()
    saved = data.get("saved_projects", [])
    try:
        idx = int(choice)
        project_info, stack = saved[idx]
    except (ValueError, IndexError):
        error_msg = "❌ Project not found. Try again /structure" if lang == "en" else "❌ Проект не найден. Попробуй снова /structure"
        await callback.message.answer(error_msg)
        return

    await state.update_data(project_info=project_info, stack=stack)
    await state.set_state(FolderGen.scope)

    short = (project_info or "")[:50]
    prompt_text = (
        f"✅ Project: <b>{escape(short)}{'…' if len(project_info) > 50 else ''}</b>\n\n"
        "Choose structure type:"
    ) if lang == "en" else (
        f"✅ Проект: <b>{escape(short)}{'…' if len(project_info) > 50 else ''}</b>\n\n"
        "Выбери тип структуры:"
    )
    await callback.message.edit_text(
        prompt_text,
        reply_markup=scope_kb(lang),
    )


@router.message(FolderGen.project_pick)
async def capture_new_project(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = await db.get_user_language(user_id)
    project_info = (message.text or "").strip()
    if not project_info:
        await message.answer("Please describe your project in text 📝" if lang == "en" else "Пожалуйста, опиши проект текстом 📝")
        return

    await state.update_data(project_info=project_info, stack="")
    await state.set_state(FolderGen.scope)
    success_msg = "✅ Project saved!\n\nChoose structure type:" if lang == "en" else "✅ Проект сохранён!\n\nВыбери тип структуры:"
    await message.answer(
        success_msg,
        reply_markup=scope_kb(lang),
    )


# ─── Scope pick ──────────────────────────────────────────────────────────────

@router.callback_query(FolderGen.scope, F.data.startswith("fscope:"))
async def pick_scope(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    lang = await db.get_user_language(user_id)
    scope = callback.data.split(":", 1)[1]
    await state.update_data(scope=scope)
    await callback.answer()

    data = await state.get_data()
    project_info = data.get("project_info", "")
    stack = data.get("stack", "")

    short_project = (project_info or "")[:60]
    scope_label = _build_scope_label(scope)
    
    summary_title = "🗂 <b>Ready to generate!</b>" if lang == "en" else "🗂 <b>Готово к генерации!</b>"
    project_label = "Project" if lang == "en" else "Проект"
    type_label = "Type" if lang == "en" else "Тип"
    stack_label = "Stack" if lang == "en" else "Стек"
    gen_hint = "Press <b>Generate</b>:" if lang == "en" else "Нажми <b>🚀 Генерировать</b>:"

    summary = (
        f"{summary_title}\n\n"
        f"📁 <b>{project_label}:</b> {escape(short_project)}{'…' if len(project_info) > 60 else ''}\n"
        f"🏗 <b>{type_label}:</b> {scope_label}\n"
        + (f"⚛️ <b>{stack_label}:</b> {escape(stack)}\n" if stack else "")
        + f"\n{gen_hint}"
    )
    await callback.message.edit_text(summary, reply_markup=confirm_structure_kb(lang))


# ─── Generate / Cancel ───────────────────────────────────────────────────────

@router.callback_query(F.data == "fstruct:cancel")
async def cancel_structure(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await db.get_user_language(callback.from_user.id)
    await state.clear()
    await callback.answer()
    cancel_text = "❌ Generation cancelled. Ready when you are!" if lang == "en" else "❌ Генерация отменена. Нажми 🗂 Структура когда будешь готов!"
    await callback.message.edit_text(cancel_text)


@router.callback_query(F.data == "fstruct:generate")
async def generate_structure(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    lang = await db.get_user_language(user_id)
    await callback.answer("⏳ Generating structure..." if lang == "en" else "⏳ Генерирую структуру...")

    # Re-check limit (double-safety in case state lingered)
    can_gen = await db.check_folder_gen_limit(user_id)
    if not can_gen:
        error_msg = "🚫 <b>Limit reached.</b> Try tomorrow!" if lang == "en" else "🚫 <b>Лимит уже исчерпан.</b> Попробуй завтра!"
        await callback.message.answer(error_msg)
        await state.clear()
        return

    data = await state.get_data()
    project_info = data.get("project_info", "")
    stack = data.get("stack", "")
    scope = data.get("scope", "fullstack")

    settings = load_settings()
    if not settings.gemini_api_key:
        await callback.message.answer("❌ GEMINI_API_KEY error")
        return

    await callback.message.answer("🤖 <b>Architect is designing...</b>" if lang == "en" else "🤖 <b>Архитектор думает над структурой...</b>")

    # Response schema for structured output — keeps JSON valid
    response_schema = {
        "type": "object",
        "properties": {
            "tree": {"type": "string"},
            "mkdir_cmd": {"type": "string"},
        },
        "required": ["tree", "mkdir_cmd"],
    }

    prompt = folder_engine.build_prompt(project_info, stack, scope)

    try:
        client = GeminiClient(
            api_key=settings.gemini_api_key,
            model="gemini-2.5-flash",
        )
        response = await client.generate_text(
            prompt,
            max_output_tokens=folder_engine.MAX_OUTPUT_TOKENS,
            response_schema=response_schema,
        )

        raw_text = (response.text or "").strip()

        # Try structured output first, fallback to JSON parse
        if response.parsed is not None:
            result = response.parsed
            if not isinstance(result, dict):
                result = json.loads(json.dumps(result, ensure_ascii=False))
        else:
            try:
                result = _try_parse_json(raw_text)
            except json.JSONDecodeError:
                result = _parse_folder_gen_fallback(raw_text)
                if not result.get("tree"):
                    logger.exception("Folder gen JSON parse failed. raw: %s", raw_text[:300])
                    await callback.message.answer(
                        "❌ <b>AI returned invalid response.</b>\nPlease try again in 30s." if lang == "en" else
                        "❌ <b>Модель вернула некорректный ответ (проблема с кавычками или переносами).</b>\n"
                        "Попробуй снова через 30 секунд."
                    )
                    return

        # Fix string literals like \n back into real newlines
        tree = str(result.get("tree") or "").replace("\\n", "\n").replace("\\t", "\t").strip()
        mkdir_cmd = str(result.get("mkdir_cmd") or "").replace("\\n", " ").strip()

        if not tree:
            await callback.message.answer("❌ <b>Failed to get structure.</b> Try again." if lang == "en" else "❌ <b>Не удалось получить структуру.</b> Попробуй снова.")
            return

        # ── Send results ─────────────────────────────────────────────────
        await callback.message.answer("✅ <b>Structure ready!</b>" if lang == "en" else "✅ <b>Структура готова!</b>")

        # 1. Folder tree
        await _send_pre(callback.message, "📁 <b>Project Tree:</b>" if lang == "en" else "📁 <b>Дерево проекта:</b>", tree)

        # 2. mkdir command (may be long — split if needed)
        if mkdir_cmd:
            await _send_pre(callback.message, "⚡ <b>Terminal Command:</b>" if lang == "en" else "⚡ <b>Команда для терминала:</b>", mkdir_cmd)

        # ── Save usage ───────────────────────────────────────────────────
        await db.increment_folder_gen_usage(user_id)
        await state.clear()

    except Exception:
        logger.exception("Folder structure generation failed")
        await callback.message.answer(
            "❌ <b>Generation error.</b>\nTry again in 30s." if lang == "en" else
            "❌ <b>Ошибка генерации.</b>\nВременный сбой API. Попробуй ещё раз через 30-60 секунд."
        )
