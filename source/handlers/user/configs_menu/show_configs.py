from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import db_manager
from source.keyboard import inline
from source.middlewares import rate_limit
from source.utils import localizer

from ..check_is_user_banned import is_user_banned


@rate_limit(limit=3)
@is_user_banned
async def show_user_configs(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id

    # Check if the user has any configurations
    is_user_have_any_configs = await db_manager.is_user_have_any_config(user_id=user_id)
    current_subscription = await db_manager.get_current_subscription_cost(user_id)
    current_balance = await db_manager.get_user_balance(user_id)


    if not is_user_have_any_configs:
        message_text = localizer.message.no_configs_found_create_new_one
    else:
        message_text = localizer.message.user_configs_list

    await call.message.edit_text(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=message_text,
        ).format(
            current_balance=current_balance,
            current_subscription=current_subscription,
        ),
        parse_mode=types.ParseMode.HTML,
        reply_markup=await inline.user_configs_list_keyboard(
            user_id=user_id, language_code=call.from_user.language_code
        ),
    )
    await state.finish()
