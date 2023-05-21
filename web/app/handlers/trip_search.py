from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData

from .cabinet import get_token
from ..utils.data_requests import get_directions, get_trips, create_reserve, get_stations, create_booking
from ..utils.date_strings import *
from ..messages.formatter import parse_trips_info
from ..utils.actions import Action
from ..utils.dbworker import create_trip, get_user_trips, update_trip, get_user_dates, create_user_date

request_cb = CallbackData('do', 'action', 'departure', 'destination', 'date', 'time', 'id', 'places', sep='|')


class TripSearch(StatesGroup):
    main_menu = State()
    direction = State()
    date = State()
    time = State()
    station = State()


async def start_trip_search(message: types.Message, state: FSMContext):
    user_data = await state.get_data()

    for item in ['departure', 'destination', 'date', 'time', 'places', 'trip_id']:
        user_data.pop(item, None)

    await state.set_data(user_data)

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

    text = 'Выбери дату поездки из списка или введи вручную в одном из следующих форматов:\n' \
           '<em>ДД.ММ.ГГГГ, ДД/ММ/ГГГГ, ДД-ММ-ГГГГ.</em>\n\nЕсли на указанную дату бронирование ещё не началось, ' \
           'можно включить <b>отслеживание даты</b>, и как только бронирование откроется, ты получишь уведомление ' \
           '<em>(работает с датами, до которых не более 30 дней)</em>.'

    await state.update_data(departure=departure, destination=destination)
    await TripSearch.date.set()
    await message.answer(text, reply_markup=keyboard)


async def date_chosen(message: types.Message, state: FSMContext):
    if message.text.lower() == 'назад':
        data = await state.get_data()
        data.pop('departure', None)
        data.pop('destination', None)
        await state.set_data(data)

        await start_trip_search(message, state)
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
        keyboard = types.InlineKeyboardMarkup()
        button_data = request_cb.new(
            action=Action.FOLLOW_DATE.value,
            departure=user_data['departure'],
            destination=user_data['destination'],
            date=parsed_date,
            time='-',
            id='-',
            places='-'
        )
        keyboard.add(types.InlineKeyboardButton('Отслеживать дату', callback_data=button_data))
        await message.answer('В выбранный день рейсы не найдены.', reply_markup=keyboard)
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


async def station_chosen(message: types.Message, state: FSMContext):
    if message.text.lower() == 'отменить':
        await message.answer('Бронирование отменено. Возвращаемся к поиску рейсов.')
        await start_trip_search(message, state)
        return

    token = await get_token(state)

    if token is None:
        await message.answer('<b>Ошибка.</b> Бронирование доступно только авторизованным пользователям. '
                             'Пройди авторизацию в личном кабинете (/account).\n\n'
                             'Возвращаемся к поиску рейсов.')
        await start_trip_search(message, state)
        return

    user_data = await state.get_data()
    stations = get_stations(user_data['departure'], user_data['destination'])

    if stations is None:
        await message.answer('<b>Ошибка</b>. Не удалось обработать сообщение.\n\nВозвращаемся к поиску рейсов.')
        await start_trip_search(message, state)
        return

    for s in stations:
        if s['name'].lower() == message.text.lower():

            booking_data = create_booking(token, user_data['departure'], user_data['destination'], user_data['date'],
                                          user_data['time'], user_data['places'], user_data['trip_id'], s['id'])

            if booking_data is None:
                await message.answer('<b>Ошибка</b>. Не удалось создать бронирование.')

            elif booking_data['status'] == 'false':
                await message.answer(f'<b>Ошибка</b>. {booking_data["error"]}')

            else:
                await message.answer('Бронирование успешно создано.\n<em>Надень в автобусе маску, пожалуйста.</em>\n\n'
                                     'Возвращаемся к поиску рейсов.')

            await start_trip_search(message, state)
            return


async def callback_start(query: types.CallbackQuery, callback_data: dict):
    callback_data.pop('@')
    keyboard = types.InlineKeyboardMarkup()
    buttons = []

    args = callback_data.copy()
    args.pop('places')

    if args['action'] == Action.BOOKING_START.value:
        args.update({'action': Action.BOOKING_PLACES.value})

        for i in range(1, min(int(callback_data['places']) + 1, 5)):
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


async def callback_follow_places(query: types.CallbackQuery, callback_data: dict):
    trip_time = datetime.datetime.strptime(f"{callback_data['date']} {callback_data['time']}", "%Y-%m-%d %H:%M")

    if trip_time < datetime.datetime.now():
        await query.answer('Нельзя отслеживать уехавшие маршрутки...', show_alert=True)
        await query.message.edit_reply_markup(None)
        return

    user_trips = get_user_trips(query.message.chat.id)

    if len([t for t in user_trips if t.status == 1]) > 6:
        await query.answer('Ты можешь отслеживать не более семи рейсов.', show_alert=True)
        return

    for t in user_trips:
        if t.departure.lower() == callback_data['departure'].lower() \
                and t.destination.lower() == callback_data['destination'].lower() \
                and t.date == callback_data['date'] \
                and t.time == callback_data['time']:

            if t.places == int(callback_data['places']):
                updated_places = None

                if t.status == 1:
                    await query.answer('Ты уже отслеживаешь этот рейс.', show_alert=True)

                    try:
                        callback_data['places'] = int(query.message.reply_markup.inline_keyboard[0][0]['text']) - 1
                        await callback_cancel(query, callback_data)
                    except ValueError:
                        await query.message.edit_reply_markup(reply_markup=None)

                    return

            else:
                updated_places = callback_data['places']

            update_trip(t.id, True, updated_places)
            await query.answer('Отслеживание рейса возобновлено.', show_alert=True)

            try:
                callback_data['places'] = int(query.message.reply_markup.inline_keyboard[0][0]['text']) - 1
                await callback_cancel(query, callback_data)
            except ValueError:
                await query.message.edit_reply_markup(reply_markup=None)

            return

    create_trip(
        query.message.chat.id,
        callback_data['departure'],
        callback_data['destination'],
        callback_data['date'],
        callback_data['time'],
        callback_data['places']
    )

    await query.answer('Рейс добавлен в отслеживаемые.', show_alert=True)

    try:
        callback_data['places'] = int(query.message.reply_markup.inline_keyboard[0][0]['text']) - 1  # not sure
        await callback_cancel(query, callback_data)
    except ValueError:
        await query.message.edit_reply_markup(reply_markup=None)


async def callback_booking_places(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    stations = get_stations(callback_data['departure'], callback_data['destination'])

    if stations is None:
        await query.answer('Ошибка. Не удалось загрузить список остановочных пунктов.', show_alert=True)
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder='Место посадки', row_width=1)
    keyboard.add(*[s['name'] for s in stations], 'Отменить')

    await state.update_data({'departure': callback_data['departure'],
                             'destination': callback_data['destination'],
                             'date': callback_data['date'],
                             'time': callback_data['time'],
                             'places': callback_data['places'],
                             'trip_id': callback_data['id']})

    await query.answer()
    await query.message.reply('Выбери место посадки.', reply_markup=keyboard)
    await TripSearch.station.set()


async def callback_reserve_places(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    token = await get_token(state)

    if token is None:
        await query.message.reply('<b>Ошибка.</b> Резервирование доступно только авторизованным пользователям. '
                                  'Пройди авторизацию в личном кабинете (/account).')
        await query.answer()
        callback_data['places'] = int(query.message.reply_markup.inline_keyboard[0][0]['text']) - 1  # not sure
        await callback_cancel(query, callback_data)
        return

    reserve_data = create_reserve(token, callback_data['id'], callback_data['places'])

    if reserve_data is None:
        await query.answer('Возникла ошибка при отправке запроса.', show_alert=True)

    elif reserve_data['status'] == 'false':
        await query.answer()
        await query.message.reply(f'<b>Ошибка.</b> {reserve_data["error"]}')

    else:
        await query.message.reply('Резервирование создано. Когда на этот рейс появятся свободные места, '
                                  'оператор свяжется с тобой.')

    callback_data['places'] = int(query.message.reply_markup.inline_keyboard[0][0]['text']) - 1  # not sure
    await callback_cancel(query, callback_data)
    return


async def callback_cancel(query: types.CallbackQuery, callback_data: dict):
    try:
        callback_data.pop('@')
        callback_data.pop('action')
    except KeyError:
        pass

    keyboard = types.InlineKeyboardMarkup()

    if int(callback_data['places']) < 4:
        follow_button_data = request_cb.new(action=Action.FOLLOW_START.value, **callback_data)
        reserve_button_data = request_cb.new(action=Action.RESERVE_START.value, **callback_data)
        keyboard.row(types.InlineKeyboardButton('Отслеживать', callback_data=follow_button_data),
                     types.InlineKeyboardButton('Резерв', callback_data=reserve_button_data))

    if int(callback_data['places']) > 0:
        booking_button_data = request_cb.new(action=Action.BOOKING_START.value, **callback_data)
        keyboard.row(types.InlineKeyboardButton('Забронировать', callback_data=booking_button_data))

    await query.answer()
    await query.message.edit_reply_markup(keyboard)

    return


async def callback_follow_date(query: types.CallbackQuery, callback_data: dict):
    dates = get_user_dates(query.message.chat.id)

    if len(dates) > 2:
        await query.answer('Ты можешь отслеживать не более трёх дат.', show_alert=True)
        return

    for d in dates:
        if d.date == callback_data['date'] \
                and d.departure == callback_data['departure'] \
                and d.destination == callback_data['destination']:
            await query.message.edit_reply_markup(None)
            await query.answer('Ты уже отслеживаешь эту дату.', show_alert=True)
            return

    create_user_date(query.message.chat.id, callback_data['date'],
                     callback_data['departure'], callback_data['destination'])

    await query.answer()
    await query.message.edit_text('<b>Отслеживание создано.</b> Когда на эту дату откроется бронирование, '
                                  'ты получишь уведомление.', reply_markup=None)

    return


def register_commands_trip_search(dp: Dispatcher):
    dp.register_message_handler(start_trip_search, commands="find", state='*')


def register_handlers_trip_search(dp: Dispatcher):
    dp.register_message_handler(direction_chosen, state=TripSearch.direction)
    dp.register_message_handler(date_chosen, state=TripSearch.date)
    dp.register_message_handler(time_chosen, state=TripSearch.time)
    dp.register_message_handler(station_chosen, state=TripSearch.station)

    dp.register_callback_query_handler(callback_cancel, request_cb.filter(action=Action.CANCEL.value), state="*")

    for action in [Action.FOLLOW_START.value, Action.RESERVE_START.value, Action.BOOKING_START.value]:
        dp.register_callback_query_handler(callback_start,
                                           request_cb.filter(action=action), state='*')

    dp.register_callback_query_handler(callback_follow_places, request_cb.filter(action=Action.FOLLOW_PLACES.value),
                                       state="*")
    dp.register_callback_query_handler(callback_reserve_places, request_cb.filter(action=Action.RESERVE_PLACES.value),
                                       state="*")
    dp.register_callback_query_handler(callback_booking_places, request_cb.filter(action=Action.BOOKING_PLACES.value),
                                       state="*")
    dp.register_callback_query_handler(callback_follow_date, request_cb.filter(action=Action.FOLLOW_DATE.value),
                                       state="*")
