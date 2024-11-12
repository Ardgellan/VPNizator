from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger
from datetime import datetime

from loader import db_manager
from source.utils import localizer
from source.keyboard import inline

from source.utils.sub_reactivation import restore_user_configs_for_subscription


async def manual_renew_subscription(call: types.CallbackQuery, state: FSMContext):

    # Узнаем есть ли у юзера вообще конфиги чтобы их обновлять
    user_id = call.from_user.id
    configs_to_renew = await db_manager.is_user_have_any_config(user_id)

    if not configs_to_renew:
        await call.message.answer(
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.nothing_to_renew_message,
            ),
            parse_mode=types.ParseMode.HTML,
        )
        await call.answer()
        return

    # Проверяем время последнего платежа
    subscription_is_active = await db_manager.get_subscription_status(user_id)

    if subscription_is_active:
        await call.message.answer(
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.subscription_is_active,
            ),
            parse_mode=types.ParseMode.HTML,
        )
        await call.answer()
        return

    # Получаем текущий баланс и стоимость подписки
    current_balance = await db_manager.get_user_balance(user_id)
    subscription_cost = await db_manager.get_current_subscription_cost(user_id)

    if current_balance >= subscription_cost:
        # Продлеваем подписку
        # Восстанавливаем конфиги пользователя в Xray
        await restore_user_configs_for_subscription([user_id])
        await call.message.answer(
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.subscription_renewed_successfully,
            ),
            parse_mode=types.ParseMode.HTML,
        )
    else:
        # Недостаточно средств
        await call.message.answer(
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.insufficient_balance_for_sub_renewal,
            ),
            parse_mode=types.ParseMode.HTML,
        )

    await call.answer()