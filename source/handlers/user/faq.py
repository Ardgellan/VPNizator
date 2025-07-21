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

    user_lang = call.from_user.language_code
    callback_data = call.data

    # Подбираем ответ по callback_data
    faq_answers = {
        "faq_q1": localizer.message.faq_q1_message,
        "faq_q2": localizer.message.faq_q2_message,
        "faq_q3": localizer.message.faq_q3_message,
    }

    answer_text = localizer.get_user_localized_text(
        user_language_code=user_lang,
        text_localization=faq_answers.get(callback_data, localizer.message.default_faq_answer),
    )

    await call.message.edit_text(
        text=answer_text,
        reply_markup=await support_hub_keyboard(language_code=user_lang),
        parse_mode=types.ParseMode.HTML,
    )