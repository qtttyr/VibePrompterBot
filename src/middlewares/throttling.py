import logging
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit_seconds: float = 1.0):
        super().__init__()
        self.limit_seconds = limit_seconds
        # dict: user_id -> last_action_timestamp
        self.users: dict[int, float] = defaultdict(lambda: 0.0)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if user_id:
            now = time.time()
            last_time = self.users[user_id]
            
            if now - last_time < self.limit_seconds:
                # Too many requests
                # We can silently drop or warn once. Silently is safer for DDOS.
                return None
            
            self.users[user_id] = now

        return await handler(event, data)
