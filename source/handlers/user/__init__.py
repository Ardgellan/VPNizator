from aiogram import Dispatcher
from aiogram.types import ContentType
from loguru import logger

from .start import start, main_menu_by_button

# from .pay import (
#     show_balance_top_up_menu_function,
#     handle_payment,
#     process_pre_checkout_query,
#     successful_payment,
# )
from .pay import *

from .configs_menu.show_configs import show_user_configs
from .trial import trial_period_function, start_trial_period_function
from .subscription import manual_renew_subscription
from .banners import about_us_function, terms_of_use_function
from .ask_support import *
from .balance import show_balance_function

from .configs_menu import register_configs_menu_handlers
from .guide import register_show_help_guide_handlers


def register_user_handlers(dp: Dispatcher):
    try:

        dp.register_message_handler(start, commands=["start", "menu"], state="*")

        dp.register_callback_query_handler(
            main_menu_by_button,
            lambda call: call.data == "back_to_main_menu",
            state="*",
        )

        dp.register_callback_query_handler(
            show_balance_top_up_menu_function,
            lambda call: call.data == "balance_top_up",
            state="*",
        )

        dp.register_callback_query_handler(
            handle_payment, lambda call: call.data.startswith("pay_"), state="*"
        )

        dp.register_callback_query_handler(
            show_balance_function,
            lambda call: call.data == "my_balance",
            state="*",
        )

        dp.register_callback_query_handler(
            show_user_configs,
            lambda call: call.data == "my_configs",
            state="*",
        )

        dp.register_callback_query_handler(
            manual_renew_subscription,
            lambda call: call.data == "renew_subscription",
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
            terms_of_use_function,
            lambda call: call.data == "terms_of_use",
            state="*",
        )

        dp.register_callback_query_handler(
            about_us_function,
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
