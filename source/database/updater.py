from datetime import datetime, timedelta

from loguru import logger

from .connector import DatabaseConnector


class Updater(DatabaseConnector):
    def __init__(self) -> None:
        super().__init__()
        logger.debug("Updater object was initialized")

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
        # logger.debug(f"Toggled user {user_id} banned status")
        return True

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
        # logger.debug(f"User {user_id} marked as having used the trial period")
        return True

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
        # logger.debug(f"Updated balance for user {user_id} by {amount}")
        return True

    async def update_last_subscription_payment(self, user_id: int, payment_time: datetime) -> bool:
        """Обновляем время последнего платежа для пользователя по его user_id"""
        query = f"""--sql
            UPDATE users
            SET last_subscription_payment = '{payment_time}'
            WHERE user_id = {user_id};
        """
        if await self._execute_query(query) is False:
            logger.error(f"Error while updating last subscription payment for user {user_id}")
            return False
        # logger.debug(f"User {user_id} last subscription payment updated to {payment_time}")
        return True

    async def update_subscription_status(self, user_id: int, is_active: bool):
        query = f"""--sql
            UPDATE users
            SET subscription_is_active = {is_active}
            WHERE user_id = {user_id};
        """
        await self._execute_query(query)
        # logger.info(f"Статус подписки для пользователя {user_id} обновлен на {is_active}.")

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
            # logger.info(f"Статус подписки для пользователей {users_ids} обновлен на {is_active}.")
        except Exception as e:
            # Логируем ошибку и пробрасываем исключение дальше
            logger.error(f"Ошибка при массовом обновлении статуса подписки для пользователей {users_ids}: {str(e)}")
            raise  # Пробрасываем исключение для обработки в вызывающей функции