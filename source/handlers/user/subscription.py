from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger
from datetime import datetime, timedelta

from loader import db_manager
from source.utils import localizer
from source.utils.xray import xray_config
from source.keyboard import inline


async def manual_renew_subscription(call: types.CallbackQuery, state: FSMContext):

    # Узнаем есть ли у юзера вообще конфиги чтобы их обновлять
    user_id = call.from_user.id
    configs_to_renew = await db_manager.is_user_have_any_config(user_id)

    if not configs_to_renew:
        await call.message.answer(
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.nothing_to_renew_message,
            )
        )
        await call.answer()
        return

    # Проверяем время последнего платежа
    last_payment_time = await db_manager.get_last_subscription_payment(user_id)

    if last_payment_time and (datetime.now() - last_payment_time) < timedelta(hours=24):
        await call.message.answer(
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.subscription_already_renewed_today,
            )
        )
        await call.answer()
        return

    # Получаем текущий баланс и стоимость подписки
    current_balance = await db_manager.get_user_balance(user_id)
    subscription_cost = await db_manager.get_current_subscription_cost(user_id)

    if current_balance >= subscription_cost:
        # Продлеваем подписку
        await db_manager.update_user_balance(user_id, -subscription_cost)
        await db_manager.update_last_subscription_payment(user_id, datetime.now())
        # Восстанавливаем конфиги пользователя в Xray
        await xray_config.reactivate_user_configs_in_xray([user_id])
        await call.message.answer(
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.subscription_renewed_successfully,
            )
        )
    else:
        # Недостаточно средств
        await call.message.answer(
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.insufficient_balance_for_sub_renewal,
            )
        )

    await call.answer()
