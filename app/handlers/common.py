from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext


async def cmd_start(message: types.Message):
    buttons = [[types.KeyboardButton('Найти рейс')],
               [types.KeyboardButton('Отслеживание'), types.KeyboardButton('Личный кабинет')],
               [types.KeyboardButton('Информация о боте')]]

    await message.answer(text='<b>okay.</b>',
                         reply_markup=types.ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True))


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
