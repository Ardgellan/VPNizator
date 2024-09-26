import asyncio

from aiogram.utils.exceptions import BotBlocked
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from loader import bot, db_manager
from source.utils import localizer
from source.utils.models import SubscriptionStatus
from source.utils.xray import xray_config


class SubscriptionChecker:
    def __init__(self):
        self._messages_limits_counter = 0
        self._scheduler = AsyncIOScheduler()
        # start checking subscriptions every day at 00:00
        self._scheduler.add_job(self._check_subscriptions, "cron", hour=21, minute=7)
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

        for user_id in users_with_active_configs:

            # *** Новая проверка: Проверяем время последнего списания ***
            if last_payment_time and last_payment_time != datetime(1970, 1, 1) and last_payment_time.date() == datetime.now().date():
            if last_payment_time and last_payment_time.date() == datetime.now().date():
                logger.info(f"Списания для пользователя {user_id} уже были сегодня, пропуск.")
                continue

            # Проверяем баланс пользователя
            logger.info(f"СУБСКРИПШН КОСТ ПРОВЕРЯЕМ!")
            subscription_cost = await db_manager.get_current_subscription_cost(user_id)
            logger.info(f"Fetching balance for user {user_id}...")
            current_balance = await db_manager.get_user_balance(user_id)
            
            logger.info(f"Checking balance for user {user_id}: current balance = {current_balance}, subscription cost = {subscription_cost}")
            if current_balance >= subscription_cost:
                users_with_sufficient_balance.append(user_id)
            else:
                users_with_insufficient_balance.append(user_id) 

        # Продление подписки для тех, у кого достаточно баланса
        logger.info(f"Users with insufficient balance: {users_with_insufficient_balance}")
        for user_id in users_with_sufficient_balance:
            await self._check_and_renew_subscription(user_id)

        if users_with_sufficient_balance:
            await xray_config.reactivate_user_configs_in_xray(users_with_sufficient_balance)

        # Блокировка конфигов для тех, у кого недостаточно средств
        if users_with_insufficient_balance:
            await self._disconnect_configs_for_users(users_with_insufficient_balance)
        logger.info("Looking for users with last day of subscription...")
        await self._find_and_notify_users_with_last_day_left_subscription()
        self._messages_limits_counter = 0

    async def _check_and_renew_subscription(self, user_id: int):

        # Сразу обновляем баланс, так как проверка уже была в основном цикле
        subscription_cost = await db_manager.get_current_subscription_cost(user_id)
        logger.info(f"Renewing subscription for user {user_id}: subscription cost = {subscription_cost}")
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
        logger.info(f"Users with last day of subscription: {users_ids_with_last_day_left_subscription}")
        await self._notify_users_about_subscription_status(
            users_ids=users_ids_with_last_day_left_subscription,
            status=SubscriptionStatus.last_day_left.value,
        )
        logger.info(f"Notified users about last day of subscription: {users_ids_with_last_day_left_subscription}")

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


# ##### ВЕРСИЯ ОРИГИНАЛ #####
# class SubscriptionChecker:
    # def __init__(self):
    #     self._messages_limits_counter = 0
    #     self._scheduler = AsyncIOScheduler()
    #     # start checking subscriptions every day at 00:00
    #     self._scheduler.add_job(self._check_subscriptions, "cron", hour=0, minute=0)
    #     self._scheduler.start()
    #     logger.info("Subscription checker was started...")

    # async def _check_subscriptions(self):
    #     """Check subscriptions and delete expired"""
    #     logger.info("Checking subscriptions...")
    #     await self._find_disconnect_and_notify_users_with_expired_subscription()
    #     await self._find_and_notify_users_with_last_day_left_subscription()
    #     await self._find_and_notify_users_with_two_days_left_subscription()
    #     self._messages_limits_counter = 0

#     async def _find_disconnect_and_notify_users_with_expired_subscription(self):
#         """Find, disconnect and notify users with expired subscription"""
#         all_configs_uuid = await xray_config.get_all_uuids()
#         expired_configs_uuid = [
#             uuid
#             for uuid in all_configs_uuid
#             if not await db_manager.check_for_user_has_sufficient_balance_by_config_uuid(
#                 config_uuid=uuid
#             )
#         ]
#         if expired_configs_uuid:
#             await self._disconnect_expired_configs_and_notify_users(
#                 configs_uuid=expired_configs_uuid
#             )

#     async def _find_and_notify_users_with_last_day_left_subscription(self):
#         """Find and notify users with last day left subscription"""
#         users_ids_with_last_day_left_subscription = (
#             await db_manager.get_users_ids_with_last_day_left_subscription()
#         )
#         await self._notify_users_about_subscription_status(
#             users_ids=users_ids_with_last_day_left_subscription,
#             status=SubscriptionStatus.last_day_left.value,
#         )

#     async def _find_and_notify_users_with_two_days_left_subscription(self):
#         """Find and notify users with two days left subscription"""
#         users_ids_with_two_days_left_subscription = (
#             await db_manager.get_users_ids_with_two_days_left_subscription()
#         )
#         await self._notify_users_about_subscription_status(
#             users_ids=users_ids_with_two_days_left_subscription,
#             status=SubscriptionStatus.two_days_left.value,
#         )

#     async def _disconnect_expired_configs_and_notify_users(self, configs_uuid: list[str]):
#         """Disconnect expired configs and notify their owners about it"""
#         users_ids_with_expired_subscription = await db_manager.get_users_ids_by_configs_uuids(
#             configs_uuid=configs_uuid
#         )
#         await xray_config.disconnect_many_uuids(uuids=configs_uuid)
#         await self._notify_users_about_subscription_status(
#             users_ids=users_ids_with_expired_subscription,
#             status=SubscriptionStatus.expired.value,
#         )

#     async def _notify_users_about_subscription_status(self, users_ids: list[int], status: str):
#         """Notify users about subscription status

#         Args:
#             users_ids (list[int]): list of users ids to notify
#             status (str): subscription status, one of SubscriptionStatus enum values

#         Raises:
#             ValueError: if status is not one of SubscriptionStatus enum values
#         """
#         match status:
#             case SubscriptionStatus.expired.value:
#                 message_text = localizer.message.subscription_expired_notification
#             case SubscriptionStatus.last_day_left.value:
#                 message_text = localizer.message.subscription_last_day_left_notification
#             case SubscriptionStatus.two_days_left.value:
#                 message_text = localizer.message.subscription_two_days_left_notification
#             case _:
#                 raise ValueError(f"Unknown subscription status: {status}")
#         for user_id in users_ids:
#             try:
#                 user = (await bot.get_chat_member(chat_id=user_id, user_id=user_id)).user
#                 await bot.send_message(
#                     chat_id=user_id,
#                     text=localizer.get_user_localized_text(
#                         user_language_code=user.language_code,
#                         text_localization=message_text,
#                     ).format(user=user.full_name),
#                 )
#             except BotBlocked:
#                 logger.error(f"Bot was blocked by user {user_id}")
#             except Exception as e:
#                 logger.error(e)
#             else:
#                 logger.info(f"User {user_id} was notified about subscription status: {status}")
#             finally:
#                 self._messages_limits_counter += 1
#                 if self._messages_limits_counter == 20:
#                     await asyncio.sleep(1)
#                     self._messages_limits_counter = 0
