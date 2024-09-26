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

    logger.info(f"User {call.from_user.id} opened trial period menu")
    # Отправляем пользователю сообщение с предложением начать пробный период

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


# Функция для проверки и инициализации пробного периода
@rate_limit(limit=1)
async def start_trial_period_function(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id

    # Проверяем, использовал ли пользователь пробный период
    trial_used = await db_manager.is_trial_used(user_id=user_id)

    if trial_used == True:
        # Если пробный период уже использован, отправляем сообщение об отказе
        rejection_text = localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.trial_period_rejection,
        )

        keyboard = await inline.insert_button_back_to_main_menu(
            keyboard=None, language_code=call.from_user.language_code
        )

        await call.message.edit_text(
            text=rejection_text,
            parse_mode=types.ParseMode.HTML,
            reply_markup=keyboard,
        )

        await call.answer()
        await state.finish()
        return

    # Если пробный период не использован, активируем его
    await db_manager.mark_trial_as_used(user_id=user_id)

    # Начисляем баланс (100 рублей)
    await db_manager.update_user_balance(user_id=user_id, amount=100.00)

    # Получаем текущий баланс пользователя
    current_balance = await db_manager.get_user_balance(user_id=user_id)

    await call.message.edit_text(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.trial_period_success,  # Сообщение о пробном периоде
        ).format(current_balance=current_balance),
        parse_mode=types.ParseMode.HTML,
        reply_markup=await inline.trial_period_success_keyboard(
            language_code=call.from_user.language_code
        ),
    )

    await call.answer()
