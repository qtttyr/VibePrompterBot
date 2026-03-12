from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from datetime import datetime, timedelta
import logging

from src.utils.db import db
from src.keyboards.inline import buy_pro_kb

logger = logging.getLogger(__name__)

router = Router()

# XTR is the official Telegram Stars currency code
CURRENCY = "XTR"

PLANS = {
    "week": {
        "name": "1 Неделя PRO",
        "description": "Безлимитные промпты и структуры на 7 дней.",
        "amount": 150,
        "days": 7,
    },
    "month": {
        "name": "1 Месяц PRO",
        "description": "Безлимитные промпты и структуры на 30 дней.",
        "amount": 450,
        "days": 30,
    },
    "lifetime": {
        "name": "PRO Навсегда",
        "description": "Безлимитно и навсегда. Доступ ко всем будущим функциям.",
        "amount": 2500,
        "days": 36500,  # 100 years
    }
}


@router.callback_query(F.data.startswith("buy_pro:"))
async def send_invoice(callback: CallbackQuery):
    plan_id = callback.data.split(":")[1]
    plan = PLANS.get(plan_id)
    
    if not plan:
        await callback.answer("Ошибка: План не найден.", show_alert=True)
        return

    # To sell digital goods for Telegram Stars, the provider token must be empty ""
    await callback.message.answer_invoice(
        title=plan["name"],
        description=plan["description"],
        payload=f"sub_{plan_id}",
        provider_token="",  
        currency=CURRENCY,
        prices=[LabeledPrice(label=plan["name"], amount=plan["amount"])],
    )
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """Answers the PreCheckoutQuery. Rejects if payload is invalid."""
    payload = pre_checkout_query.invoice_payload
    if payload.startswith("sub_") and payload.split("_")[1] in PLANS:
        await pre_checkout_query.answer(ok=True)
    else:
        await pre_checkout_query.answer(ok=False, error_message="Что-то пошло не так. План не найден.")


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    """Processes successful payment and grants subscription in DB."""
    payment = message.successful_payment
    payload = payment.invoice_payload
    plan_id = payload.split("_")[1]
    plan = PLANS.get(plan_id)
    
    if not plan:
        logger.error(f"Received successful payment for unknown payload: {payload}")
        return

    user_id = message.from_user.id
    
    # Calculate expiration date
    expires_at_dt = datetime.utcnow() + timedelta(days=plan["days"])
    expires_at_str = expires_at_dt.isoformat()

    # Grant in DB
    await db.grant_subscription(user_id=user_id, plan=plan["name"], expires_at=expires_at_str)

    await message.answer(
        f"🎉 <b>Спасибо за покупку!</b>\n\n"
        f"Тебе выдан статус <b>{plan['name']}</b>.\n"
        f"Теперь у тебя нет ограничений на промпты и структуру проекта. Твори без границ 🚀"
    )
