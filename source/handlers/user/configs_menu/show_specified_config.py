from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger
import aiohttp

from loader import db_manager
from source.keyboard import inline
from source.utils import localizer
from source.utils.qr_generator import create_qr_code_from_config_as_link_str
from source.middlewares import rate_limit
from source.utils.code_to_flag import *


# @rate_limit(limit=3)
# async def show_specified_config(call: types.CallbackQuery, state: FSMContext):

#     config_uuid = call.data.split("_")[-1]
#     config_name = await db_manager.get_config_name_by_config_uuid(config_uuid=config_uuid)
#     config_as_link_str = await xray_config.create_user_config_as_link_string(
#         uuid=config_uuid,
#         config_name=config_name,
#     )
#     config_qr_code = create_qr_code_from_config_as_link_str(config=config_as_link_str)

#     await call.message.delete()

#     await call.message.answer_photo(
#         photo=config_qr_code,
#         caption=localizer.get_user_localized_text(
#             user_language_code=call.from_user.language_code,
#             text_localization=localizer.message.config_requseted,
#         ).format(config_name=config_name, config_data=config_as_link_str),
#         parse_mode=types.ParseMode.HTML,
#         reply_markup=await inline.delete_specified_config_keyboard(
#             config_uuid=config_uuid, language_code=call.from_user.language_code
#         ),
#     )
#     # Завершаем текущее состояние перед удалением сообщения
#     await state.finish()

@rate_limit(limit=3)
async def show_specified_config(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"Extracting config UUID from callback data: {call.data}")
    config_uuid = call.data.split("_")[-1]
    country_name = await db_manager.get_country_name_by_uuid(config_uuid)
    country_code = await db_manager.get_country_code_by_uuid(config_uuid)
    country_flag = country_code_to_flag(country_code)
    # Получаем имя конфигурации из базы данных
    logger.info(f"Fetching config name from database for UUID: {config_uuid}")
    config_name = await db_manager.get_config_name_by_config_uuid(config_uuid=config_uuid)
    logger.info(f"Config name fetched successfully: {config_name}")
    logger.info(f"Fetching domain from database for config UUID: {config_uuid}")
    target_server = await db_manager.get_domain_by_uuid(config_uuid=config_uuid)
    logger.info(f"Domain fetched successfully for config UUID {config_uuid}: {target_server}")

    # Отправляем запрос к API для получения сгенерированной ссылки
    logger.info("Creating HTTP session and sending GET request to API for config link...")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://nginxtest.vpnizator.online/show_specified_config/{target_server}/",
            params={"config_uuid": config_uuid, "config_name": config_name}
        ) as response:
            logger.info(f"Received response from API. Status code: {response.status}")
            if response.status == 200:
                logger.info("Response status is 200. Parsing JSON data...")
                data = await response.json()
                config_as_link_str = data.get("config_link")
                logger.info(f"Config link fetched from API: {config_as_link_str}")

                # Генерация QR-кода для конфигурации
                logger.info("Generating QR code from the config link...")
                config_qr_code = create_qr_code_from_config_as_link_str(config=config_as_link_str)
                logger.info("QR code generated successfully.")

                # Удаляем сообщение с кнопкой
                logger.info("Deleting previous message with button...")
                await call.message.delete()

                # Отправляем QR-код и ссылку
                logger.info("Sending QR code and config link to user...")
                await call.message.answer_photo(
                    photo=config_qr_code,
                    caption=localizer.get_user_localized_text(
                        user_language_code=call.from_user.language_code,
                        text_localization=localizer.message.config_requseted,
                    ).format(config_name=config_name, config_data=config_as_link_str, country_name=country_name, country_code=country_flag),
                    parse_mode=types.ParseMode.HTML,
                    reply_markup=await inline.delete_specified_config_keyboard(
                        config_uuid=config_uuid, language_code=call.from_user.language_code
                    ),
                )
                logger.info("QR code and config link sent to user successfully.")
                # Завершаем текущее состояние
                logger.info("Finishing the current state.")
                await state.finish()
                logger.info("State finished.")
            else:
                # Если что-то пошло не так
                logger.error(f"Failed to retrieve config. Status code: {response.status}, Response: {await response.text()}")
                await call.message.answer(
                    text="Ошибка при получении конфигурации.",
                    parse_mode=types.ParseMode.HTML,
                )