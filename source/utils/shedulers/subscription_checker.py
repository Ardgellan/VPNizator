import asyncio

from datetime import datetime, timedelta
from aiogram.utils.exceptions import BotBlocked
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from aiogram import types

from loader import bot, db_manager
from source.utils import localizer
from source.utils.models import SubscriptionStatus
from source.utils.xray import xray_config


class SubscriptionChecker:
    def __init__(self):
        self._messages_limits_counter = 0
        self._scheduler = AsyncIOScheduler()
        # start checking subscriptions every day at 00:00
        self._scheduler.add_job(self._check_subscriptions, "cron", hour=21, minute=42)
        self._scheduler.start()
        logger.info("Subscription checker was started...")

    async def _check_subscriptions(self):
        """Проверяем подписки пользователей"""
         
        users_with_sufficient_balance = await db_manager.get_users_with_sufficient_balance()
        users_with_insufficient_balance = await db_manager.get_users_with_insufficient_balance()
        users_to_restore = await db_manager.get_users_to_restore()

        if users_with_sufficient_balance:
            await self._check_and_renew_subscription(users_with_sufficient_balance)

        if users_to_restore:
            await xray_config.reactivate_user_configs_in_xray(users_to_restore)

        if users_with_insufficient_balance:
            await self._disconnect_configs_for_users(users_with_insufficient_balance)

        await self._find_and_notify_users_with_last_day_left_subscription()
        self._messages_limits_counter = 0

    async def _check_and_renew_subscription(self, user_ids: list[int]):
        """
        Продлеваем подписку для списка пользователей.
        """
        tasks = []
        for user_id in user_ids:
            tasks.append(self._renew_single_subscription(user_id))

        # Выполняем все задачи параллельно
        await asyncio.gather(*tasks)

    async def _renew_single_subscription(self, user_id: int):
        """
        Продлеваем подписку для одного пользователя.
        """
        try:
            subscription_cost = await db_manager.get_current_subscription_cost(user_id)
            logger.info(f"Renewing subscription for user {user_id}: subscription cost = {subscription_cost}")

            # Обновляем баланс пользователя
            await db_manager.update_user_balance(user_id, -subscription_cost)
            logger.info(f"Updated balance for user {user_id} after renewal")

            # Обновляем время последнего платежа
            await db_manager.update_last_subscription_payment(user_id, datetime.now())
            logger.info(f"Updated last payment time for user {user_id}")
    
        except Exception as e:
            logger.error(f"Error renewing subscription for user {user_id}: {e}")


    async def _disconnect_configs_for_users(self, users_ids: list[int]):
        """
        Отключаем конфиги для пользователей с недостаточным балансом и обновляем статус подписки.
        """
        # Шаг 1: Массово обновляем статус подписки для всех пользователей
        await db_manager.update_subscription_status_for_users(users_ids, is_active=False)
        logger.info(f"Updated subscription status for users: {users_ids}")

        # Шаг 2: Получаем все UUID конфигов для отключения за один раз
        all_config_uuids = await db_manager.get_all_config_uuids_for_users(users_ids)

        if all_config_uuids:
            # Отключаем все конфиги за один вызов
            await xray_config.deactivate_user_configs_in_xray(uuids=all_config_uuids)
            logger.info(f"Deactivated configs for users: {users_ids}")

        # Шаг 3: Уведомляем всех пользователей о статусе подписки
        await self._notify_users_about_subscription_status(
            users_ids=users_ids,
            status=SubscriptionStatus.expired.value,
        )
        logger.info(f"Notified users with expired subscription: {users_ids}")


    async def _find_and_notify_users_with_last_day_left_subscription(self):
        """Find and notify users with last day left subscription"""
        users_ids_with_last_day_left_subscription = (
            await db_manager.get_users_ids_with_last_day_left_subscription()
        )
        logger.info(
            f"Users with last day of subscription: {users_ids_with_last_day_left_subscription}"
        )
        await self._notify_users_about_subscription_status(
            users_ids=users_ids_with_last_day_left_subscription,
            status=SubscriptionStatus.last_day_left.value,
        )
        logger.info(
            f"Notified users about last day of subscription: {users_ids_with_last_day_left_subscription}"
        )


    async def _notify_users_about_subscription_status(self, users_ids: list[int], status: str):
        """Notify users about subscription status"""
        logger.info(f"Notifying users {users_ids} about subscription status: {status}")
        match status:
            case SubscriptionStatus.expired.value:
                message_text = localizer.message.subscription_expired_notification
            case SubscriptionStatus.last_day_left.value:
                message_text = localizer.message.subscription_last_day_left_notification
            case _:
                raise ValueError(f"Unknown subscription status: {status}")

        tasks = []
        for user_id in users_ids:
            tasks.append(self._send_subscription_notification(user_id, message_text))
        await asyncio.gather(*tasks)

    async def _send_subscription_notification(self, user_id: int, message_text: str):
        """Helper function to send notification to a single user"""
        try:
            user = (await bot.get_chat_member(chat_id=user_id, user_id=user_id)).user
            logger.info(f"Sending message to user {user_id}")
            await bot.send_message(
                chat_id=user_id,
                text=localizer.get_user_localized_text(
                    user_language_code=user.language_code,
                    text_localization=message_text,
                ).format(user=user.full_name),
                parse_mode=types.ParseMode.HTML,
            )
        except BotBlocked:
            logger.error(f"Bot was blocked by user {user_id}")
        except Exception as e:
            logger.error(e)
        else:
            logger.info(f"User {user_id} was notified about subscription status")
        finally:
            self._messages_limits_counter += 1
            if self._messages_limits_counter == 20:
                await asyncio.sleep(1)
                self._messages_limits_counter = 0

