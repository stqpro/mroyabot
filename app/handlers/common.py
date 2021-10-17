from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.utils.callback_data import CallbackData

from app.handlers.trip_search import TripSearch, start_trip_search
from app.handlers.cabinet import cabinet_start
from app.utils.dbworker import get_user_trips, update_status
from app.messages.formatter import parse_favourite


unfollow_cb = CallbackData('unfollow', 'id', 'confirm')


async def reset_state(state: FSMContext):
    user_data = await state.get_data()

    for item in ['departure', 'destination', 'date', 'time']:
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


async def main_menu_handler(message: types.Message, state: FSMContext):
    if message.text.lower() == 'поиск рейсов':
        await start_trip_search(message)

    elif message.text.lower() == 'отслеживание':
        trips = get_user_trips(message.chat.id, active=True)

        if len(trips) == 0:
            await message.answer('Отслеживаемые рейсы не найдены.')

        for t in trips:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton('Удалить', callback_data=unfollow_cb.new(id=t.id, confirm='no')))
            await message.answer(parse_favourite(t), reply_markup=keyboard)

    elif message.text.lower() == 'личный кабинет':
        await cabinet_start(message, state)

    elif message.text.lower() == 'информация о боте':
        pass


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
        print(update_status(callback_data['id'], False))
        await query.message.edit_text('Рейс удален из отслеживаемых.', reply_markup=None)

    elif callback_data['confirm'] == 'cancel':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton('Удалить', callback_data=unfollow_cb.new(id=callback_data['id'], confirm='no')))

        await query.message.edit_text(query.message.parse_entities().split('\n\n<b>Ты')[0], reply_markup=keyboard)


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(main_menu_handler, state=TripSearch.main_menu.state)
    dp.register_callback_query_handler(callback_unfollow, unfollow_cb.filter(), state="*")
