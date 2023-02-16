import datetime
import schedule
import time


from create_bot import db


def renew_tickets():
    if int(datetime.date.today().day) == 1:
        for user in db.get_users():
            db.renew_users_tickets(user[0])
    print('Tickets were updated successfully')


schedule.every().day.at("00:00").do(renew_tickets)


while 1:
    schedule.run_pending()
    time.sleep(1)
