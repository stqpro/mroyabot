import re

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData

from app.utils.data_requests import get_directions, get_trips
from app.utils.date_strings import *
from app.messages.formatter import parse_trips_info
from app.utils.actions import Action

request_cb = CallbackData('do', 'action', 'departure', 'destination', 'date', 'time', 'id', 'places', sep='|')


class TripSearch(StatesGroup):
    main_menu = State()
    direction = State()
    date = State()
    time = State()


async def start_trip_search(message: types.Message):
    directions = get_directions()

    if directions is None:
        await message.answer('<b>Ошибка.</b> Не удалось загрузить список доступных маршрутов.')
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, input_field_placeholder='Выбор маршрута')
    keyboard.add(*directions)

    await TripSearch.direction.set()
    await message.answer('Выбери интересующий маршрут.', reply_markup=keyboard)


async def direction_chosen(message: types.Message, state: FSMContext):
    directions = get_directions()

    if message.text not in directions:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2,
                                             input_field_placeholder='Выбор маршрута')
        keyboard.add(*directions)

        await message.answer('Указанный маршрут не найден.', reply_markup=keyboard)
        return

    departure, destination = message.text.split(" – ", maxsplit=1)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, input_field_placeholder='Дата поездки')
    keyboard.row('сегодня', 'завтра')
    keyboard.add(*generate_date_strings(offset=2, length=13), 'Назад')

    await state.update_data(departure=departure, destination=destination)
    await TripSearch.date.set()
    await message.answer('Выбери дату поездки.', reply_markup=keyboard)


async def date_chosen(message: types.Message, state: FSMContext):
    if message.text.lower() == 'назад':
        data = await state.get_data()
        data.pop('departure')
        data.pop('destination')
        await state.set_data(data)

        await start_trip_search(message)
        return

    parsed_date = parse_date_string(message.text.lower())

    if parsed_date is None:
        return

    user_data = await state.get_data()

    trips = get_trips(parsed_date, user_data['departure'], user_data['destination'])

    if trips is None:
        await message.answer('<b>Ошибка.</b> Не удалось загрузить список рейсов.')
        return

    if len(trips) == 0:
        await message.answer('В выбранный день рейсы не найдены.')
        return

    merged_trips = {}

    for t in trips:
        merged_trips.setdefault(t['time'], 0)
        merged_trips[t['time']] += t['free_places']

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, input_field_placeholder='Время поездки')
    keyboard.add(*[f"{key} (мест: {value})" for key, value in merged_trips.items()], 'Назад')

    await state.update_data(date=parsed_date)
    await TripSearch.time.set()
    await message.answer('Выбери время поездки.', reply_markup=keyboard)


async def time_chosen(message: types.Message, state: FSMContext):
    if message.text.lower() == 'назад':
        data = await state.get_data()
        data.pop('date')

        # подмена текста сообщения на случай нажатия кнопки 'Назад'
        message.text = f"{data['departure']} – {data['destination']}"

        await state.set_data(data)
        await direction_chosen(message, state)
        return

    parsed_time = message.text.split(' ', maxsplit=1)[0]
    if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', parsed_time):
        return None

    user_data = await state.get_data()
    trips = get_trips(user_data['date'], user_data['departure'], user_data['destination'], parsed_time)

    if len(trips) == 0:
        await message.answer('На выбранное время рейсы не найдены.')
        return

    answer_data = parse_trips_info(trips, f"{user_data['departure']} – {user_data['destination']}")

    for msg in answer_data:
        keyboard = types.InlineKeyboardMarkup()

        args = {
            'departure': user_data['departure'],
            'destination': user_data['destination'],
            'date': user_data['date'],
            'time': parsed_time,
            'id': msg['id'],
            'places': msg['places']
        }

        if msg['places'] < 4:
            follow_button_data = request_cb.new(action=Action.FOLLOW_START.value, **args)
            reserve_button_data = request_cb.new(action=Action.RESERVE_START.value, **args)
            keyboard.row(types.InlineKeyboardButton('Отслеживать', callback_data=follow_button_data),
                         types.InlineKeyboardButton('Резерв', callback_data=reserve_button_data))

        if msg['places'] > 0:
            booking_button_data = request_cb.new(action=Action.BOOKING_START.value, **args)
            keyboard.row(types.InlineKeyboardButton('Забронировать', callback_data=booking_button_data))

        await message.answer(msg['message'], reply_markup=keyboard)


async def callback_start(query: types.CallbackQuery, callback_data: dict):
    callback_data.pop('@')
    keyboard = types.InlineKeyboardMarkup()
    buttons = []

    args = callback_data.copy()
    args.pop('places')

    if args['action'] == Action.BOOKING_START.value:
        args.update({'action': Action.BOOKING_PLACES.value})

        for i in range(1, int(callback_data['places']) + 1):
            buttons.append(types.InlineKeyboardButton(str(i), callback_data=request_cb.new(places=str(i), **args)))

    else:

        if args['action'] == Action.FOLLOW_START.value:
            args.update({'action': Action.FOLLOW_PLACES.value})
        elif args['action'] == Action.RESERVE_START.value:
            args.update({'action': Action.RESERVE_PLACES.value})

        for i in range(int(callback_data['places']) + 1, 5):
            buttons.append(types.InlineKeyboardButton(str(i), callback_data=request_cb.new(places=str(i), **args)))

    keyboard.row(*buttons)

    args.update({'action': Action.CANCEL.value, 'places': callback_data['places']})
    keyboard.row(types.InlineKeyboardButton('Отмена', callback_data=request_cb.new(**args)))

    await query.message.edit_reply_markup(keyboard)
    await query.answer('Укажи необходимое количество мест.')


async def callback_cancel(query: types.CallbackQuery, callback_data: dict):
    callback_data.pop('@')
    callback_data.pop('action')
    keyboard = types.InlineKeyboardMarkup()

    if int(callback_data['places']) < 4:
        follow_button_data = request_cb.new(action=Action.FOLLOW_START.value, **callback_data)
        reserve_button_data = request_cb.new(action=Action.RESERVE_START.value, **callback_data)
        keyboard.row(types.InlineKeyboardButton('Отслеживать', callback_data=follow_button_data),
                     types.InlineKeyboardButton('Резерв', callback_data=reserve_button_data))

    if int(callback_data['places']) > 0:
        booking_button_data = request_cb.new(action=Action.BOOKING_START.value, **callback_data)
        keyboard.row(types.InlineKeyboardButton('Забронировать', callback_data=booking_button_data))

    await query.message.edit_reply_markup(keyboard)


def register_handlers_trip_search(dp: Dispatcher):
    dp.register_message_handler(start_trip_search, commands="find", state='*')
    dp.register_message_handler(direction_chosen, state=TripSearch.direction)
    dp.register_message_handler(date_chosen, state=TripSearch.date)
    dp.register_message_handler(time_chosen, state=TripSearch.time)

    dp.register_callback_query_handler(callback_cancel, request_cb.filter(action=Action.CANCEL.value), state="*")

    for action in [Action.FOLLOW_START.value, Action.RESERVE_START.value, Action.BOOKING_START.value]:
        dp.register_callback_query_handler(callback_start,
                                           request_cb.filter(action=action), state='*')
