import datetime
import random
import re

from create_bot import db

numbs = []
meeting_numbs = []
meeting_time = []
meeting_rooms = []
booking_codes = []
meeting_codes = []


def check_birthdate(date):
    reg = '^(((0[1-9]|[12][0-9]|30)[.](0[13-9]|1[012])|31[.](0[13578]|1[02])|(0[1-9]|1[0-9]|2[0-8])[.]02)[.][0-9]{4}|29[.]02[.]([0-9]{2}(([2468][048]|[02468][48])|[13579][26])|([13579][26]|[02468][048]|0[0-9]|1[0-6])00))$'
    return re.match(reg, date)


def check_email(email):
    reg = '^(?:[a-z0-9!#$%&\'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&\'*+\/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])$'
    return re.match(reg, email.lower())


def filter_working_days(obj, cal, day, month, year):
    return filter(
        lambda x: x >= day and cal.is_working_day(datetime.date(year, month, x)),
        obj.itermonthdays(year, month)
    )


def get_randint():
    return random.randint(10000, 100000000)


def get_today():
    day = datetime.date.today().day
    year = datetime.date.today().year
    month = datetime.date.today().month
    return day, year, month


def check_user_exist(user_id):
    from bot import set_language_file

    if db.user_exist(user_id):
        language = db.get_user_language(user_id)[0]
        set_language_file(*language)


def create_time(number):
    return f"{number}:00 - {number + 1}:00"


def create_name_of_meet_room(text, number):
    return f"{text} {number}"


def reduce_tickets(date, user_id):
    if str(datetime.date.today().month) == date.split('-')[1]:
        db.reduce_users_tickets_this_month(user_id)
    else:
        db.reduce_users_tickets_next_month(user_id)


def format_meeting_data(data):
    date, time, room = data
