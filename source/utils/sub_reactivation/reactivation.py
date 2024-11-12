from aiogram import types
from loguru import logger
import asyncio
import aiohttp

from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loader import db_manager


async def restore_user_configs_for_subscription(self, user_ids: list[int]) -> bool:
    """
    Восстанавливает конфиги пользователей с активной подпиской.
    Включает обновление статуса подписки, списание средств и получение UUID конфигов,
    сгруппированных по доменам для восстановления на нужных серверах.
    """
    # Словарь для хранения конфигов, сгруппированных по доменам
    configs_by_domain = {}

    # Списываем средства и обновляем статус подписки для каждого пользователя
    for user_id in user_ids:
        # Списываем стоимость подписки с баланса
        subscription_cost = await db_manager.get_current_subscription_cost(user_id)
        await db_manager.update_user_balance(user_id, -subscription_cost)
        
        # Обновляем время последнего платежа и статус подписки на активный
        await db_manager.update_last_subscription_payment(user_id, datetime.now())
        await db_manager.update_subscription_status(user_id=user_id, is_active=True)

    # Получаем UUID конфигов для всех пользователей, сгруппированные по доменам
    user_configs_with_domains = await db_manager.get_config_uuids_grouped_by_domain(user_ids=user_ids)

    # Группируем UUID по доменам
    for domain, uuids in user_configs_with_domains.items():
        configs_by_domain.setdefault(domain, []).extend(uuids)

    # Проверяем, если есть конфиги для восстановления
    if configs_by_domain:
        # Инициализируем клиент для HTTP-запросов с aiohttp
        async with aiohttp.ClientSession() as session:
            for domain, uuids in configs_by_domain.items():
                # Формируем URL с доменом
                url = f"http://nginxtest.vpnizator.online/restore_configs/{domain}/"

                try:
                    # Отправляем запрос на эндпоинт для восстановления конфигов
                    async with session.post(url, json={"config_uuids": uuids}) as response:
                        # Если статус не 200, продолжаем с следующим доменом
                        if response.status != 200:
                            return False  # Если хотя бы один запрос не успешен, возвращаем False

            # Если все запросы прошли успешно, возвращаем True
            return True

    return False




