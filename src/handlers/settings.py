from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from src.keyboards.inline import editors_kb, models_kb, stacks_kb
from src.utils.states import PromptGen

router = Router()


@router.message(PromptGen.project_info)
async def capture_project_info(message: Message, state: FSMContext) -> None:
    project_info = (message.text or "").strip()
    if not project_info:
        await message.answer("Пожалуйста, опиши свой проект текстом 📝")
        return

    await state.update_data(project_info=project_info)
    await state.set_state(PromptGen.editor)
    
    await message.answer(
        "Принято! 👌\n\nТеперь выбери <b>AI-редактор</b>, для которого мы будем готовить конфиги:",
        reply_markup=editors_kb()
    )


@router.callback_query(PromptGen.editor, F.data.startswith("editor:"))
async def pick_editor(callback: CallbackQuery, state: FSMContext) -> None:
    editor = callback.data.split(":", 1)[1]
    await state.update_data(editor=editor)
    await state.set_state(PromptGen.stack)

    await callback.answer()
    await callback.message.edit_text(
        f"Ок, редактор: <b>{editor}</b>\n\n"
        "Выбери стек:",
        reply_markup=stacks_kb()
    )


@router.callback_query(PromptGen.stack, F.data.startswith("stack:"))
async def pick_stack(callback: CallbackQuery, state: FSMContext) -> None:
    stack = callback.data.split(":", 1)[1]
    await state.update_data(stack=stack)
    await state.set_state(PromptGen.model)

    await callback.answer()
    await callback.message.edit_text(
        f"Стек: <b>{stack}</b>\n\n"
        "Выбери модель:",
        reply_markup=models_kb()
    )


@router.callback_query(PromptGen.model, F.data.startswith("model:"))
async def pick_model(callback: CallbackQuery, state: FSMContext) -> None:
    model = callback.data.split(":", 1)[1]
    await state.update_data(model=model)
    await state.set_state(PromptGen.idea)

    await callback.answer()
    await callback.message.edit_text(
        "Модель выбрана ✅\n\nТеперь опиши задачу/идею одним сообщением:",
        reply_markup=None,
    )
