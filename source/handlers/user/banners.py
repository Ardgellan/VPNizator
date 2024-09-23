from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger

from loader import db_manager
from source.keyboard import inline
from source.middlewares import rate_limit
from source.utils import localizer

async def terms_of_use_function(call: types.CallbackQuery, state: FSMContext):
    
    await state.finish()

    await call.message.answer(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.terms_of_use_message,
        ),
        reply_markup=await inline.insert_button_back_to_main_menu(
            language_code=call.from_user.language_code,
        )
    )

    await call.answer()