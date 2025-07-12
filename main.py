import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from Middleware.dbMiddleware import DbMiddleware, CheckUserMiddleware
from Middleware.langMiddleware import LanguageMiddleware
from db.database import create_pool, close_pool
from keyboards.commands import set_bot_commands
from config_data.config import load_config, Config
from handlers.user_message import user_message
from handlers.user_callback import user_callback
from services.roulette_logic import process_last_update

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s'
    )
    config: Config = load_config(r'.env')

    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()
    dp.include_router(user_message)
    dp.include_router(user_callback)

    await set_bot_commands(bot)

    # Подключение к БД
    try:
        dp['dp_pool'] = await create_pool()
        pool = dp['dp_pool']
        logging.info('Database successfully connected')
    except Exception as error:
        logging.error('Database refused connection')
        logging.error(error)
        return  # Завершаем, если нет базы

    # Регистрируем middleware
    logging.info('Подключаем middleware')
    dp.update.outer_middleware(DbMiddleware(pool))
    dp.update.outer_middleware(CheckUserMiddleware(pool))
    dp.update.outer_middleware(LanguageMiddleware(pool))

    await process_last_update(bot)

    try:
        await dp.start_polling(bot)  # Запуск основного цикла обработки обновлений
    finally:
        # Корректное закрытие ресурсов после остановки бота
        await close_pool(pool)
        # await bot.session.close()


if __name__ == "__main__":
    logger.info("Bot successfully started")
    try:
        asyncio.run(main())
    except KeyboardInterrupt or RuntimeError:
        logger.info("Bot has shut down")
