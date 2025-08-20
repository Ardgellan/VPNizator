import asyncio
import aiohttp
from aiogram import types
from aiogram.dispatcher import FSMContext

from loguru import logger
from loader import db_manager

async def cleanup_all_servers(call: types.CallbackQuery):
    """
    Асинхронная очистка всех серверов от неактуальных клиентов.
    Запускается вручную через админскую кнопку (Nginx-проксирование).
    """
    try:
        # Получаем актуальный список UUID, сгруппированный по серверам
        domain_to_uuids = await db_manager.get_all_configs_grouped_by_domain()

        async with aiohttp.ClientSession() as session:
            tasks = []

            for domain, uuids in domain_to_uuids.items():
                url = f"https://newproxynode.vpnizator.online/cleanup_configs/{domain}/"
                logger.info(f"Отправляем запрос на очистку {domain}. Всего UUID: {len(uuids)}")

                task = session.delete(url, json={"valid_uuids": uuids})
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for domain, response in zip(domain_to_uuids.keys(), responses):
                if isinstance(response, Exception):
                    logger.error(f"Ошибка при очистке {domain}: {response}")
                else:
                    result = await response.json()
                    if response.status == 200:
                        logger.info(f"Очистка сервера {domain} прошла успешно: {result}")
                    else:
                        logger.error(f"Ошибка при очистке {domain}: {result}")

        summary_message = (
            f"✅ Очистка всех серверов завершена!\n"
        )

        logger.info(summary_message)
        await call.message.answer(summary_message)

    except Exception as e:
        error_message = f"🚨 Ошибка при очистке серверов: {str(e)}"
        logger.error(error_message)
        await callback_query.message.answer(error_message)