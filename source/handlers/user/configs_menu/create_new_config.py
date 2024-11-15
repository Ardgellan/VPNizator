from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger
import aiohttp

from loader import db_manager
from source.middlewares import rate_limit
from source.utils import localizer, qr_generator
from source.utils.states.user import GeneratingNewConfig
from source.keyboard import inline
from source.utils.code_to_flag import *

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


async def request_user_for_config_name(call: types.CallbackQuery, state: FSMContext):
    selected_country = call.data.split("_")[1]
    await state.update_data(selected_country=selected_country)

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
    selected_country = user_data.get("selected_country")
    selected_country = selected_country.lower()




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

    # Теперь отправляем запрос к API для добавления пользователя и получения ссылки
    try:

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://nginxtest.vpnizator.online/add_user/{selected_country}/",  # Указываем правильный URL API
                params={"user_id": user_id, "config_name": config_name}  # Передаем параметры в теле запроса
            ) as response:
                
                # Проверяем статус ответа
                if response.status == 200:
                    
                    data = await response.json() # Асинхронно читаем JSON-ответ

                    user_link = data.get("link")
                    config_uuid = data.get("config_uuid")  # Получаем UUID конфигурации
                    server_domain = data.get("server_domain")
                    country_name = data.get("server_country")
                    country_code = data.get("server_country_code")

                    config_as_link_str_with_flag = f"{user_link} {country_code_to_flag(country_code)}"
                    # Генерация QR-кода для конфига
                    config_qr_code = qr_generator.create_qr_code_from_config_as_link_str(user_link)

                    
                    # Отправляем QR-код и данные конфига
                    await message.answer_photo(
                        photo=config_qr_code,
                        caption=localizer.get_user_localized_text(
                            user_language_code=message.from_user.language_code,
                            text_localization=localizer.message.config_generated,
                        ).format(config_name=config_name, country_name=country_name, country_code=country_code, config_data=config_as_link_str_with_flag),
                        parse_mode=types.ParseMode.HTML,
                        reply_markup=await inline.config_generation_keyboard(
                            language_code=message.from_user.language_code
                        ),
                    )

                    async with db_manager.transaction() as conn:
                        await db_manager.insert_new_vpn_config(
                            user_id=user_id,  # Получаем Telegram ID
                            config_name=config_name,
                            config_uuid=config_uuid,
                            server_domain=server_domain,
                            country_name=country_name,
                            country_code=country_code,
                            conn=conn,  # Передаем транзакцию для консистентности
                        )

                    await db_manager.update_user_balance(user_id, -3.00)

                    # Завершаем состояние
                    await state.finish()

                else:
                    error_message = await response.text()
                    logger.error(f"API request failed with status code {response.status}. Response: {error_message}")
                    raise Exception(f"Failed to add user: {await response.text()}")

    except Exception as e:
        logger.error(f"Error while generating config: {str(e)}")
        await state.finish()
