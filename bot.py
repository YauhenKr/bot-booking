import datetime
import logging

import yaml
import re
import calendar

from aiogram import executor, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dateutil.relativedelta import relativedelta

from create_bot import dp, bot, db, admins_id, cal, obj
from handlers import admin, mailing
from services import check_date, check_email, filter_working_days, \
    numbs, get_randint, get_today, meeting_numbs, meeting_time, create_time, \
    create_name_of_meet_room, meeting_rooms, reduce_tickets, booking_codes, meeting_codes, \
    check_the_month_upgrade_tickets, recreate_month, recreate_day, custom_holidays
from states import RegistrationStateGroup, BookingStateGroup, MeetingStateGroup, DeleteAppointmentState


logging.basicConfig(level=logging.INFO)

text_from_file = {}


admin.register_handlers_admin(dp)
mailing.register_handlers_admin(dp)


# open file bel or rus
def get_text_data(language_file):
    with open(language_file, 'r', encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def set_language_file(message):
    global text_from_file
    language_file = ''
    if message == 'Беларуская':
        language_file = 'text_bel.yaml'
    elif message == 'English':
        language_file = 'text_eng.yaml'
    text_from_file = get_text_data(language_file)


@dp.message_handler(commands=['start'])
async def choice_lang(message: types.Message):
    if db.user_exist(message.chat.id):
        language = db.get_user_language(message.chat.id)[0]
        set_language_file(*language)
        menu_markup = main_menu()
        await message.answer(text_from_file['menu']['msg'], reply_markup=menu_markup)
    else:
        markup = choose_lang_markup()
        await message.answer('Абярыце мову / Choose the language', reply_markup=markup)
        types.ReplyKeyboardRemove(selective=False)


@dp.message_handler(text=['English', 'Беларуская'])
async def check_code(message: types.Message):
    if not db.users_lang_exist(message.chat.id):
        db.add_users_lang(message.chat.id, message.text)
    set_language_file(message.text)
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
    go = types.KeyboardButton(text_from_file['hi_b'])
    markup.add(go)
    await message.answer(text_from_file['hi'], reply_markup=markup)


@dp.message_handler(text=['Рэгістрацыя', 'Registration'])
async def start(message: types.Message):
    if message.chat.type == 'private':
        markup = conditions_markup()
        await message.answer(text_from_file['start']['text'], reply_markup=markup)


@dp.callback_query_handler(text='cancel')
async def cancel(call: CallbackQuery):
    if call.message.chat.type == 'private':
        await call.message.answer(text_from_file['canceling'])


@dp.callback_query_handler(text='next', state=None)
async def enter_username(call: CallbackQuery):
    markup = cancel_markup()
    await call.message.answer(text_from_file['reg']['name'], reply_markup=markup)
    await RegistrationStateGroup.name.set()


@dp.message_handler(state=RegistrationStateGroup.name)
async def username_answer_and_email(message: types.Message, state: FSMContext):
    answer = message.text
    regex = re.compile(r'[@_!#$%^&*()<>?/\|}{~:0123456789]')
    markup = cancel_markup()
    if regex.search(answer) is not None:
        await message.answer(text_from_file['reg']['only_let'])
    elif 2 > len(message.text) or len(message.text) > 30:
        await message.answer(text_from_file['reg']['huge_name'])
    else:
        async with state.proxy() as data:
            data['name'] = answer
        await message.answer(text_from_file['reg']['email'], reply_markup=markup)
        await RegistrationStateGroup.next()


@dp.message_handler(state=RegistrationStateGroup.email)
async def email_and_birthdate(message: types.Message, state: FSMContext):
    global text_from_file
    answer = message.text
    if not check_email(answer):
        await message.answer(text_from_file['reg']['invalid_e'])
    else:
        markup = cancel_markup()
        async with state.proxy() as data:
            data['email'] = answer
        await message.answer(text_from_file['reg']['birthdate'], reply_markup=markup)
        await RegistrationStateGroup.next()


@dp.message_handler(state=RegistrationStateGroup.birth_date)
async def birthdate_and_finish(message: types.Message, state: FSMContext):
    answer = message.text
    if not check_date(answer):
        await message.answer(text_from_file['reg']['invalid_d'])
    else:
        async with state.proxy() as data:
            data['birthdate'] = answer
        markup = yes_no_markup()
        await message.answer(f"{text_from_file['reg']['ask']} \n\n"
                             f"{text_from_file['reg']['check_name']}: {data.get('name')} \n"
                             f"{text_from_file['reg']['check_email']}: {data.get('email')} \n"
                             f"{text_from_file['reg']['check_birth']}: {data.get('birthdate')} \n", reply_markup=markup)


@dp.callback_query_handler(text='next', state=RegistrationStateGroup.birth_date)
async def finish_registration(call: types.CallbackQuery, state: FSMContext):
    user_id = call.message.chat.id
    data = await state.get_data()
    username = data.get('name')
    email = data.get('email')
    birthdate = data.get('birthdate')
    db.add_user(user_id, username, birthdate, email)
    db.add_tickets_register(user_id)
    menu_markup = main_menu()
    await state.finish()
    await call.message.answer(text_from_file['reg']['success'], reply_markup=menu_markup)


@dp.callback_query_handler(
    text='quit',
    state=[RegistrationStateGroup.name, RegistrationStateGroup.email, RegistrationStateGroup.birth_date])
async def cancel_registration(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.answer(text_from_file['reg']['cancel'])


# main menu
# co-working flow
@dp.message_handler(text=['КАВОРКІНГ', 'CO-WORKING'])
async def coworking_room_and_registration(message: types.Message):
    if db.user_exist(message.chat.id):
        language = db.get_user_language(message.chat.id)[0]
        set_language_file(*language)
    markup = coworking_markup()
    photo = open(f'place.jpg', 'rb')
    await message.answer_photo(photo=photo, caption=text_from_file['cw']['msg'], reply_markup=markup)


@dp.callback_query_handler(text=['register', 'onemore'], state=None)
async def current_month_menu(call: types.CallbackQuery):
    user_id = call.message.chat.id
    tickets = db.get_users_tickets_this_month(user_id)[0][0]
    if tickets != 0:
        current_day, current_year, current_month = get_today()
        buttons = []
        numbs.clear()
        markup = types.InlineKeyboardMarkup(row_width=5)
        for day in filter_working_days(obj, cal, current_day, current_month, current_year):
            day = recreate_day(day)
            current_month = recreate_month(current_month)
            ymd = f"{current_year}-{current_month}-{day}"
            if db.get_amount_of_places(1) > db.get_bookings_day_count(ymd)\
                    and not db.get_user_existing_or_no_booking_thisday(user_id, ymd)\
                    and ymd not in custom_holidays:
                numbs.append(ymd)
                buttons.append(types.InlineKeyboardButton(str(day), callback_data=ymd))
        btn = types.InlineKeyboardButton(text_from_file['cw_reg']['msg_btn_next'], callback_data='next_month')
        mydate = datetime.datetime.now()
        btn_month = types.InlineKeyboardButton(text=str(mydate.strftime("%B")), callback_data='-')
        markup.row(btn_month).add(*buttons).row(btn)
        await call.message.answer(text_from_file['cw_reg']['msg'], reply_markup=markup)
        await BookingStateGroup.date_1.set()
    else:
        await call.message.answer(text_from_file['cw_reg']['no_tickets'])


@dp.callback_query_handler(text=numbs, state=[BookingStateGroup.date_1, BookingStateGroup.date_2])
async def booking_from_current_month(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['date_1'] = call.data
    markup = booking_yes_no_markup()
    await call.message.answer(f"{text_from_file['cw_reg']['msg_book']} {call.data}", reply_markup=markup)


@dp.callback_query_handler(text='reg', state=[BookingStateGroup.date_1, BookingStateGroup.date_2])
async def booking(call: types.CallbackQuery, state: FSMContext):
    user_id = call.message.chat.id
    data = await state.get_data()
    date = data.get('date_1')
    numbs.clear()
    code = get_randint()
    db.add_booking(user_id, 1, date, code)
    if user_id not in admins_id:
        reduce_tickets(date, user_id)
    markup = one_more_booking_markup()
    markup2 = main_menu()
    await state.finish()
    await call.message.answer(
        f"{text_from_file['cw_reg']['info']} \n\n"
        f"{text_from_file['cw_reg']['info1']}: {code} \n"
        f"{text_from_file['cw_reg']['info2']}\n"
        f"{text_from_file['cw_reg']['info3']}: {date}\n",
        reply_markup=markup)
    await call.message.answer(text_from_file['room']['mm'], reply_markup=markup2)


@dp.callback_query_handler(text='unreg', state=[BookingStateGroup.date_1, BookingStateGroup.date_2])
async def cancel_booking(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.answer(text_from_file['cw_reg']['unreg'])


@dp.callback_query_handler(text='next_month', state=BookingStateGroup.date_1)
async def next_month_menu(call: types.CallbackQuery):
    user_id = call.message.chat.id
    tickets = db.get_users_tickets_this_month(user_id)[0][0]
    if tickets != 0:
        user_id = call.message.chat.id
        date = datetime.date.today() + relativedelta(months=1)
        start_day = 1
        year = date.year
        month = date.month
        buttons = []
        markup = types.InlineKeyboardMarkup(row_width=5)
        for day in filter_working_days(obj, cal, start_day, month, year):
            day = recreate_day(day)
            month = recreate_month(month)
            ymd = f"{year}-{month}-{day}"
            if db.get_amount_of_places(1) > db.get_bookings_day_count(ymd) \
                    and not db.get_user_existing_or_no_booking_thisday(user_id, ymd)\
                    and ymd not in custom_holidays:
                numbs.append(ymd)
                buttons.append(types.InlineKeyboardButton(str(day), callback_data=ymd))
        btn_month = types.InlineKeyboardButton(text=str(date.strftime("%B")), callback_data='-')
        markup.row(btn_month).add(*buttons)
        await call.message.answer(text_from_file['cw_reg']['msg'], reply_markup=markup)
        await BookingStateGroup.date_2.set()
    else:
        await call.message.answer(text_from_file['cw_reg']['no_tickets'])


# community and events flow
@dp.message_handler(text=["КАМ'ЮНІЦІ І ПАДЗЕІ", 'COMMUNITY AND EVENTS'])
async def community_events(message: types.Message):
    if db.user_exist(message.chat.id):
        language = db.get_user_language(message.chat.id)[0]
        set_language_file(*language)
    markup = community_events_markup()
    await message.answer(text_from_file['commeven']['msg'], reply_markup=markup)


@dp.callback_query_handler(text='community')
async def community(call: types.CallbackQuery):
    markup = community_markup()
    await call.message.answer(text_from_file['commeven']['btn1'], reply_markup=markup)


@dp.callback_query_handler(text='events')
async def events(call: types.CallbackQuery):
    markup = events_markup()
    await call.message.answer(text_from_file['commeven']['btn2'], reply_markup=markup)


# my profile flow
@dp.message_handler(text=["МОЙ КАБІНЕТ", 'MY PROFILE'])
async def profile_menu(message: types.Message):
    if db.user_exist(message.chat.id):
        language = db.get_user_language(message.chat.id)[0]
        set_language_file(*language)
    tickets_this_month = db.get_users_tickets_this_month(message.chat.id)[0][0]
    tickets_next_month = db.get_users_tickets_next_month(message.chat.id)[0][0]
    markup = profile_markup()
    await message.answer(
        f"{text_from_file['profile']['msg']}\n\n"
        f"{text_from_file['profile']['tick_this']}: {tickets_this_month}\n\n"
        f"{text_from_file['profile']['tick_next']}: {tickets_next_month}",
        reply_markup=markup)


@dp.callback_query_handler(text='bookings')
async def bookings_and_meetings(call: types.CallbackQuery):
    booking_codes.clear()
    meeting_codes.clear()
    today = datetime.date.today()
    buttons_bookings, buttons_meetings = [], []
    markup = types.InlineKeyboardMarkup(row_width=1)
    user_id = call.message.chat.id
    bookings = db.get_users_bookings(user_id)
    meetings = db.get_users_meetings(user_id)
    for book in bookings:
        year, month, day = book[0].split('-')
        if datetime.date(int(year), int(month), int(day)) >= today:
            booking_codes.append(book[1])
            buttons_bookings.append(types.InlineKeyboardButton(
                f"{text_from_file['cw']['name']} {str(book[0])}", callback_data=str(book[1])))
    for meet in meetings:
        year, month, day = meet[0].split('-')
        if datetime.date(int(year), int(month), int(day)) >= today:
            meeting_codes.append(meet[3])
            buttons_meetings.append(types.InlineKeyboardButton(
                f"{text_from_file['room'][int(meet[2])]} [{meet[0]} {meet[1]}]", callback_data=str(meet[3])))
    markup.add(*buttons_bookings, *buttons_meetings)
    await call.message.answer(text_from_file['profile']['books'], reply_markup=markup)


@dp.callback_query_handler(text=booking_codes, state=None)
async def bookings_info(call: types.CallbackQuery, state: FSMContext):
    user_id = call.message.chat.id
    code = call.data
    date = db.get_booking_date(user_id, code)[0][0]
    async with state.proxy() as data:
        data['booking_code'] = code
    markup = delete_booking_meeting_markup()
    await DeleteAppointmentState.booking_code.set()
    await call.message.answer(
        f"{text_from_file['profile']['code_book']}: {code} \n\n"
        f"{text_from_file['profile']['date_book']}: {date}",
        reply_markup=markup
    )


@dp.callback_query_handler(text=meeting_codes, state=None)
async def meetings_info(call: types.CallbackQuery, state: FSMContext):
    user_id = call.message.chat.id
    code = call.data
    date = db.get_meetings_datetime(user_id, code)[0][0]
    time = db.get_meetings_datetime(user_id, code)[0][1]
    async with state.proxy() as data:
        data['meeting_code'] = code
    markup = delete_booking_meeting_markup()
    await DeleteAppointmentState.meeting_code.set()
    await call.message.answer(
        f"{text_from_file['profile']['code_book']}: {code} \n\n"
        f"{text_from_file['profile']['datetime_meet']}: {date} {time}",
        reply_markup=markup
    )


@dp.callback_query_handler(
    text='exit',
    state=[DeleteAppointmentState.booking_code, DeleteAppointmentState.meeting_code])
async def exit_delete_booking_meetings(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    markup = main_menu()
    await call.message.answer(text_from_file['profile']['exit_msg'], reply_markup=markup)


@dp.callback_query_handler(
    text='delete',
    state=[DeleteAppointmentState.booking_code, DeleteAppointmentState.meeting_code])
async def delete_booking_meetings(call: types.CallbackQuery, state: FSMContext):
    user_id = call.message.chat.id
    data = await state.get_data()
    booking_code = data.get('booking_code')
    meeting_code = data.get('meeting_code')
    current_month = datetime.date.today().month
    if booking_code:
        date = db.get_booking_date(user_id, booking_code)[0][0]
        booking_month = int(date.split('-')[1])
        db.delete_booking(booking_code)
        check_the_month_upgrade_tickets(current_month, booking_month, user_id)
    elif meeting_code:
        date = db.get_meetings_datetime(user_id, meeting_code)[0][0]
        meeting_month = int(date.split('-')[1])
        db.delete_meeting(meeting_code)
        check_the_month_upgrade_tickets(current_month, meeting_month, user_id)
    await state.finish()
    await call.message.answer(text_from_file['profile']['success_delete'])


# meeting room flow
@dp.message_handler(text=["ПЕРАГАВОРНЫЯ ПАКОІ", 'MEETING ROOMS'])
async def rooms(message: types.Message):
    if db.user_exist(message.chat.id):
        language = db.get_user_language(message.chat.id)[0]
        set_language_file(*language)
    markup = book_meeting_markup()
    await message.answer(text_from_file['room']['info'], reply_markup=markup)


@dp.callback_query_handler(text=['choice_room', 'onemore_meeting'], state=None)
async def choice_the_meeting_room(call: types.CallbackQuery):
    meeting_rooms.clear()
    meeting_room_numbers = db.get_meeting_rooms()
    markup_description = create_meeting_room_buttons(meeting_room_numbers)
    await call.message.answer(markup_description[1], reply_markup=markup_description[0])
    await MeetingStateGroup.room.set()


@dp.callback_query_handler(text=meeting_rooms, state=MeetingStateGroup.room)
async def this_month_meetings(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['room'] = call.data
    user_id = call.message.chat.id
    tickets = db.get_users_tickets_this_month(user_id)[0][0]
    if tickets != 0:
        current_day, current_year, current_month = get_today()
        buttons = []
        meeting_numbs.clear()
        markup = types.InlineKeyboardMarkup(row_width=5)
        for day in filter_working_days(obj, cal, current_day, current_month, current_year):
            day = recreate_day(day)
            current_month = recreate_month(current_month)
            ymd = f"{current_year}-{current_month}-{day}"
            user_meetings_amount = db.get_particular_meetings_count(ymd, user_id)[0][0]
            if db.get_meetings_count(ymd, call.data)[0][0] < 8 and ymd not in custom_holidays\
                    and user_meetings_amount < 2:
                meeting_numbs.append(ymd)
                buttons.append(types.InlineKeyboardButton(str(day), callback_data=ymd))
        btn = types.InlineKeyboardButton(text_from_file['cw_reg']['msg_btn_next'], callback_data='next_month_meetings')
        mydate = datetime.datetime.now()
        btn_month = types.InlineKeyboardButton(text=str(mydate.strftime("%B")), callback_data='-')
        markup.row(btn_month).add(*buttons).row(btn)
        await call.message.answer(text_from_file['room']['msg'], reply_markup=markup)
        await MeetingStateGroup.date_1.set()
    else:
        await call.message.answer(text_from_file['cw_reg']['no_tickets'])


@dp.callback_query_handler(text='next_month_meetings', state=MeetingStateGroup.date_1)
async def next_month_meetings(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    number_of_room = data.get('room')
    user_id = call.message.chat.id
    tickets = db.get_users_tickets_this_month(user_id)[0][0]
    if tickets != 0:
        date = datetime.date.today() + relativedelta(months=1)
        start_day = 1
        year = date.year
        month = date.month
        buttons = []
        markup = types.InlineKeyboardMarkup(row_width=5)
        for day in filter_working_days(obj, cal, start_day, month, year):
            day = recreate_day(day)
            month = recreate_month(month)
            ymd = f"{year}-{month}-{day}"
            user_meetings_amount = db.get_particular_meetings_count(ymd, user_id)[0][0]
            if db.get_meetings_count(ymd, number_of_room)[0][0] < 8 and ymd not in custom_holidays\
                    and user_meetings_amount < 2:
                meeting_numbs.append(ymd)
                buttons.append(types.InlineKeyboardButton(str(day), callback_data=ymd))
        btn_month = types.InlineKeyboardButton(text=str(date.strftime("%B")), callback_data='-')
        markup.row(btn_month).add(*buttons)
        await call.message.answer(text_from_file['cw_reg']['msg'], reply_markup=markup)
        await MeetingStateGroup.date_2.set()
    else:
        await call.message.answer(text_from_file['cw_reg']['no_tickets'])


@dp.callback_query_handler(text=meeting_numbs, state=[MeetingStateGroup.date_1, MeetingStateGroup.date_2])
async def time_for_meetings(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['date_1'] = call.data
    meeting_time.clear()
    markup = types.InlineKeyboardMarkup(row_width=1)
    buttons = []
    for gap in range(10, 18):
        time = create_time(gap)
        if db.get_meetings_room_count(time, call.data)[0][0] < 1:
            meeting_time.append(time)
            buttons.append(types.InlineKeyboardButton(time, callback_data=str(time)))
    btn_cancel = types.InlineKeyboardButton(text=text_from_file['room']['unreg'], callback_data='unreg_meetings')
    markup.add(*buttons).row(btn_cancel)
    await MeetingStateGroup.time.set()
    await call.message.answer(f"{text_from_file['cw_reg']['msg_book']} {call.data}", reply_markup=markup)


@dp.callback_query_handler(text=meeting_time, state=MeetingStateGroup.time)
async def book_particular_meeting_room(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['time'] = call.data
    data = await state.get_data()
    room = data.get('room')
    photo = open(f'{room}.jpg', 'rb')
    markup = meeting_yes_no_markup()
    await MeetingStateGroup.final_room.set()
    await call.message.answer_photo(
        photo=photo,
        caption=f"{text_from_file['room']['sure']}: \n\n"
                f"{text_from_file['room'][int(room)]} \n\n"
                f"{text_from_file['room']['date']}: {data.get('date_1')} \n"
                f"{text_from_file['room']['time']}: {data.get('time')}",
        reply_markup=markup)


@dp.callback_query_handler(text='reg_meetings', state=MeetingStateGroup.final_room)
async def book_meeting(call: types.CallbackQuery, state: FSMContext):
    user_id = call.message.chat.id
    data = await state.get_data()
    date = data.get('date_1')
    room = data.get('room')
    time = data.get('time')
    code = get_randint()
    db.add_meeting(user_id, room, date, time, code)
    if user_id not in admins_id:
        reduce_tickets(date, user_id)
    markup = one_more_meeting_markup()
    markup2 = main_menu()
    meeting_numbs.clear()
    meeting_time.clear()
    meeting_rooms.clear()
    await state.finish()
    await call.message.answer(
        f"{text_from_file['room']['done']} \n\n"
        f"{text_from_file['room']['code']}: {code} \n"
        f"{text_from_file['room'][int(room)]}\n"
        f"{text_from_file['room']['date_meet']}: {date}\n"
        f"{text_from_file['room']['time_meet']}: {time}\n",
        reply_markup=markup)
    await call.message.answer(text_from_file['room']['mm'], reply_markup=markup2)



@dp.callback_query_handler(
    text='unreg_meetings',
    state=[
        MeetingStateGroup.date_1, MeetingStateGroup.date_2,
        MeetingStateGroup.time,
        MeetingStateGroup.room
    ])
async def cancel_booking(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.answer(text_from_file['cw_reg']['unreg'])


@dp.message_handler(state="*", commands=['stopstates'])
async def unstate(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(text_from_file['restart'])


# buttons
def choose_lang_markup():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
    bel = types.KeyboardButton('Беларуская')
    eng = types.KeyboardButton('English')
    markup.add(bel, eng)
    return markup


def cancel_markup():
    markup = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[[InlineKeyboardButton(text_from_file['reg']['ask_bn'], callback_data='quit')]],
        resize_keyboard=True
    )
    return markup


def main_menu():
    menu_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
    btn_1 = types.KeyboardButton(text_from_file['menu']['btns']['cowork'])
    btn_2 = types.KeyboardButton(text_from_file['menu']['btns']['comm'])
    btn_3 = types.KeyboardButton(text_from_file['menu']['btns']['rooms'])
    btn_4 = types.KeyboardButton(text_from_file['menu']['btns']['mycab'])
    menu_markup.add(btn_1, btn_2, btn_3, btn_4)
    return menu_markup


def conditions_markup():
    markup = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [
                InlineKeyboardButton(text_from_file['start']['buttons']['rules'], text_from_file['start']['url']),
                InlineKeyboardButton(text_from_file['start']['buttons']['next'], callback_data='next'),
                InlineKeyboardButton(text_from_file['start']['buttons']['cancel'], callback_data='cancel'),
            ]
        ], resize_keyboard=True)
    return markup


def coworking_markup():
    markup = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[[InlineKeyboardButton(text_from_file['cw']['btn'], callback_data='register')]],
        resize_keyboard=True
    )
    return markup


def community_events_markup():
    markup = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [InlineKeyboardButton(
                text_from_file['commeven']['btn1'],
                callback_data='community'
            )],
            [InlineKeyboardButton(
                text_from_file['commeven']['btn2'],
                callback_data='events'
            )]
        ],
        resize_keyboard=True
    )
    return markup


def community_markup():
    markup = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [InlineKeyboardButton(
                text_from_file['commeven']['community1'],
                url=text_from_file['commeven']['link1']
            )],
            [InlineKeyboardButton(
                text_from_file['commeven']['community2'],
                url=text_from_file['commeven']['link2']
            )]
        ],
        resize_keyboard=True
    )
    return markup


def yes_no_markup():
    markup = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [InlineKeyboardButton(text_from_file['reg']['ask_by'], callback_data='next'),
             InlineKeyboardButton(text_from_file['reg']['ask_bn'], callback_data='quit')]
        ],
        resize_keyboard=True
    )
    return markup


def booking_yes_no_markup():
    markup = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [InlineKeyboardButton(text_from_file['cw_reg']['btn_reg'], callback_data='reg'),
             InlineKeyboardButton(text_from_file['cw_reg']['btn_unreg'], callback_data='unreg')]
        ],
        resize_keyboard=True
    )
    return markup


def one_more_booking_markup():
    markup = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[[InlineKeyboardButton(text_from_file['cw_reg']['onemore'], callback_data='onemore')]],
        resize_keyboard=True
    )
    return markup


def profile_markup():
    markup = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [InlineKeyboardButton(
                text_from_file['profile']['btn1'],
                callback_data='bookings'
            )],
            [InlineKeyboardButton(
                text_from_file['profile']['btn2'],
                url=text_from_file['commeven']['link1']
            )],
            [InlineKeyboardButton(
                text_from_file['profile']['btn3'],
                url=text_from_file['profile']['manager']
            )]
        ],
        resize_keyboard=True
    )
    return markup


def meeting_yes_no_markup():
    markup = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [InlineKeyboardButton(text_from_file['room']['reg'], callback_data='reg_meetings'),
             InlineKeyboardButton(text_from_file['room']['unreg'], callback_data='unreg_meetings')]
        ],
        resize_keyboard=True
    )
    return markup


def one_more_meeting_markup():
    markup = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[[InlineKeyboardButton(text_from_file['room']['onemore'], callback_data='onemore_meeting')]],
        resize_keyboard=True
    )
    return markup


def book_meeting_markup():
    markup = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[[InlineKeyboardButton(text_from_file['room']['btn'], callback_data='choice_room')]],
        resize_keyboard=True
    )
    return markup


def delete_booking_meeting_markup():
    markup = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [InlineKeyboardButton(text_from_file['profile']['delete'], callback_data='delete')],
            [InlineKeyboardButton(text_from_file['profile']['exit'], callback_data='exit')]
        ],
        resize_keyboard=True
    )
    return markup


def events_markup():
    markup = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [InlineKeyboardButton(
                text_from_file['commeven']['checkevents'],
                url=text_from_file['commeven']['evenlink1']
            )],
            [InlineKeyboardButton(
                text_from_file['commeven']['createevents'],
                url=text_from_file['commeven']['evenlink2']
            )]
        ],
        resize_keyboard=True
    )
    return markup


# logic part for meeting rooms
def get_room_name(number):
    if number == 1:
        return text_from_file['room']['bibl']
    elif number == 2:
        return text_from_file['room']['wind']


def create_meeting_room_buttons(room_numbers):
    buttons = []
    description = ''
    markup = types.InlineKeyboardMarkup(row_width=1)
    for number in room_numbers:
        button_text = create_name_of_meet_room(
            text_from_file['room']['meet_room'],
            get_room_name(number[0])
        )
        buttons.append(types.InlineKeyboardButton(button_text, callback_data=str(number[0])))
        description += text_from_file['room'][number[0]] + '\n'
        meeting_rooms.append(number[0])
    markup.add(*buttons)
    return markup, description, meeting_rooms


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
