from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger

from loader import db_manager
from source.data import config
from source.keyboard import inline
from source.utils import localizer


def has_sufficient_balance(func):
    async def wrapper(message_or_call: types.Message | types.CallbackQuery, state: FSMContext):
        user_id = message_or_call.from_user.id

        # Получаем текущий баланс пользователя
        current_balance = await db_manager.get_user_balance(user_id)

        # Проверяем, хватает ли средств для создания одного нового конфига (стоимость 3 рубля)
        if current_balance < 3.00:
            if isinstance(message_or_call, types.CallbackQuery):
                message = message_or_call.message
                language_code = (await message_or_call.bot.get_chat_member(chat_id=user_id, user_id=user_id)).user.language_code
            else:
                message = message_or_call
                language_code = message_or_call.from_user.language_code

            # Сообщение о нехватке средств для создания конфига
            await message.answer(
                text=localizer.get_user_localized_text(
                    user_language_code=language_code,
                    text_localization=localizer.message.insufficient_balance_for_conf_gen_message,  # Локализация сообщения о нехватке средств
                ),
            )
            await state.finish()
            return

        # Если средств хватает, продолжаем выполнение функции
        await func(message_or_call, state)
    return wrapper


# def is_user_subscribed(func):
#     async def wrapper(message_or_call: types.Message | types.CallbackQuery, state: FSMContext):

#         user_id = message_or_call.from_user.id
#         trial_used = await db_manager.is_trial_used(
#             user_id=user_id
#         )

#         if (
#             user_id not in config.admins_ids and trial_used == True
#         ):
#             if isinstance(message_or_call, types.CallbackQuery):
#                 message = message_or_call.message
#                 language_code = (
#                     await message_or_call.bot.get_chat_member(chat_id=user_id, user_id=user_id)
#                 ).user.language_code
#             else:
#                 message = message_or_call
#                 language_code = message_or_call.from_user.language_code

#             if not await db_manager.check_for_user_has_active_subscription_by_user_id(
#                 user_id=user_id
#             ):
#                 await message.answer(
#                     text=localizer.get_user_localized_text(
#                         user_language_code=language_code,
#                         text_localization=localizer.message.you_dont_have_subscription,
#                     ),
#                 )
#                 await state.finish()
#                 return
#         await func(message_or_call, state)

#     return wrapper