import datetime

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from create_bot import db, admins_id, dp
from services import custom_holidays, check_holiday, check_code, day_or_month_without_null
from states import CustomHolidaysState, CodesBookingsMeetingsState, CheckCodeState, DeleteUserState


# async def get_qrcodes(message: types.Message):
#     day, year, month = get_today()
#     ymd = f"{year}-{month}-{day}"
#     await message.answer(db.get_bookings_codes(ymd))


# delete user drum table users
async def delete_user(message: types.Message):
    markup = InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[[InlineKeyboardButton(text='Скасаваць', callback_data='quit_delete')]]
    )
    await message.answer(f'Увядзіце ID карыстальніка, які трэба выдаліць', reply_markup=markup)
    await DeleteUserState.code.set()


async def user_deleting(message: types.Message, state: FSMContext):
    code = int(message.text)
    if type(code) != int:
        await message.answer('Код павінен складацца з лічбаў')
    else:
        db.delete_user(code)
        await state.finish()
        await message.answer('Карыстальнік выдален')


async def cancel_user_deleting(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.answer('Вы спынілі выдаленьне карыстальніка')


# adding of custom holidays
async def do_holiday(message: types.Message):
    markup = InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[[InlineKeyboardButton(text='Скасаваць', callback_data='quit')]]
    )
    await message.answer(f'Увядзіце дату, каб зрабіць яе выходным у фармаце ГГГГ-ММ-ДД', reply_markup=markup)
    await CustomHolidaysState.holiday.set()


async def adding_holiday(message: types.Message, state: FSMContext):
    holiday = str(message.text)
    if not check_holiday(holiday):
        await message.answer('Фармат даты павінен быць ГГГГ-ММ-ДД')
    else:
        db.add_custom_holidays(holiday)
        await state.finish()
        await message.answer('Выходны зроблены.')


async def cancel_adding_holiday(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.answer('Вы спынілі даданьне выходнага')


# checking out of spare day in space
async def get_codes_for_day(message: types.Message):
    await message.answer(f'Увядзіце дату у фармаце ГГГГ-ММ-ДД, каб дазнацца, ці свабодная яна')
    await CodesBookingsMeetingsState.date.set()


async def checking_day(message: types.Message, state: FSMContext):
    from bot import cal

    date = str(message.text)
    year, month, day = date.split('-')
    day = day_or_month_without_null(day)
    month = day_or_month_without_null(month)
    isholiday = cal.is_working_day(datetime.date(int(year), int(month), int(day)))
    if not check_holiday(date):
        await message.answer('Фармат даты павінен быць ГГГГ-ММ-ДД')
    else:
        if len(db.get_bookings_codes(date)) != 0 or len(db.get_meetings_codes(date)) != 0:
            await message.answer('Гэты дзень заняты')
        elif date in custom_holidays or not isholiday:
             await message.answer('Гэты дзень выходны')
        else:
            await message.answer('Гэты дзень свабодны')
        await state.finish()


async def enter_the_code(message: types.Message):
    # markup = InlineKeyboardMarkup(
    #     row_width=2,
    #     inline_keyboard=[[InlineKeyboardButton(text='Скасаваць', callback_data='cancel_code')]]
    # )
    await message.answer(f'Увядзіце код (толькі лічбы), каб даведацца на інфармацыю аб ім')
    await CheckCodeState.code.set()


async def find_information(message: types.Message, state: FSMContext):
    code = message.text
    if check_code(code):
        bookings = db.select_all_from_bookings(code)
        meetings = db.select_all_from_meetings(code)
        if bookings:
            await message.answer(f"Дата кода квітка для каворкінга: {bookings[0][2]}")
        elif meetings:
            await message.answer(f"Дата кода перагаворнага пакою: {meetings[0][0]} \n"
                                 f"Час перагаворнага пакою: {meetings[0][1]}\n"
                                 f"Месца: {meetings[0][2]}\n"
                                 )
        else:
            await message.answer('Вы ўпэўнены, што такі код ёсьць?')
        await state.finish()
    else:
        await message.answer('Праверце напісаньне коду. Ён павінен складаца толькі з лічб.')

# @dp.callback_query_handler(text='cancel_code')
# async def cancel_the_checking(call: types.CallbackQuery, state: FSMContext):
#     await state.finish()
#     await call.message.answer('Пошук інфармацыі аб кодзе скасаваны')


def register_handlers_admin(dp: Dispatcher):
    # dp.register_message_handler(get_qrcodes, commands=['today'], chat_id=admins_id)

    dp.register_message_handler(delete_user, commands=['deleteuser'], chat_id=admins_id)
    dp.register_message_handler(user_deleting, state=DeleteUserState.code, chat_id=admins_id)
    dp.register_callback_query_handler(cancel_user_deleting, state=DeleteUserState.code, chat_id=admins_id)

    dp.register_message_handler(do_holiday, commands=['holiday'], chat_id=admins_id)
    dp.register_message_handler(adding_holiday, state=CustomHolidaysState.holiday, chat_id=admins_id)
    dp.register_callback_query_handler(cancel_adding_holiday, state=CustomHolidaysState.holiday, chat_id=admins_id)

    dp.register_message_handler(get_codes_for_day, commands=['check'], chat_id=admins_id)
    dp.register_message_handler(checking_day, state=CodesBookingsMeetingsState.date, chat_id=admins_id)

    dp.register_message_handler(enter_the_code, commands=['code'], chat_id=admins_id)
    dp.register_message_handler(find_information, state=CheckCodeState.code, chat_id=admins_id)
    # dp.register_message_handler(cancel_the_checking, chat_id=admins_id)