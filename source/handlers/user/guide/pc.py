from aiogram import types

from source.keyboard import inline
from source.middlewares import rate_limit
from source.utils import localizer
from source.utils.guide_images_loader import GuideImagesLoader


@rate_limit(limit=1)
async def show_help_guide_pc(call: types.CallbackQuery):

    await call.message.edit_text(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.which_os_do_you_have_message,
        ),
        parse_mode=types.ParseMode.HTML,
        reply_markup=await inline.choose_your_os_keyboard(
            language_code=call.from_user.language_code,
        ),
    )

@rate_limit(limit=1)
async def show_help_guide_macos(call: types.CallbackQuery):
    guide_images = await GuideImagesLoader().get_macos_guide_images()
    media_group = [types.InputMediaPhoto(media=photo) for photo in guide_images]

    await call.message.answer_media_group(
        media=media_group,
    )

    await call.message.answer(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.help_guide_message_macos,
        ),
        parse_mode=types.ParseMode.HTML,
        reply_markup=await inline.download_app_for_connect_to_vpn_keyboard(
            language_code=call.from_user.language_code,
            platform="macos",
        ),
    )

@rate_limit(limit=1)
async def show_help_guide_windows(call: types.CallbackQuery):
    guide_images = await GuideImagesLoader().get_windows_guide_images()
    media_group = [types.InputMediaPhoto(media=photo) for photo in guide_images]

    await call.message.answer_media_group(
        media=media_group,
    )

    await call.message.answer(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.help_guide_message_windows,
        ),
        parse_mode=types.ParseMode.HTML,
        reply_markup=await inline.download_app_for_connect_to_vpn_keyboard(
            language_code=call.from_user.language_code,
            platform="windows",
        ),
    )

@rate_limit(limit=1)
async def show_help_guide_linux(call: types.CallbackQuery):
    guide_images = await GuideImagesLoader().get_linux_guide_images()
    media_group = [types.InputMediaPhoto(media=photo) for photo in guide_images]

    await call.message.answer_media_group(
        media=media_group,
    )

    await call.message.answer(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.help_guide_message_linux,
        ),
        parse_mode=types.ParseMode.HTML,
        reply_markup=await inline.download_app_for_connect_to_vpn_keyboard(
            language_code=call.from_user.language_code,
            platform="linux",
        ),
    )
