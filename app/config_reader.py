import configparser
from dataclasses import dataclass


@dataclass
class TelegramBot:
    token: str
    admin_id: int


@dataclass
class Config:
    telegram_bot: TelegramBot


def load_config(path: str):
    config = configparser.ConfigParser()
    config.read(path)

    telegram_bot = config["telegram_bot"]

    return Config(telegram_bot=TelegramBot(token=telegram_bot["token"], admin_id=int(telegram_bot["admin_id"])))
