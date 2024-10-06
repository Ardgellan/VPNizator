# from aiogram import types
# from aiogram.dispatcher import FSMContext
# from aiogram.types import LabeledPrice, PreCheckoutQuery
# from loguru import logger

# from loader import dp, db_manager
# from source.keyboard import inline
# from source.utils import localizer
# from source.data import config

# from source.middlewares import rate_limit
# from .check_is_user_banned import is_user_banned

# @is_user_banned
# async def show_balance_top_up_menu_function(call: types.CallbackQuery, state: FSMContext):
#     logger.info(f"Пользователь {call.from_user.id} открыл меню пополнения баланса")
#     await state.finish()
#     await call.message.edit_text(
#         text=localizer.get_user_localized_text(
#             user_language_code=call.from_user.language_code,
#             text_localization=localizer.message.balance_top_up_message,
#         ),
#         reply_markup=await inline.balance_top_up_menu_keyboard(
#             language_code=call.from_user.language_code
#         ),
#     )
#     await call.answer()


# # Отправляем инвойс
# async def handle_payment(call: types.CallbackQuery):
#     # Карта соответствия callback_data и суммы
#     amount_map = {
#         "pay_fifty_rubles": 50,
#         "pay_hundred_rubles": 100,
#         "pay_three_hundred_rubles": 300,
#         "pay_five_hundred_rubles": 500,
#         "pay_seven_hundred_rubles": 700,
#         "pay_thousand_rubles": 1000,
#         "pay_three_thousand_rubles": 3000,
#     }

#     # Получаем ключ из callback_data
#     amount_key = call.data  # Например, "pay_fifty_rubles"
#     amount = amount_map.get(amount_key)  # Извлекаем соответствующую сумму

#     if amount:
#         # Логируем процесс
#         logger.info(f"Пользователь {call.from_user.id} выбрал оплату на {amount} рублей")

#         # Создаем инвойс с указанной суммой
#         prices = [
#             types.LabeledPrice(label=f"Пополнение баланса на {amount} руб.", amount=amount * 100)
#         ]  # Сумма в копейках

#         # Отправляем инвойс
#         await call.message.bot.send_invoice(
#             chat_id=call.message.chat.id,
#             title=f"Пополнение баланса на {amount} руб.",
#             description=f"Оплата {amount} рублей на баланс.",
#             payload=f"payment_{amount}",  # Платёжный идентификатор
#             provider_token=config.yookassa_token,  # Тестовый токен Юкассы
#             currency="RUB",
#             prices=prices,
#             start_parameter="pay",
#         )

#         # Подтверждаем обработку коллбека
#         await call.answer()
#     else:
#         logger.error(f"Неизвестная сумма: {call.data}")
#         await call.answer("Произошла ошибка при выборе суммы", show_alert=True)


# async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
#     logger.info(f"Pre-checkout query received from {pre_checkout_query.from_user.id}")
#     try:
#         await dp.bot.answer_pre_checkout_query(
#             pre_checkout_query.id, ok=True
#         )  # Подтверждаем готовность к оплате
#         logger.info(
#             f"Pre-checkout query answered successfully for {pre_checkout_query.from_user.id}"
#         )
#     except Exception as e:
#         logger.error(f"Error while answering PreCheckoutQuery: {e}")


# # Обработка успешной оплаты
# async def successful_payment(message: types.Message):
#     logger.info(f"User {message.from_user.id} made a successful payment")

#     payment_info = message.successful_payment

#     amount = payment_info.total_amount / 100

#     logger.info(f"Payment of {amount} RUB received from user {message.from_user.id}")

#     await db_manager.update_user_balance(user_id=message.from_user.id, amount=amount)
#     logger.info(f"Баланс пользователя {message.from_user.id} пополнен на {amount} руб.")

#     await message.answer(
#         text=localizer.get_user_localized_text(
#             user_language_code=message.from_user.language_code,
#             text_localization=localizer.message.successfull_payment_message,
#         ).format(amount=amount),
#         reply_markup=await inline.insert_button_back_to_main_menu(
#             language_code=message.from_user.language_code
#         ),
#     )



# from aiogram import types
# from aiogram.dispatcher import FSMContext

# from yookassa import Configuration, Payment

# from loguru import logger

# from loader import dp, db_manager
# from source.keyboard import inline
# from source.utils import localizer
# from source.data import config

# # Настройка конфигурации для ЮKassa
# Configuration.account_id = '461741'  # Ваш Shop ID
# Configuration.secret_key = 'test_iQvI0ynCTlfEwvT9qCOGE7R0n2lOylUvq_GsCezwZes'  # Ваш Secret Key

# async def handle_payment(message: types.Message):
#     amount = '100.00'  # Сумма платежа
#     description = 'Оплата подписки'  # Описание платежа
#     return_url = 'https://t.me/VPNizatorBot'  # URL для возврата после оплаты

#     try:
#         # Создаем платеж через ЮKassa
#         payment_url, payment_id = create_payment(amount, description, return_url)
#         if payment_url:
#             # Отправляем ссылку пользователю
#             await message.answer(f"Перейдите по ссылке для оплаты: {payment_url}")
#             # Отправляем пользователю идентификатор платежа и инструкцию
#             await message.answer(f"Ваш payment_id: {payment_id}. Используйте его для проверки статуса платежа.")
#             await message.answer(f"После завершения оплаты, введите команду /check_payment {payment_id} для проверки статуса платежа.")
#         else:
#             await message.answer("Произошла ошибка при создании платежа. Попробуйте снова.")
#     except Exception as e:
#         logger.error(f"Ошибка при обработке платежа: {e}")
#         await message.answer("Произошла ошибка. Попробуйте снова позже.")

# # Функция для создания платежа через ЮKassa
# def create_payment(amount, description, return_url):
#     try:
#         payment = Payment.create({
#             "amount": {
#                 "value": amount,  # Сумма платежа в формате "рубли.копейки"
#                 "currency": "RUB"  # Валюта
#             },
#             "confirmation": {
#                 "type": "redirect",  # Тип подтверждения - редирект на страницу оплаты
#                 "return_url": return_url  # URL, на который вернется пользователь после оплаты
#             },
#             "capture": True,  # Автоматически списать средства после успешной оплаты
#             "description": description  # Описание платежа
#         })
#         return payment.confirmation.confirmation_url
#     except Exception as e:
#         logger.error(f"Ошибка при создании платежа: {e}")
#         return None, None

# # Хендлер для проверки статуса платежа
# @dp.message_handler(commands=["check_payment"])
# async def check_payment_status(message: types.Message):
#     payment_id = message.get_args()  # Получаем ID платежа из аргументов команды
#     if not payment_id:
#         await message.answer("Пожалуйста, предоставьте идентификатор платежа.")
#         return

#     try:
#         payment = Payment.find_one(payment_id)
#         status = payment.status

#         if status == 'succeeded':
#             await message.answer("Оплата прошла успешно!")
#         elif status == 'pending':
#             await message.answer("Оплата еще не завершена. Пожалуйста, подождите.")
#         else:
#             await message.answer(f"Статус платежа: {status}. Пожалуйста, проверьте детали оплаты.")
#     except Exception as e:
#         logger.error(f"Ошибка при проверке статуса платежа: {e}")
#         await message.answer("Не удалось проверить статус платежа.")

from aiogram import types
from aiogram.dispatcher import FSMContext

from yookassa import Configuration, Payment
import uuid

from loguru import logger

from loader import dp, db_manager
from source.keyboard import inline
from source.utils import localizer
from source.data import config

# Настройка конфигурации для ЮKassa
Configuration.account_id = '461741'  # Ваш Shop ID
Configuration.secret_key = 'test_iQvI0ynCTlfEwvT9qCOGE7R0n2lOylUvq_GsCezwZes'  # Ваш Secret Key


async def handle_payment(message: types.Message):
    logger.info("Пользователь нажал /pay")  # Логируем действие
    payment_url, payment_id = await create_payment(100, message.chat.id)

    if payment_url:
        await message.answer(f"Ссылка на оплату: {payment_url}\nID платежа: {payment_id}")
    else:
        await message.answer("Произошла ошибка при создании платежа.")

async def create_payment(amount, chat_id):
    id_key = str(uuid.uuid4())
    payment = Payment.create({
    "amount": {
        "value": amount,
        "currency": "RUB"
    },
    "payment_method_data": {
        "type": "bank_card"
    },
    "confirmation": {
        "type": "redirect",
        "return_url": "https://t.me/VPNizatorBot"
    },
    "capture": True,
    "metadata": {
        "chat_id": chat_id
    },  
    "description": "Гони Дзенги!"
    }, id_key)
    return payment.confirmation.confirmation_url, payment.id



