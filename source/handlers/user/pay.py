from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils import exceptions
import asyncio
import uuid
import json

from loguru import logger
from yookassa import Configuration, Payment

from loader import dp, db_manager
from source.keyboard import inline
from source.utils import localizer
from source.data import config
from source.middlewares import rate_limit
from .check_is_user_banned import is_user_banned

# Настройка конфигурации для ЮKassa
Configuration.account_id = config.yookassa_shop_id
Configuration.secret_key = config.yookassa_api_token
# ВАЖНО: Ставим таймаут 15 секунд, чтобы бот не висел вечно при проблемах с сетью
Configuration.timeout = 15 


@is_user_banned
@rate_limit(limit=1)
async def show_balance_top_up_menu_function(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    
    # Безопасный ответ на коллбек
    try:
        await call.answer()
    except exceptions.InvalidQueryID:
        pass
    except Exception as e:
        logger.error(f"Error answering callback: {e}")

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
    # Безопасный ответ в самом начале
    try:
        await call.answer()
    except exceptions.InvalidQueryID:
        pass 
    except Exception as e:
        logger.error(f"Error answering payment callback: {e}")
    
    amount_mapping = {
        "pay_50_rubles": 50,
        "pay_100_rubles": 100,
        "pay_300_rubles": 300,
        "pay_500_rubles": 500,
        "pay_700_rubles": 700,
        "pay_1000_rubles": 1000,
        "pay_3000_rubles": 3000,
    }
    amount = amount_mapping.get(call.data)

    if amount is not None:
        try:
            logger.info(f"User {call.from_user.id} initiating payment for {amount} RUB")
            
            # Создаем платеж (асинхронно)
            payment_url, payment_id = await create_payment(amount, call.from_user.id)

            if payment_url:
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

                # Запускаем проверку статуса
                await check_payment_status(
                    payment_id, 
                    call.from_user.id, 
                    amount, 
                    call.from_user.language_code
                )
            else:
                logger.error("Payment URL was None")
                await call.message.answer("Ошибка получения ссылки на оплату.")

        except Exception as e:
            # Если словим таймаут сети или ошибку ключей
            logger.error(f"FATAL ERROR creating payment for user {call.from_user.id}: {e}")
            await call.message.answer(
                text="Произошла ошибка соединения с платежной системой. Попробуйте позже.",
                reply_markup=await inline.insert_button_back_to_main_menu(
                    language_code=call.from_user.language_code
                ),
            )
    else:
        await call.message.answer("Неизвестная сумма. Пожалуйста, попробуйте снова.")


async def create_payment(amount, chat_id):
    loop = asyncio.get_running_loop()
    
    def _create_sync():
        id_key = str(uuid.uuid4())
        try:
            return Payment.create(
                {
                    "amount": {"value": str(amount), "currency": "RUB"},
                    "confirmation": {"type": "redirect", "return_url": "https://t.me/VPNizatorBot"},
                    "capture": True,
                    "metadata": {"chat_id": chat_id},
                    "description": "Пополнение баланса VPNizator",
                    "receipt": {
                        "customer": {"email": "user@example.com"},
                        "items": [
                            {
                                "description": "Оплата Подписки",
                                "quantity": "1",
                                "amount": {"value": str(amount), "currency": "RUB"},
                                "vat_code": 1,
                            }
                        ],
                    },
                },
                id_key,
            )
        except Exception as e:
            raise e

    payment = await loop.run_in_executor(None, _create_sync)
    return payment.confirmation.confirmation_url, payment.id


async def check_payment_status(payment_id, chat_id, amount, language_code):
    loop = asyncio.get_running_loop()

    def _get_status_sync():
        p = Payment.find_one(payment_id)
        return p.status

    try:
        # Первая проверка
        status = await loop.run_in_executor(None, _get_status_sync)
        
        # Счетчик безопасности (15 минут максимум)
        checks = 0
        max_checks = 180 # 180 * 5 сек = 15 минут

        while status == "pending" and checks < max_checks:
            await asyncio.sleep(5)
            status = await loop.run_in_executor(None, _get_status_sync)
            checks += 1

        if status == "succeeded":
            logger.info(f"Payment {payment_id} SUCCEEDED for user {chat_id}.")
            
            # Обновление баланса (3 попытки)
            success = False
            for attempt in range(3):
                try:
                    async with db_manager.transaction() as conn:
                        await db_manager.update_user_balance(chat_id, amount, conn=conn)
                    
                    logger.info(f"Balance updated for user {chat_id} (+{amount} rub).")
                    
                    current_balance = await db_manager.get_user_balance(chat_id)
                    
                    await dp.bot.send_message(
                        chat_id=chat_id,
                        text=localizer.get_user_localized_text(
                            user_language_code=language_code,
                            text_localization=localizer.message.successfull_payment_message,
                        ).format(amount=amount, current_balance=current_balance),
                        parse_mode=types.ParseMode.HTML,
                        reply_markup=await inline.successfull_payment_keyboard(language_code)
                    )
                    success = True
                    break
                except Exception as e:
                    logger.error(f"DB Error updating balance (attempt {attempt+1}): {e}")
                    await asyncio.sleep(2)

            if not success:
                logger.critical(f"CRITICAL: Money taken but balance NOT updated! User: {chat_id}, Amount: {amount}")
                await dp.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️<b>CRITICAL ERROR. Please contact support immediately.</b>",
                    parse_mode=types.ParseMode.HTML,
                )
                return False
            return True

        elif status == "canceled":
            logger.info(f"Payment {payment_id} CANCELED for user {chat_id}.")
            return False
        
        else:
            logger.info(f"Payment {payment_id} timeout or unknown status: {status}")
            return False
            
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")
        return False