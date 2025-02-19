# import asyncio

# from aiogram import Dispatcher, types
# from aiogram.dispatcher import DEFAULT_RATE_LIMIT
# from aiogram.dispatcher.handler import CancelHandler, current_handler
# from aiogram.dispatcher.middlewares import BaseMiddleware
# from aiogram.utils.exceptions import Throttled


# def rate_limit(limit: int, key=None):
#     """
#     Decorator for configuring rate limit and key in different functions.

#     :param limit:
#     :param key:
#     :return:
#     """

#     def decorator(func):
#         setattr(func, "throttling_rate_limit", limit)
#         if key:
#             setattr(func, "throttling_key", key)
#         return func

#     return decorator


# class ThrottlingMiddleware(BaseMiddleware):
#     """
#     Simple middleware
#     """

#     def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix="antiflood_"):
#         self.rate_limit = limit
#         self.prefix = key_prefix
#         super(ThrottlingMiddleware, self).__init__()

#     async def on_process_message(self, message: types.Message, data: dict):
#         """
#         This handler is called when dispatcher receives a message

#         :param message:
#         """
#         # Get current handler
#         handler = current_handler.get()

#         # Get dispatcher from context
#         dispatcher = Dispatcher.get_current()
#         # If handler was configured, get rate limit and key from handler
#         if handler:
#             limit = getattr(handler, "throttling_rate_limit", self.rate_limit)
#             key = getattr(handler, "throttling_key", f"{self.prefix}_{handler.__name__}")
#         else:
#             limit = self.rate_limit
#             key = f"{self.prefix}_message"

#         # Use Dispatcher.throttle method.
#         try:
#             await dispatcher.throttle(key, rate=limit)
#         except Throttled as t:
#             # Execute action
#             await self.message_throttled(message, t)

#             # Cancel current handler
#             raise CancelHandler()

#     async def message_throttled(self, message: types.Message, throttled: Throttled):
#         """
#         Notify user only on first exceed and notify about unlocking only on last exceed

#         :param message:
#         :param throttled:
#         """
#         handler = current_handler.get()
#         dispatcher = Dispatcher.get_current()
#         if handler:
#             key = getattr(handler, "throttling_key", f"{self.prefix}_{handler.__name__}")
#         else:
#             key = f"{self.prefix}_message"

#         # Calculate how many time is left till the block ends
#         delta = throttled.rate - throttled.delta

#         # Prevent flooding
#         if throttled.exceeded_count <= 2:
#             await message.reply(f"Пожалуйста, подождите {int(delta)} секунды")

#         # Sleep.
#         await asyncio.sleep(delta)

#         # Check lock status
#         thr = await dispatcher.check_key(key)

#         # If current message is not last with current key - do not send message
#         if thr.exceeded_count == throttled.exceeded_count:
#             await message.reply("Доступ получен 👀")


# import time
# import asyncio
# from collections import defaultdict
# from aiogram import Dispatcher, types
# from aiogram.dispatcher.middlewares import BaseMiddleware
# from aiogram.dispatcher.handler import CancelHandler, current_handler

# def rate_limit(limit: int, key=None):
#     """ Декоратор для задания лимита на команды """
#     def decorator(func):
#         setattr(func, "throttling_rate_limit", limit)
#         if key:
#             setattr(func, "throttling_key", key)
#         return func
#     return decorator

# class ThrottlingMiddleware(BaseMiddleware):
#     def __init__(self, default_message_limit=2, default_callback_limit=1, cleanup_interval=600, cleanup_threshold=1800):
#         """
#         :param default_message_limit: Лимит сообщений по умолчанию (сек)
#         :param default_callback_limit: Лимит callback-запросов по умолчанию (сек)
#         :param cleanup_interval: Как часто очищать старые данные (сек)
#         :param cleanup_threshold: Время неактивности пользователя для удаления (сек)
#         """
#         super().__init__()
#         self.default_message_limit = default_message_limit
#         self.default_callback_limit = default_callback_limit
#         self.cleanup_threshold = cleanup_threshold  # Время неактивности перед удалением
#         self.user_limits = defaultdict(lambda: {"message": {}, "callback": {}, "last_active": time.time()})

#         # Запускаем фоновую задачу для очистки данных
#         asyncio.create_task(self._cleanup_task(cleanup_interval))

#     async def on_process_message(self, message: types.Message, data: dict):
#         """ Проверка лимита для сообщений (с поддержкой @rate_limit) """
#         user_id = message.from_user.id
#         now = time.time()

#         handler = current_handler.get()
#         if handler:
#             limit = getattr(handler, "throttling_rate_limit", self.default_message_limit)
#             key = getattr(handler, "throttling_key", message.text)
#         else:
#             limit = self.default_message_limit
#             key = "default_message"

#         if key in self.user_limits[user_id]["message"] and now - self.user_limits[user_id]["message"][key] < limit:
#             await message.reply(f"⏳ Подожди {int(limit - (now - self.user_limits[user_id]['message'][key]))} сек.")
#             raise CancelHandler()

#         self.user_limits[user_id]["message"][key] = now
#         self.user_limits[user_id]["last_active"] = now  # Обновляем время активности

#     async def on_process_callback_query(self, call: types.CallbackQuery, data: dict):
#         """ Проверка лимита для callback-кнопок (с поддержкой @rate_limit) """
#         user_id = call.from_user.id
#         now = time.time()

#         handler = current_handler.get()
#         if handler:
#             limit = getattr(handler, "throttling_rate_limit", self.default_callback_limit)
#             key = getattr(handler, "throttling_key", call.data)
#         else:
#             limit = self.default_callback_limit
#             key = "default_callback"

#         if key in self.user_limits[user_id]["callback"] and now - self.user_limits[user_id]["callback"][key] < limit:
#             await call.answer(f"⏳ Подожди {int(limit - (now - self.user_limits[user_id]['callback'][key]))} сек.", show_alert=True)
#             raise CancelHandler()

#         self.user_limits[user_id]["callback"][key] = now
#         self.user_limits[user_id]["last_active"] = now  # Обновляем время активности

#     async def _cleanup_task(self, interval):
#         """ Фоновая задача для очистки неактивных пользователей """
#         while True:
#             await asyncio.sleep(interval)
#             now = time.time()
#             to_delete = [user_id for user_id, data in self.user_limits.items() if now - data["last_active"] > self.cleanup_threshold]

#             for user_id in to_delete:
#                 del self.user_limits[user_id]  # Удаляем неактивного пользователя

#             print(f"🧹 Очистка памяти: удалено {len(to_delete)} пользователей")  # Лог очистки


import time
import asyncio
from collections import defaultdict
from aiogram import Dispatcher, types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler, current_handler

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, default_message_limit=2, default_callback_limit=1):
        super().__init__()
        self.default_message_limit = default_message_limit
        self.default_callback_limit = default_callback_limit
        self.user_limits = defaultdict(lambda: {"message": 0, "callback": 0})  # Время последнего действия

    async def on_process_message(self, message: types.Message, data: dict):
        """ Проверка лимита для сообщений с учётом @rate_limit """
        user_id = message.from_user.id
        now = time.time()

        handler = current_handler.get()
        limit = getattr(handler, "throttling_rate_limit", self.default_message_limit)  # Получаем лимит из декоратора

        if now - self.user_limits[user_id]["message"] < limit:
            await message.reply(f"⏳ Подожди {int(limit - (now - self.user_limits[user_id]['message']))} сек.")
            raise CancelHandler()

        self.user_limits[user_id]["message"] = now

    async def on_process_callback_query(self, call: types.CallbackQuery, data: dict):
        """ Проверка лимита для callback-кнопок с учётом @rate_limit """
        user_id = call.from_user.id
        now = time.time()

        handler = current_handler.get()
        limit = getattr(handler, "throttling_rate_limit", self.default_callback_limit)  # Получаем лимит из декоратора

        if now - self.user_limits[user_id]["callback"] < limit:
            await call.answer(f"⏳ Подожди {int(limit - (now - self.user_limits[user_id]['callback']))} сек.", show_alert=True)
            raise CancelHandler()

        self.user_limits[user_id]["callback"] = now

