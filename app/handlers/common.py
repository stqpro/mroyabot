from aiogram import Dispatcher, types

from app.handlers.trip_search import TripSearch, start_trip_search


async def cmd_start(message: types.Message):
    buttons = [[types.KeyboardButton('Поиск рейсов')],
               [types.KeyboardButton('Отслеживание'), types.KeyboardButton('Личный кабинет')],
               [types.KeyboardButton('Информация о боте')]]

    await TripSearch.main_menu.set()
    await message.answer(text='Выбери нужный пункт меню.',
                         reply_markup=types.ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True,
                                                                input_field_placeholder='Главное меню'))


async def main_menu_handler(message: types.Message):
    if message.text.lower() == 'поиск рейсов':
        await start_trip_search(message)

    elif message.text.lower() == 'отслеживание':
        pass

    elif message.text.lower() == 'личный кабинет':
        pass

    elif message.text.lower() == 'информация о боте':
        pass


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(main_menu_handler, state=TripSearch.main_menu.state)
