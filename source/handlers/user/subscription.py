from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger

from loader import db_manager
from source.utils import localizer


async def get_current_subscription_cost(user_id: int) -> int:
    # Получаем количество активных конфигов
    active_configs_count = await db_manager.get_active_configs_count_by_user_id(user_id)
    # Рассчитываем общую стоимость подписки (3 рубля за каждый активный конфиг)
    total_cost = active_configs_count * 3
    return total_cost


async def check_and_renew_subscription(user_id: int) -> bool:
    # Получаем текущий баланс пользователя
    current_balance = await db_manager.get_user_balance(user_id)

    # Получаем текущую стоимость подписки за все активные конфиги
    subscription_cost = await get_current_subscription_cost(user_id)

    # Проверяем, хватает ли средств для оплаты подписки
    if current_balance >= subscription_cost:
        # Если средств хватает, списываем стоимость подписки
        await db_manager.update_user_balance(user_id, -subscription_cost)

        # Активируем все конфиги пользователя
        await db_manager.unblock_all_user_configs(user_id)
        logger.info(f"Подписка пользователя {user_id} успешно продлена.")
        return True
    else:
        logger.info(f"У пользователя {user_id} недостаточно средств для продления подписки.")
        return False


async def restore_subscription(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id

    # Проверяем возможность продления подписки
    if await check_and_renew_subscription(user_id):
        await call.message.answer(
            localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.subscription_restored
            )
        )
    else:
        await call.message.answer(
            localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.insufficient_balance_for_sub_renewal
            )
        )

    await call.answer()
