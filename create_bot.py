from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from db import DataBase

bot = Bot(token='5577372088:AAF2LE-_ThgGP7se8W28OD99hE-K14TH0BE')
dp = Dispatcher(bot, storage=MemoryStorage())
db = DataBase('database.db')

admins_id = [
    655796453
]
