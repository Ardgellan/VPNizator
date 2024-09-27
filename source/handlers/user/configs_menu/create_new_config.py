from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger

from loader import db_manager
from source.middlewares import rate_limit
from source.utils import localizer, qr_generator
from source.utils.states.user import GeneratingNewConfig
from source.utils.xray import xray_config
from source.keyboard import inline

from ..check_balance import has_sufficient_balance_for_conf_generation


@rate_limit(limit=1)
@has_sufficient_balance_for_conf_generation
async def request_user_for_config_name(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text(
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

    # Генерация конфига
    config = await xray_config.add_new_user(
        config_name=config_name, user_telegram_id=user_id
    )

    # Генерация QR-кода для конфига
    config_qr_code = qr_generator.create_qr_code_from_config_as_link_str(config)

    # Отправляем QR-код и данные конфига
    await message.answer_photo(
        photo=config_qr_code,
        caption=localizer.get_user_localized_text(
            user_language_code=message.from_user.language_code,
            text_localization=localizer.message.config_generated,
        ).format(config_name=config_name, config_data=config),
        parse_mode=types.ParseMode.HTML,
        reply_markup=await inline.config_generation_keyboard(
            language_code=message.from_user.language_code
        )
    )

    # Обновляем баланс пользователя
    await db_manager.update_user_balance(user_id, -3.00)

    # Завершаем состояние
    await state.finish()
