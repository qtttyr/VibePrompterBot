from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from src.keyboards.inline import editors_kb
from src.utils.db import db
from src.utils.states import PromptGen
from html import escape

router = Router()


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Quick action keyboard that stays pinned at the bottom."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="⚡ Новый промпт"),
                KeyboardButton(text="🗂 Структура"),
            ],
            [
                KeyboardButton(text="👤 Профиль"),
                KeyboardButton(text="❓ Помощь"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие или напиши...",
    )


from datetime import datetime
from src.keyboards.inline import editors_kb, buy_pro_kb

@router.message(Command("pro"))
async def cmd_pro(message: Message):
    """Direct command to open PRO subscription options."""
    await message.answer(
        "💎 <b>План PRO</b>\n\n"
        "Открой для себя безграничные возможности генерации!\n"
        "• Безлимитные системные промпты\n"
        "• Безлимитные структуры папок\n"
        "• Сохранение 50+ проектов в историю\n"
        "• Ранний доступ к новым моделям\n\n"
        "Оплата производится безопасно через Telegram Stars (⭐️). Выбери свой план:",
        reply_markup=buy_pro_kb()
    )


@router.message(Command("profile"))
@router.message(Command("dashboard"))
async def cmd_profile(message: Message):
    user_id = message.from_user.id
    usage_count = await db.get_user_usage(user_id)
    history = await db.get_last_generations(user_id)
    sub = await db.get_user_subscription(user_id)

    is_pro = sub and sub["expires_at"] > datetime.utcnow().isoformat()
    
    profile_lines = [
        f"👤 <b>Профиль</b>",
        "",
        f"🆔 ID: <code>{user_id}</code>",
    ]

    if is_pro:
        # User is PRO
        try:
            exp_date = datetime.fromisoformat(sub['expires_at']).strftime("%d.%m.%Y")
            if "36500" in sub['expires_at'] or exp_date.startswith("21"):  # roughly lifetime indicator
                status = "💎 PRO Навсегда"
            else:
                status = f"💎 PRO до {exp_date}"
        except Exception:
            status = "💎 PRO"

        profile_lines.extend([
            f"⭐️ Статус: <b>{status}</b>",
            f"📊 Промпты: <b>Безлимит</b> ✨",
            f"🗂 Структуры: <b>Безлимит</b> ✨",
            "",
            "📁 <b>Последние проекты (PRO):</b>"
        ])
    else:
        # Free User
        remaining = max(0, 2 - usage_count)
        used_blocks = "🟩" * usage_count
        free_blocks = "⬜" * remaining
        usage_bar = used_blocks + free_blocks if (usage_count + remaining) > 0 else "⬜⬜"

        profile_lines.extend([
            f"⭐️ Статус: <b>Бесплатный</b>",
            f"📊 Промпты: {usage_bar} <b>{usage_count}/2</b>",
            f"🎁 Осталось: <b>{remaining}</b> генерации",
            "",
            "📁 <b>Последние проекты:</b>"
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
        profile_lines[-1] = "📁 <i>История проекта пуста.</i>"

    # If normal user, attach the "Buy PRO" keyboard below the text
    kb = None if is_pro else buy_pro_kb()

    await message.answer(
        "\n".join(profile_lines),
        reply_markup=kb,
    )
    
    # Send the main menu purely to refresh the bottom reply-kbd if needed
    if is_pro:
        await message.answer("Чем займёмся?", reply_markup=main_menu_kb())


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(PromptGen.project_info)

    welcome_text = (
        "🪐 <b>Vibe Coding Prompter</b>\n\n"
        "Генерирую персональные промпты для AI-редакторов: системный промпт, "
        "<code>.cursorrules</code>, <code>.windsurfrules</code> и советы — всё под твой проект.\n\n"
        "📝 <b>Шаг 1/5 — Проект</b>\n"
        "Расскажи о своём проекте: что строишь, в какой стек, есть ли документация или особенности?"
    )

    await message.answer(welcome_text, reply_markup=main_menu_kb())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    user_id = message.from_user.id
    sub = await db.get_user_subscription(user_id)
    is_pro = False
    if sub:
        from datetime import datetime
        is_pro = sub["expires_at"] > datetime.utcnow().isoformat()
        
    limit_text = (
        "📊 <b>Лимиты (PRO 💎):</b>\n"
        "• Промпт: <b>Безлимит</b>\n"
        "• Структура: <b>Безлимит</b>\n\n"
    ) if is_pro else (
        "📊 <b>Лимиты (бесплатно):</b>\n"
        "• Промпт: 2 генерации в день\n"
        "• Структура: 1 генерация в день\n"
        "<i>Подписывайся на PRO (/pro), чтобы убрать лимиты!</i>\n\n"
    )
    
    await message.answer(
        "🪐 <b>Как пользоваться:</b>\n\n"
        "1️⃣ Нажми <b>⚡ Новый промпт</b> или /start \u2192 генерируй system prompt\n"
        "2️⃣ Нажми <b>🗂 Структура</b> или /structure \u2192 генерируй дерево папок + mkdir\n\n"
        f"{limit_text}"
        "❓ Вопросы? Просто напиши!",
        reply_markup=main_menu_kb(),
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


@router.message(lambda m: m.text in ("⚡ Новый промпт",))
async def quick_new_prompt(message: Message, state: FSMContext) -> None:
    """Quick button: start new prompt generation flow."""
    await state.clear()
    await state.set_state(PromptGen.project_info)
    await message.answer(
        "📝 <b>Шаг 1/5 \u2014 Проект</b>\n\n"
        "Расскажи о своём проекте: что строишь, стек, особенности?",
        reply_markup=main_menu_kb(),
    )


@router.message(lambda m: m.text in ("👤 Профиль",))
async def quick_profile(message: Message) -> None:
    """Quick button: show profile."""
    await cmd_profile(message)


@router.message(lambda m: m.text in ("❓ Помощь",))
async def quick_help(message: Message) -> None:
    """Quick button: show help."""
    await cmd_help(message)
