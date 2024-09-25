from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger

from loader import db_manager
from source.utils import localizer


async def manual_renew_subscription(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id

    # Проверяем время последнего платежа
    last_payment_time = await db_manager.get_last_subscription_payment(user_id)
    if last_payment_time and last_payment_time.date() == datetime.now().date():
        await call.message.answer(
            localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.subscription_already_renewed_today,
            )
        )
        logger.info(
            f"Попытка продления подписки для пользователя {user_id}, но подписка уже была продлена сегодня."
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
            localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.subscription_renewed_successfully,
            )
        )
        logger.info(f"Подписка пользователя {user_id} успешно продлена вручную.")
    else:
        # Недостаточно средств
        await call.message.answer(
            localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.insufficient_balance_for_sub_renewal,
            )
        )
        logger.info(f"Недостаточно средств для продления подписки у пользователя {user_id}.")

    await call.answer()
