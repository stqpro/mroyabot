import requests

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from app.handlers.common import reset_state
from app.utils.data_requests import send_code, check_code


class Cabinet(StatesGroup):
    non_authorized = State()
    check_code = State()


async def get_token(state: FSMContext):
    user_data = await state.get_data()

    if 'token' not in user_data:
        return None

    return user_data['token']


async def cabinet_start(message: types.Message, state: FSMContext):
    await reset_state(state)

    if (await get_token(state)) is None:
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

    pass  # authorized


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
    await message.answer('ok')


def register_handlers_cabinet(dp: Dispatcher):
    dp.register_message_handler(cabinet_start, commands="cabinet", state="*")
    dp.register_message_handler(contact_sent, content_types=types.ContentType.CONTACT,
                                state=Cabinet.non_authorized.state)
    dp.register_message_handler(code_sent, state=Cabinet.check_code.state)
