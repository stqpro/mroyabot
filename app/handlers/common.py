from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext


async def cmd_start(message: types.Message):
    buttons = [[types.KeyboardButton('Поиск рейсов')],
               [types.KeyboardButton('Отслеживание'), types.KeyboardButton('Личный кабинет')],
               [types.KeyboardButton('Информация о боте')]]

    await message.answer(text='Выбери нужный пункт меню.',
                         reply_markup=types.ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True,
                                                                input_field_placeholder='Главное меню'))


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
