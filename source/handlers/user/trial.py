from datetime import datetime, timedelta

from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger

from loader import db_manager
from source.handlers.user import (
    configs_menu,  # Изначально тут было - from source.hadlers.user.configs_menu import request_user_for_config_name
)
from source.keyboard import inline
from source.middlewares import rate_limit
from source.utils import localizer


# Функция для показа меню с предложением начать пробный период
@rate_limit(limit=1)
async def trial_period_function(call: types.CallbackQuery, state: FSMContext):

    # Получаем текущий баланс пользователя
    current_balance = await db_manager.get_user_balance(user_id=call.from_user.id)

    await call.message.edit_text(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.trial_period_greeting,  # Сообщение о пробном периоде
        ).format(current_balance=current_balance),
        parse_mode=types.ParseMode.HTML,
        reply_markup=await inline.trial_menu_keyboard(language_code=call.from_user.language_code),
    )
    await state.finish()


@rate_limit(limit=1)
async def start_trial_period_function(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id

    # Проверяем, использовал ли пользователь пробный период
    trial_used = await db_manager.is_trial_used(user_id=user_id)

    if trial_used:
        await call.message.edit_text(
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.trial_period_rejection,
            ),
            parse_mode=types.ParseMode.HTML,
            reply_markup=await inline.insert_button_back_to_main_menu(
                keyboard=None, language_code=call.from_user.language_code
            ),
        )
        await call.answer()
        await state.finish()
        return

    # Используем транзакцию для выполнения нескольких запросов
    async with db_manager.transaction() as conn:
        try:
            # Помечаем, что пользователь использовал пробный период
            await db_manager.mark_trial_as_used(user_id=user_id, conn=conn)

            # Обновляем баланс пользователя
            await db_manager.update_user_balance(user_id=user_id, amount=6.00, conn=conn)

            # Получаем обновленный баланс
            current_balance = await db_manager.get_user_balance(user_id=user_id, conn=conn)

            # Сообщаем об успешной активации
            await call.message.edit_text(
                text=localizer.get_user_localized_text(
                    user_language_code=call.from_user.language_code,
                    text_localization=localizer.message.trial_period_success,
                ).format(current_balance=current_balance),
                parse_mode=types.ParseMode.HTML,
                reply_markup=await inline.trial_period_success_keyboard(
                    language_code=call.from_user.language_code
                ),
            )
            await call.answer()

        except Exception as e:
            # Если произошла ошибка, транзакция откатывается
            logger.error(f"Error during trial period activation for user {user_id}: {str(e)}")
            await call.message.edit_text(
                text=localizer.get_user_localized_text(
                    user_language_code=call.from_user.language_code,
                    text_localization=localizer.message.error_occurred_during_trial_activation,
                ),
                parse_mode=types.ParseMode.HTML,
                reply_markup=await inline.insert_button_back_to_main_menu(
                    keyboard=None, language_code=call.from_user.language_code
                ),
            )
            await call.answer()
            await state.finish()


# # Функция для проверки и инициализации пробного периода
# @rate_limit(limit=1)
# async def start_trial_period_function(call: types.CallbackQuery, state: FSMContext):
#     user_id = call.from_user.id

#     # Проверяем, использовал ли пользователь пробный период
#     trial_used = await db_manager.is_trial_used(user_id=user_id)

#     if trial_used == True:
#         await call.message.edit_text(
#             text=localizer.get_user_localized_text(
#             user_language_code=call.from_user.language_code,
#             text_localization=localizer.message.trial_period_rejection,
#         ),
#             parse_mode=types.ParseMode.HTML,
#             reply_markup=await inline.insert_button_back_to_main_menu(
#             keyboard=None, language_code=call.from_user.language_code
#         ),
#         )
#         await call.answer()
#         await state.finish()
#         return

#     await db_manager.mark_trial_as_used(user_id=user_id)
#     await db_manager.update_user_balance(user_id=user_id, amount=6.00)
#     current_balance = await db_manager.get_user_balance(user_id=user_id)

#     await call.message.edit_text(
#         text=localizer.get_user_localized_text(
#             user_language_code=call.from_user.language_code,
#             text_localization=localizer.message.trial_period_success,
#         ).format(current_balance=current_balance),
#         parse_mode=types.ParseMode.HTML,
#         reply_markup=await inline.trial_period_success_keyboard(
#             language_code=call.from_user.language_code
#         ),
#     )

#     await call.answer()
