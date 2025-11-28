from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils import exceptions
import json
import asyncio
import traceback # Импортируем для полной детализации ошибок

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
@rate_limit(limit=1)
async def show_balance_top_up_menu_function(call: types.CallbackQuery, state: FSMContext):
    # logger.info(f"Пользователь {call.from_user.id} открыл меню пополнения баланса")
    await state.finish()
    
    # Безопасный answer, чтобы не мешал диагностике
    try:
        await call.answer()
    except:
        pass

    await call.message.edit_text(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.balance_top_up_message,
        ),
        reply_markup=await inline.balance_top_up_menu_keyboard(
            language_code=call.from_user.language_code
        ),
    )


@rate_limit(limit=1)
async def handle_payment(call: types.CallbackQuery):
    logger.info(f"⚡️ [DIAGNOSTIC] 1. Хендлер запущен. Юзер: {call.from_user.id}, Кнопка: {call.data}")

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
        logger.info(f"⚡️ [DIAGNOSTIC] 2. Сумма определена: {amount}. Вызываем create_payment...")
        
        try:
            # Создаем платеж с соответствующей суммой
            # Внимание: тут нет await, если функция синхронная, но ты ее пометил как async def
            # поэтому await нужен.
            payment_url, payment_id = await create_payment(amount, call.from_user.id)
            
            logger.info(f"⚡️ [DIAGNOSTIC] 5. Платеж создан успешно! ID: {payment_id}")

            if payment_url:
                logger.info(f"⚡️ [DIAGNOSTIC] 6. Отправляем ссылку пользователю...")
                await call.message.answer(
                    text=localizer.get_user_localized_text(
                        user_language_code=call.from_user.language_code,
                        text_localization=localizer.message.payment_confirmation_message,
                    ),
                    parse_mode=types.ParseMode.HTML,
                    reply_markup=await inline.payment_confirmation_keyboard(
                        language_code=call.from_user.language_code, payment_url=payment_url
                    ),
                )

                # Запуск проверки статуса платежа
                logger.info(f"⚡️ [DIAGNOSTIC] 7. Запускаем проверку статуса (цикл ожидания)...")
                payment_success = await check_payment_status(payment_id, call.from_user.id, amount)
                
                if payment_success:
                    logger.info(f"⚡️ [DIAGNOSTIC] 8. Оплата прошла успешно!")
                    current_balance = await db_manager.get_user_balance(call.from_user.id)
                    await call.message.answer(
                        text=localizer.get_user_localized_text(
                            user_language_code=call.from_user.language_code,
                            text_localization=localizer.message.successfull_payment_message,
                        ),
                        parse_mode=types.ParseMode.HTML,
                        reply_markup=await inline.successfull_payment_keyboard(
                            language_code=call.from_user.language_code
                        ),
                    )
            else:
                logger.error(f"⚡️ [DIAGNOSTIC] ERROR: URL платежа пустой!")
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
        except Exception as e:
            logger.error(f"⚡️ [DIAGNOSTIC] CRITICAL ERROR в handle_payment:\n{traceback.format_exc()}")
            await call.message.answer(f"Произошла ошибка: {str(e)}")
            
    else:
        logger.warning(f"⚡️ [DIAGNOSTIC] Сумма НЕ определена. call.data={call.data}")
        await call.message.answer("Неизвестная сумма. Пожалуйста, попробуйте снова.")

    try:
        await call.answer()  # Подтверждаем обработку коллбека
    except Exception:
        pass


async def create_payment(amount, chat_id):
    logger.info(f"⚡️ [DIAGNOSTIC] 3. Внутри create_payment. Начинаем синхронный запрос к ЮКассе...")
    id_key = str(uuid.uuid4())
    
    try:
        # Этот вызов блокирующий. Если тут зависнет — значит сеть или ЮКасса.
        payment = Payment.create(
            {
                "amount": {"value": amount, "currency": "RUB"},
                "confirmation": {"type": "redirect", "return_url": "https://t.me/VPNizatorBot"},
                "capture": True,
                "metadata": {"chat_id": chat_id},
                "description": "Пополнение баланса VPNizator",
                "receipt": {
                    "customer": {"email": "user@example.com"},  # Или номер телефона, если нет email
                    "items": [
                        {
                            "description": "Оплата Подписки",
                            "quantity": 1,
                            "amount": {"value": amount, "currency": "RUB"},
                            "vat_code": 1,
                        }
                    ],
                },
            },
            id_key,
        )
        logger.info(f"⚡️ [DIAGNOSTIC] 4. Ответ от ЮКассы получен!")
        return payment.confirmation.confirmation_url, payment.id
        
    except Exception as e:
        logger.error(f"⚡️ [DIAGNOSTIC] Ошибка ПРИ СОЗДАНИИ платежа (Payment.create):\n{traceback.format_exc()}")
        raise e


async def check_payment_status(payment_id, chat_id, amount):
    logger.info(f"⚡️ [DIAGNOSTIC] Начало проверки статуса {payment_id}")
    try:
        payment = json.loads((Payment.find_one(payment_id)).json())

        while payment["status"] == "pending":
            # logger.info(f"Платеж {payment_id} для пользователя {chat_id} находится в ожидании.")
            await asyncio.sleep(5)
            payment = json.loads((Payment.find_one(payment_id)).json())

        logger.info(f"⚡️ [DIAGNOSTIC] Статус изменился: {payment['status']}")

        if payment["status"] == "succeeded":
            logger.info(f"Платеж {payment_id} успешно выполнен пользователем {chat_id}.")

            # Попробуем трижды обновить баланс
            attempts = 3
            success = False
            for attempt in range(attempts):
                try:
                    # Используем транзакцию для обновления баланса
                    async with db_manager.transaction() as conn:
                        await db_manager.update_user_balance(chat_id, amount, conn=conn)
                    logger.info(
                        f"Баланс пользователя {chat_id} был успешно обновлен на {amount} рублей (попытка {attempt + 1})."
                    )
                    success = True
                    break  # Если обновление прошло успешно, выходим из цикла
                except Exception as e:
                    logger.error(
                        f"Ошибка при обновлении баланса пользователя {chat_id} (попытка {attempt + 1}): {str(e)}"
                    )
                    await asyncio.sleep(2)  # Ожидание между попытками

            if success:
                return True
            else:
                # Если все попытки не удались, отправляем сообщение в лог и пользователю
                logger.critical(
                    f"Не удалось пополнить баланс пользователя {chat_id} после успешного платежа. Пожалуйста, проверьте вручную."
                )
                await dp.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️<b>Критическая ошибка в процессе пополнения баланса...</b>",
                    parse_mode=types.ParseMode.HTML,
                )
                return False

        elif payment["status"] == "canceled":
            logger.info(f"Платеж {payment_id} был отменен для пользователя {chat_id}.")
            return False
            
    except Exception as e:
        logger.error(f"⚡️ [DIAGNOSTIC] Ошибка внутри check_payment_status:\n{traceback.format_exc()}")
        return False