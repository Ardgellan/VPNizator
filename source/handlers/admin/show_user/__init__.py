from aiogram import Dispatcher
from loguru import logger

# from .ban_toggle import toggle_ban_for_user

from .show_user_profile import *




def register_admin_show_user_handlers(dp: Dispatcher):
    try:
        dp.register_callback_query_handler(
            show_info_about_user,
            lambda call: call.data.startswith("show_user")
            and not call.data.startswith("show_users_configs"),
            state="*",
        )
        dp.register_message_handler(
            check_is_user_exist,
            content_types=types.ContentTypes.TEXT,
            state=GetUserInfo.wait_for_user_id_or_username,
        )

        # dp.register_callback_query_handler(
        #     toggle_ban_for_user,
        #     lambda call: call.data.startswith("ban_user_"),
        #     state="*",
        # )


    except Exception as e:
        logger.error(f"Error while registering admin handlers: {e}")

    else:
        logger.info("Admin handlers for show user funcs registered successfully")
