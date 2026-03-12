import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import load_settings
from src.handlers.common import router as common_router
from src.handlers.folder_gen import router as folder_gen_router
from src.handlers.generator import router as generator_router
from src.handlers.settings import router as settings_router
from src.handlers.payments import router as payments_router
from src.middlewares.throttling import ThrottlingMiddleware
from src.utils.db import db


logger = logging.getLogger(__name__)


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    # Add Anti-Spam (DDoS protection)
    dp.message.middleware(ThrottlingMiddleware(limit_seconds=1.0))
    dp.callback_query.middleware(ThrottlingMiddleware(limit_seconds=1.0))

    dp.include_router(common_router)
    dp.include_router(folder_gen_router)
    dp.include_router(settings_router)
    dp.include_router(generator_router)
    dp.include_router(payments_router)
    return dp


async def run_bot() -> None:
    settings = load_settings()
    await db.setup()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()

    logger.info("Starting polling")
    await dp.start_polling(bot)
