from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger

from loader import db_manager
from source.keyboard import inline
from source.middlewares import rate_limit
from source.utils import localizer


@rate_limit(limit=1)
async def show_balance_function(call: types.CallbackQuery, state: FSMContext):

    current_balance = await db_manager.get_user_balance(user_id=call.from_user.id)

    await call.message.edit_text(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.my_balance_message,
        ).format(current_balance=current_balance),
        parse_mode=types.ParseMode.HTML,
        reply_markup=await inline.insert_button_back_to_main_menu(
            language_code=call.from_user.language_code
        ),
    )
    await state.finish()
