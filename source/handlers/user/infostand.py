from aiogram import types

from loader import db_manager
from source.keyboard import inline

from source.utils import localizer

from loguru import logger

from source.middlewares import rate_limit
from .check_is_user_banned import is_user_banned


# @rate_limit(limit=1)
# @is_user_banned
# async def show_about_us(call: types.CallbackQuery):
#     await call.message.edit_text(
#         text=localizer.get_user_localized_text(
#             user_language_code=call.from_user.language_code,
#             text_localization=localizer.message.about_us_message,
#         ),
#         reply_markup=await inline.insert_button_back_to_main_menu(language_code=call.from_user.language_code)
#     )
#     await call.answer()


# @rate_limit(limit=1)
# @is_user_banned
# async def show_terms_of_use(call: types.CallbackQuery):
#     await call.message.edit_text(
#         text=localizer.get_user_localized_text(
#             user_language_code=call.from_user.language_code,
#             text_localization=localizer.message.terms_of_use_message,
#         ),
#         reply_markup=await inline.insert_button_back_to_main_menu(language_code=call.from_user.language_code)
#     )
#     await call.answer()

@rate_limit(limit=1)
@is_user_banned
async def show_about_us(call: types.CallbackQuery):
    logger.debug("Гарбанушка 1")
    await call.message.answer("SALAM")
    await call.answer()
    logger.info("Гарбанушка 2")

@rate_limit(limit=1)
@is_user_banned
async def show_terms_of_use(call: types.CallbackQuery):
    logger.debug("Джабулака 1")
    await call.message.answer("SALAM")
    await call.answer()
    logger.debug("Джабулака 2")