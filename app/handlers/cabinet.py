import datetime
import re

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData

from app.messages.formatter import parse_active, parse_archive
from app.utils.data_requests import send_code, check_code, get_user, get_tickets, cancel_trip, update_last_name

cancel_cb = CallbackData('cancel', 'type', 'id', 'confirmed')

months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
          'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']


class Cabinet(StatesGroup):
    non_authorized = State()
    check_code = State()
    authorized = State()
    archive = State()
    last_name = State()


async def get_token(state: FSMContext):
    user_data = await state.get_data()

    if 'token' not in user_data:
        return None

    return user_data['token']


async def cabinet_start(message: types.Message, state: FSMContext):
    user_data = await state.get_data()

    for item in ['departure', 'destination', 'date', 'time', 'places', 'trip_id']:
        user_data.pop(item, None)

    await state.set_data(user_data)

    token = await get_token(state)

    if token is None:
        text = "Для просмотра личного кабинета необходимо пройти авторизацию с помощью номера телефона. После " \
               "авторизации тебе станут доступны:\n• бронирование мест прямо из бота;\n• запись в резерв;\n" \
               "• управление профилем и активными заявками;\n• просмотр статистики поездок.\n\n" \
               "Для продолжения авторизации необходимо отправить боту свой контакт. " \
               "<em>Это безопасно: бот не хранит информацию о пользователях.</em>"

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton('Отправить контакт', request_contact=True))

        await Cabinet.non_authorized.set()
        await message.answer(text, reply_markup=keyboard)
        return

    user_info = get_user(token)

    if user_info is None:
        await message.answer('<b>Ошибка.</b> Не удалось загрузить пользовательские данные.')
        return

    text = f"<b>Личный кабинет\n\nID пользователя:</b> {user_info['client_id']}\n<b>Фамилия:</b> "

    if user_info['fio'] is None:
        text += 'не задана\n\n<em>Без указания фамилии ты не сможешь бронировать и резервировать места.</em>'
    else:
        text += user_info['fio']

    buttons = [[types.KeyboardButton('Активные поездки'), types.KeyboardButton('Резерв')],
               [types.KeyboardButton('Архив поездок'), types.KeyboardButton('Изменить фамилию')],
               [types.KeyboardButton('Выход из профиля')]]

    keyboard = types.ReplyKeyboardMarkup(buttons, resize_keyboard=True, input_field_placeholder='Личный кабинет')
    await message.answer(text, reply_markup=keyboard)
    await Cabinet.authorized.set()


async def cabinet_main_menu(message: types.Message, state: FSMContext):
    token = await get_token(state)

    if message.text.lower() in ['активные поездки', 'резерв']:
        if token is None:
            await message.answer('<b>Ошибка</b>. Не удалось загрузить информацию профиля.')
            return

        if message.text.lower() == 'активные поездки':
            mode = 'booking'
        else:
            mode = 'reserve'

        tickets = get_tickets(token, mode)

        if tickets is None:
            await message.answer('<b>Ошибка.</b> Не удалось загрузить список заявок.')
            return

        tickets.sort(key=lambda x: x['date'])

        if len(tickets) == 0:
            if message.text.lower() == 'активные поездки':
                await message.answer('Активные поездки не найдены.')
            else:
                await message.answer('Заявки в резерв не найдены.')
            return

        for t in tickets:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton('Отменить',
                                                    callback_data=cancel_cb.new(type=mode, id=t['id'], confirmed='0')))
            await message.reply(parse_active(t), reply_markup=keyboard)

        return

    if message.text.lower() == 'архив поездок':
        if token is None:
            await message.answer('<b>Ошибка</b>. Не удалось загрузить информацию профиля.')
            return

        archive = get_tickets(token, 'archive')
        archive.sort(key=lambda x: x['date'], reverse=True)

        merged_trips = {}

        for item in archive:
            date_object = datetime.datetime.strptime(item['date'], '%Y-%m-%d')
            name = f"{months[date_object.month - 1]} {date_object.year}"
            merged_trips.setdefault(name, 0)
            merged_trips[name] += 1

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder='Архив поездок', row_width=2)
        keyboard.add(*[f"{t[0]} ({t[1]})" for t in merged_trips.items()], 'Назад')

        await message.answer(f'<b>Поездок в архиве:</b> {len(archive)}\n\nДля удобства просмотра информация о поездках '
                             f'разделена на группы по месяцам, в скобках указано количество заказов.',
                             reply_markup=keyboard)
        await Cabinet.archive.set()
        return

    if message.text.lower() == 'изменить фамилию':
        if token is None:
            await message.answer('<b>Ошибка</b>. Не удалось загрузить информацию профиля.')
            return

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder='Смена фамилии')
        keyboard.add('Отменить')
        await message.answer('Отправь новую фамилию в сообщении.', reply_markup=keyboard)
        await Cabinet.last_name.set()
        return

    if message.text.lower() == 'выход из профиля':
        user_data = await state.get_data()
        user_data.pop('token', None)
        await state.set_data(user_data)

        await cabinet_start(message, state)
        return


async def cabinet_last_name(message: types.Message, state: FSMContext):
    if message.text.lower() == 'отменить':
        await cabinet_start(message, state)
        return

    if re.match(r'^([А-Яа-я -]+)$', message.text) is None:
        await message.answer('<b>Ошибка.</b> Фамилия содержит недопустимые символы.')
        return

    token = await get_token(state)

    if token is None:
        await message.answer('<b>Ошибка.</b> Не удалось загрузить информацию профиля.')
        return

    update_data = update_last_name(message.text, token)

    if update_data is None:
        await message.answer('<b>Ошибка.</b> Не удалось обработать ответ сервера.')
        return

    if update_data['status'] == 'false':
        await message.answer(f'<b>Ошибка.</b> {update_data["error"]}')
        return

    await message.answer('Фамилия изменена.')
    await cabinet_start(message, state)
    return


async def cabinet_archive(message: types.Message, state: FSMContext):
    if message.text.lower() == 'назад':
        await cabinet_start(message, state)
        return

    try:
        parts = message.text.lower().split(' ', maxsplit=2)

        if parts[0] in months and re.match(r'20[1-2][0-9]', parts[1]):

            month_idx = -1

            for idx, m in enumerate(months):
                if parts[0] == m:
                    month_idx = idx + 1
                    break

            token = await get_token(state)

            if token is None:
                await message.answer('<b>Ошибка</b>. Не удалось загрузить информацию профиля.')
                return

            archive = get_tickets(token, 'archive')
            archive.sort(key=lambda x: x['date'])

            for t in archive:
                date_object = datetime.datetime.strptime(t['date'], '%Y-%m-%d')
                if date_object.month == month_idx and date_object.year == int(parts[1]):
                    await message.reply(parse_archive(t))

    except KeyError:
        pass


async def contact_sent(message: types.Message, state: FSMContext):
    contact_id = None

    try:
        contact_id = message.contact.user_id
    except KeyError:
        pass

    if contact_id != message.chat.id:
        await message.answer('Хорошая попытка.')
        return

    phone = message.contact.phone_number.replace('+', '')
    confirm_id = send_code(phone)

    if confirm_id is None:
        await message.answer('<b>Ошибка.</b> Не удалось отправить SMS с кодом.')
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton('Назад'))

    await state.update_data(confirm_id=confirm_id)
    await Cabinet.check_code.set()
    await message.answer('На твой номер выслано SMS с кодом авторизации. Отправь его в сообщении.',
                         reply_markup=keyboard)


async def code_sent(message: types.Message, state: FSMContext):
    if message.text.lower() == 'назад':
        await cabinet_start(message, state)
        return

    user_data = await state.get_data()
    confirm_data = check_code(user_data['confirm_id'], message.text.strip())

    if confirm_data is None:
        await message.answer('<b>Ошибка.</b> Не удалось проверить код авторизации.')
        return

    if confirm_data['status'] == 'false':
        await message.answer(f"<b>Ошибка.</b> {confirm_data['error']}")
        return

    await state.update_data({'token': confirm_data['user']['personal_token']})
    await message.answer('Авторизация произведена успешно.')
    await cabinet_start(message, state)
    return


async def callback_cancel_ticket(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    if callback_data['type'] == 'booking':
        action = 'Бронирование'
    else:
        action = 'Резервирование'

    if callback_data['confirmed'] == '0':
        callback_data.pop('@')
        callback_data.pop('confirmed')

        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton('Да', callback_data=cancel_cb.new(**callback_data, confirmed='1')),
                     types.InlineKeyboardButton('Нет', callback_data=cancel_cb.new(**callback_data, confirmed='2')))

        await query.answer()
        await query.message.edit_text(f"{query.message.parse_entities()}\n\n"
                                      f"<b>Ты точно хочешь отменить {action.lower()}?</b>", reply_markup=keyboard)
        return

    if callback_data['confirmed'] == '1':
        token = await get_token(state)

        if token is None:
            await query.answer('Для отмены поездки необходима авторизация.', show_alert=True)
            await query.message.edit_reply_markup(None)
            return

        cancel_data = cancel_trip(callback_data['type'], callback_data['id'], token)

        if cancel_data is None:
            await query.answer('Ошибка. Возникла проблема при отправке запроса.', show_alert=True)
            return

        if cancel_data['status'] == 'false':
            await query.answer(f'Ошибка. {cancel_data["error"]}', show_alert=True)
            return

        await query.answer()
        await query.message.edit_text(f"{query.message.parse_entities().split('<b>Ты', maxsplit=1)[0]}"
                                      f"<em>{action} отменено.</em>", reply_markup=None)
        return

    if callback_data['confirmed'] == '2':
        callback_data.pop('@')
        callback_data.pop('confirmed')

        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton('Отменить',
                                                callback_data=cancel_cb.new(**callback_data, confirmed='0')))

        await query.answer()
        await query.message.edit_text(query.message.parse_entities().split('\n\n<b>Ты', maxsplit=1)[0],
                                      reply_markup=keyboard)

        return


def register_commands_cabinet(dp: Dispatcher):
    dp.register_message_handler(cabinet_start, commands="account", state="*")


def register_handlers_cabinet(dp: Dispatcher):
    dp.register_message_handler(contact_sent, content_types=types.ContentType.CONTACT,
                                state=Cabinet.non_authorized.state)
    dp.register_message_handler(code_sent, state=Cabinet.check_code.state)
    dp.register_message_handler(cabinet_main_menu, state=Cabinet.authorized.state)
    dp.register_message_handler(cabinet_archive, state=Cabinet.archive.state)
    dp.register_message_handler(cabinet_last_name, state=Cabinet.last_name.state)
    dp.register_callback_query_handler(callback_cancel_ticket, cancel_cb.filter(), state="*")
