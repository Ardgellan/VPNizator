from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger

from loader import db_manager
from source.keyboard import inline
from source.middlewares import rate_limit
from source.utils import localizer


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
