from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger

from loader import db_manager
from source.keyboard import inline
from source.middlewares import rate_limit
from source.utils import localizer


@rate_limit(limit=1)
async def frequently_asked_questions(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.edit_text(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.faq_message,
        ),
        reply_markup=await inline.faq_keyboard(
            language_code=call.from_user.language_code,
        ),
    )


@rate_limit(limit=1)
async def show_faq_answer(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    logger.debug("Salam_1")
    user_lang = call.from_user.language_code
    callback_data = call.data

    # Подбираем ответ по callback_data
    faq_answers = {
        "faq_q1": localizer.message.faq_q1_message,
        "faq_q2": localizer.message.faq_q2_message,
        "faq_q3": localizer.message.faq_q3_message,
    }
    answer = faq_answers.get(call.data)
    logger.debug("Salam_2")
    answer_text = localizer.get_user_localized_text(
        user_language_code=user_lang,
        text_localization=answer,
    )
    logger.debug("Salam_3")

    await call.message.edit_text(
        text=answer_text,
        reply_markup=await inline.support_hub_keyboard(language_code=user_lang),
        parse_mode=types.ParseMode.HTML,
    )
    logger.debug("Salam_4")

# @rate_limit(limit=1)
# async def show_faq_answer(call: types.CallbackQuery, state: FSMContext):
#     await state.finish()
#     logger.debug("Salam_1 - handler started")

#     user_lang = call.from_user.language_code
#     callback_data = call.data
#     logger.debug(f"Salam_2 - user_lang: {user_lang}, callback_data: {callback_data}")

#     # Маппинг callback -> локализованный текст
#     faq_answers = {
#         "faq_q1": localizer.message.faq_q1_message,
#         "faq_q2": localizer.message.faq_q2_message,
#         "faq_q3": localizer.message.faq_q3_message,
#     }

#     answer_localization = faq_answers.get(callback_data)
#     if not answer_localization:
#         logger.error(f"Salam_3 - No FAQ answer found for callback_data: {callback_data}")
#         await call.answer("Извините, ответ на этот вопрос не найден.", show_alert=True)
#         return

#     try:
#         answer_text = localizer.get_user_localized_text(
#             user_language_code=user_lang,
#             text_localization=answer_localization,
#         )
#         logger.debug(f"Salam_4 - Localized answer text: {answer_text}")

#         keyboard = await inline.support_hub_keyboard(language_code=user_lang)
#         logger.debug(f"Salam_5 - Keyboard generated: {keyboard}")

#         await call.message.edit_text(
#             text=answer_text,
#             reply_markup=keyboard,
#             parse_mode=types.ParseMode.HTML,
#         )
#         logger.debug("Salam_6 - Message edited successfully")

#     except Exception as e:
#         logger.error(f"Salam_7 - Exception while editing message: {e}", exc_info=True)
#         await call.answer("Произошла ошибка при отображении ответа. Попробуйте позже.", show_alert=True)

