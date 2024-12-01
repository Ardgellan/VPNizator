from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger

from loader import db_manager
from source.keyboard import inline
from source.utils import localizer


async def show_global_stats(call: types.CallbackQuery, state: FSMContext):
    logger.debug("Entered show_global_stats. Headed to get global stats")
    global_stats = await db_manager.get_global_stats()
    logger.debug("Out of gathering global stats. Headed forward")

    await call.message.edit_text(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.global_stats,
        ).format(
            users_registered=global_stats.users_registered,
            users_banned=global_stats.users_banned,
            # users_with_active_subscription=global_stats.users_with_active_subscription,
            active_configs_count=global_stats.active_configs_count,
        ),
        parse_mode=types.ParseMode.HTML,
        reply_markup=await inline.insert_button_back_to_main_menu(
            language_code=call.from_user.language_code,
        ),
    )
