import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from app.config_reader import load_config
from app.handlers.common import register_handlers_common


logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    logger.info("Starting bot...")

    config = load_config('config/bot.ini')

    bot = Bot(token=config.telegram_bot.token, parse_mode='HTML')
    dp = Dispatcher(bot=bot, storage=MemoryStorage())

    register_handlers_common(dp)

    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())
