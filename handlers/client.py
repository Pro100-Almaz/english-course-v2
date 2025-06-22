from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from create_bot import bot, bot_address
from keyboards import kb_client
from school_database import sqlite_db
from handlers.payment import payment_handler


# Handler for /start and /help
async def start_bot(message: types.Message):
    user_id = message.from_user.id
    print("user id is", user_id)

    sqlite_db.save_new_user(message.from_user)
    if not sqlite_db.record_payment(user_id):
        try:
            await bot.send_message(message.chat.id, 
                                   f'Привет, Это бот English Course. Практики подходят людям любого уровня подготовки.\n\n'
                                   f'Для доступа к материалам необходимо оплатить подписку.\n\n',
                                   reply_markup=None)
            await payment_handler(message)
            await message.delete()
        except Exception as e:
            await message.reply(f'Пожалуйста напишите боту в ЛС: {bot_address}\n\nОшибка: {str(e)}')
        return
    try:
        await bot.send_message(message.chat.id, 
                               f'Добро пожаловать обратно! Вы уже оплатили подписку.\n\n'
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


async def random_message(message: types.Message):
    if sqlite_db.get_user_by_id(message.from_user.id):
        await bot.send_message(message.chat.id,
                               f'Добро пожаловать обратно! Вы уже оплатили подписку.\n\n'
                               f'Пожалуйста воспользуйтесь клавиатурой, чтобы узнать больше о нашем центре.',
                               reply_markup=kb_client)
    else:
        await bot.send_message(message.chat.id,
                               f'Привет, Это бот English Course. Вижу что ты не заплатил за курс, если хочешь к нам '
                               f'просто оплати подписку и учись с наслаждением.\n\n',
                               reply_markup=None)


# Register handlers
def handlers_register(dp: Dispatcher):
    print('✅ Регистрируем хендлеры клиента')
    dp.register_message_handler(start_bot, commands=['start', 'help'])
    dp.register_message_handler(get_contacts, Text(equals='Контакты', ignore_case=True))
    dp.register_message_handler(get_work_hours, Text(equals='Режим работы', ignore_case=True))
    dp.register_message_handler(get_training_courses, Text(equals='Тренировки', ignore_case=True))
    dp.register_message_handler(get_trainers_info, Text(equals='Преподаватели', ignore_case=True))
