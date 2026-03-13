from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from src.keyboards.inline import editors_kb, models_kb, stacks_kb
from src.utils.db import db
from src.utils.i18n import _
from src.utils.states import PromptGen

router = Router()


@router.message(PromptGen.project_info)
async def capture_project_info(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = await db.get_user_language(user_id)
    project_info = (message.text or "").strip()
    if not project_info:
        await message.answer("Please describe your project in text 📝" if lang == "en" else "Пожалуйста, опиши свой проект текстом 📝")
        return

    await state.update_data(project_info=project_info)
    await state.set_state(PromptGen.editor)
    
    await message.answer(
        _("step_2", lang),
        reply_markup=editors_kb(lang)
    )


@router.callback_query(PromptGen.editor, F.data.startswith("editor:"))
async def pick_editor(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    lang = await db.get_user_language(user_id)
    editor = callback.data.split(":", 1)[1]
    await state.update_data(editor=editor)
    await state.set_state(PromptGen.stack)

    await callback.answer()
    
    confirm_text = f"Ok, editor: <b>{editor}</b>\n\nChoose stack:" if lang == "en" else f"Ок, редактор: <b>{editor}</b>\n\nВыбери стек:"
    
    await callback.message.edit_text(
        confirm_text,
        reply_markup=stacks_kb(lang)
    )


@router.callback_query(PromptGen.stack, F.data.startswith("stack:"))
async def pick_stack(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    lang = await db.get_user_language(user_id)
    stack = callback.data.split(":", 1)[1]
    await state.update_data(stack=stack)
    await state.set_state(PromptGen.model)

    await callback.answer()
    
    confirm_text = f"Stack: <b>{stack}</b>\n\nChoose model:" if lang == "en" else f"Стек: <b>{stack}</b>\n\nВыбери модель:"
    
    await callback.message.edit_text(
        confirm_text,
        reply_markup=models_kb(lang)
    )


@router.callback_query(PromptGen.model, F.data.startswith("model:"))
async def pick_model(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    lang = await db.get_user_language(user_id)
    model = callback.data.split(":", 1)[1]
    await state.update_data(model=model)
    await state.set_state(PromptGen.idea)

    await callback.answer()
    
    confirm_text = "Model selected ✅\n\nNow describe your task/idea in one message:" if lang == "en" else "Модель выбрана ✅\n\nТеперь опиши задачу/идею одним сообщением:"
    
    await callback.message.edit_text(
        confirm_text,
        reply_markup=None,
    )
