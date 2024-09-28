from .base_localized_object import BaseLocalizedObject
from .localized_text_model import LocalizedText


class LocalizedMessageText(BaseLocalizedObject):
    """class with messages localization from localization.json"""

    def __init__(
        self,
    ) -> None:
        super().__init__(entity_type="message")

    @property
    def new_user_greeting(self) -> LocalizedText:
        return self._get_entity_text("new_user_greeting")

    @property
    def greeting(self) -> LocalizedText:
        return self._get_entity_text("greeting")

    @property
    def payment_method_card(self) -> LocalizedText:
        return self._get_entity_text("payment_method_card")

    @property
    def payment_method_card_success(self) -> LocalizedText:
        return self._get_entity_text("payment_method_card_success")

    @property
    def admin_notification_about_new_payment(self) -> LocalizedText:
        return self._get_entity_text("admin_notification_about_new_payment")

    @property
    def payment_accepted_for_admin(self) -> LocalizedText:
        return self._get_entity_text("payment_accepted_for_admin")

    @property
    def payment_accepted_for_user(self) -> LocalizedText:
        return self._get_entity_text("payment_accepted_for_user")

    @property
    def error_while_accepting_payment(self) -> LocalizedText:
        return self._get_entity_text("error_while_accepting_payment")

    @property
    def reject_payment(self) -> LocalizedText:
        return self._get_entity_text("reject_payment")

    @property
    def user_info(self) -> LocalizedText:
        return self._get_entity_text("user_info")

    @property
    def user_configs_list_active(self) -> LocalizedText:
        return self._get_entity_text("user_configs_list_active")

    @property
    def user_configs_list_inactive(self) -> LocalizedText:
        return self._get_entity_text("user_configs_list_inactive")

    @property
    def no_configs_found_create_new_one(self) -> LocalizedText:
        return self._get_entity_text("no_configs_found_create_new_one")

    @property
    def request_config_name(self) -> LocalizedText:
        return self._get_entity_text("request_config_name")

    @property
    def got_config_name_start_generating(self) -> LocalizedText:
        return self._get_entity_text("got_config_name_start_generating")

    @property
    def config_generated(self) -> LocalizedText:
        return self._get_entity_text("config_generated")

    @property
    def subscription_expired_notification(self) -> LocalizedText:
        return self._get_entity_text("subscription_expired_notification")

    @property
    def subscription_last_day_left_notification(self) -> LocalizedText:
        return self._get_entity_text("subscription_last_day_left_notification")

    @property
    def subscription_two_days_left_notification(self) -> LocalizedText:
        return self._get_entity_text("subscription_two_days_left_notification")

    @property
    def request_user_id_or_username(self) -> LocalizedText:
        return self._get_entity_text("request_user_id_or_username")

    @property
    def error_user_not_found(self) -> LocalizedText:
        return self._get_entity_text("error_user_not_found")

    @property
    def ask_support_question(self) -> LocalizedText:
        return self._get_entity_text("ask_support_question")

    @property
    def support_question_sent_by_user(self) -> LocalizedText:
        return self._get_entity_text("support_question_sent_by_user")

    @property
    def admin_notification_about_new_support_question(self) -> LocalizedText:
        return self._get_entity_text("admin_notification_about_new_support_question")

    @property
    def ask_admin_for_support_answer(self) -> LocalizedText:
        return self._get_entity_text("ask_admin_for_support_answer")

    @property
    def support_answer_from_admin(self) -> LocalizedText:
        return self._get_entity_text("support_answer_from_admin")

    @property
    def support_answer_sent_to_user(self) -> LocalizedText:
        return self._get_entity_text("support_answer_sent_to_user")

    @property
    def you_are_banned(self) -> LocalizedText:
        return self._get_entity_text("you_are_banned")

    @property
    def global_stats(self) -> LocalizedText:
        return self._get_entity_text("global_stats")

    @property
    def ask_admin_for_subscription_duration(self) -> LocalizedText:
        return self._get_entity_text("ask_admin_for_subscription_duration")

    @property
    def subscription_given(self) -> LocalizedText:
        return self._get_entity_text("subscription_given")

    @property
    def admin_give_you_days_subscription(self) -> LocalizedText:
        return self._get_entity_text("admin_give_you_days_subscription")

    @property
    def subscription_duration_must_be_digit(self) -> LocalizedText:
        return self._get_entity_text("subscription_duration_must_be_digit")

    @property
    def you_dont_have_subscription(self) -> LocalizedText:
        return self._get_entity_text("you_dont_have_subscription")

    @property
    def ask_admin_for_count_of_bonus_generations_to_give(self) -> LocalizedText:
        return self._get_entity_text("ask_admin_for_count_of_bonus_generations_to_give")

    @property
    def count_of_bonus_generations_to_give_must_be_digit(self) -> LocalizedText:
        return self._get_entity_text("count_of_bonus_generations_to_give_must_be_digit")

    @property
    def admin_give_you_bonus_config_generations(self) -> LocalizedText:
        return self._get_entity_text("admin_give_you_bonus_config_generations")

    @property
    def confirm_delete_config(self) -> LocalizedText:
        return self._get_entity_text("confirm_delete_config")

    @property
    def config_deleted(self) -> LocalizedText:
        return self._get_entity_text("config_deleted")

    @property
    def help_guide_select_device(self) -> LocalizedText:
        return self._get_entity_text("help_guide_select_device")

    @property
    def help_guide_ios(self) -> LocalizedText:
        return self._get_entity_text("help_guide_ios")

    @property
    def help_guide_android(self) -> LocalizedText:
        return self._get_entity_text("help_guide_android")

    @property
    def create_mailing_message(self) -> LocalizedText:
        return self._get_entity_text("create_mailing_message")

    @property
    def confirm_mailing_message(self) -> LocalizedText:
        return self._get_entity_text("confirm_mailing_message")

    @property
    def mailing_message_sent(self) -> LocalizedText:
        return self._get_entity_text("mailing_message_sent")

    @property
    def trial_period_greeting(self) -> LocalizedText:
        return self._get_entity_text("trial_period_greeting")

    @property
    def trial_period_success(self) -> LocalizedText:
        return self._get_entity_text("trial_period_success")

    @property
    def trial_period_rejection(self) -> LocalizedText:
        return self._get_entity_text("trial_period_rejection")

    @property
    def terms_of_use_message(self) -> LocalizedText:
        return self._get_entity_text("terms_of_use_message")

    @property
    def about_us_message(self) -> LocalizedText:
        return self._get_entity_text("about_us_message")

    @property
    def balance_top_up_message(self) -> LocalizedText:
        return self._get_entity_text("balance_top_up_message")

    @property
    def insufficient_balance_for_conf_gen_message(self) -> LocalizedText:
        return self._get_entity_text("insufficient_balance_for_conf_gen_message")

    @property
    def insufficient_balance_for_sub_renewal(self) -> LocalizedText:
        return self._get_entity_text("insufficient_balance_for_sub_renewal")

    @property
    def subscription_is_active(self) -> LocalizedText:
        return self._get_entity_text("subscription_is_active")

    @property
    def subscription_renewed_successfully(self) -> LocalizedText:
        return self._get_entity_text("subscription_renewed_successfully")

    @property
    def nothing_to_renew_message(self) -> LocalizedText:
        return self._get_entity_text("nothing_to_renew_message")

    @property
    def my_balance_message(self) -> LocalizedText:
        return self._get_entity_text("my_balance_message")

    @property
    def config_requseted(self) -> LocalizedText:
        return self._get_entity_text("config_requseted")

    @property
    def which_os_do_you_have_message(self) -> LocalizedText:
        return self._get_entity_text("which_os_do_you_have_message")

    @property
    def help_guide_message_macos(self) -> LocalizedText:
        return self._get_entity_text("help_guide_message_macos")

    @property
    def help_guide_message_windows(self) -> LocalizedText:
        return self._get_entity_text("help_guide_message_windows")

    @property
    def help_guide_message_linux(self) -> LocalizedText:
        return self._get_entity_text("help_guide_message_linux")
