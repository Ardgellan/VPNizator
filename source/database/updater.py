from datetime import datetime, timedelta

from loguru import logger

from .connector import DatabaseConnector


class Updater(DatabaseConnector):
    def __init__(self) -> None:
        super().__init__()
        logger.debug("Updater object was initialized")

    async def add_days_to_user_subscription(self, user_id: int, days: int) -> bool:
        """
        Add days to user subscription if subscription_end_date >= current_date
        else set subscription_end_date to current_date + days
        """
        query = f"""--sql
            UPDATE users
            SET subscription_end_date = CASE
                WHEN subscription_end_date >= CURRENT_DATE
                THEN subscription_end_date + INTERVAL '{days} days'
                ELSE CURRENT_DATE + INTERVAL '{days} days'
            END
            WHERE user_id = {user_id};
        """
        if await self._execute_query(query) is False:
            logger.error(f"Error while adding {days} days to user {user_id} subscription")
            return False
        logger.debug(f"Added {days} days to user {user_id} subscription")
        return True

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

    async def upsert_bonus_config_generations_to_user(
        self, user_id: int, new_bonus_config_count: int
    ):
        query = f"""--sql
            INSERT INTO bonus_configs_for_users (user_id, bonus_config_count)
            VALUES ({user_id}, {new_bonus_config_count})
            ON CONFLICT (user_id)
            DO UPDATE SET bonus_config_count = {new_bonus_config_count};
        """
        if await self._execute_query(query) is False:
            logger.error(f"Error while setting bonus config generations to user {user_id}")
            return False
        logger.debug(f"Set bonus config generations to user {user_id}")
        return True

    async def activate_trial_period(self, user_id: int, trial_start: datetime, trial_end: datetime):
        query = f"""--sql
            UPDATE users
            SET trial_start_date = '{trial_start}', trial_end_date = '{trial_end}'
            WHERE user_id = {user_id};
        """
        await self._execute_query(query)
        logger.debug(f"Trial period for user {user_id} activated: {trial_start} - {trial_end}")
        return True

    async def mark_trial_as_used(self, user_id: int):
        query = f"""--sql
            UPDATE users
            SET trial_used = TRUE
            WHERE user_id = {user_id};
        """
        await self._execute_query(query)
        logger.debug(f"User {user_id} marked as having used the trial period")
        return True

    async def update_user_balance(self, user_id: int, amount: float) -> bool:
        """Обновляем баланс пользователя, добавляя или вычитая средства"""
        query = f"""--sql
            UPDATE users
            SET balance = balance + {amount}
            WHERE user_id = {user_id};
        """
        if await self._execute_query(query) is False:
            logger.error(f"Error while updating balance for user {user_id}")
            return False
        logger.debug(f"Updated balance for user {user_id} by {amount}")
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
        logger.debug(f"User {user_id} last subscription payment updated to {payment_time}")
        return True

    # async def deactivate_configs(self, uuids: list[str]) -> bool:
    #     """Деактивируем конфиги в базе данных вместо их удаления"""
    #     query = f"""--sql
    #         UPDATE vpn_configs
    #         SET is_active = FALSE
    #         WHERE config_uuid = ANY(ARRAY[{', '.join(f"'{uuid}'" for uuid in uuids)}]);
    #     """
    #     return await self._execute_query(query)

    # async def reactivate_configs(self, user_id: int) -> bool:
    #     """Активируем конфиги в базе данных"""
    #     query = f"""--sql
    #         UPDATE vpn_configs
    #         SET is_active = TRUE
    #         WHERE user_id = {user_id};
    #     """
    #     return await self._execute_query(query)
