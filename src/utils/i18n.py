MESSAGES = {
    "ru": {
        "welcome": (
            "🪐 <b>Vibe Coding Prompter</b>\n\n"
            "Генерирую персональные промпты для AI-редакторов: системный промпт, "
            "<code>.cursorrules</code>, <code>.windsurfrules</code> и советы — всё под твой проект.\n\n"
            "📝 <b>Шаг 1/5 — Проект</b>\n"
            "Расскажи о своём проекте: что строишь, в какой стек, есть ли документация или особенности?"
        ),
        "help": (
            "🪐 <b>Как пользоваться:</b>\n\n"
            "1️⃣ Нажми <b>⚡ Новый промпт</b> или /start \u2192 генерируй system prompt\n"
            "2️⃣ Нажми <b>🗂 Структура</b> или /structure \u2192 генерируй дерево папок + mkdir\n\n"
            "{limit_text}"
            "❓ Вопросы? Просто напиши!"
        ),
        "limit_free": (
            "📊 <b>Лимиты (бесплатно):</b>\n"
            "• Промпт: 2 генерации в день\n"
            "• Структура: 1 генерация в день\n"
            "<i>Подписывайся на PRO (/pro), чтобы убрать лимиты!</i>\n\n"
        ),
        "limit_pro": (
            "📊 <b>Лимиты (PRO 💎):</b>\n"
            "• Промпт: <b>Безлимит</b>\n"
            "• Структура: <b>Безлимит</b>\n\n"
        ),
        "profile_title": "👤 <b>Профиль</b>",
        "status_pro_lifetime": "💎 PRO Навсегда",
        "status_pro_until": "💎 PRO до {date}",
        "status_free": "Бесплатный",
        "usage_today": "📊 Сегодня: {bar} <b>{count}/{limit}</b>",
        "remaining_gens": "🎁 Осталось: <b>{count}</b> генерации",
        "last_projects": "📁 <b>Последние проекты:</b>",
        "history_empty": "📁 <i>История пуста — создай первый промпт!</i>",
        "kb_new_prompt": "⚡ Новый промпт",
        "kb_structure": "🗂 Структура",
        "kb_profile": "👤 Профиль",
        "kb_help": "❓ Помощь",
        "kb_other_project": "Другой проект",
        "kb_generate": "Генерировать",
        "kb_cancel": "Отмена",
        "scope_backend": "Backend",
        "scope_frontend": "Frontend",
        "scope_fullstack": "Fullstack",
        "pro_title": "💎 <b>План PRO</b>",
        "pro_desc": (
            "Открой для себя безграничные возможности генерации!\n"
            "• Безлимитные системные промпты\n"
            "• Безлимитные структуры папок\n"
            "• Сохранение 50+ проектов в историю\n"
            "• Ранний доступ к новым моделям\n\n"
            "Оплата производится безопасно через Telegram Stars (⭐️). Выбери свой план:"
        ),
        "buy_button_prefix": "⭐️ Купить PRO",
        "select_language": "🌐 Выберите язык / Select language:",
        "lang_ru": "Русский 🇷🇺",
        "lang_en": "English 🇺🇸",
        "step_1": "📝 <b>Шаг 1/5 — Проект</b>\n\nРасскажи о своём проекте: что строишь, стек, особенности?",
        "step_2": "💻 <b>Шаг 2/5 — Редактор</b>\n\nВ каком AI-редакторе будешь кодить?",
        "step_3": "⚙️ <b>Шаг 3/5 — Стек</b>\n\nВыбери основной стек технологий:",
        "step_4": "🧠 <b>Шаг 4/5 — Модель</b>\n\nКакую AI модель планируешь использовать?",
        "step_5": "💡 <b>Шаг 5/5 — Идея</b>\n\nЧто именно хочешь сделать прямо сейчас? (опиши фичу или этап)",
        "generating": "⏳ Генерирую идеальный промпт... это займет 10-15 секунд.",
        "gen_done": "🪐 <b>Твой Vibe-промпт готов!</b>\nСкопируй его в свой редактор.",
        "folder_gen_start": "🗂 <b>Генератор структуры</b>\n\nВыбери проект из списка или опиши новый:",
        "folder_gen_scope": "🔍 <b>Область генерации</b>\n\nЧто отрисовать?",
        "folder_gen_confirm": "🚀 <b>Готов генерировать структуру?</b>\nЭто создаст дерево папок и команду для терминала.",
        "folder_gen_result_title": "📁 Дерево проекта:",
        "folder_gen_mkdir_title": "💻 Команда для терминала:",
        "folder_gen_notes_title": "📝 Заметки по структуре:",
        "error_json": "❌ Ошибка: модель выдала некорректный ответ. Попробуй еще раз.",
        "error_limit": "❌ Лимит исчерпан. Возвращайся завтра или купи PRO!",
        "error_plan_not_found": "❌ План не найден.",
        "plan_week_name": "1 Неделя PRO",
        "plan_week_desc": "Безлимитные промпты и структуры на 7 дней.",
        "plan_month_name": "1 Месяц PRO",
        "plan_month_desc": "Безлимитные промпты и структуры на 30 дней.",
        "plan_lifetime_name": "PRO Навсегда",
        "plan_lifetime_desc": "Безлимитно и навсегда. Доступ ко всем будущим функциям.",
    },
    "en": {
        "welcome": (
            "🪐 <b>Vibe Coding Prompter</b>\n\n"
            "I generate personal prompts for AI editors: system prompts, "
            "<code>.cursorrules</code>, <code>.windsurfrules</code>, and tips — all tailored to your project.\n\n"
            "📝 <b>Step 1/5 — Project</b>\n"
            "Tell me about your project: what are you building, what's your stack, any documentation or specifics?"
        ),
        "help": (
            "🪐 <b>How to use:</b>\n\n"
            "1️⃣ Press <b>⚡ New Prompt</b> or /start \u2192 generate system prompt\n"
            "2️⃣ Press <b>🗂 Structure</b> or /structure \u2192 generate folder tree + mkdir\n\n"
            "{limit_text}"
            "❓ Questions? Just write to me!"
        ),
        "limit_free": (
            "📊 <b>Limits (Free):</b>\n"
            "• Prompt: 2 generations per day\n"
            "• Structure: 1 generation per day\n"
            "<i>Subscribe to PRO (/pro) to remove limits!</i>\n\n"
        ),
        "limit_pro": (
            "📊 <b>Limits (PRO 💎):</b>\n"
            "• Prompt: <b>Unlimited</b>\n"
            "• Structure: <b>Unlimited</b>\n\n"
        ),
        "profile_title": "👤 <b>Profile</b>",
        "status_pro_lifetime": "💎 PRO Lifetime",
        "status_pro_until": "💎 PRO until {date}",
        "status_free": "Free",
        "usage_today": "📊 Today: {bar} <b>{count}/{limit}</b>",
        "remaining_gens": "🎁 Remaining: <b>{count}</b> generations",
        "last_projects": "📁 <b>Recent Projects:</b>",
        "history_empty": "📁 <i>History is empty — create your first prompt!</i>",
        "kb_new_prompt": "⚡ New Prompt",
        "kb_structure": "🗂 Structure",
        "kb_profile": "👤 Profile",
        "kb_help": "❓ Help",
        "kb_other_project": "Other project",
        "kb_generate": "Generate",
        "kb_cancel": "Cancel",
        "scope_backend": "Backend",
        "scope_frontend": "Frontend",
        "scope_fullstack": "Fullstack",
        "pro_title": "💎 <b>PRO Plan</b>",
        "pro_desc": (
            "Unlock limitless generation possibilities!\n"
            "• Unlimited system prompts\n"
            "• Unlimited folder structures\n"
            "• Save 50+ projects in history\n"
            "• Early access to new models\n\n"
            "Payments are secure via Telegram Stars (⭐️). Choose your plan:"
        ),
        "buy_button_prefix": "⭐️ Buy PRO",
        "select_language": "🌐 Выберите язык / Select language:",
        "lang_ru": "Русский 🇷🇺",
        "lang_en": "English 🇺🇸",
        "step_1": "📝 <b>Step 1/5 — Project</b>\n\nWhat are you building? Tell me about the stack and features.",
        "step_2": "💻 <b>Step 2/5 — Editor</b>\n\nWhich AI editor will you use?",
        "step_3": "⚙️ <b>Step 3/5 — Stack</b>\n\nChoose the main technology stack:",
        "step_4": "🧠 <b>Step 4/5 — Model</b>\n\nWhich AI model do you plan to use?",
        "step_5": "💡 <b>Step 5/5 — Idea</b>\n\nWhat exactly do you want to build right now? (feature or stage)",
        "generating": "⏳ Generating the perfect prompt... this will take 10-15 seconds.",
        "gen_done": "🪐 <b>Your Vibe-prompt is ready!</b>\nCopy it to your editor.",
        "folder_gen_start": "🗂 <b>Structure Generator</b>\n\nChoose a project from the list or describe a new one:",
        "folder_gen_scope": "🔍 <b>Generation Scope</b>\n\nWhat to draw?",
        "folder_gen_confirm": "🚀 <b>Ready to generate structure?</b>\nThis will create a folder tree and a terminal command.",
        "folder_gen_result_title": "📁 Project Tree:",
        "folder_gen_mkdir_title": "💻 Terminal Command:",
        "folder_gen_notes_title": "📝 Structure Notes:",
        "error_json": "❌ Error: AI gave an invalid response. Try again.",
        "error_limit": "❌ Limit reached. Come back tomorrow or buy PRO!",
        "error_plan_not_found": "❌ Plan not found.",
        "plan_week_name": "1 Week PRO",
        "plan_week_desc": "Unlimited prompts and structures for 7 days.",
        "plan_month_name": "1 Month PRO",
        "plan_month_desc": "Unlimited prompts and structures for 30 days.",
        "plan_lifetime_name": "PRO Lifetime",
        "plan_lifetime_desc": "Unlimited and forever. Access to all future features.",
    }
}


def _(key: str, lang: str = "ru") -> str:
    """Retrieve localized string."""
    return MESSAGES.get(lang, MESSAGES["ru"]).get(key, MESSAGES["ru"].get(key, key))
