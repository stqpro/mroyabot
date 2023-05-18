import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.utils.config_reader import load_config
from app.handlers.common import register_handlers_common, register_default_handler, register_stats_handler
from app.handlers.trip_search import register_handlers_trip_search, register_commands_trip_search
from app.handlers.cabinet import register_handlers_cabinet, register_commands_cabinet
from app.utils.dbworker import check_trips, clear_trips, check_dates

logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="главное меню"),
        BotCommand(command="/find", description="поиск рейсов"),
        BotCommand(command="/following", description="отслеживаемые рейсы"),
        BotCommand(command="/account", description="личный кабинет")
    ]
    await bot.set_my_commands(commands)


async def send_notifications(bot: Bot):
    messages = check_trips()

    for m in messages:
        await bot.send_message(m[0], m[1], reply_markup=m[2])


async def check_following_dates(bot: Bot):
    messages = check_dates()

    for m in messages:
        await bot.send_message(m[0], m[1])


async def main():
    logging.basicConfig(filename='log.txt', level=logging.WARN, filemode='a',
                        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    logger.info("Starting bot...")

    config = load_config('config/bot.ini')
    logger.info(config.telegram_bot.token)

    bot = Bot(token=config.telegram_bot.token, parse_mode='HTML')
    storage = RedisStorage2(host="redis", db=0, prefix='mb')
    dp = Dispatcher(bot=bot, storage=storage)

    await set_commands(bot)

    register_commands_trip_search(dp)
    register_commands_cabinet(dp)

    register_stats_handler(dp, config.telegram_bot.admin_id)

    register_handlers_common(dp)
    register_handlers_trip_search(dp)
    register_handlers_cabinet(dp)

    register_default_handler(dp)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_notifications, 'interval', (bot,), minutes=3)
    scheduler.add_job(check_following_dates, 'cron', (bot,), minute='5,35', misfire_grace_time=None)
    scheduler.add_job(clear_trips, 'cron', minute=4, misfire_grace_time=None)

    scheduler.start()

    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())
