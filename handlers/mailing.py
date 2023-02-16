from asyncio import sleep

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from create_bot import db, admins_id, dp
from states import BotMailing


async def start_mailing(message: types.Message):
    await message.answer(f'Увядзіце тэкст рассылкі')
    await BotMailing.text.set()


async def mailing_text(message: types.Message, state: FSMContext):
    answer = message.text
    markup = InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Дадаць фатаздымак', callback_data='add_photo'),
                InlineKeyboardButton(text='Апулікаваць', callback_data='next'),
                InlineKeyboardButton(text='Скасаваць', callback_data='quit')
            ]
        ]
    )
    await state.update_data(text=answer)
    await message.answer(text=answer, reply_markup=markup)
    await BotMailing.state.set()


@dp.callback_query_handler(text='next', state=BotMailing.state, chat_id=admins_id)
async def start(call: CallbackQuery, state: FSMContext):
    from create_bot import dp, bot
    users = db.get_users_mailing()
    data = await state.get_data()
    text = data.get('text')
    await state.finish()
    for user in users:
        try:
            await dp.bot.send_message(chat_id=user[0], text=text)
            if int(user[1]) != 1:
                db.set_active(user[0], 1)
        except:
            db.set_active(user[0], 0)

        await sleep(0.3)
    await call.message.answer('Рассылка зроблена')


@dp.callback_query_handler(text='add_photo', state=BotMailing.state, chat_id=admins_id)
async def add_photo(call: CallbackQuery):
    await call.message.answer('Дашліце фота')
    await BotMailing.photo.set()


async def check_mailing_text(message: types.Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo=photo_file_id)
    data = await state.get_data()
    text = data.get('text')
    photo = data.get('photo')
    markup = InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Апублікаваць', callback_data='next'),
                InlineKeyboardButton(text='Скасаваць', callback_data='quit')
            ]
        ]
    )
    await message.answer_photo(photo=photo, caption=text, reply_markup=markup)


@dp.callback_query_handler(text='next', state=BotMailing.photo, chat_id=admins_id)
async def send_photo_text(call: types.CallbackQuery, state: FSMContext):
    from create_bot import dp
    users = db.get_users()
    data = await state.get_data()
    text = data.get('text')
    photo = data.get('photo')
    await state.finish()
    for user in users:
        try:
            await dp.bot.send_photo(chat_id=user[0], photo=photo, caption=text)
            await sleep(0.3)
        except Exception:
            pass
    await call.message.answer('Рассылка зроблена')


async def no_photo(message: types.Message):
    markup = InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[[InlineKeyboardButton(text='Скасаваць', callback_data='quit')]]
    )
    await message.answer('Дашлі мне фатаздымак', reply_markup=markup)


@dp.callback_query_handler(
    text='quit',
    state=[BotMailing.photo, BotMailing.text, BotMailing.state],
    chat_id=admins_id
)
async def quit_mailing(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.answer('Рассылка скасавана')


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(start_mailing, commands=['mailing'], chat_id=admins_id)
    dp.register_message_handler(mailing_text, state=BotMailing.text, chat_id=admins_id)
    dp.register_message_handler(start, state=BotMailing.state, chat_id=admins_id)
    dp.register_message_handler(add_photo, state=BotMailing.state, chat_id=admins_id)
    dp.register_message_handler(
        check_mailing_text,
        state=BotMailing.photo,
        content_types=types.ContentType.PHOTO,
        chat_id=admins_id
    )
    dp.register_message_handler(send_photo_text, state=BotMailing.photo, chat_id=admins_id)
    dp.register_message_handler(no_photo, state=BotMailing.photo, chat_id=admins_id)
    dp.register_message_handler(
        quit_mailing,
        state=[BotMailing.photo, BotMailing.text, BotMailing.state],
        chat_id=admins_id)
