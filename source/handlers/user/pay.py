# from aiogram import types
# from aiogram.dispatcher import FSMContext
# from loguru import logger

# from source.data import config
# from source.keyboard import inline
# from source.middlewares import rate_limit
# from source.utils import localizer
# from source.utils.states.user import PaymentViaBankTransfer

# from .check_is_user_banned import is_user_banned


@rate_limit(limit=1)
@is_user_banned
async def show_payment_method(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} started payment")
    await state.finish()
    await message.answer(
        text=localizer.get_user_localized_text(
            user_language_code=message.from_user.language_code,
            text_localization=localizer.message.payment_method_card,
        ).format(
            amount=config.subscription_monthly_price,
            payment_card=config.payment_card,
        ),
        parse_mode=types.ParseMode.HTML,
    )
    await PaymentViaBankTransfer.waiting_for_payment_screenshot_or_receipt.set()


async def notify_admin_about_new_payment(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} started payment")
    await state.finish()
    await message.answer(
        text=localizer.get_user_localized_text(
            user_language_code=message.from_user.language_code,
            text_localization=localizer.message.payment_method_card_success,
        ),
        parse_mode=types.ParseMode.HTML,
    )
    for admin_id in config.admins_ids:
        await message.forward(admin_id)
        admin_user = (await message.bot.get_chat_member(chat_id=admin_id, user_id=admin_id)).user

        await message.bot.send_message(
            chat_id=admin_id,
            text=localizer.get_user_localized_text(
                user_language_code=admin_user.language_code,
                text_localization=localizer.message.admin_notification_about_new_payment,
            ).format(
                user_id=message.from_user.id,
                username=(
                    message.from_user.username
                    if message.from_user.username
                    else message.from_user.full_name
                ),
            ),
            parse_mode=types.ParseMode.HTML,
            reply_markup=await inline.admin_payment_notification_keyboard(
                language_code=admin_user.language_code,
                from_user_id=message.from_user.id,
            ),
        )


# from aiogram import types
# from aiogram.types import LabeledPrice, PreCheckoutQuery

# async def send_test_invoice(message: types.Message):
#     prices = [types.LabeledPrice(label="Тест VPN", amount=100 * 100 )]  # 100 рублей в копейках

#     await message.bot.send_invoice(
#         chat_id=message.chat.id,
#         title="Тестовая оплата VPN",
#         description="Оплата за тестовый VPN на 1 месяц",
#         payload="vpn_test_payment",
#         provider_token="381764678:TEST:95796",  # Тестовый токен от BotFather
#         currency="RUB",
#         prices=prices,
#         # start_parameter="test-vpn-payment"
#     )


# async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
#     await pre_checkout_query.answer(ok=True)  # Подтверждаем, что всё готово для оплаты


# async def successful_payment(message: types.Message):
#     await message.answer("Оплата прошла успешно! Ваш VPN будет активирован.")
#     # Логика активации VPN для пользователя
