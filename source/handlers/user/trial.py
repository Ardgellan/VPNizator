from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger

from loader import db_manager
from source.keyboard import inline
from source.middlewares import rate_limit
from source.utils import localizer
from source.handlers.user import configs_menu  # Изначально тут было - from source.hadlers.user.configs_menu import request_user_for_config_name
from datetime import datetime, timedelta


# Функция для показа меню с предложением начать пробный период
@rate_limit(limit=1)
async def trial_period_function(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} opened trial period menu")
    # Отправляем пользователю сообщение с предложением начать пробный период
    await call.message.answer(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.trial_period_greeting,  # Сообщение о пробном периоде
        ),
        parse_mode=types.ParseMode.HTML,
        reply_markup=await inline.trial_menu_keyboard(
            language_code=call.from_user.language_code
        ),
    )
    await state.finish()


# Функция для проверки и инициализации пробного периода
@rate_limit(limit=1)
async def start_trial_period_function(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    language_code = call.from_user.language_code

    # Проверяем, использовал ли пользователь пробный период
    trial_used = await db_manager.is_trial_used(user_id=user_id)

    if trial_used:
        # Если пробный период уже использован, отправляем сообщение об отказе
        await call.message.answer(
            text=localizer.get_user_localized_text(
                user_language_code=language_code,
                text_localization=localizer.message.trial_period_rejection,  # Сообщение об отказе
            ),
            parse_mode=types.ParseMode.HTML,
            reply_markup=await inline.back_to_main_menu_keyboard(language_code=language_code)
        )

        await call.answer()
        await state.finish()
        return

    # Если пробный период не использован, активируем его
    trial_start = datetime.now()
    trial_end = trial_start + timedelta(days=7)  # Например, пробный период длится 7 дней
    await db_manager.activate_trial_period(user_id=user_id, trial_start=trial_start, trial_end=trial_end)
    await db_manager.mark_trial_as_used(user_id=user_id)
    
    # Используем существующую функцию для запроса имени нового VPN-конфига
    await configs_menu.request_user_for_config_name(call, state)
    await call.answer()
