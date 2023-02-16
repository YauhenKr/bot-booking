import calendar

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from workalendar.europe import Lithuania

from db import DataBase

bot = Bot(token='5577372088:AAECVVpilXmGyNI3t3lp23EoJQT1OyBTDgM')
dp = Dispatcher(bot, storage=MemoryStorage())
db = DataBase('database.db')

admins_id = [
    655796453
]

cal = Lithuania()
obj = calendar.Calendar()
