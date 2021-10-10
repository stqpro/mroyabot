from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from app.utils.data_requests import get_directions
from app.utils.date_strings import generate_date_keyboard


class TripSearch(StatesGroup):
    waiting_for_direction = State()
    waiting_for_date = State()
    waiting_for_time = State()


async def trip_search_start(message: types.Message):
    directions = get_directions()

    if directions is None:
        await message.answer('<b>Ошибка.</b> Не удалось загрузить список доступных маршрутов.')
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2,
                                         input_field_placeholder='Выбор маршрута')
    keyboard.add(*directions)

    await TripSearch.next()
    await message.answer('Выбери интересующий маршрут.', reply_markup=keyboard)


async def trip_search_direction_chosen(message: types.Message, state: FSMContext):
    directions = get_directions()

    if message.text not in directions:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2,
                                             input_field_placeholder='Выбор маршрута')
        keyboard.add(*directions)

        await message.answer('Указанный маршрут не найден.', reply_markup=keyboard)
        return

    departure, destination = message.text.split(" – ", maxsplit=1)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=1,
                                         input_field_placeholder='Дата поездки')
    keyboard.row('сегодня', 'завтра')
    keyboard.add(*generate_date_keyboard()[2:], 'Назад')

    await state.update_data(departure=departure, destination=destination)
    await TripSearch.next()
    await message.answer('Выбери дату поездки.', reply_markup=keyboard)


def register_handlers_trip_search(dp: Dispatcher):
    dp.register_message_handler(trip_search_start, commands="find", state='*')
    dp.register_message_handler(trip_search_direction_chosen, state=TripSearch.waiting_for_direction)
