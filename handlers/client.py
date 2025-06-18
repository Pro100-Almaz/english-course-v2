from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from create_bot import bot, bot_address
from keyboards import kb_client
from school_database import sqlite_db


# Handler for /start and /help
async def start_bot(message: types.Message):
    try:
        await bot.send_message(message.chat.id, 
                               f'Привет, Это бот English Course. Практики подходят людям любого уровня подготовки.\n\n'
                               f'Пожалуйста воспользуйтесь клавиатурой, чтобы узнать больше о нашем центре.',
                               reply_markup=kb_client)
        await message.delete()
    except Exception as e:
        await message.reply(f'Пожалуйста напишите боту в ЛС: {bot_address}\n\nОшибка: {str(e)}')

# Handler for "Контакты"
async def get_contacts(message: types.Message):
    address = "English's Street, 00/00"
    phones = '+000 000-00-00'
    await bot.send_message(message.chat.id, f'Адрес школы: {address} \nКонтактные номера: {phones}')

# Handler for "Режим работы"
async def get_work_hours(message: types.Message):
    w_days = 'пн-вс'
    w_hours = '06.30–22.30'
    await bot.send_message(message.chat.id, f'Время работы: {w_days} {w_hours}')

# Handler for "Тренировки"
async def get_training_courses(message: types.Message):
    await sqlite_db.sql_read_from_courses(message)

# Handler for "Преподаватели"
async def get_trainers_info(message: types.Message):
    await sqlite_db.sql_read_from_teachers(message)

# Register handlers
def handlers_register(dp: Dispatcher):
    print('✅ Регистрируем хендлеры клиента')
    dp.register_message_handler(start_bot, commands=['start', 'help'])
    dp.register_message_handler(get_contacts, Text(equals='Контакты', ignore_case=True))
    dp.register_message_handler(get_work_hours, Text(equals='Режим работы', ignore_case=True))
    dp.register_message_handler(get_training_courses, Text(equals='Тренировки', ignore_case=True))
    dp.register_message_handler(get_trainers_info, Text(equals='Преподаватели', ignore_case=True))
