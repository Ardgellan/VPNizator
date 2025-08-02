from datetime import datetime

from loguru import logger

from source.data import config
from source.utils.models import GlobalStatistics, UserInfo, VpnConfigDB, VpnConfigDB_N

from .connector import DatabaseConnector


class Selector(DatabaseConnector):
    def __init__(self) -> None:
        super().__init__()
        logger.debug("Selector object was initialized")

    async def get_user_by_id(self, user_id: int) -> UserInfo:
        (
            username,
            is_banned,
            created_at,
        ) = await self._get_user_base_info_by_id(user_id)

        if not created_at:
            raise ValueError(f"User {user_id} not found")
        
        user = UserInfo(
            user_id=user_id,
            username=username,
            is_not_banned="🟢" if not is_banned else "🔴",
            created_at=created_at,
        )
        # logger.debug(f"User info object created: {user}")
        return user

    async def _get_user_base_info_by_id(
        self, user_id: int
    ) -> tuple[str, bool, datetime] | tuple[None, None, None]:
        query = f"""--sql
            SELECT username, is_banned, created_at
            FROM users
            WHERE user_id = {user_id};
        """
        result = await self._execute_query(query)
        if result == []:
            logger.error(f"User {user_id} not found")
            return None, None, None
        username, is_banned, created_at = result[0]
        # logger.debug(f"User {user_id} base info was fetched")
        return username, is_banned, created_at

    async def _get_created_configs_count_by_user_id(self, user_id: int) -> int:
        query = f"""--sql
            SELECT COUNT(*)
            FROM vpn_configs
            WHERE user_id = {user_id};
        """
        result = await self._execute_query(query)
        # logger.debug(f"Created configs count for user {user_id} was fetched: {result[0][0]}")
        return result[0][0]

    async def _get_bonus_configs_count_by_user_id(self, user_id: int) -> int:
        query = f"""--sql
            SELECT bonus_config_count
            FROM bonus_configs_for_users
            WHERE user_id = {user_id};
        """
        result = await self._execute_query(query)
        bonus_configs_count = result[0][0] if result else 0
        # logger.debug(f"Bonus configs count for user {user_id} was fetched: {bonus_configs_count}")
        return bonus_configs_count

    async def is_user_registered(self, user_id: int) -> bool:
        query = f"""--sql
            SELECT EXISTS(
                SELECT 1
                FROM users
                WHERE user_id = {user_id}
            );
        """
        result = await self._execute_query(query)
        # logger.debug(f"User {user_id} exist: {result[0][0]}")
        return result[0][0]

    async def is_user_have_any_config(self, user_id: int) -> bool:
        query = f"""--sql
            SELECT EXISTS(
                SELECT 1
                FROM vpn_configs
                WHERE user_id = {user_id}
            );
        """
        result = await self._execute_query(query)
        # logger.debug(f"User {user_id} have any config: {result[0][0]}")
        return result[0][0]

    async def get_user_config_names_and_uuids(self, user_id: int) -> list[VpnConfigDB] | None:
        query = f"""--sql
            SELECT id, config_name, config_uuid
            FROM vpn_configs
            WHERE user_id = {user_id};
        """
        result = await self._execute_query(query)
        # logger.debug(f"User {user_id} configs: {result}")
        if not result:
            return None
        return [
            VpnConfigDB(
                config_id=record[0],
                user_id=user_id,
                config_name=record[1],
                config_uuid=record[2],
            )
            for record in result
        ]

    async def get_user_id_by_username(self, username: str) -> int | None:
        query = f"""--sql
            SELECT user_id
            FROM users
            WHERE username = '{username}';
        """
        result = await self._execute_query(query)
        # logger.debug(f"User id by username {username}: {result}")
        return result[0][0] if result else None

    async def check_is_user_banned(self, user_id: int) -> bool:
        query = f"""--sql
            SELECT is_banned
            FROM users
            WHERE user_id = {user_id};
        """
        result = await self._execute_query(query)
        is_banned = result[0][0] if result else False
        # logger.debug(f"User {user_id} is banned: {is_banned}")
        return is_banned

    async def get_config_name_by_config_uuid(self, config_uuid: str) -> str:
        query = f"""--sql
            SELECT config_name
            FROM vpn_configs
            WHERE config_uuid = '{config_uuid}';
        """
        result = await self._execute_query(query)
        # logger.debug(f"Config name by config uuid {config_uuid}: {result[0][0]}")
        return result[0][0]

    # async def get_global_stats(self) -> GlobalStatistics: #OLD
    #     query = """--sql
    #         SELECT
    #             (SELECT COUNT(*) FROM users) AS users_registered,
    #             (SELECT COUNT(*) FROM users WHERE is_banned) AS users_banned,
    #             (SELECT COUNT(*) FROM users WHERE subscription_is_active = TRUE) AS users_with_active_subscription,
    #             (SELECT COUNT(*) FROM vpn_configs) AS active_configs_count
    #     """
    #     result = await self._execute_query(query)
    #     global_stats = GlobalStatistics(
    #         users_registered=result[0][0],
    #         users_banned=result[0][1],
    #         # users_with_active_subscription=result[0][2],
    #         active_configs_count=result[0][2], # тут изменено [0][3] - yf [0][2]
    #     )
    #     # logger.debug(f"Global stats: {global_stats}")
    #     return global_stats

    async def get_global_stats(self) -> GlobalStatistics:
        query = """--sql
            SELECT
                (SELECT COUNT(*) FROM users) AS users_registered,
                (SELECT COUNT(*) FROM users WHERE is_banned) AS users_banned,
                (SELECT COUNT(*) FROM vpn_configs) AS active_configs_count
        """
        result = await self._execute_query(query)
        global_stats = GlobalStatistics(
            users_registered=result[0][0],
            users_banned=result[0][1],
            active_configs_count=result[0][2], # тут изменено [0][3] - yf [0][2]
        )
        # logger.debug(f"Global stats: {global_stats}")
        return global_stats

    async def get_unblocked_users_ids(self) -> list[int]:
        query = """--sql
            SELECT user_id
            FROM users
            WHERE is_banned = FALSE;
        """
        result = await self._execute_query(query)
        # logger.debug(f"Unblocked users ids: {result}")
        return [record[0] for record in result]

    async def is_trial_used(self, user_id: int) -> bool:
        # logger.debug(f"Breakpoint in debugging is_trial_used #1")
        query = f"""--sql
            SELECT trial_used
            FROM users
            WHERE user_id = {user_id};
        """
        result = await self._execute_query(query)
        # logger.debug(f"Note about used trial was made: {result}")
        return result[0][0] if result else False

    async def get_user_balance(self, user_id: int, conn=None) -> float:
        query = f"""--sql
            SELECT balance
            FROM users
            WHERE user_id = {user_id};
        """
        if conn:
            # Если передано соединение, выполняем запрос через него
            result = await conn.fetchrow(query)
        else:
            # Если соединение не передано, создаем новое и выполняем запрос
            result = await self._execute_query_with_returning_one(query)

        if result:
            balance = result["balance"]
            # logger.debug(f"User {user_id} balance fetched: {balance}")
            return balance
        else:
            logger.error(f"User {user_id} not found or balance could not be retrieved")
            return 0.0

    async def get_current_subscription_cost(self, user_id: int) -> float:
        """Получаем текущую стоимость подписки пользователя"""
        # Получаем количество активных конфигов пользователя
        query = f"""--sql
            SELECT COUNT(*)
            FROM vpn_configs
            WHERE user_id = {user_id}
        """
        result = await self._execute_query(query)

        if result:
            active_configs_count = result[0][0]  # Количество активных конфигов
            subscription_cost = active_configs_count * 3  # Стоимость подписки — 3 рубля за конфиг
            return subscription_cost
        else:
            logger.error(f"Не удалось получить активные конфиги для пользователя {user_id}")
            return 0.0

    async def get_users_with_active_configs(self) -> list[int]:
        """Получаем список всех пользователей, у которых есть активные конфиги"""
        query = """--sql
            SELECT DISTINCT user_id
            FROM vpn_configs;
        """
        result = await self._execute_query(query)
        return [record[0] for record in result] if result else []

    # async def get_users_ids_with_last_day_left_subscription(self) -> list[int]: #OLD
    #     """
    #     Получаем список пользователей, у которых после списания за текущий день
    #     подписки баланс не позволяет оплатить следующий день подписки.
    #     """
    #     query = """--sql
    #         SELECT DISTINCT u.user_id
    #         FROM users u
    #         JOIN vpn_configs vc ON vc.user_id = u.user_id
    #         WHERE u.subscription_is_active = TRUE  -- Только активные пользователи
    #         GROUP BY u.user_id, u.balance
    #         HAVING u.balance < (COUNT(vc.config_uuid) * 3)
    #     """
    #     result = await self._execute_query(query)
    #     return [record[0] for record in result] if result else []

    async def get_users_ids_with_last_day_left_subscription(self) -> list[int]:
        """
        Получаем список пользователей, у которых после списания за текущий день
        подписки баланс не позволяет оплатить следующий день подписки.
        """
        query = """--sql
            SELECT DISTINCT u.user_id
            FROM users u
            JOIN vpn_configs vc ON vc.user_id = u.user_id
            GROUP BY u.user_id, u.balance
            HAVING u.balance < (COUNT(vc.config_uuid) * 3)
        """
        result = await self._execute_query(query)
        return [record[0] for record in result] if result else []

    async def get_users_ids_with_two_days_left_subscription(self) -> list[int]:
        """
        Получаем список пользователей, у которых баланс позволяет оплатить один день подписки,
        но не хватает на два дня.
        """
        query = """--sql
            SELECT DISTINCT u.user_id
            FROM users u
            JOIN vpn_configs vc ON vc.user_id = u.user_id
            GROUP BY u.user_id, u.balance
            HAVING u.balance >= (COUNT(vc.config_uuid) * 3)
                AND u.balance < (COUNT(vc.config_uuid) * 6)
        """
        result = await self._execute_query(query)
        return [record[0] for record in result] if result else []

    async def get_last_subscription_payment(self, user_id: int) -> datetime:
        """Получаем время последнего платежа пользователя по его user_id"""
        query = f"""--sql
            SELECT last_subscription_payment
            FROM users
            WHERE user_id = {user_id};
        """
        result = await self._execute_query(query)
        if result:
            last_payment_time = result[0][0]
            # logger.debug(f"User {user_id} last subscription payment fetched: {last_payment_time}")
            return last_payment_time
        else:
            logger.error(
                f"User {user_id} not found or last subscription payment could not be retrieved"
            )
            return None

    async def get_user_uuids_by_user_id(self, user_id: int) -> list[str]:
        """Получаем все UUID конфигов пользователя по user_id"""
        query = f"""--sql
            SELECT config_uuid
            FROM vpn_configs
            WHERE user_id = {user_id};
        """
        result = await self._execute_query(query)
        return [record[0] for record in result] if result else []

    # async def get_subscription_status(self, user_id: int) -> bool:
    #     query = f"""--sql
    #         SELECT subscription_is_active
    #         FROM users
    #         WHERE user_id = {user_id};
    #     """
    #     result = await self._execute_query(query)
    #     subscription_status = result[0][0] if result else False
    #     # logger.debug(f"Subscription status for user {user_id}: {subscription_status}")
    #     return subscription_status

    # async def get_users_with_sufficient_balance(self) -> list[int]: #OLD
    #     """
    #     Получаем список уникальных user_id, у которых подписка активна,
    #     последнее списание было более 24 часов назад,
    #     и баланс достаточен для оплаты конфигов (по 3 рубля за каждый конфиг).
    #     """
    #     query = """
    #         SELECT DISTINCT u.user_id
    #         FROM users u
    #         JOIN vpn_configs vc ON u.user_id = vc.user_id
    #         WHERE u.subscription_is_active = TRUE
    #         AND u.last_subscription_payment::date < CURRENT_DATE
    #         GROUP BY u.user_id
    #         HAVING u.balance >= COUNT(vc.config_uuid) * 3;
    #     """
    #     result = await self._execute_query(query)
    #     # logger.info(f"Найдено пользователей с достаточным балансом: {result}")
    #     # Возвращаем список user_id, если есть результат, иначе возвращаем пустой список
    #     return [record[0] for record in result] if result else []

    async def get_users_with_sufficient_balance(self) -> list[int]:
        """
        Получаем список уникальных user_id, у которых подписка активна,
        последнее списание было более 24 часов назад,
        и баланс достаточен для оплаты конфигов (по 3 рубля за каждый конфиг).
        """
        query = """
            SELECT DISTINCT u.user_id
            FROM users u
            JOIN vpn_configs vc ON u.user_id = vc.user_id
            WHERE u.last_subscription_payment::date < CURRENT_DATE
            GROUP BY u.user_id
            HAVING u.balance >= COUNT(vc.config_uuid) * 3;
        """
        result = await self._execute_query(query)
        # logger.info(f"Найдено пользователей с достаточным балансом: {result}")
        # Возвращаем список user_id, если есть результат, иначе возвращаем пустой список
        return [record[0] for record in result] if result else []

    # async def get_users_with_insufficient_balance(self) -> list[int]: #OLD
    #     """
    #     Получаем список уникальных user_id, у которых подписка активна,
    #     последнее списание было более 24 часов назад,
    #     и баланс недостаточен для оплаты конфигов (по 3 рубля за каждый конфиг).
    #     """
    #     query = """
    #         SELECT DISTINCT u.user_id
    #         FROM users u
    #         JOIN vpn_configs vc ON u.user_id = vc.user_id
    #         WHERE u.subscription_is_active = TRUE
    #         AND u.last_subscription_payment::date < CURRENT_DATE
    #         GROUP BY u.user_id
    #         HAVING u.balance < COUNT(vc.config_uuid) * 3;
    #     """
    #     result = await self._execute_query(query)
    #     # logger.info(f"Найдено пользователей с недостаточным балансом: {result}")
    #     # Возвращаем список user_id, если есть результат, иначе возвращаем пустой список
    #     return [record[0] for record in result] if result else []

    async def get_users_with_insufficient_balance(self) -> list[int]:
        """
        Получаем список уникальных user_id, у которых подписка активна,
        последнее списание было более 24 часов назад,
        и баланс недостаточен для оплаты конфигов (по 3 рубля за каждый конфиг).
        """
        query = """
            SELECT DISTINCT u.user_id
            FROM users u
            JOIN vpn_configs vc ON u.user_id = vc.user_id
            WHERE u.last_subscription_payment::date < CURRENT_DATE
            GROUP BY u.user_id
            HAVING u.balance < COUNT(vc.config_uuid) * 3;
        """
        result = await self._execute_query(query)
        # Возвращаем список user_id, если есть результат, иначе возвращаем пустой список
        return [record[0] for record in result] if result else []

    # async def get_users_to_restore(self) -> list[int]:
    #     """
    #     Получаем список уникальных user_id, у которых подписка неактивна,
    #     но баланс достаточен для восстановления подписки (по 3 рубля за каждый конфиг).
    #     """
    #     query = """
    #         SELECT DISTINCT u.user_id
    #         FROM users u
    #         JOIN vpn_configs vc ON u.user_id = vc.user_id
    #         WHERE u.subscription_is_active = FALSE
    #         GROUP BY u.user_id
    #         HAVING u.balance >= COUNT(vc.config_uuid) * 3;
    #     """
    #     result = await self._execute_query(query)
    #     # logger.info(f"Найдено пользователей для восстановления подписки: {result}")
    #     # Возвращаем список user_id, если есть результат, иначе возвращаем пустой список
    #     return [record[0] for record in result] if result else []

    async def get_all_config_uuids_for_users(self, users_ids: list[int]) -> list[str]:
        """
        Получаем все UUID конфигов для списка пользователей.
        Возвращаем плоский список всех UUID конфигов.
        """
        query = """
            SELECT config_uuid
            FROM vpn_configs
            WHERE user_id = ANY($1);
        """
        result = await self._execute_query(query, users_ids)

        # Возвращаем все UUID в одном списке
        return [record[0] for record in result] if result else []

    async def get_user_payment_method(self, user_id: int) -> str | None:
        query = f"""--sql
            SELECT payment_method_id
            FROM users
            WHERE user_id = {user_id};
        """
        result = await self._execute_query(query)
        payment_method_id = result[0][0] if result and result[0][0] else None
        # logger.debug(f"Payment method ID for user {user_id}: {payment_method_id}")
        return payment_method_id

    async def get_config_uuids_grouped_by_domain(self, users_ids: list[int]) -> dict[str, list[str]]:
        """
        Получаем все конфиги для отключения, сгруппированные по доменам, для списка user_ids.
        Возвращаем словарь, где ключи — домены, а значения — списки UUID конфигов.
        """
        query = """
            SELECT vc.server_domain, vc.config_uuid
            FROM vpn_configs vc
            WHERE vc.user_id = ANY($1::bigint[])
            ORDER BY vc.server_domain;
        """
        result = await self._execute_query(query, [users_ids])

        domain_to_uuids = {}
        for record in result:
            domain = record[0]
            uuid = record[1]

            if domain not in domain_to_uuids:
                domain_to_uuids[domain] = []
            
            domain_to_uuids[domain].append(uuid)

        return domain_to_uuids

    async def get_domain_by_uuid(self, config_uuid: str) -> str | None:
        query = f"""
            SELECT server_domain
            FROM vpn_configs
            WHERE config_uuid = '{config_uuid}';
        """
        result = await self._execute_query(query)
        return result[0][0] if result else None
    

    async def get_country_name_by_uuid(self, config_uuid: str):
        query = f"""
            SELECT country_name
            FROM vpn_configs
            WHERE config_uuid = '{config_uuid}'
            LIMIT 1;
        """
        result = await self._execute_query(query)
        return result[0][0] if result else None

    async def get_country_code_by_uuid(self, config_uuid: str):
        query = f"""
            SELECT country_code
            FROM vpn_configs
            WHERE config_uuid = '{config_uuid}'
            LIMIT 1;
        """
        result = await self._execute_query(query)
        return result[0][0] if result else None

    async def get_user_config_names_and_uuids_and_country_code(self, user_id: int) -> list[VpnConfigDB_N] | None:
        query = f"""--sql
            SELECT id, config_name, config_uuid, country_code
            FROM vpn_configs
            WHERE user_id = {user_id};
        """
        result = await self._execute_query(query)
        if not result:
            return None
        return [
            VpnConfigDB_N(
                config_id=record[0],
                user_id=user_id,
                config_name=record[1],
                config_uuid=record[2],
                country_code=record[3],  # Добавляем country_code в объект
            )
            for record in result
        ]

    async def get_config_creation_date(self, uuid: str) -> datetime | None:
        """
        Получает дату создания конфигурации по ее UUID.
        :param uuid: Уникальный идентификатор конфигурации.
        :return: Дата создания конфигурации или None, если конфигурация не найдена.
        """
        query = f"""
            SELECT created_at
            FROM vpn_configs
            WHERE config_uuid = '{uuid}'
            LIMIT 1;
        """
        result = await self._execute_query(query)
        return result[0][0] if result else None

    async def get_germany_configs_count(self):
        query = f"""
            SELECT count(*)
            FROM vpn_configs
            WHERE country_name = 'Germany';
        """
        result = await self._execute_query(query)
        return result[0][0] if result else None

    async def get_finland_configs_count(self):
        query = f"""
            SELECT count(*)
            FROM vpn_configs
            WHERE country_name = 'Finland';
        """
        result = await self._execute_query(query)
        return result[0][0] if result else None

    async def get_america_configs_count(self):
        query = f"""
            SELECT count(*)
            FROM vpn_configs
            WHERE country_name = 'America';
        """
        result = await self._execute_query(query)
        return result[0][0] if result else None

    async def get_count_of_users_with_active_configs(self) -> int:
        """Получаем количество пользователей, у которых есть хотя бы один конфиг"""
        query = """--sql
            SELECT COUNT(DISTINCT user_id)
            FROM vpn_configs;
        """
        result = await self._execute_query(query)
        return result[0][0] if result else 0

    async def get_all_configs_grouped_by_domain(self) -> dict[str, list[str]]:
        """
        Получаем все конфиги из базы данных, сгруппированные по доменам.
        Возвращаем словарь, где ключи — домены, а значения — списки UUID конфигов.
        """
        query = """
            SELECT vc.server_domain, vc.config_uuid
            FROM vpn_configs vc
            ORDER BY vc.server_domain;
        """
        result = await self._execute_query(query)

        domain_to_uuids = {}
        for record in result:
            domain = record[0]
            uuid = record[1]

            if domain not in domain_to_uuids:
                domain_to_uuids[domain] = []

            domain_to_uuids[domain].append(uuid)

        return domain_to_uuids


    async def get_all_unique_server_domains(self) -> list[str]:
        """
        Получает список всех уникальных серверов (server_domain), 
        отсортированных по алфавиту.
        """
        query = """
            SELECT DISTINCT server_domain
            FROM vpn_configs
            ORDER BY server_domain ASC;
        """
        result = await self._execute_query(query)
        return [row[0] for row in result] if result else []


    async def get_unblocked_users_ids_by_domain(self, domain: str) -> list[int]:
        """
        Получаем список user_id пользователей с конфигами на заданном домене,
        которые не заблокированы (is_banned = FALSE).
        """
        query = f"""
            SELECT DISTINCT vc.user_id
            FROM vpn_configs vc
            JOIN users u ON vc.user_id = u.user_id
            WHERE vc.server_domain = '{domain}'
            AND u.is_banned = FALSE;
        """
        result = await self._execute_query(query)
        # logger.debug(f"Users for domain '{domain}': {result}")
        return [record[0] for record in result] if result else []


    async def get_user_configs_count(self, user_id: int) -> int:
        """
        Возвращает количество VPN-конфигов пользователя по user_id.
        :param user_id: Telegram user ID
        :return: Количество конфигураций
        """
        query = f"""--sql
            SELECT COUNT(*)
            FROM vpn_configs
            WHERE user_id = {user_id};
        """
        result = await self._execute_query(query)
        return result[0][0] if result else 0