import asyncio
import aiohttp

from datetime import datetime, timedelta
from aiogram.utils.exceptions import BotBlocked
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from aiogram import types

from loader import bot, db_manager
from source.utils import localizer
from source.utils.models import SubscriptionStatus
# from source.utils.sub_reactivation import restore_user_configs_for_subscription


class SubscriptionChecker:
    def __init__(self):
        self._messages_limits_counter = 0
        self._scheduler = AsyncIOScheduler()
        # start checking subscriptions every day at 12:00
        self._scheduler.add_job(self._check_subscriptions, "cron", hour=15, minute=0)
        self._scheduler.start()
        logger.info("Subscription checker was started...")

    async def _check_subscriptions(self):
        """Проверяем подписки пользователей"""

        users_with_sufficient_balance = await db_manager.get_users_with_sufficient_balance()
        users_with_insufficient_balance = await db_manager.get_users_with_insufficient_balance()
        # users_to_restore = await db_manager.get_users_to_restore()

        if users_with_sufficient_balance:
            await self._check_and_renew_subscription(users_with_sufficient_balance)

        # if users_to_restore:
        #     await restore_user_configs_for_subscription(users_to_restore)

        if users_with_insufficient_balance:
            await self._disconnect_configs_for_users(users_with_insufficient_balance)

        await self._find_and_notify_users_with_last_day_left_subscription()
        self._messages_limits_counter = 0

        

    async def _check_and_renew_subscription(self, user_ids: list[int]):
        """
        Продлеваем подписку для списка пользователей, ограничивая количество
        одновременно выполняющихся задач.
        """
        semaphore = asyncio.Semaphore(50)  # Ограничиваем до 10 одновременных задач
        tasks = []
        for user_id in user_ids:
            tasks.append(self._renew_with_semaphore(user_id, semaphore))

        await asyncio.gather(*tasks)

    async def _renew_with_semaphore(self, user_id: int, semaphore: asyncio.Semaphore):
        """
        Обертка для продления подписки с использованием семафора.
        """
        async with semaphore:
            await self._renew_single_subscription(user_id)

    async def _renew_single_subscription(self, user_id: int):
        """
        Продлеваем подписку для одного пользователя.
        """
        try:
            subscription_cost = await db_manager.get_current_subscription_cost(user_id)

            # Обновляем баланс пользователя
            await db_manager.update_user_balance(user_id, -subscription_cost)

            # Обновляем время последнего платежа
            await db_manager.update_last_subscription_payment(user_id, datetime.now())

        except Exception as e:
            logger.error(f"Error renewing subscription for user {user_id}: {e}")


    async def _disconnect_configs_for_users(self, users_ids: list[int]):
        """
        Отключаем конфиги для пользователей с недостаточным балансом и обновляем статус подписки,
        только если деактивация конфигов прошла успешно. Обновление статуса подписки повторяется до 3 раз в случае неудачи.
        """
        # Шаг 1: Получаем UUID конфигов, сгруппированные по доменам
        configs_by_domain = await db_manager.get_config_uuids_grouped_by_domain(users_ids)

        # Если есть конфиги для отключения, начинаем процесс деактивации
        if configs_by_domain:
            try:
                # Отключаем конфиги для каждого домена
                for domain, uuids in configs_by_domain.items():
                    # Отправляем запрос на эндпоинт для деактивации конфигов на конкретном сервере
                    response = await self._send_deactivation_request(domain, uuids)
                
                    if response.status != 200:
                        logger.error(f"Ошибка при деактивации конфигов на {domain}: {response.text}")
                        continue
                    else:
                        logger.info(f"Конфиги успешно деактивированы на домене {domain}.")

                # Шаг 2: Попытки обновить статус подписки для всех пользователей
                # attempts = 3
                # for attempt in range(attempts):
                #     try:
                #         await db_manager.update_subscription_status_for_users(
                #             users_ids, is_active=False
                #         )
                #         break
                #     except Exception as e:
                #         logger.error(
                #             f"Попытка {attempt + 1} обновления статуса подписки для пользователей {users_ids} не удалась: {str(e)}"
                #         )
                #         if attempt < attempts - 1:
                #             await asyncio.sleep(2)
                #         else:
                #             logger.critical(
                #                 f"Не удалось обновить статус подписки для пользователей {users_ids} после {attempts} попыток."
                #             )
                #             return

                all_uuids = [uuid for uuids in configs_by_domain.values() for uuid in uuids]
                await db_manager.delete_many_vpn_configs_by_uuids(all_uuids)

                # Шаг 3: Уведомляем пользователей о статусе подписки
                await self._notify_users_about_subscription_status(
                    users_ids=users_ids,
                    status=SubscriptionStatus.expired.value,
                )

            except Exception as e:
                logger.error(
                    f"Ошибка при деактивации конфигов для пользователей {users_ids}: {str(e)}"
                )
                return

    async def _send_deactivation_request(self, domain: str, uuids: list[str]):
        """
        Отправляем запрос на удаление конфигов для пользователей на конкретном сервере.
        Используется aiohttp для отправки HTTP-запроса.
        """
        try:
            # Формируем URL запроса
            url = f"https://proxynode.vpnizator.online/deactivate_configs/{domain}/"
        
            # Открываем сессию aiohttp для отправки запроса
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, json={"config_uuids": uuids}) as response:
                    # Проверка, что запрос прошел успешно
                    if response.status == 200:
                        return response
                    else:
                        # Если статус не 200, логируем ошибку
                        logger.error(f"Ошибка при деактивации конфигов на {domain}. Код ошибки: {response.status}")
                        return response
        except Exception as e:
            # Логируем ошибку при отправке запроса
            logger.error(f"Ошибка при отправке запроса на деактивацию конфигов на {domain}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при деактивации конфигов на сервере.")


    async def _find_and_notify_users_with_last_day_left_subscription(self):
        """Find and notify users with last day left subscription"""
        users_ids_with_last_day_left_subscription = (
            await db_manager.get_users_ids_with_last_day_left_subscription()
        )

        await self._notify_users_about_subscription_status(
            users_ids=users_ids_with_last_day_left_subscription,
            status=SubscriptionStatus.last_day_left.value,
        )


    async def _notify_users_about_subscription_status(self, users_ids: list[int], status: str):
        """Notify users about subscription status"""

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
