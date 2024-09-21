from aiogram import types
from aiogram.dispatcher import FSMContext # МОЖЕТ НАДО УДАЛИТЬ
from source.keyboard import inline

from source.utils import localizer

from source.middlewares import rate_limit

from loguru import logger

@rate_limit(limit=1)
async def function_show_about_us(call: types.CallbackQuery):
    logger.info("SALAM")
    await call.message.edit_text(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.about_us_message,
        ),
        reply_markup=await inline.insert_button_back_to_main_menu(language_code=call.from_user.language_code)
    )
    await call.answer()


@rate_limit(limit=1)
async def function_show_terms_of_use(call: types.CallbackQuery):
    await call.message.edit_text(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.terms_of_use_message,
        ),
        reply_markup=await inline.insert_button_back_to_main_menu(language_code=call.from_user.language_code)
    )
    await call.answer()