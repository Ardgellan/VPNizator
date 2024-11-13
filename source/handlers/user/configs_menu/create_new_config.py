from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger
import aiohttp

from loader import db_manager
from source.middlewares import rate_limit
from source.utils import localizer, qr_generator
from source.utils.states.user import GeneratingNewConfig
from source.keyboard import inline

from ..check_balance import has_sufficient_balance_for_conf_generation


@rate_limit(limit=1)
@has_sufficient_balance_for_conf_generation
async def request_user_for_country(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.choose_country_message,
        ),
        parse_mode=types.ParseMode.HTML,
        reply_markup=await inline.country_selection_keyboard(
            language_code=call.from_user.language_code
        )
    )
    logger.info("we finished choose_country")



async def request_user_for_config_name(call: types.CallbackQuery, state: FSMContext):
    country_name = call.data.split("_")[1]
    await state.update_data(country_name=country_name)

    await call.message.answer(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.request_config_name,
        ),
        parse_mode=types.ParseMode.HTML,
    )
    await GeneratingNewConfig.waiting_for_config_name.set()


async def generate_config_for_user(message: types.Message, state: FSMContext):
    # Получаем имя конфигурации от пользователя
    config_name = message.text
    user_id = message.from_user.id

    user_data = await state.get_data()
    country_name = user_data.get("country_name")
    country_name = country_name.lower()
    logger.info(f"Country name = {country_name}")

    # Отправляем сообщение, что генерация началась
    await message.answer(
        text=localizer.get_user_localized_text(
            user_language_code=message.from_user.language_code,
            text_localization=localizer.message.got_config_name_start_generating,
        ),
        parse_mode=types.ParseMode.HTML,
    )

    # Отправляем действие "загрузка"
    await message.answer_chat_action(action=types.ChatActions.UPLOAD_PHOTO)

    # # Страна, которую нужно передать в API
    # country = "estonia"  # Пример страны, можно настроить динамически

    # Теперь отправляем запрос к API для добавления пользователя и получения ссылки
    try:
        logger.info("Creating HTTP session and sending POST request to API...")
        async with aiohttp.ClientSession() as session:
            logger.info(f"Sending POST request to add user. Params: user_id={user_id}, config_name={config_name}")
            async with session.post(
                f"https://nginxtest.vpnizator.online/add_user/{country_name}/",  # Указываем правильный URL API
                params={"user_id": user_id, "config_name": config_name}  # Передаем параметры в теле запроса
            ) as response:
                logger.info(f"Received response from API. Status code: {response.status}")
                
                # Проверяем статус ответа
                if response.status == 200:
                    logger.info("Response status is 200. Proceeding with further processing...")
                    
                    data = await response.json() # Асинхронно читаем JSON-ответ
                    logger.info("Parsed JSON response from API.")

                    user_link = data.get("link")
                    config_uuid = data.get("config_uuid")  # Получаем UUID конфигурации
                    server_domain = data.get("server_domain")

                    logger.info(f"Extracted values - user_link: {user_link}, config_uuid: {config_uuid}, server_domain: {server_domain}")

                    # Генерация QR-кода для конфига
                    logger.info("Generating QR code for config...")
                    config_qr_code = qr_generator.create_qr_code_from_config_as_link_str(user_link)
                    logger.info("QR code generated successfully.")

                    # Отправляем QR-код и данные конфига
                    logger.info(f"Sending QR code and configuration data to user: {message.from_user.id}")
                    await message.answer_photo(
                        photo=config_qr_code,
                        caption=localizer.get_user_localized_text(
                            user_language_code=message.from_user.language_code,
                            text_localization=localizer.message.config_generated,
                        ).format(config_name=config_name, config_data=user_link),
                        parse_mode=types.ParseMode.HTML,
                        reply_markup=await inline.config_generation_keyboard(
                            language_code=message.from_user.language_code
                        ),
                    )
                    logger.info("QR code and config data sent to user.")

                    # Теперь данные передаем на бекэнд для записи в базу данных
                    # Работа с базой данных на бекэнде:
                    logger.info("Inserting config data into the database...")
                    async with db_manager.transaction() as conn:
                        await db_manager.insert_new_vpn_config(
                            user_id=user_id,  # Получаем Telegram ID
                            config_name=config_name,
                            config_uuid=config_uuid,
                            server_domain=server_domain,
                            conn=conn,  # Передаем транзакцию для консистентности
                        )
                    logger.info("Config data successfully inserted into the database.")

                    # Обновляем баланс пользователя
                    logger.info(f"Updating user balance for user_id={user_id}...")
                    await db_manager.update_user_balance(user_id, -3.00)
                    logger.info("User balance updated successfully.")

                    # Завершаем состояние
                    logger.info("Finishing the state and ending the process.")
                    await state.finish()
                    logger.info("Finished the state and ended the process.")

                else:
                    error_message = await response.text()
                    logger.error(f"API request failed with status code {response.status}. Response: {error_message}")
                    raise Exception(f"Failed to add user: {await response.text()}")

    except Exception as e:
        logger.error(f"Error while generating config: {str(e)}")
        await state.finish()
