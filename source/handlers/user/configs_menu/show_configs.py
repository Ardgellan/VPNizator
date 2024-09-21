from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import db_manager
from source.keyboard import inline
from source.middlewares import rate_limit
from source.utils import localizer

from ..check_is_user_banned import is_user_banned

from loguru import logger

@rate_limit(limit=1)
@is_user_banned
async def show_user_configs(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    logger.debug("GARBANUSHKA")
    # Завершаем текущее состояние, чтобы оно не мешало следующей обработке
    #await state.finish()
    logger.debug("GARBANUSHKA2")
    is_user_have_any_configs = await db_manager.is_user_have_any_config(user_id=user_id)
    logger.debug("GARBANUSHKA3") # ОБА РАЗА ДОХОДИТ ДОСЮДА! НО ТУТ КРАШИТСЯ
    try:
        await call.message.edit_text( # СМЕНА С call.message.edit_text на call.message.answer рещила проблему, но фунцкция превратилась в кошмарный спам. 
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=(
                    localizer.message.user_configs_list
                    if is_user_have_any_configs
                    else localizer.message.no_configs_found_create_new_one
                ),
            ),
            parse_mode=types.ParseMode.HTML,
            reply_markup=await inline.user_configs_list_keyboard(
                user_id=user_id, language_code=call.from_user.language_code
            ),
        )
    except Exception as e:
        await call.message.answer( # СМЕНА С call.message.edit_text на call.message.answer рещила проблему, но фунцкция превратилась в кошмарный спам. 
            text=localizer.get_user_localized_text(
                user_language_code=call.from_user.language_code,
                text_localization=(
                    localizer.message.user_configs_list
                    if is_user_have_any_configs
                    else localizer.message.no_configs_found_create_new_one
                ),
            ),
            parse_mode=types.ParseMode.HTML,
            reply_markup=await inline.user_configs_list_keyboard(
                user_id=user_id, language_code=call.from_user.language_code
            ),
        )

    logger.debug("GARBANUSHKA_4") # ВОТ ЭТО УЖЕ НЕ ПОВТОРЯЕТСЯ ПРИ ЗАХОДЕ ИЗ МЕНЮ КОНКРЕТНОГО КОНФИГА
