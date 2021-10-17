import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from app.utils.config_reader import load_config
from app.handlers.common import register_handlers_common
from app.handlers.trip_search import register_handlers_trip_search
from app.handlers.cabinet import register_handlers_cabinet

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    logger.info("Starting bot...")

    config = load_config('config/bot.ini')

    bot = Bot(token=config.telegram_bot.token, parse_mode='HTML')
    storage = RedisStorage2(db=0)
    dp = Dispatcher(bot=bot, storage=storage)

    register_handlers_common(dp)
    register_handlers_trip_search(dp)
    register_handlers_cabinet(dp)

    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())
