import calendar
import datetime
import schedule
import time

from create_bot import db

print(calendar.monthrange(datetime.date.today().year, datetime.date.today().month))


def renew_tickets():
    if int(datetime.date.today().day) == 1:
        for user in db.get_users()[0]:
            db.renew_users_tickets(user)
        print('Done')


schedule.every().day.at("00:00").do(renew_tickets)


while 1:
    schedule.run_pending()
    time.sleep(1)
