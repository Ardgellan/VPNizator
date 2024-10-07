from aiogram import types
from aiogram.dispatcher import FSMContext
import json
import asyncio

from loguru import logger

from loader import dp, db_manager
from source.keyboard import inline
from source.utils import localizer
from source.data import config

from source.middlewares import rate_limit
from .check_is_user_banned import is_user_banned


from yookassa import Configuration, Payment
import uuid

# Настройка конфигурации для ЮKassa
Configuration.account_id = config.yookassa_shop_id
Configuration.secret_key = config.yookassa_api_token


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


async def handle_payment(call: types.CallbackQuery):
    # Получаем сумму из callback_data
    amount_mapping = {
        "pay_50_rubles": 50,
        "pay_100_rubles": 100,
        "pay_300_rubles": 300,
        "pay_500_rubles": 500,
        "pay_700_rubles": 700,
        "pay_1000_rubles": 1000,
        "pay_3000_rubles": 3000,
    }
    amount = amount_mapping.get(call.data)  # Получаем сумму по нажатой кнопке

    if amount is not None:

        # Создаем платеж с соответствующей суммой
        payment_url, payment_id = await create_payment(amount, call.from_user.id)

        if payment_url:
            await call.message.answer(
                text=localizer.get_user_localized_text(
                    user_language_code=call.from_user.language_code,
                    text_localization=localizer.message.payment_confirmation_message,
                ),
                parse_mode=types.ParseMode.HTML,
                reply_markup=await inline.payment_confirmation_keyboard(
                    language_code=call.from_user.language_code,
                    payment_url=payment_url
                ),
            )

            # Запуск проверки статуса платежа
            payment_success = await check_payment_status(payment_id, call.from_user.id, amount)
            if payment_success:
                await call.message.answer(
                    text=localizer.get_user_localized_text(
                        user_language_code=call.from_user.language_code,
                        text_localization=localizer.message.successfull_payment_message,
                    ).format(amount=amount),
                    reply_markup=await inline.insert_button_back_to_main_menu(
                        language_code=call.from_user.language_code
                    ),
                )
            else:
                await call.message.answer(f"Ваш платеж был отменен.")
        else:
            await call.message.answer(
                text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.payment_assembly_error_message,
                ),
                parse_mode=types.ParseMode.HTML,
                reply_markup=await inline.insert_button_back_to_main_menu(
                language_code=call.from_user.language_code
                ),
            )
    else:
        await call.message.answer("Неизвестная сумма. Пожалуйста, попробуйте снова.")

    await call.answer()  # Подтверждаем обработку коллбека



# async def handle_payment(call: types.CallbackQuery):
#     # Получаем сумму из callback_data
#     amount_mapping = {
#         "pay_50_rubles": 50,
#         "pay_100_rubles": 100,
#         "pay_300_rubles": 300,
#         "pay_500_rubles": 500,
#         "pay_700_rubles": 700,
#         "pay_1000_rubles": 1000,
#         "pay_3000_rubles": 3000,
#     }
#     amount = amount_mapping.get(call.data)  # Получаем сумму по нажатой кнопке

#     if amount is not None:
#         # Проверяем, есть ли у пользователя сохраненный метод оплаты
#         payment_method_id = await db_manager.get_user_payment_method(call.from_user.id)

#         if payment_method_id:
#             # Если есть сохраненный метод, создаем платеж с его использованием
#             payment_url, payment_id = await create_payment(
#                 amount, call.from_user.id, payment_method_id
#             )
#         else:
#             # Если нет сохраненного метода, создаем обычный платеж
#             payment_url, payment_id = await create_payment(amount, call.from_user.id)

#         if payment_url:
#             await call.message.answer(
#                 text=localizer.get_user_localized_text(
#                     user_language_code=call.from_user.language_code,
#                     text_localization=localizer.message.payment_confirmation_message,
#                 ),
#                 parse_mode=types.ParseMode.HTML,
#                 reply_markup=await inline.payment_confirmation_keyboard(
#                     language_code=call.from_user.language_code, payment_url=payment_url
#                 ),
#             )

#             # Запуск проверки статуса платежа
#             payment_success = await check_payment_status(payment_id, call.from_user.id, amount)
#             if payment_success:
#                 await call.message.answer(
#                     text=localizer.get_user_localized_text(
#                         user_language_code=call.from_user.language_code,
#                         text_localization=localizer.message.successfull_payment_message,
#                     ).format(amount=amount),
#                     reply_markup=await inline.insert_button_back_to_main_menu(
#                         language_code=call.from_user.language_code
#                     ),
#                 )
#             else:
#                 await call.message.answer(f"Ваш платеж был отменен.")
#         else:
#             await call.message.answer(
#                 text=localizer.get_user_localized_text(
#                     user_language_code=call.from_user.language_code,
#                     text_localization=localizer.message.payment_assembly_error_message,
#                 ),
#                 parse_mode=types.ParseMode.HTML,
#                 reply_markup=await inline.insert_button_back_to_main_menu(
#                     language_code=call.from_user.language_code
#                 ),
#             )
#     else:
#         await call.message.answer("Неизвестная сумма. Пожалуйста, попробуйте снова.")

#     await call.answer()  # Подтверждаем обработку коллбека


async def create_payment(amount, chat_id):
    id_key = str(uuid.uuid4())
    logger.debug("ПРОВЕРКА_1")
    payment = Payment.create({
    "amount": {
        "value": amount,
        "currency": "RUB"
    },
    "payment_method_data": {
        "type": "sberbank"
    },
    "confirmation": {
        "type": "redirect",
        "return_url": "https://t.me/VPNizatorBot"
    },
    "capture": True,
    "metadata": {
        "chat_id": chat_id
    },
    "description": "Пополнение баланса VPNizator",
    "receipt": {
        "customer": {
            "email": "user@example.com"  # Или номер телефона, если нет email
        },
        "items": [
            {
                "description": "Оплата Подписки",
                "quantity": 1,
                "amount": {
                    "value": amount,
                    "currency": "RUB"
                },
                "vat_code": 1
            }
        ]
    }
    }, id_key)
    logger.debug("ПРОВЕРКА_2")
    return payment.confirmation.confirmation_url, payment.id


# async def create_payment(amount, chat_id, payment_method_id=None):
#     id_key = str(uuid.uuid4())
#     logger.debug("ПРОВЕРКА_1")
#     payment_data = {
#         "amount": {
#             "value": amount,
#             "currency": "RUB"
#             },
#         "payment_method_data": {
#             "type": "bank_card"
#             },
#         "confirmation": {
#             "type": "redirect", 
#             "return_url": "https://t.me/VPNizatorBot"
#             },
#         "capture": True,
#         "metadata": {
#             "chat_id": chat_id
#             },
#         "description": "Пополнение баланса VPNizator",
#     }
#     logger.debug("ПРОВЕРКА_2")
#     # Если у пользователя нет сохраненного метода оплаты, добавляем параметр save_payment_method
#     if payment_method_id is None:
#         payment_data["save_payment_method"] = True
#         logger.debug(f"Creating payment with save_payment_method=True for user {chat_id}")
#     else:
#         payment_data["payment_method_id"] = payment_method_id
#         logger.debug(f"Creating payment with payment_method_id={payment_method_id} for user {chat_id}")
#     logger.debug(f"ULTRABABASRAKA! Full payment data before sending: {payment_data}")
#     payment = Payment.create(payment_data, id_key)
#     logger.debug(f"ULTRABABASRAKA! Payment created: {payment.json()}")
#     logger.debug(f"Payment created: {payment.json()}")
#     return payment.confirmation.confirmation_url, payment.id


async def check_payment_status(payment_id, chat_id, amount):
    # max_attempts = 120  # Максимальное количество попыток (например, 10 минут с шагом 5 секунд)
    # attempts = 0
    # Опрос API ЮKassa на предмет статуса платежа
    payment = json.loads((Payment.find_one(payment_id)).json())

    while payment['status'] == 'pending':   #and attempts < max_attempts
        logger.info(f"Платеж {payment_id} для пользователя {chat_id} находится в ожидании.")
        await asyncio.sleep(5)  # Ожидание 5 секунд перед следующим запросом
        payment = json.loads((Payment.find_one(payment_id)).json())
        # attempts += 1
    if payment['status'] == 'succeeded':
        logger.info(f"Платеж {payment_id} успешно выполнен пользователем {chat_id}.")
        # Обновляем баланс пользователя
        await db_manager.update_user_balance(chat_id, amount)
        return True
    elif payment['status'] == 'canceled':
        logger.info(f"Платеж {payment_id} был отменен для пользователя {chat_id}.")
        return False


# async def check_payment_status(payment_id, chat_id, amount):
#     # max_attempts = 120  # Максимальное количество попыток (например, 10 минут с шагом 5 секунд)
#     # attempts = 0
#     # Опрос API ЮKassa на предмет статуса платежа
#     payment = json.loads((Payment.find_one(payment_id)).json())
#     # Логируем ответ на первый запрос к ЮKassa
#     logger.debug(f"Initial payment status for payment_id={payment_id}: {payment}")

#     while payment["status"] == "pending":  # and attempts < max_attempts
#         logger.info(f"Платеж {payment_id} для пользователя {chat_id} находится в ожидании.")
#         await asyncio.sleep(5)  # Ожидание 5 секунд перед следующим запросом
#         payment = json.loads((Payment.find_one(payment_id)).json())
#         # attempts += 1
#         logger.debug(f"Updated payment status for payment_id={payment_id}: {payment}")

#     if payment["status"] == "succeeded":
#         logger.info(f"Платеж {payment_id} успешно выполнен пользователем {chat_id}.")
#         # Сохраняем payment_method_id, если он есть
#         if "payment_method" in payment:
#             logger.debug(f"Saving payment_method_id={payment['payment_method']['id']} for user {chat_id}")
#             await db_manager.save_user_payment_method(chat_id, payment["payment_method"]["id"])

#         # Обновляем баланс пользователя
#         await db_manager.update_user_balance(chat_id, amount)
#         return True
#     elif payment["status"] == "canceled":
#         logger.info(f"Платеж {payment_id} был отменен для пользователя {chat_id}.")
#         return False
