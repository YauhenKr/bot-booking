from aiogram.dispatcher.filters.state import StatesGroup, State


class RegistrationStateGroup(StatesGroup):
    name = State()
    email = State()
    birth_date = State()


class BookingStateGroup(StatesGroup):
    date_1 = State()
    date_2 = State()


class MeetingStateGroup(StatesGroup):
    date_1 = State()
    date_2 = State()
    time = State()
    free_room = State()
    room = State()
