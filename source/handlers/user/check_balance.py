from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger

from loader import db_manager
from source.data import config
from source.keyboard import inline
from source.utils import localizer


def has_sufficient_balance_for_conf_generation(func):
    async def wrapper(message_or_call: types.Message | types.CallbackQuery, state: FSMContext):
        user_id = message_or_call.from_user.id

        # Получаем текущий баланс пользователя
        current_balance = await db_manager.get_user_balance(user_id)
        # Получаем текущую стоимость подписки (за все активные конфиги)
        current_subscription_cost = await db_manager.get_current_subscription_cost(user_id)
        # Добавляем стоимость нового конфига (3 рубля) к общей стоимости
        total_cost_with_new_config = current_subscription_cost + 3.00

        # Проверяем, хватает ли средств для создания одного нового конфига (стоимость 3 рубля)
        if current_balance < 3.00:
            if isinstance(message_or_call, types.CallbackQuery):
                message = message_or_call.message
                language_code = (
                    await message_or_call.bot.get_chat_member(chat_id=user_id, user_id=user_id)
                ).user.language_code
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

        # Проверяем, хватает ли средств для продления подписки с новым конфигом
        elif current_balance < total_cost_with_new_config:
            if isinstance(message_or_call, types.CallbackQuery):
                message = message_or_call.message
                language_code = (
                    await message_or_call.bot.get_chat_member(chat_id=user_id, user_id=user_id)
                ).user.language_code
            else:
                message = message_or_call
                language_code = message_or_call.from_user.language_code

            # Сообщение о том, что создание нового конфига приведет к невозможности продления подписки
            await message.answer(
                text=localizer.get_user_localized_text(
                    user_language_code=language_code,
                    text_localization=localizer.message.config_generation_is_cost_prohibitive,  # Локализация сообщения
                ).format(
                    current_subscription_cost=current_subscription_cost, 
                    total_cost_with_new_config=total_cost_with_new_config
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
