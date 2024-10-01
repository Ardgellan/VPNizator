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
        self._scheduler.add_job(self._check_subscriptions, "cron", hour=2, minute=32)
        self._scheduler.start()
        logger.info("Subscription checker was started...")

    async def _check_subscriptions(self):
        """Проверяем подписки пользователей"""
        logger.info("Checking subscriptions based on balance...")
        logger.info("ULTRABABASRAKA3000!!!")
        users_with_active_configs = await db_manager.get_users_with_active_configs()
        logger.info(f"Users with active configs: {users_with_active_configs}")
        users_with_sufficient_balance = []
        users_with_insufficient_balance = []
        users_to_restore = []

        for user_id in users_with_active_configs:
            # Логируем начало работы с каждым пользователем
            logger.info(f"Начинаем проверку для пользователя {user_id}")

            # Получаем время последнего списания
            last_payment_time = await db_manager.get_last_subscription_payment(user_id)

            # *** Новая проверка: Проверяем время последнего списания ***
            if last_payment_time and (datetime.now() - last_payment_time) < timedelta(hours=24):
                logger.info(
                    f"Списания для пользователя {user_id} были в последние 24 часа, пропуск."
                )
                continue

            # Проверяем баланс пользователя
            logger.info(f"Fetching balance for user {user_id}...")
            current_balance = await db_manager.get_user_balance(user_id)
            logger.info(f"Current balance for user {user_id}: {current_balance}")

            # Проверяем стоимость подписки
            logger.info(f"СУБСКРИПШН КОСТ ПРОВЕРЯЕМ для пользователя {user_id}")
            subscription_cost = await db_manager.get_current_subscription_cost(user_id)
            logger.info(f"Subscription cost for user {user_id}: {subscription_cost}")

            if current_balance >= subscription_cost:
                users_with_sufficient_balance.append(user_id)
                logger.info(f"User {user_id} has sufficient balance.")
            else:
                users_with_insufficient_balance.append(user_id)
                logger.info(f"User {user_id} has insufficient balance.")

        logger.info(f"Users with sufficient balance: {users_with_sufficient_balance}")
        for user_id in users_with_sufficient_balance:
            await self._check_and_renew_subscription(user_id)
            sub_is_active = await db_manager.get_subscription_status(user_id)
            if not sub_is_active:
                users_to_restore.append(user_id)

        if users_to_restore:
            await xray_config.reactivate_user_configs_in_xray(users_to_restore)
        logger.info("Reactivated sufficient users")

        # Блокировка конфигов для тех, у кого недостаточно средств
        logger.info(f"Users with insufficient balance: {users_with_insufficient_balance}")
        if users_with_insufficient_balance:
            await self._disconnect_configs_for_users(users_with_insufficient_balance)

        logger.info("Looking for users with last day of subscription...")
        await self._find_and_notify_users_with_last_day_left_subscription()
        self._messages_limits_counter = 0

    async def _check_and_renew_subscription(self, user_id: int):

        # Сразу обновляем баланс, так как проверка уже была в основном цикле
        subscription_cost = await db_manager.get_current_subscription_cost(user_id)
        logger.info(
            f"Renewing subscription for user {user_id}: subscription cost = {subscription_cost}"
        )
        await db_manager.update_user_balance(user_id, -subscription_cost)
        logger.info(f"Updated balance for user {user_id} after renewal")

        # *** Новое: обновляем время последнего платежа ***
        await db_manager.update_last_subscription_payment(user_id, datetime.now())
        logger.info(f"Updated last payment time for user {user_id}")
        logger.info(f"Подписка пользователя {user_id} успешно продлена.")
        return True

    async def _disconnect_configs_for_users(self, users_ids: list[int]):
        """Отключаем конфиги для пользователей с недостаточным балансом"""

        all_config_uuids = []  # Список для хранения всех UUID конфигов

        # Собираем UUID конфигов для всех пользователей
        for user_id in users_ids:
            await db_manager.update_subscription_status(user_id=user_id, is_active=False)
            user_uuids = await db_manager.get_user_uuids_by_user_id(user_id)
            if user_uuids:
                all_config_uuids.extend(user_uuids)
                logger.info(f"Collected UUIDs for user {user_id}: {user_uuids}")

        # Если есть конфиги для отключения, передаем их в Xray за один вызов
        if all_config_uuids:
            await xray_config.deactivate_user_configs_in_xray(uuids=all_config_uuids)
            logger.info(f"Deactivated configs for users: {users_ids}")

        # Уведомляем всех пользователей с недостаточным балансом за один вызов
        await self._notify_users_about_subscription_status(
            users_ids=users_ids,  # Передаем список всех пользователей
            status=SubscriptionStatus.expired.value,  # Статус истекшей подписки
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

        for user_id in users_ids:
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
                logger.info(f"User {user_id} was notified about subscription status: {status}")
            finally:
                self._messages_limits_counter += 1
                if self._messages_limits_counter == 20:
                    await asyncio.sleep(1)
                    self._messages_limits_counter = 0
