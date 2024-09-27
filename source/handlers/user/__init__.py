from aiogram import Dispatcher
from aiogram.types import ContentType
from loguru import logger

from .ask_support import *
from .banners import about_us_function, terms_of_use_function
from .configs_menu import register_configs_menu_handlers
from .configs_menu.show_configs import *
from .guide import register_show_help_guide_handlers
from .my_profile import show_my_profile
from .start import start, main_menu_by_button
from .trial import trial_period_function, start_trial_period_function
from .subscription import manual_renew_subscription
from .pay import show_balance_top_up_menu_function, handle_payment, process_pre_checkout_query, successful_payment

def register_user_handlers(dp: Dispatcher):
    try:
        # 1
        dp.register_message_handler(start, commands=["start", "menu"], state="*")

        # 2
        dp.register_callback_query_handler(
            main_menu_by_button,
            lambda call: call.data == "back_to_main_menu",
            state="*",
        )
        # 3
        dp.register_callback_query_handler(
            show_balance_top_up_menu_function,
            lambda call: call.data == "balance_top_up",
            state="*",
        )
        
        # 4
        dp.register_callback_query_handler(
            handle_payment,
            lambda call: call.data.startswith("pay_"),
            state="*"
        )

        # 5
        dp.register_pre_checkout_query_handler(process_pre_checkout_query)

        # 6
        dp.register_message_handler(
            successful_payment, content_types=types.ContentType.SUCCESSFUL_PAYMENT
        )

        # 7
        dp.register_callback_query_handler(
            manual_renew_subscription,
            lambda call: call.data == "renew_subscription",
            state="*",
        )

        # 8
        dp.register_callback_query_handler(
            show_my_profile,
            lambda call: call.data == "my_profile",
            state="*",
        )

        # 9
        dp.register_callback_query_handler(
            ask_user_for_question_to_support,
            lambda call: call.data == "create_support_ticket",
            state="*",
        )

        # 10
        dp.register_callback_query_handler(
            trial_period_function,
            lambda call: call.data == "trial_period",
            state="*",
        )

        # 11
        dp.register_callback_query_handler(
            start_trial_period_function,
            lambda call: call.data == "start_trial_period",
            state="*",
        )

        # 12
        dp.register_callback_query_handler(
            terms_of_use_function,
            lambda call: call.data == "terms_of_use",
            state="*",
        )

        # 13
        dp.register_callback_query_handler(
            about_us_function,
            lambda call: call.data == "about_us",
            state="*",
        )

        # 14
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
