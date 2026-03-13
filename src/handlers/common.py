from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from src.keyboards.inline import editors_kb, buy_pro_kb, language_kb
from src.utils.db import db
from src.utils.i18n import _
from src.utils.states import PromptGen
from html import escape

router = Router()


def main_menu_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    """Quick action keyboard that stays pinned at the bottom."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("kb_new_prompt", lang)),
                KeyboardButton(text=_("kb_structure", lang)),
            ],
            [
                KeyboardButton(text=_("kb_profile", lang)),
                KeyboardButton(text=_("kb_help", lang)),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="..." if lang == "en" else "Выбери действие или напиши...",
    )


from datetime import datetime
from src.keyboards.inline import editors_kb, buy_pro_kb

@router.message(Command("pro"))
async def cmd_pro(message: Message):
    """Direct command to open PRO subscription options."""
    lang = await db.get_user_language(message.from_user.id)
    await message.answer(
        f"<b>{_('pro_title', lang)}</b>\n\n{_('pro_desc', lang)}",
        reply_markup=buy_pro_kb(lang)
    )


@router.message(Command("lang"))
async def cmd_language(message: Message):
    """Command to change language."""
    lang = await db.get_user_language(message.from_user.id)
    await message.answer(_("select_language", lang), reply_markup=language_kb())


from aiogram.types import CallbackQuery
@router.callback_query(F.data.startswith("setlang:"))
async def set_language(callback: CallbackQuery):
    lang = callback.data.split(":")[1]
    await db.set_user_language(callback.from_user.id, lang)
    # We don't bother with _(..., lang) yet in the answer because it might be confusing if the user just switched
    confirm_text = "Language updated! 🇺🇸" if lang == "en" else "Язык изменен! 🇷🇺"
    await callback.answer(confirm_text)
    await callback.message.edit_text(
        _("welcome", lang), 
        reply_markup=main_menu_kb(lang)
    )


@router.message(Command("profile"))
@router.message(Command("dashboard"))
async def cmd_profile(message: Message):
    user_id = message.from_user.id
    lang = await db.get_user_language(user_id)
    usage_count = await db.get_user_usage(user_id)
    history = await db.get_last_generations(user_id)
    sub = await db.get_user_subscription(user_id)

    is_pro = sub and sub["expires_at"] > datetime.utcnow().isoformat()
    
    profile_lines = [
        f"{_('profile_title', lang)}",
        "",
        f"🆔 ID: <code>{user_id}</code>",
    ]

    if is_pro:
        # User is PRO
        try:
            exp_date = datetime.fromisoformat(sub['expires_at']).strftime("%d.%m.%Y")
            if "36500" in sub['expires_at'] or exp_date.startswith("21"):  # roughly lifetime indicator
                status = _("status_pro_lifetime", lang)
            else:
                status = _("status_pro_until", lang).format(date=exp_date)
        except Exception:
            status = "💎 PRO"

        profile_lines.extend([
            f"⭐️ Status: <b>{status}</b>",
            f"{_('usage_today', lang).format(bar='✨', count='∞', limit='∞')}",
            "",
            f"{_('last_projects', lang)} (PRO):"
        ])
    else:
        # Free User
        remaining = max(0, 2 - usage_count)
        used_blocks = "🟩" * usage_count
        free_blocks = "⬜" * remaining
        usage_bar = used_blocks + free_blocks if (usage_count + remaining) > 0 else "⬜⬜"

        profile_lines.extend([
            f"⭐️ Status: <b>{_('status_free', lang)}</b>",
            f"{_('usage_today', lang).format(bar=usage_bar, count=usage_count, limit=2)}",
            f"{_('remaining_gens', lang).format(count=remaining)}",
            "",
            f"{_('last_projects', lang)}"
        ])

    if history:
        for i, (project, editor, stack, idea, created_at) in enumerate(history, 1):
            project_short = (project[:28] + "…") if project and len(project) > 28 else (project or "—")
            idea_short = (idea[:32] + "…") if idea and len(idea) > 32 else (idea or "—")
            # Format date: just time if today, otherwise short date
            try:
                from datetime import date
                dt = datetime.fromisoformat(str(created_at))
                if dt.date() == date.today():
                    time_str = dt.strftime("%H:%M")
                else:
                    time_str = dt.strftime("%d.%m")
            except Exception:
                time_str = ""

            profile_lines.append(
                f"  {i}. <b>{escape(str(project_short))}</b>"
                + (f" · {time_str}" if time_str else "")
            )
            profile_lines.append(
                f"     <i>{escape(str(editor or '?'))} · {escape(idea_short)}</i>"
            )
    else:
        profile_lines[-1] = _("history_empty", lang)

    # If normal user, attach the "Buy PRO" keyboard below the text
    kb = None if is_pro else buy_pro_kb(lang)

    await message.answer(
        "\n".join(profile_lines),
        reply_markup=kb,
    )
    
    # Send the main menu purely to refresh the bottom reply-kbd if needed
    if is_pro:
        await message.answer("...", reply_markup=main_menu_kb(lang))


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    
    # Auto-detect language
    tg_lang = (message.from_user.language_code or "ru").lower()
    lang = "en" if "en" in tg_lang else "ru"
    await db.set_user_language(message.from_user.id, lang)

    await message.answer(_("welcome", lang), reply_markup=main_menu_kb(lang))
    # Note: we don't set state here immediately to allow user to see the welcome/lang options first
    # But usually /start triggers step 1. Let's keep it consistent.
    await state.set_state(PromptGen.project_info)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    user_id = message.from_user.id
    lang = await db.get_user_language(user_id)
    sub = await db.get_user_subscription(user_id)
    is_pro = False
    if sub:
        is_pro = sub["expires_at"] > datetime.utcnow().isoformat()
        
    limit_text = _("limit_pro", lang) if is_pro else _("limit_free", lang)
    
    await message.answer(
        _("help", lang).format(limit_text=limit_text),
        reply_markup=main_menu_kb(lang),
    )


@router.message(Command("founder_make_me_pro"))
async def cmd_founder_pro(message: Message):
    """Secret command for the founder to get Lifetime PRO for free."""
    args = message.text.split(maxsplit=1)
    from src.config import load_settings
    settings = load_settings()
    
    if len(args) < 2 or args[1] != settings.founder_password:
        return  # silently ignore or respond with generic message to avoid brute forcing
        
    user_id = message.from_user.id
    from datetime import datetime, timedelta
    
    expires_at = (datetime.utcnow() + timedelta(days=36500)).isoformat()
    await db.grant_subscription(user_id, "💎 PRO Навсегда (Founder)", expires_at)
    
    await message.answer(
        "🤫 <b>Режим Создателя Активирован.</b>\n\n"
        "Тебе выдана подписка 💎 PRO Навсегда абсолютно бесплатно.\n"
        "Спасибо за создание этого бота! 🚀",
        reply_markup=main_menu_kb()
    )


@router.message(lambda m: m.text in ("⚡ Новый промпт", "⚡ New Prompt"))
async def quick_new_prompt(message: Message, state: FSMContext) -> None:
    """Quick button: start new prompt generation flow."""
    lang = await db.get_user_language(message.from_user.id)
    await state.clear()
    await state.set_state(PromptGen.project_info)
    await message.answer(
        _("step_1", lang),
        reply_markup=main_menu_kb(lang),
    )


@router.message(lambda m: m.text in ("👤 Профиль", "👤 Profile"))
async def quick_profile(message: Message) -> None:
    """Quick button: show profile."""
    await cmd_profile(message)


@router.message(lambda m: m.text in ("❓ Помощь", "❓ Help"))
async def quick_help(message: Message) -> None:
    """Quick button: show help."""
    await cmd_help(message)
