from os import getenv

from dotenv import load_dotenv
from flag import flag

from source.utils import IPInfo


class DotEnvVariableNotFound(Exception):
    def __init__(self, variable_name: str):
        self.variable_name = variable_name

    def __str__(self):
        return f"Variable {self.variable_name} not found in .env file"


class Configuration:
    def __init__(self):
        load_dotenv()
        self._bot_token: str = self._get_bot_token()
        self._yookassa_shop_id: str = self._get_yookassa_shop_id()  # Добавляем shop_id
        self._yookassa_api_token: str = self._get_yookassa_api_token()
        self._admins_ids: list[int] = self._get_admins_ids()
        self._user_config_prefix: str = self._get_user_config_prefix()
        self._database_connection_parameters: dict[str, str] = (
            self._get_database_connection_parameters()
        )
        self._xray_publickey: str = self._get_xray_publickey()
        self._xray_shortid: str = self._get_xray_shortid()
        self._xray_config_path: str = self._get_xray_config_path()
        self._server_ip: str = self._get_server_ip()
        self._server_country: str = self._get_server_country()
        self._xray_sni: str = self._get_xray_sni()

    def _get_bot_token(self) -> str:
        bot_token = getenv("TG_BOT_TOKEN")
        if not bot_token:
            raise DotEnvVariableNotFound("TG_BOT_TOKEN")
        return bot_token

    def _get_yookassa_shop_id(self) -> str:  # Новый метод для shop_id
        yookassa_shop_id = getenv("YOOKASSA_SHOP_ID")
        if not yookassa_shop_id:
            raise DotEnvVariableNotFound("YOOKASSA_SHOP_ID")
        return yookassa_shop_id

    def _get_yookassa_api_token(self) -> str:  # новый метод
        yookassa_api_token = getenv("YOOKASSA_API_TOKEN")
        if not yookassa_api_token:
            raise DotEnvVariableNotFound("YOOKASSA_API_TOKEN")
        return yookassa_api_token

    def _get_admins_ids(self) -> list[int]:
        admins_ids = getenv("ADMINS_IDS")
        if not admins_ids:
            raise DotEnvVariableNotFound("ADMINS_IDS")
        return [int(admin_id) for admin_id in admins_ids.split(",") if admin_id]

    def _get_user_config_prefix(self) -> str:
        user_config_prefix = getenv("CONFIGS_PREFIX")
        if not user_config_prefix:
            raise DotEnvVariableNotFound("CONFIGS_PREFIX")
        return user_config_prefix

    def _get_database_connection_parameters(self) -> dict[str, str]:
        for parameter in [
            "DB_HOST",
            "DB_PORT",
            "DB_USER",
            "DB_USER_PASSWORD",
            "DB_NAME",
        ]:
            if not getenv(parameter):
                raise DotEnvVariableNotFound(parameter)

        return {
            "host": getenv("DB_HOST"),
            "port": getenv("DB_PORT"),
            "user": getenv("DB_USER"),
            "password": getenv("DB_USER_PASSWORD"),
            "database": getenv("DB_NAME"),
        }

    def _get_xray_publickey(self) -> str:
        xray_publickey = getenv("XRAY_PUBLICKEY")
        if not xray_publickey:
            raise DotEnvVariableNotFound("XRAY_PUBLICKEY")
        return xray_publickey

    def _get_xray_shortid(self) -> str:
        xray_shortid = getenv("XRAY_SHORTID")
        if not xray_shortid:
            raise DotEnvVariableNotFound("XRAY_SHORTID")
        return xray_shortid

    def _get_xray_config_path(self) -> str:
        xray_config_path = getenv("XRAY_CONFIG_PATH")
        if not xray_config_path:
            raise DotEnvVariableNotFound("XRAY_CONFIG_PATH")
        return xray_config_path

    def _get_server_ip(self) -> str:
        return IPInfo().get_server_ip()

    def _get_server_country(self) -> str:
        ip_info = IPInfo()
        server_country = ip_info.get_server_country_name()
        server_country_code = ip_info.get_server_country_code()
        return f"{flag(server_country_code)} {server_country}"

    def _get_xray_sni(self) -> str:
        xray_sni = getenv("XRAY_SNI")
        if not xray_sni:
            raise DotEnvVariableNotFound("XRAY_SNI")
        return xray_sni

    @property
    def bot_token(self) -> str:
        return self._bot_token

    @property
    def yookassa_shop_id(self) -> str:  # Добавляем новое свойство
        return self._yookassa_shop_id

    @property
    def yookassa_api_token(self) -> str:  # обновленная переменная
        return self._yookassa_api_token

    @property
    def admins_ids(self) -> list[int]:
        return self._admins_ids

    @property
    def user_config_prefix(self) -> str:
        return self._user_config_prefix

    @property
    def database_connection_parameters(self) -> dict[str, str]:
        return self._database_connection_parameters

    @property
    def xray_publickey(self) -> str:
        return self._xray_publickey

    @property
    def xray_shortid(self) -> str:
        return self._xray_shortid

    @property
    def xray_config_path(self) -> str:
        return self._xray_config_path

    @property
    def server_ip(self) -> str:
        return self._server_ip

    @property
    def server_country(self) -> str:
        return self._server_country

    @property
    def xray_sni(self) -> str:
        return self._xray_sni
