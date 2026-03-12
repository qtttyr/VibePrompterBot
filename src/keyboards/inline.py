from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def editors_kb() -> InlineKeyboardMarkup:
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


def stacks_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="React + Tailwind ⚛️", callback_data="stack:react_tailwind")],
            [InlineKeyboardButton(text="Next.js + Tailwind 🚀", callback_data="stack:next_tailwind")],
            [InlineKeyboardButton(text="FastAPI ⚡", callback_data="stack:fastapi")],
            [InlineKeyboardButton(text="Claude Code Native 🤖", callback_data="stack:claude_native")],
        ]
    )


def models_kb() -> InlineKeyboardMarkup:
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


def generate_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Generate", callback_data="action:generate")],
        ]
    )


def project_pick_kb(projects: list) -> InlineKeyboardMarkup:
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
    rows.append([InlineKeyboardButton(text="➕ Другой проект", callback_data="fproj:new")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def scope_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🖥 Backend", callback_data="fscope:backend")],
            [InlineKeyboardButton(text="⚛️ Frontend", callback_data="fscope:frontend")],
            [InlineKeyboardButton(text="🌐 Fullstack", callback_data="fscope:fullstack")],
        ]
    )


def confirm_structure_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Генерировать", callback_data="fstruct:generate")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="fstruct:cancel")],
        ]
    )

def buy_pro_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐️ 1 Неделя PRO (150)", callback_data="buy_pro:week")],
            [InlineKeyboardButton(text="⭐️ 1 Месяц PRO (450)", callback_data="buy_pro:month")],
            [InlineKeyboardButton(text="⭐️ PRO Навсегда (2500)", callback_data="buy_pro:lifetime")],
        ]
    )
