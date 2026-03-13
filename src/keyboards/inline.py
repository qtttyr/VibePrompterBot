from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from src.utils.i18n import _


def editors_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Cursor 🚀", callback_data="editor:cursor")],
            [InlineKeyboardButton(text="Windsurf 🌊", callback_data="editor:windsurf")],
            [InlineKeyboardButton(text="VS Code 🟦", callback_data="editor:vscode")],
            [InlineKeyboardButton(text="Claude Code 🤖", callback_data="editor:claude_code")],
            [InlineKeyboardButton(text="Trae ⚡", callback_data="editor:trae")],
            [InlineKeyboardButton(text="Antigravity 🪐", callback_data="editor:antigravity")],
        ]
    )


def stacks_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="React + Tailwind ⚛️", callback_data="stack:react_tailwind")],
            [InlineKeyboardButton(text="Next.js + Tailwind 🚀", callback_data="stack:next_tailwind")],
            [InlineKeyboardButton(text="FastAPI ⚡", callback_data="stack:fastapi")],
            [InlineKeyboardButton(text="Claude Code Native 🤖", callback_data="stack:claude_native")],
        ]
    )


def models_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Gemini 2.5 Flash",
                    callback_data="model:gemini-2.5-flash",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Groq: Llama 3.3 70B",
                    callback_data="model:llama-3.3-70b-versatile",
                )
            ],
        ]
    )


def generate_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_( "kb_generate", lang ), callback_data="action:generate")],
        ]
    )


def project_pick_kb(projects: list, lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline keyboard with the user's saved projects and a 'new project' option."""
    rows = []
    for i, (project_info, stack) in enumerate(projects):
        label = (project_info or "")[:32]
        if len(project_info or "") > 32:
            label += "…"
        rows.append([InlineKeyboardButton(
            text=f"{i + 1}. {label}",
            callback_data=f"fproj:{i}",
        )])
    rows.append([InlineKeyboardButton(text=f"➕ {_( 'kb_other_project', lang )}", callback_data="fproj:new")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Русский 🇷🇺", callback_data="setlang:ru"),
                InlineKeyboardButton(text="English 🇺🇸", callback_data="setlang:en"),
            ]
        ]
    )


def scope_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🖥 {_( 'scope_backend', lang )}", callback_data="fscope:backend")],
            [InlineKeyboardButton(text=f"⚛️ {_( 'scope_frontend', lang )}", callback_data="fscope:frontend")],
            [InlineKeyboardButton(text=f"🌐 {_( 'scope_fullstack', lang )}", callback_data="fscope:fullstack")],
        ]
    )


def confirm_structure_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🚀 {_( 'kb_generate', lang )}", callback_data="fstruct:generate")],
            [InlineKeyboardButton(text=f"❌ {_( 'kb_cancel', lang )}", callback_data="fstruct:cancel")],
        ]
    )

def buy_pro_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    prefix = _("buy_button_prefix", lang)
    plan_week = _("plan_week_name", lang)
    plan_month = _("plan_month_name", lang)
    plan_lifetime = _("plan_lifetime_name", lang)
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{prefix} (150⭐️) - {plan_week}", callback_data="buy_pro:week")],
            [InlineKeyboardButton(text=f"{prefix} (450⭐️) - {plan_month}", callback_data="buy_pro:month")],
            [InlineKeyboardButton(text=f"{prefix} (2500⭐️) - {plan_lifetime}", callback_data="buy_pro:lifetime")],
        ]
    )
