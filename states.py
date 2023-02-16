from aiogram.dispatcher.filters.state import StatesGroup, State


class RegistrationStateGroup(StatesGroup):
    name = State()
    email = State()
    birth_date = State()


class BookingStateGroup(StatesGroup):
    date_1 = State()
    date_2 = State()


class MeetingStateGroup(StatesGroup):
    room = State()
    date_1 = State()
    date_2 = State()
    time = State()
    final_room = State()


class DeleteAppointmentState(StatesGroup):
    booking_code = State()
    meeting_code = State()


class CustomHolidaysState(StatesGroup):
    holiday = State()


class CodesBookingsMeetingsState(StatesGroup):
    date = State()


class BotMailing(StatesGroup):
    text = State()
    photo = State()
    state = State()


class CheckCodeState(StatesGroup):
    code = State()


class DeleteUserState(StatesGroup):
    code = State()
