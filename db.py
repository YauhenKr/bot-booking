import sqlite3


class DataBase:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def user_exist(self, user_id):
        with self.connection:
            result = self.cursor.execute(
                '''SELECT * FROM users WHERE user_id = ?''',
                (user_id, )
            ).fetchmany(1)
            return bool(len(result))

    def add_user(self, user_id, username, birthdate, email):
        with self.connection:
            return self.cursor.execute(
                '''INSERT OR IGNORE INTO users (user_id, username, birthdate, email) VALUES (?,?,?,?)''',
                (user_id, username, birthdate, email)
            )

    def add_users_lang(self, user_id, lang):
        with self.connection:
            return self.cursor.execute(
                '''INSERT OR IGNORE INTO users_language (user_id, language) VALUES (?,?)''',
                (user_id, lang)
            )

    def users_lang_exist(self, user_id):
        with self.connection:
            result = self.cursor.execute(
                '''SELECT * FROM 'users_language' WHERE 'user_id' = ?''',
                (user_id, )
            ).fetchmany(1)
            return bool(len(result))

    def get_user_language(self, user_id):
        with self.connection:
            return self.cursor.execute(
                '''SELECT language FROM users_language WHERE user_id = (?) ''',
                (user_id, )
            ).fetchmany(1)

    def add_booking(self, user_id, room, date, qrcode):
        with self.connection:
            return self.cursor.execute(
                '''INSERT OR IGNORE INTO users_bookings (user_id, room, booking_date, qrcode) VALUES (?,?,?,?)''',
                (user_id, room, date, qrcode)
            )

    def get_bookings_codes(self, date):
        with self.connection:
            return self.cursor.execute(
                '''SELECT qrcode FROM users_bookings WHERE booking_date = (?) ''',
                (date,)
            ).fetchall()

    def get_meetings_codes(self, date):
        with self.connection:
            return self.cursor.execute(
                '''SELECT code FROM users_meetings WHERE booking_date = (?) ''',
                (date,)
            ).fetchall()

    def get_amount_of_places(self, room):
        with self.connection:
            return self.cursor.execute(
                '''SELECT workplaces FROM rooms WHERE number = (?) ''',
                (room, )
            ).fetchmany(1)

    def get_bookings_day_count(self, date):
        with self.connection:
            return self.cursor.execute(
                '''SELECT COUNT(booking_date) FROM users_bookings WHERE booking_date = (?) ''',
                (date, )
            ).fetchmany(1)

    def get_users_tickets_this_month(self, user_id):
        with self.connection:
            return self.cursor.execute(
                '''SELECT this_month_tickets FROM users_tickets WHERE user_id = (?) ''',
                (user_id, )
            ).fetchmany(1)

    def get_users_tickets_next_month(self, user_id):
        with self.connection:
            return self.cursor.execute(
                '''SELECT next_month_tickets FROM users_tickets WHERE user_id = (?) ''',
                (user_id, )
            ).fetchmany(1)

    def get_user_existing_or_no_booking_thisday(self, user_id, date):
        with self.connection:
            result = self.cursor.execute(
                '''SELECT booking_date FROM users_bookings WHERE user_id = (?) AND booking_date = (?)''',
                (user_id, date)
            ).fetchmany(1)
            return bool(len(result))

    def reduce_users_tickets_this_month(self, user_id):
        with self.connection:
            return self.cursor.execute(
                '''UPDATE users_tickets SET this_month_tickets = (this_month_tickets - 1) WHERE user_id = (?)''',
                (user_id, )
            )

    def reduce_users_tickets_next_month(self, user_id):
        with self.connection:
            return self.cursor.execute(
                '''UPDATE users_tickets SET next_month_tickets = (next_month_tickets - 1) WHERE user_id = (?)''',
                (user_id, )
            )

    def add_tickets_register(self, user_id):
        with self.connection:
            return self.cursor.execute(
                '''INSERT OR IGNORE INTO users_tickets (user_id, this_month_tickets, next_month_tickets)
                VALUES (?, 22, 22)''',
                (user_id, )
            )

    def renew_users_tickets(self, user_id):
        with self.connection:
            return self.cursor.execute(
                '''UPDATE users_tickets SET this_month_tickets = next_month_tickets, 
                next_month_tickets = 22 WHERE user_id = (?)''',
                (user_id, )
            )

    def get_users(self):
        with self.connection:
            return self.cursor.execute(
                '''SELECT user_id FROM users_tickets''',
            ).fetchall()

    def get_meetings_count(self, date, number):
        with self.connection:
            return self.cursor.execute(
                '''SELECT COUNT(meeting_time) FROM users_meetings WHERE booking_date = (?) AND room = (?) ''',
                (date, number)
            ).fetchmany(1)

    def get_meetings_room_count(self, time, date):
        with self.connection:
            return self.cursor.execute(
                '''SELECT COUNT(meeting_time) FROM users_meetings WHERE meeting_time = (?) AND booking_date = (?) ''',
                (time, date)
            ).fetchmany(1)

    def get_booked_room_this_meeting(self, time, date):
        with self.connection:
            return self.cursor.execute(
                '''SELECT room FROM users_meetings WHERE meeting_time = (?) AND booking_date = (?) ''',
                (time, date)
            ).fetchall()

    def get_spare_room_this_meeting(self, room):
        with self.connection:
            if not room:
                room = (0, )
            return self.cursor.execute(
                '''SELECT number FROM meeting_rooms WHERE number NOT IN (?)''',
                (room, )
            ).fetchall()

    def get_meeting_rooms(self):
        with self.connection:
            return self.cursor.execute(
                '''SELECT number FROM meeting_rooms''',
            ).fetchall()

    def add_meeting(self, user_id, room, date, time, code):
        with self.connection:
            return self.cursor.execute(
                '''INSERT OR IGNORE
                INTO users_meetings (user_id, room, booking_date, meeting_time, code) VALUES (?,?,?,?,?)''',
                (user_id, room, date, time, code)
            )

    def get_users_bookings(self, user_id):
        with self.connection:
            return self.cursor.execute(
                '''SELECT booking_date, qrcode FROM users_bookings 
                WHERE user_id = (?) ORDER BY date(booking_date) ASC''',
                (user_id, )
            ).fetchall()

    def get_users_meetings(self, user_id):
        with self.connection:
            return self.cursor.execute(
                '''SELECT booking_date, meeting_time, room, code FROM users_meetings
                WHERE user_id = (?) ORDER BY date(booking_date) ASC''',
                (user_id, )
            ).fetchall()

    def get_booking_date(self, user_id, code):
        with self.connection:
            return self.cursor.execute(
                '''SELECT booking_date FROM users_bookings 
                WHERE user_id = (?) AND qrcode = (?)''',
                (user_id, code)
            ).fetchall()

    def get_meetings_datetime(self, user_id, code):
        with self.connection:
            return self.cursor.execute(
                '''SELECT booking_date, meeting_time, room FROM users_meetings
                WHERE user_id = (?) AND code = (?)''',
                (user_id, code)
            ).fetchall()

    def delete_booking(self, code):
        with self.connection:
            return self.cursor.execute(
                '''DELETE FROM users_bookings WHERE qrcode = (?)''',
                (code, )
            )

    def delete_meeting(self, code):
        with self.connection:
            return self.cursor.execute(
                '''DELETE FROM users_meetings WHERE code = (?)''',
                (code, )
            )

    def update_plusone_ticket_this_month(self, user_id):
        with self.connection:
            return self.cursor.execute(
                '''UPDATE users_tickets SET this_month_tickets = this_month_tickets + 1 WHERE user_id = (?)''',
                (user_id, )
            )

    def update_plusone_ticket_next_month(self, user_id):
        with self.connection:
            return self.cursor.execute(
                '''UPDATE users_tickets SET next_month_tickets = next_month_tickets + 1 WHERE user_id = (?)''',
                (user_id, )
            )

    def add_custom_holidays(self, date):
        with self.connection:
            return self.cursor.execute(
                '''INSERT OR IGNORE INTO custom_holidays (date) VALUES (?)''',
                (date, )
            )

    def get_custom_holidays(self):
        with self.connection:
            return self.cursor.execute(
                '''SELECT date FROM custom_holidays'''
            ).fetchall()

    def set_active(self, user_id, active):
        with self.connection:
            return self.cursor.execute(
                '''UPDATE users SET active = ? WHERE user_id = ?''',
                (active, user_id, )
            )

    def get_users_mailing(self):
        with self.connection:
            return self.cursor.execute('''SELECT user_id, active FROM users ''').fetchall()

    def select_all_from_bookings(self, code):
        with self.connection:
            return self.cursor.execute(
                '''SELECT * FROM users_bookings WHERE qrcode = (?)''',
                (code, )
            ).fetchall()

    def select_all_from_meetings(self, code):
        with self.connection:
            return self.cursor.execute(
                '''SELECT users_meetings.booking_date, users_meetings.meeting_time, meeting_rooms.name 
                    FROM users_meetings
                    INNER JOIN meeting_rooms
                    ON users_meetings.room = meeting_rooms.id
                    WHERE users_meetings.code = (?)''',
                (code, )
            ).fetchall()

    def get_particular_meetings_count(self, date, user_id):
        with self.connection:
            return self.cursor.execute(
                '''SELECT COUNT(meeting_time) FROM users_meetings WHERE booking_date = (?) AND user_id = (?) ''',
                (date, user_id)
            ).fetchmany(1)

    def delete_user(self, code):
        with self.connection:
            return self.cursor.execute(
                '''DELETE FROM users WHERE user_id = ?''',
                (code, )
            )
