from .base_localized_object import BaseLocalizedObject
from .localized_text_model import LocalizedText


class LocalizedButtonText(BaseLocalizedObject):
    """class with buttons localization from localization.json"""

    def __init__(
        self,
    ) -> None:
        super().__init__(entity_type="button")

    @property
    def pc(self) -> LocalizedText:
        return self._get_entity_text("pc")

    @property
    def android(self) -> LocalizedText:
        return self._get_entity_text("android")

    @property
    def ios(self) -> LocalizedText:
        return self._get_entity_text("ios")

    @property
    def my_configs(self) -> LocalizedText:
        return self._get_entity_text("my_configs")

    @property
    def my_profile(self) -> LocalizedText:
        return self._get_entity_text("my_profile")

    @property
    def show_user(self) -> LocalizedText:
        return self._get_entity_text("show_user")

    @property
    def show_user_configs(self) -> LocalizedText:
        return self._get_entity_text("show_user_configs")

    @property
    def give_user_subscription(self) -> LocalizedText:
        return self._get_entity_text("give_user_subscription")

    @property
    def take_user_subscription(self) -> LocalizedText:
        return self._get_entity_text("take_user_subscription")

    @property
    def show_statistics(self) -> LocalizedText:
        return self._get_entity_text("show_statistics")

    @property
    def accept(self) -> LocalizedText:
        return self._get_entity_text("accept")

    @property
    def reject(self) -> LocalizedText:
        return self._get_entity_text("reject")

    @property
    def delete_keyboard(self) -> LocalizedText:
        return self._get_entity_text("delete_keyboard")

    @property
    def create_new_config(self) -> LocalizedText:
        return self._get_entity_text("create_new_config")

    @property
    def back_to_main_menu(self) -> LocalizedText:
        return self._get_entity_text("back_to_main_menu")

    @property
    def support(self) -> LocalizedText:
        return self._get_entity_text("support")

    @property
    def answer_to_user_as_support(self) -> LocalizedText:
        return self._get_entity_text("answer_to_user_as_support")

    @property
    def give_bonus_configs(self) -> LocalizedText:
        return self._get_entity_text("give_bonus_configs")

    @property
    def ban_user(self) -> LocalizedText:
        return self._get_entity_text("ban_user")

    @property
    def delete_config(self) -> LocalizedText:
        return self._get_entity_text("delete_config")

    @property
    def download_app(self) -> LocalizedText:
        return self._get_entity_text("download_app")

    @property
    def confirm_mailing_message(self) -> LocalizedText:
        return self._get_entity_text("confirm_mailing_message")

    @property
    def trial_period(self) -> LocalizedText:
        return self._get_entity_text("trial_period")

    @property
    def vpn_payment(self) -> LocalizedText:
        return self._get_entity_text("vpn_payment")

    @property
    def vpn_installation_manual(self) -> LocalizedText:
        return self._get_entity_text("vpn_installation_manual")
    
    @property
    def terms_of_use(self) -> LocalizedText:
        return self._get_entity_text("terms_of_use")

    @property
    def about_us(self) -> LocalizedText:
        return self._get_entity_text("about_us")