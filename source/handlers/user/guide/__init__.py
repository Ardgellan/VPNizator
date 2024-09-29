from aiogram import Dispatcher
from aiogram.types import ContentType
from loguru import logger

from .android import show_help_guide_android
from .guide_menu import show_help_guide_inline  # show_help_guide,
from .ios import show_help_guide_ios
from .pc import (
    show_help_guide_pc,
    show_help_guide_macos,
    show_help_guide_windows,
    show_help_guide_linux,
)


def register_show_help_guide_handlers(dp: Dispatcher):
    try:
        # dp.register_message_handler(
        #     show_help_guide,
        #     commands=["help", "guide", "h"],
        #     state="*",
        # )
        dp.register_callback_query_handler(
            show_help_guide_inline,
            lambda call: call.data == "vpn_installation_manual",
            state="*",
        )
        dp.register_callback_query_handler(
            show_help_guide_ios,
            lambda call: call.data == "show_help_ios",
            state="*",
        )
        dp.register_callback_query_handler(
            show_help_guide_android,
            lambda call: call.data == "show_help_android",
            state="*",
        )
        dp.register_callback_query_handler(
            show_help_guide_pc,
            lambda call: call.data == "show_help_pc",
            state="*",
        )
        dp.register_callback_query_handler(
            show_help_guide_macos,
            lambda call: call.data == "show_help_mac",
            state="*",
        )
        dp.register_callback_query_handler(
            show_help_guide_windows,
            lambda call: call.data == "show_help_windows",
            state="*",
        )
        dp.register_callback_query_handler(
            show_help_guide_linux,
            lambda call: call.data == "show_help_linux",
            state="*",
        )

    except Exception as err:
        logger.error(f"Error while registering show_help_guide handlers: {err}")

    else:
        logger.info("show_help_guide handlers registered successfully")
