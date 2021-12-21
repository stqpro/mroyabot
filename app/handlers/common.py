from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.utils.callback_data import CallbackData

from app.handlers.trip_search import TripSearch, start_trip_search
from app.handlers.cabinet import cabinet_start
from app.utils.dbworker import get_user_trips, update_trip, get_stats, get_user_dates, delete_record
from app.messages.formatter import parse_favourite, parse_favourite_date

unfollow_cb = CallbackData('unfollow', 'id', 'confirm')


async def reset_state(state: FSMContext):
    user_data = await state.get_data()

    for item in ['departure', 'destination', 'date', 'time', 'places', 'trip_id']:
        user_data.pop(item, None)

    await state.set_data(user_data)


async def cmd_start(message: types.Message, state: FSMContext):
    await reset_state(state)

    buttons = [[types.KeyboardButton('Поиск рейсов')],
               [types.KeyboardButton('Отслеживание'), types.KeyboardButton('Личный кабинет')],
               [types.KeyboardButton('Информация о боте')]]

    await TripSearch.main_menu.set()
    await message.answer(text='Выбери нужный пункт меню.',
                         reply_markup=types.ReplyKeyboardMarkup(buttons, resize_keyboard=True,
                                                                input_field_placeholder='Главное меню'))


async def cmd_following(message: types.Message):
    trips = get_user_trips(message.chat.id, active=True)
    dates = get_user_dates(message.chat.id)

    if len(dates) == 0 and len(trips) == 0:
        await message.answer('Отслеживаемые рейсы и даты не найдены.')
        return

    if len(dates) > 0:
        for d in dates:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton('Удалить', callback_data=unfollow_cb.new(id=d.id, confirm='date')))
            await message.answer(parse_favourite_date(d), reply_markup=keyboard)

    if len(trips) > 0:
        for t in trips:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton('Удалить', callback_data=unfollow_cb.new(id=t.id, confirm='no')))
            await message.answer(parse_favourite(t), reply_markup=keyboard)

    return


async def main_menu_handler(message: types.Message, state: FSMContext):
    if message.text.lower() == 'поиск рейсов':
        await start_trip_search(message, state)

    elif message.text.lower() == 'отслеживание':
        await cmd_following(message)

    elif message.text.lower() == 'личный кабинет':
        await cabinet_start(message, state)

    elif message.text.lower() == 'информация о боте':
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(types.InlineKeyboardButton('Вся информация',
                                                url='https://telegra.ph/Vsya-informaciya-pro-MROYABOT-10-27'),
                     types.InlineKeyboardButton('Блог разработки', url='tg://resolve?domain=mroyabotinfo'))
        await message.answer("<b>MROYABOT</b> – это независимый чат-бот, который умеет оповещать об освободившихся "
                             "местах на нужные маршрутки сервиса znami.by, а также позволяет производить "
                             "бронирование и резервирование мест и управлять аккаунтом прямо из чата.",
                             reply_markup=keyboard, disable_web_page_preview=True)


async def callback_unfollow(query: types.CallbackQuery, callback_data: dict):
    if callback_data['confirm'] == 'no':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton('Да', callback_data=unfollow_cb.new(id=callback_data['id'], confirm='yes')),
            types.InlineKeyboardButton('Нет', callback_data=unfollow_cb.new(id=callback_data['id'], confirm='cancel'))
        )

        await query.message.edit_text(f"{query.message.parse_entities()}\n\n"
                                      f"<b>Ты точно хочешь удалить рейс из отслеживаемых?</b>", reply_markup=keyboard)

    elif callback_data['confirm'] == 'yes':
        update_trip(callback_data['id'], False)
        await query.message.edit_text('Рейс удален из отслеживаемых.', reply_markup=None)

    elif callback_data['confirm'] == 'date':  # without confirmation
        delete_record(callback_data['id'])
        await query.message.edit_text('Дата удалена из отслеживаемых.', reply_markup=None)

    elif callback_data['confirm'] == 'cancel':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton('Удалить', callback_data=unfollow_cb.new(id=callback_data['id'], confirm='no')))

        await query.message.edit_text(query.message.parse_entities().split('\n\n<b>Ты')[0], reply_markup=keyboard)

    await query.answer()


async def get_bot_stats(message: types.Message):
    unique_users, active_followings = get_stats()
    await message.answer(f"<b>Активных отслеживаний:</b> {active_followings}\n<b>Пользователей:</b> {unique_users}")


async def default_handler(message: types.Message, state: FSMContext):
    await message.answer('<b>Добро пожаловать в MROYABOT версии 3.1!</b> Переписанный с нуля, гораздо более быстрый, '
                         'функциональный и красивый бот снова готов искать места в маршрутках на самое удобное для '
                         'тебя время!\n\nПолное описание обновления можно прочитать в нашем '
                         '<a href="tg://resolve?domain=mroyabotinfo">блоге</a>. Возвращаемся в главное меню.',
                         disable_web_page_preview=True)
    await cmd_start(message, state)


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(cmd_following, commands="following", state="*")
    dp.register_message_handler(main_menu_handler, state=TripSearch.main_menu.state)
    dp.register_callback_query_handler(callback_unfollow, unfollow_cb.filter(), state="*")


def register_stats_handler(dp: Dispatcher, admin_id):
    dp.register_message_handler(get_bot_stats, lambda msg: msg.chat.id == admin_id, commands="stats", state="*")


def register_default_handler(dp: Dispatcher):
    dp.register_message_handler(default_handler, content_types=types.ContentTypes.TEXT, state="*")
