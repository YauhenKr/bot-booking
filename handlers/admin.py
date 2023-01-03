from aiogram import types, Dispatcher

from create_bot import db, admins_id
from services import get_today


async def get_qrcodes(message: types.Message):
    day, year, month = get_today()
    ymd = f"{year}-{month}-{day}"
    await message.answer(db.get_today_bookings_codes(ymd))


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(get_qrcodes, commands=['codes'], chat_id=admins_id)
