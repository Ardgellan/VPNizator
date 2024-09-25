# from aiogram import types
# from aiogram.dispatcher import FSMContext
# from loguru import logger

# from source.data import config
# from source.keyboard import inline
# from source.middlewares import rate_limit
# from source.utils import localizer
# from source.utils.states.user import PaymentViaBankTransfer

# from .check_is_user_banned import is_user_banned


# @rate_limit(limit=1)
# @is_user_banned
# async def show_payment_method(message: types.Message, state: FSMContext):
#     logger.info(f"User {message.from_user.id} started payment")
#     await state.finish()
#     await message.answer(
#         text=localizer.get_user_localized_text(
#             user_language_code=message.from_user.language_code,
#             text_localization=localizer.message.payment_method_card,
#         ).format(
#             amount=config.subscription_monthly_price,
#             payment_card=config.payment_card,
#         ),
#         parse_mode=types.ParseMode.HTML,
#     )
#     await PaymentViaBankTransfer.waiting_for_payment_screenshot_or_receipt.set()


# async def notify_admin_about_new_payment(message: types.Message, state: FSMContext):
#     logger.info(f"User {message.from_user.id} started payment")
#     await state.finish()
#     await message.answer(
#         text=localizer.get_user_localized_text(
#             user_language_code=message.from_user.language_code,
#             text_localization=localizer.message.payment_method_card_success,
#         ),
#         parse_mode=types.ParseMode.HTML,
#     )
#     for admin_id in config.admins_ids:
#         await message.forward(admin_id)
#         admin_user = (await message.bot.get_chat_member(chat_id=admin_id, user_id=admin_id)).user

#         await message.bot.send_message(
#             chat_id=admin_id,
#             text=localizer.get_user_localized_text(
#                 user_language_code=admin_user.language_code,
#                 text_localization=localizer.message.admin_notification_about_new_payment,
#             ).format(
#                 user_id=message.from_user.id,
#                 username=(
#                     message.from_user.username
#                     if message.from_user.username
#                     else message.from_user.full_name
#                 ),
#             ),
#             parse_mode=types.ParseMode.HTML,
#             reply_markup=await inline.admin_payment_notification_keyboard(
#                 language_code=admin_user.language_code,
#                 from_user_id=message.from_user.id,
#             ),
#         )


from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import LabeledPrice, PreCheckoutQuery
from loguru import logger

from loader import dp, db_manager
from source.keyboard import inline
from source.utils import localizer


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
            provider_token="381764678:TEST:95796",  # Тестовый токен Юкассы
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

    # Получаем информацию о платеже из message.successful_payment
    payment_info = message.successful_payment

    # Извлекаем сумму платежа в рублях (сумма в копейках, поэтому делим на 100)
    amount = payment_info.total_amount / 100  # Например, 50000 копеек -> 500 рублей

    # Логируем успешный платеж
    logger.info(f"Payment of {amount} RUB received from user {message.from_user.id}")

    # Пополняем баланс пользователя
    await db_manager.update_user_balance(user_id=message.from_user.id, amount=amount)
    logger.info(f"Баланс пользователя {message.from_user.id} пополнен на {amount} руб.")

    # Отправляем сообщение пользователю об успешном пополнении баланса
    await message.answer(
        f"Оплата на сумму {amount} руб. прошла успешно! Ваш баланс был пополнен."
    )
