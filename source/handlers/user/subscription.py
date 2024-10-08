from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger
from datetime import datetime

from loader import db_manager
from source.utils import localizer
from source.utils.xray import xray_config
from source.keyboard import inline


# async def manual_renew_subscription(call: types.CallbackQuery, state: FSMContext):

#     # Узнаем есть ли у юзера вообще конфиги чтобы их обновлять
#     user_id = call.from_user.id
#     configs_to_renew = await db_manager.is_user_have_any_config(user_id)

#     if not configs_to_renew:
#         await call.message.answer(
#             text=localizer.get_user_localized_text(
#                 user_language_code=call.from_user.language_code,
#                 text_localization=localizer.message.nothing_to_renew_message,
#             ),
#             parse_mode=types.ParseMode.HTML,
#         )
#         await call.answer()
#         return

#     # Проверяем время последнего платежа
#     subscription_is_active = await db_manager.get_subscription_status(user_id)

#     if subscription_is_active:
#         await call.message.answer(
#             text=localizer.get_user_localized_text(
#                 user_language_code=call.from_user.language_code,
#                 text_localization=localizer.message.subscription_is_active,
#             ),
#             parse_mode=types.ParseMode.HTML,
#         )
#         await call.answer()
#         return

#     # Получаем текущий баланс и стоимость подписки
#     current_balance = await db_manager.get_user_balance(user_id)
#     subscription_cost = await db_manager.get_current_subscription_cost(user_id)

#    if current_balance >= subscription_cost:
#     async with db_manager.transaction() as conn:
#         try:
#             # Продлеваем подписку: обновляем баланс и время последнего платежа
#             await db_manager.update_user_balance(user_id, -subscription_cost, conn=conn)
#             await db_manager.update_last_subscription_payment(user_id, datetime.now(), conn=conn)

#             # Если оба обновления прошли успешно, восстанавливаем конфиги пользователя в Xray
#             await xray_config.reactivate_user_configs_in_xray([user_id])

#             await call.message.answer(
#                 text=localizer.get_user_localized_text(
#                     user_language_code=call.from_user.language_code,
#                     text_localization=localizer.message.subscription_renewed_successfully,
#                 ),
#                 parse_mode=types.ParseMode.HTML,
#             )
#         except Exception as e:
#             # Если произошла ошибка, транзакция откатывается, и конфиги не восстанавливаются
#             logger.error(f"Error during subscription renewal for user {user_id}: {str(e)}")
#             await call.message.answer(
#                 text=localizer.get_user_localized_text(
#                     user_language_code=call.from_user.language_code,
#                     text_localization=localizer.message.error_occurred_during_sub_renewal,
#                 ),
#                 parse_mode=types.ParseMode.HTML,
#             )
#     else:
#         # Недостаточно средств
#         await call.message.answer(
#         text=localizer.get_user_localized_text(
#             user_language_code=call.from_user.language_code,
#             text_localization=localizer.message.insufficient_balance_for_sub_renewal,
#         ),
#         parse_mode=types.ParseMode.HTML,
#     )

#     await call.answer()


async def manual_renew_subscription(call: types.CallbackQuery, state: FSMContext):

    # Узнаем, есть ли у юзера вообще конфиги, чтобы их обновлять
    user_id = call.from_user.id
    configs_to_renew = await db_manager.is_user_have_any_config(user_id)

    if not configs_to_renew:
        await call.message.answer(
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.nothing_to_renew_message,
            ),
            parse_mode=types.ParseMode.HTML,
        )
        await call.answer()
        return

    # Проверяем время последнего платежа
    subscription_is_active = await db_manager.get_subscription_status(user_id)

    if subscription_is_active:
        await call.message.answer(
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.subscription_is_active,
            ),
            parse_mode=types.ParseMode.HTML,
        )
        await call.answer()
        return

    # Получаем текущий баланс и стоимость подписки
    current_balance = await db_manager.get_user_balance(user_id)
    subscription_cost = await db_manager.get_current_subscription_cost(user_id)

    if current_balance >= subscription_cost:
        async with db_manager.transaction() as conn:
            try:
                logger.debug("Step_1")
                # Продлеваем подписку: обновляем баланс и время последнего платежа
                await db_manager.update_user_balance(user_id, -subscription_cost, conn=conn)
                logger.debug("Step_2")
                await db_manager.update_last_subscription_payment(
                    user_id, datetime.now(), conn=conn
                )
                logger.debug("Step_3")
                await xray_config.reactivate_user_configs_in_xray([user_id])
                logger.debug("Step_4")
                await call.message.answer(
                    text=localizer.get_user_localized_text(
                        user_language_code=call.from_user.language_code,
                        text_localization=localizer.message.subscription_renewed_successfully,
                    ),
                    parse_mode=types.ParseMode.HTML,
                )
            except Exception as e:
                # Если произошла ошибка, транзакция откатывается, и конфиги не восстанавливаются
                logger.error(f"Error during subscription renewal for user {user_id}: {str(e)}")
                await call.message.answer(
                    text=localizer.get_user_localized_text(
                        user_language_code=call.from_user.language_code,
                        text_localization=localizer.message.error_occurred_during_sub_renewal,
                    ),
                    parse_mode=types.ParseMode.HTML,
                )
    else:
        # Недостаточно средств
        await call.message.answer(
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.insufficient_balance_for_sub_renewal,
            ),
            parse_mode=types.ParseMode.HTML,
        )

    await call.answer()
