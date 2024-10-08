from datetime import datetime, timedelta

from loguru import logger

from .connector import DatabaseConnector


class Updater(DatabaseConnector):
    def __init__(self) -> None:
        super().__init__()
        logger.debug("Updater object was initialized")

    # async def add_days_to_user_subscription(self, user_id: int, days: int) -> bool:
    #     """
    #     Add days to user subscription if subscription_end_date >= current_date
    #     else set subscription_end_date to current_date + days
    #     """
    #     query = f"""--sql
    #         UPDATE users
    #         SET subscription_end_date = CASE
    #             WHEN subscription_end_date >= CURRENT_DATE
    #             THEN subscription_end_date + INTERVAL '{days} days'
    #             ELSE CURRENT_DATE + INTERVAL '{days} days'
    #         END
    #         WHERE user_id = {user_id};
    #     """
    #     if await self._execute_query(query) is False:
    #         logger.error(f"Error while adding {days} days to user {user_id} subscription")
    #         return False
    #     logger.debug(f"Added {days} days to user {user_id} subscription")
    #     return True

    async def toggle_user_banned_status(self, user_id: int) -> bool:
        """
        Toggle user banned status
        """
        query = f"""--sql
            UPDATE users
            SET is_banned = NOT is_banned
            WHERE user_id = {user_id};
        """
        if await self._execute_query(query) is False:
            logger.error(f"Error while toggling user {user_id} banned status")
            return False
        logger.debug(f"Toggled user {user_id} banned status")
        return True

    # async def upsert_bonus_config_generations_to_user(
    #     self, user_id: int, new_bonus_config_count: int
    # ):
    #     query = f"""--sql
    #         INSERT INTO bonus_configs_for_users (user_id, bonus_config_count)
    #         VALUES ({user_id}, {new_bonus_config_count})
    #         ON CONFLICT (user_id)
    #         DO UPDATE SET bonus_config_count = {new_bonus_config_count};
    #     """
    #     if await self._execute_query(query) is False:
    #         logger.error(f"Error while setting bonus config generations to user {user_id}")
    #         return False
    #     logger.debug(f"Set bonus config generations to user {user_id}")
    #     return True

    # async def mark_trial_as_used(self, user_id: int):
    #     query = f"""--sql
    #         UPDATE users
    #         SET trial_used = TRUE
    #         WHERE user_id = {user_id};
    #     """
    #     await self._execute_query(query)
    #     logger.debug(f"User {user_id} marked as having used the trial period")
    #     return True

    async def mark_trial_as_used(self, user_id: int, conn=None):
        query = f"""--sql
            UPDATE users
            SET trial_used = TRUE
            WHERE user_id = {user_id};
        """
        if conn:
            # Если передано соединение, используем его для выполнения запроса
            await conn.execute(query)
        else:
            # Если соединение не передано, создаем новое и выполняем запрос
            await self._execute_query(query)
        logger.debug(f"User {user_id} marked as having used the trial period")
        return True

    # async def update_user_balance(self, user_id: int, amount: float) -> bool:
    #     """Обновляем баланс пользователя, добавляя или вычитая средства"""
    #     query = f"""--sql
    #         UPDATE users
    #         SET balance = balance + {amount}
    #         WHERE user_id = {user_id};
    #     """
    #     if await self._execute_query(query) is False:
    #         logger.error(f"Error while updating balance for user {user_id}")
    #         return False
    #     logger.debug(f"Updated balance for user {user_id} by {amount}")
    #     return True

    async def update_user_balance(self, user_id: int, amount: float, conn=None) -> bool:
        query = f"""--sql
            UPDATE users
            SET balance = balance + {amount}
            WHERE user_id = {user_id};
        """
        if conn:
            # Если передано соединение, выполняем запрос через него
            await conn.execute(query)
        else:
            # Если соединение не передано, создаем новое и выполняем запрос
            if await self._execute_query(query) is False:
                logger.error(f"Error while updating balance for user {user_id}")
                return False
        logger.debug(f"Updated balance for user {user_id} by {amount}")
        return True

    # async def update_last_subscription_payment(self, user_id: int, payment_time: datetime) -> bool:
    #     """Обновляем время последнего платежа для пользователя по его user_id"""
    #     query = f"""--sql
    #         UPDATE users
    #         SET last_subscription_payment = '{payment_time}'
    #         WHERE user_id = {user_id};
    #     """
    #     if await self._execute_query(query) is False:
    #         logger.error(f"Error while updating last subscription payment for user {user_id}")
    #         return False
    #     logger.debug(f"User {user_id} last subscription payment updated to {payment_time}")
    #     return True

    async def update_last_subscription_payment(
        self, user_id: int, payment_time: datetime, conn=None
    ) -> bool:
        """Обновляем время последнего платежа для пользователя по его user_id"""
        query = f"""--sql
            UPDATE users
            SET last_subscription_payment = '{payment_time}'
            WHERE user_id = {user_id};
        """
        if conn:
            # Если передано соединение, выполняем запрос через него
            await conn.execute(query)
        else:
            # Если соединение не передано, создаем новое и выполняем запрос
            if await self._execute_query(query) is False:
                logger.error(f"Error while updating last subscription payment for user {user_id}")
                return False
        logger.debug(f"User {user_id} last subscription payment updated to {payment_time}")
        return True

    # async def update_subscription_status(self, user_id: int, is_active: bool):
    #     query = f"""--sql
    #         UPDATE users
    #         SET subscription_is_active = {is_active}
    #         WHERE user_id = {user_id};
    #     """
    #     await self._execute_query(query)
    #     logger.info(f"Статус подписки для пользователя {user_id} обновлен на {is_active}.")

    async def update_subscription_status(self, user_id: int, is_active: bool):
        query = f"""--sql
            UPDATE users
            SET subscription_is_active = {is_active}
            WHERE user_id = {user_id};
        """
        try:
            await self._execute_query(query)  # Выполняем запрос
            logger.info(f"Статус подписки для пользователя {user_id} обновлен на {is_active}.")
        except Exception as e:
            # Логируем ошибку и пробрасываем исключение дальше
            logger.error(f"Ошибка при обновлении статуса подписки для пользователя {user_id}: {str(e)}")
            raise  # Пробрасываем исключение дальше для обработки в вызывающей функции


    # async def update_subscription_status_for_users(self, users_ids: list[int], is_active: bool):
    #     """
    #     Массово обновляем статус подписки для списка пользователей.
    #     """
    #     query = """
    #         UPDATE users
    #         SET subscription_is_active = $2
    #         WHERE user_id = ANY($1);
    #     """
    #     await self._execute_query(query, users_ids, is_active)
    #     logger.info(f"Статус подписки для пользователей {users_ids} обновлен на {is_active}.")

    async def update_subscription_status_for_users(self, users_ids: list[int], is_active: bool):
        """
        Массово обновляем статус подписки для списка пользователей.
        """
        query = """
            UPDATE users
            SET subscription_is_active = $2
            WHERE user_id = ANY($1);
        """
        try:
            await self._execute_query(query, users_ids, is_active)  # Выполняем запрос
            logger.info(f"Статус подписки для пользователей {users_ids} обновлен на {is_active}.")
        except Exception as e:
            # Логируем ошибку и пробрасываем исключение дальше
            logger.error(f"Ошибка при массовом обновлении статуса подписки для пользователей {users_ids}: {str(e)}")
            raise  # Пробрасываем исключение для обработки в вызывающей функции

    async def save_user_payment_method(self, user_id: int, payment_method_id: str):
        query = f"""--sql
            UPDATE users
            SET payment_method_id = '{payment_method_id}'
            WHERE user_id = {user_id};
        """
        await self._execute_query(query)
        logger.debug(f"Payment method ID for user {user_id} saved: {payment_method_id}")
