from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import LabeledPrice, PreCheckoutQuery
from loguru import logger

from loader import dp, db_manager
from source.keyboard import inline
from source.utils import localizer
from source.data import config

from source.middlewares import rate_limit
from .check_is_user_banned import is_user_banned

@is_user_banned
async def show_balance_top_up_menu_function(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"Пользователь {call.from_user.id} открыл меню пополнения баланса")
    await state.finish()
    await call.message.edit_text(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.balance_top_up_message,
        ),
        reply_markup=await inline.balance_top_up_menu_keyboard(
            language_code=call.from_user.language_code
        ),
    )
    await call.answer()


# Отправляем инвойс
async def handle_payment(call: types.CallbackQuery):
    # Карта соответствия callback_data и суммы
    amount_map = {
        "pay_fifty_rubles": 50,
        "pay_hundred_rubles": 100,
        "pay_three_hundred_rubles": 300,
        "pay_five_hundred_rubles": 500,
        "pay_seven_hundred_rubles": 700,
        "pay_thousand_rubles": 1000,
    }

    # Получаем ключ из callback_data
    amount_key = call.data  # Например, "pay_fifty_rubles"
    amount = amount_map.get(amount_key)  # Извлекаем соответствующую сумму

    if amount:
        # Логируем процесс
        logger.info(f"Пользователь {call.from_user.id} выбрал оплату на {amount} рублей")

        # Создаем инвойс с указанной суммой
        prices = [
            types.LabeledPrice(label=f"Пополнение баланса на {amount} руб.", amount=amount * 100)
        ]  # Сумма в копейках

        # Отправляем инвойс
        await call.message.bot.send_invoice(
            chat_id=call.message.chat.id,
            title=f"Пополнение баланса на {amount} руб.",
            description=f"Оплата {amount} рублей на баланс.",
            payload=f"payment_{amount}",  # Платёжный идентификатор
            provider_token=config.yookassa_token,  # Тестовый токен Юкассы
            currency="RUB",
            prices=prices,
            start_parameter="pay",
        )

        # Подтверждаем обработку коллбека
        await call.answer()
    else:
        logger.error(f"Неизвестная сумма: {call.data}")
        await call.answer("Произошла ошибка при выборе суммы", show_alert=True)


async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    logger.info(f"Pre-checkout query received from {pre_checkout_query.from_user.id}")
    try:
        await dp.bot.answer_pre_checkout_query(
            pre_checkout_query.id, ok=True
        )  # Подтверждаем готовность к оплате
        logger.info(
            f"Pre-checkout query answered successfully for {pre_checkout_query.from_user.id}"
        )
    except Exception as e:
        logger.error(f"Error while answering PreCheckoutQuery: {e}")


# Обработка успешной оплаты
async def successful_payment(message: types.Message):
    logger.info(f"User {message.from_user.id} made a successful payment")

    payment_info = message.successful_payment

    amount = payment_info.total_amount / 100

    logger.info(f"Payment of {amount} RUB received from user {message.from_user.id}")

    await db_manager.update_user_balance(user_id=message.from_user.id, amount=amount)
    logger.info(f"Баланс пользователя {message.from_user.id} пополнен на {amount} руб.")

    await message.answer(f"Оплата на сумму {amount} руб. прошла успешно! Ваш баланс был пополнен.")
