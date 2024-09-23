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


def register_user_handlers(dp: Dispatcher):
    try:
        # Место 1
        dp.register_message_handler(
            start, commands=["start", "menu"], state="*"
        )

        
        # Место 2
        # dp.register_callback_query_handler(
        #     main_menu_by_button,
        #     lambda call: call.data == "back_to_main_menu",
        #     state="*",
        # )
        
        # Место 3
        dp.register_message_handler(
            show_payment_method, commands="pay", state="*"
        )# Был на месте 3

        # Место 4
        dp.register_message_handler(
            notify_admin_about_new_payment,
            content_types=[
                ContentType.PHOTO,
                ContentType.DOCUMENT,
            ],
            state=PaymentViaBankTransfer.waiting_for_payment_screenshot_or_receipt,
        )# Был на месте 4

        # Место 5
        dp.register_callback_query_handler(
            show_my_profile,
            lambda call: call.data == "my_profile",
            state="*",
        )# Был на месте 5
        
        # Место 6
        dp.register_callback_query_handler(
            ask_user_for_question_to_support,
            lambda call: call.data == "create_support_ticket",
            state="*",
        )# Был на месте 6

        # Место 7
        dp.register_callback_query_handler(
            trial_period_function,
            lambda call: call.data == "trial_period",
            state="*",
        )# Был на месте 7

        # Место 8
        dp.register_callback_query_handler(
            start_trial_period_function,
            lambda call: call.data == "start_trial_period",
            state="*",
        )# Был на месте 8

        # Место 9
        dp.register_message_handler(
            forward_question_to_admins,
            state=AskSupport.waiting_for_question,
        )# Был на месте 9

        register_configs_menu_handlers(dp)
        register_show_help_guide_handlers(dp)
    except Exception as e:
        logger.error(f"Error while registering user handlers: {e}")
    else:
        logger.info("User handlers registered successfully")
