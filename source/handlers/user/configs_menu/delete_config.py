from aiogram import types
from aiogram.dispatcher import FSMContext
import aiohttp
from logguru import logger

from source.keyboard import inline
from source.middlewares import rate_limit
from source.utils import localizer
from loader import db_manager


@rate_limit(limit=1)
async def confirm_delete_config(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"Entered_confirm_delete_config")
    await call.message.delete()
    config_uuid = call.data.split("_")[-1]
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
    logger.info(f"Exiting_confirm_delete_config")


# async def delete_config(call: types.CallbackQuery, state: FSMContext):
#     logger.info(f"Entered_delete_config")
#     config_uuid = call.data.split("_")[-1]
#     await xray_config.disconnect_user_by_uuid(uuid=config_uuid)
#     await db_manager.delete_one_vpn_config_by_uuid(uuid=uuid)
#     await call.message.answer(
#         text=localizer.get_user_localized_text(
#             user_language_code=call.from_user.language_code,
#             text_localization=localizer.message.config_deleted,
#         ),
#         parse_mode=types.ParseMode.HTML,
#         reply_markup=await inline.insert_button_back_to_main_menu(
#             language_code=call.from_user.language_code
#         ),
#     )
#     await call.answer()
#     await call.message.delete()
#     await state.finish()
#     logger.info(f"Successfully_deleted_config")


async def delete_config(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"Started deleting config with UUID: {call.data}")
    config_uuid = call.data.split("_")[-1]  # Получаем UUID конфигурации из данных callback
    logger.info(f"Extracted config UUID: {config_uuid}")
    
    # Получаем домен для конфигурации
    target_server = await db_manager.get_domain_by_uuid(uuid=config_uuid)
    logger.info(f"Fetched domain for UUID {config_uuid}: {target_server}")
        
    # Формируем URL для удаления конфигурации с учётом target_server
    url = f"https://nginxtest.vpnizator.online/delete_config/{target_server}/"
    logger.info(f"Formed delete URL: {url}")
        
    # Используем aiohttp для отправки POST-запроса на эндпоинт
    async with aiohttp.ClientSession() as session:
        logger.info(f"Sending DELETE request to {url} with config_uuid={config_uuid}...")
        async with session.delete(url, params={"config_uuid": config_uuid}) as response:
            logger.info(f"Received response from DELETE request. Status code: {response.status}")
            if response.status == 200:
                logger.info(f"Config {config_uuid} successfully deleted on the server.")
                # Успешно удалили конфиг на сервере, теперь удаляем его из базы данных
                await db_manager.delete_one_vpn_config_by_uuid(uuid=config_uuid)
                logger.info(f"Config {config_uuid} removed from the database.")
                    
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
                logger.info(f"Message about config deletion sent to user {call.from_user.id}.")
                await call.message.delete()
                logger.info(f"Deleted the message with the callback for user {call.from_user.id}.")
                await state.finish()
                logger.info(f"State finished for user {call.from_user.id}.")
            else:
                logger.error(f"Failed to delete config {config_uuid} on the server. Status: {response.status}, Response: {await response.text()}")
                await call.message.answer(
                    text="Ошибка при удалении конфигурации.",
                    parse_mode=types.ParseMode.HTML,
                )
                logger.error(f"Sent error message to user {call.from_user.id}.")
