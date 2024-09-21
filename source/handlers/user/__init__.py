from aiogram import Dispatcher
from aiogram.types import ContentType
from loguru import logger

from source.utils.states.user import PaymentViaBankTransfer

from .ask_support import *
from .configs_menu import register_configs_menu_handlers
from .configs_menu.show_configs import *
from .guide import register_show_help_guide_handlers
from .my_profile import show_my_profile
from .pay import *
from .start import *
from .trial import *
from .infostand import *


def register_user_handlers(dp: Dispatcher):
    try:
        dp.register_message_handler(start, commands=["start", "menu"], state="*")
        dp.register_callback_query_handler(
            main_menu_by_button,
            lambda call: call.data == "back_to_main_menu",
            state="*",
        )
        dp.register_message_handler(show_payment_method, commands="pay", state="*")

        dp.register_message_handler(
            notify_admin_about_new_payment,
            content_types=[
                ContentType.PHOTO,
                ContentType.DOCUMENT,
            ],
            state=PaymentViaBankTransfer.waiting_for_payment_screenshot_or_receipt,
        )

        dp.register_callback_query_handler(
            show_my_profile,
            lambda call: call.data == "my_profile",
            state="*",
        )

        dp.register_callback_query_handler(
            ask_user_for_question_to_support,
            lambda call: call.data == "create_support_ticket",
            state="*",
        )

        dp.register_callback_query_handler(
            trial_period_function,
            lambda call: call.data == "trial_period",
            state="*",
        )

        dp.register_callback_query_handler(
            start_trial_period_function,
            lambda call: call.data == "start_trial_period",
            state="*",
        )

        dp.register_callback_query_handler(
            show_terms_of_use,
            lambda call: call.data == "terms_of_use",
            state="*",
        )

        dp.register_callback_query_handler(
            show_about_us,
            lambda call: call.data == "about_us",
            state="*",
        )

        dp.register_message_handler(
            forward_question_to_admins,
            state=AskSupport.waiting_for_question,
        )

        register_configs_menu_handlers(dp)
        register_show_help_guide_handlers(dp)
    except Exception as e:
        logger.error(f"Error while registering user handlers: {e}")
    else:
        logger.info("User handlers registered successfully")
