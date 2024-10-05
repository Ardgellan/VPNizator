from aiogram import executor


async def set_commands(dp):
    from aiogram import types

    await dp.bot.set_my_commands(
        commands=[
            types.BotCommand(command="/menu", description="Show main menu / Вызвать главное меню"),
            types.BotCommand(command="/pay", description="Make a payment / Оформить платеж"),  # Добавляем команду /pay
            types.BotCommand(command="/check_payment", description="Check payment status / Проверить статус платежа")  # Добавляем команду /check_payment
        ]
    )


async def on_startup(dp):
    import time

    from loguru import logger
    from source import handlers, middlewares
    from source.utils.shedulers import SubscriptionChecker

    logger.add(
        f'logs/{time.strftime("%Y-%m-%d__%H-%M")}.log',
        level="DEBUG",
        rotation="500 MB",
        compression="zip",
    )

    subscription_checker = SubscriptionChecker()

    middlewares.setup(dp)
    await set_commands(dp)
    handlers.setup(dp)

    logger.success("[+] Bot started successfully")


if __name__ == "__main__":
    # Launch
    from aiogram import executor

    from source.handlers import dp

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
