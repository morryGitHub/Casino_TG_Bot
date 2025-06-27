import asyncio
import os
import logging

from aiogram import Bot, Router, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from services.updates import process_last_update
from config_data.config import load_config, Config
from handlers.user import user

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s'
    )
    config: Config = load_config(r'.env')

    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()
    dp.include_router(user)

    # await set_main_menu(bot)

    # Регистриуем роутеры
    logger.info('Подключаем роутеры')
    ...

    # Регистрируем миддлвари
    logger.info('Подключаем миддлвари')
    ...
    try:
        await process_last_update(bot)
    finally:
        await bot.session.close()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot successfully started")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot has shut down")
