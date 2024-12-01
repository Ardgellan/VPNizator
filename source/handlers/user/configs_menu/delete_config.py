from aiogram import types
from aiogram.dispatcher import FSMContext
import aiohttp
from loguru import logger
from datetime import datetime, timedelta

from source.keyboard import inline
from source.middlewares import rate_limit
from source.utils import localizer
from loader import db_manager


@rate_limit(limit=1)
async def confirm_delete_config(call: types.CallbackQuery, state: FSMContext):

    await call.message.delete()
    config_uuid = call.data.split("_")[-1]

    # Получение даты создания конфигурации
    config_creation_date = await db_manager.get_config_creation_date(uuid=config_uuid)

    if datetime.now() - config_creation_date < timedelta(hours=24):
        await call.message.answer(
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.can_not_delete_config_yet
            )
        )
    else:
        await call.message.answer(
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=localizer.message.confirm_delete_config,
            ),
            parse_mode=types.ParseMode.HTML,
            reply_markup=await inline.confirm_delete_config_keyboard(
                config_uuid=config_uuid, language_code=call.from_user.language_code
            ),
        )



async def delete_config(call: types.CallbackQuery, state: FSMContext):

    config_uuid = call.data.split("_")[-1]  # Получаем UUID конфигурации из данных callback
   
    # Получаем домен для конфигурации
    target_server = await db_manager.get_domain_by_uuid(config_uuid=config_uuid)

        
    # Формируем URL для удаления конфигурации с учётом target_server
    url = f"https://proxynode.vpnizator.online/delete_config/{target_server}/"

        
    # Используем aiohttp для отправки POST-запроса на эндпоинт
    async with aiohttp.ClientSession() as session:

        async with session.delete(url, params={"config_uuid": config_uuid}) as response:

            if response.status == 200:

                # Успешно удалили конфиг на сервере, теперь удаляем его из базы данных
                await db_manager.delete_one_vpn_config_by_uuid(uuid=config_uuid)

                    
                # Отправляем сообщение о том, что конфиг удален
                await call.message.answer(
                    text=localizer.get_user_localized_text(
                        user_language_code=call.from_user.language_code,
                        text_localization=localizer.message.config_deleted,
                    ),
                    parse_mode=types.ParseMode.HTML,
                    reply_markup=await inline.insert_button_back_to_main_menu(
                        language_code=call.from_user.language_code
                    ),
                )
                
                await call.answer()

                await call.message.delete()

                await state.finish()

            else:
                logger.error(f"Failed to delete config {config_uuid} on the server. Status: {response.status}, Response: {await response.text()}")

