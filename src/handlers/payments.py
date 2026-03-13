from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from datetime import datetime, timedelta
import logging

from src.utils.db import db
from src.utils.i18n import _
from src.keyboards.inline import buy_pro_kb

logger = logging.getLogger(__name__)

router = Router()

# XTR is the official Telegram Stars currency code
CURRENCY = "XTR"

# PLANS are for technical iteration, names/descriptions are lookups in i18n
PLANS = {
    "week": {
        "days": 7,
        "amount": 150,
    },
    "month": {
        "days": 30,
        "amount": 450,
    },
    "lifetime": {
        "days": 36500,  # 100 years
        "amount": 2500,
    }
}


@router.callback_query(F.data.startswith("buy_pro:"))
async def send_invoice(callback: CallbackQuery):
    plan_id = callback.data.split(":")[1]
    plan = PLANS.get(plan_id)
    user_id = callback.from_user.id
    lang = await db.get_user_language(user_id)
    
    if not plan:
        await callback.answer(_("error_plan_not_found", lang), show_alert=True)
        return

    title = _(f"plan_{plan_id}_name", lang)
    description = _(f"plan_{plan_id}_desc", lang)

    # To sell digital goods for Telegram Stars, the provider token must be empty ""
    await callback.message.answer_invoice(
        title=title,
        description=description,
        payload=f"sub_{plan_id}",
        provider_token="",  
        currency=CURRENCY,
        prices=[LabeledPrice(label=title, amount=plan["amount"])],
    )
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """Answers the PreCheckoutQuery. Rejects if payload is invalid."""
    payload = pre_checkout_query.invoice_payload
    user_id = pre_checkout_query.from_user.id
    lang = await db.get_user_language(user_id)
    
    if payload.startswith("sub_") and payload.split("_")[1] in PLANS:
        await pre_checkout_query.answer(ok=True)
    else:
        await pre_checkout_query.answer(ok=False, error_message=_("error_plan_not_found", lang))


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
    lang = await db.get_user_language(user_id)
    
    # Calculate expiration date
    expires_at_dt = datetime.utcnow() + timedelta(days=plan["days"])
    expires_at_str = expires_at_dt.isoformat()

    plan_name = _(f"plan_{plan_id}_name", lang)

    # Grant in DB
    await db.grant_subscription(user_id=user_id, plan=plan_name, expires_at=expires_at_str)

    thanks = "🎉 <b>Thanks for your purchase!</b>" if lang == "en" else "🎉 <b>Спасибо за покупку!</b>"
    granted = f"You are now <b>{plan_name}</b>." if lang == "en" else f"Тебе выдан статус <b>{plan_name}</b>."
    magic = "Now you have unlimited prompts and structures. Create without limits 🚀" if lang == "en" else "Теперь у тебя нет ограничений на промпты и структуру проекта. Твори без границ 🚀"

    await message.answer(f"{thanks}\n\n{granted}\n{magic}")
