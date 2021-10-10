from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from app.utils.data_requests import get_directions


class TripSearch(StatesGroup):
    waiting_for_direction = State()
    waiting_for_date = State()
    waiting_for_time = State()


async def trip_search_start(message: types.Message, state: FSMContext):
    pass
