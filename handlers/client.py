import html
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from create_bot import bot, bot_address, dp
from keyboards import kb_client, kb_start
from school_database import sqlite_db
from handlers.payment import payment_handler, successful_payment
from school_database.sqlite_db import get_support


# Handler for /start and /help
async def start_bot(message: types.Message):
    user_id = message.from_user.id
    print("user id is", user_id)
    sqlite_db.save_new_user(message.from_user)
    if not sqlite_db.get_user_payment_status(user_id):      #если пользователь уже является клиентом
        try:
            await bot.send_message(message.chat.id,
                                   f'Привет! Я бот-помощник закрытого канала по английскому языку!\n'
                                   f'Ты сделал первый шаг к новым знаниям, развитию и позитивным переменам!\n\n'
                                   f'Тут можно оформить подписку для вступления в наш клуб и отменить ее. Жми нужную кнопку и будет доступен следующий шаг',
                                   reply_markup=kb_start)
            await message.delete()
            return
        except Exception as e:
            await message.reply(f'Пожалуйста напишите боту в ЛС1: {bot_address}\n\nОшибка: {str(e)}')

    try:                                   #если пользователь только собирается оплатить курс
        await bot.send_message(message.chat.id,
                               f'Добро пожаловать обратно! Вы уже оплатили подписку.\n\n'
                               f'Пожалуйста воспользуйтесь клавиатурой, чтобы узнать больше о нашем центре.',
                               reply_markup=kb_client)
        await message.delete()
    except Exception as e:
        await message.reply(f'Пожалуйста напишите боту в ЛС2: {bot_address}\n\nОшибка: {str(e)}')

@dp.callback_query_handler(lambda c: c.data.startswith('client_start_'))
async def handle_payment(cb: types.CallbackQuery):
    param = cb.data.split('_')[-1]
    user_id = cb.message.from_user.id
    message = cb.message
    if param == 'payment':
        await message.answer(f'💳 Подписка на 1 месяц — 8000 тг \n'
                       f'Можете оплатить по ссылке внизу👇\n'
                       f'После оплаты обязательно отправьте чек об оплате, чтобы мы активировали доступ.')
        await payment_handler(message) #оформить подписку и изменить статус подписки в бд

    if param == 'info':
        await message.answer('Вот что тебя ждёт:\n\n'
                             f'📌 Ежемесячные видеокурсы\n'
                             f'Каждый месяц тебя ждёт новый курс — смотри, учись и применяй на практике!\n'
                             f'💡 Ежедневная польза\n'
                             f'Советы, задания, мотивация и фишки, которые помогут расти каждый день.\n\n'
                             f'🎙 Живые эфиры каждую неделю\n'
                             f'Общаемся, обсуждаем важное, отвечаем на твои вопросы в прямом эфире!\n\n'
                             f'🤝 Поддержка от кураторов\n'
                             f'Наши кураторы всегда на связи:\n'
                             f'✅ Ответят на вопросы\n'
                             f'✅ Помогут с заданиями\n'
                             f'✅ Организуют челленджи, чтобы тебе было интересно и ты не бросал начатое!\n\n'
                             f'💳 Подписка на 1 месяц — 8000 тг\n'
                             f'Можете оплатить нажав на кнопку "Оформить подписку" внизу👇\n'
                             f'После оплаты обязательно отправьте чек об оплате, чтобы мы активировали доступ.',
                             reply_markup=kb_start)
        await message.delete()
    if param == 'support':
        await message.answer('Если у вас еще остались вопросы то можете написать по следующему телеграм хэнлу\n'
                             'Sandugash - @Sakokas',
                             reply_markup=kb_start)


async def get_main_channel(message: types.Message):
    if not sqlite_db.get_user_payment_status(message.from_user.id):
        await message.answer('К сожалению эта команда доступна только для подписчиков курса',
                       reply_markup=kb_start)
        await message.delete()
        return

    text = (
        'Вот наш основной канал с навигатором и с ежедневными новостями:\n'
    )

    await bot.send_message(
        message.chat.id,
        text,
        reply_markup= InlineKeyboardMarkup(row_width = 2).add(InlineKeyboardButton(text= "Ссылка на канал!!", url="https://t.me/+5_06M-kpB-ozMDRi")),
        parse_mode=types.ParseMode.HTML
    )


async def get_courses(message: types.Message):
    if not sqlite_db.get_user_payment_status(message.from_user.id):
        await message.answer('К сожалению эта команда доступна только для подписчиков курса',
                       reply_markup=kb_start)
        await message.delete()
        return

    courses = sqlite_db.load_courses_text()
    if not courses:
        await bot.send_message(message.chat.id, "Пока нет ни одного сохранённого курса.")
        return

    # 1) build the text body
    lines = ["<b>Список курсов:</b>"]
    for c in courses:
        name = html.escape(c['name'])
        desc = html.escape(c['description'])
        lines.append(f"\n<b>{name}</b>\n{desc}")
    text = "\n".join(lines)

    # 2) build the inline keyboard
    kb = types.InlineKeyboardMarkup(row_width=1)
    for c in courses:
        name = html.escape(c['name'])
        url  = c['url']
        kb.add(types.InlineKeyboardButton(
            text=f"Перейти к «{name}»",
            url=url
        ))

    # 3) send!
    await bot.send_message(
        chat_id=message.chat.id,
        text=text,
        parse_mode=types.ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=kb
    )


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
async def get_support(message: types.Message):
    if not sqlite_db.get_user_payment_status(message.from_user.id):
        await message.answer('К сожалению эта команда доступна только для подписчиков курса',
                       reply_markup=kb_start)
        await message.delete()
        return
    await sqlite_db.sql_read_from_teachers(message)

# Handler for random message
async def random_message(message: types.Message):
    if not sqlite_db.get_user_payment_status(message.from_user.id):
        await start_bot(message)
    else:
        await bot.send_message(message.chat.id,
            f'Добро пожаловать обратно! Вы уже оплатили подписку.\n\n'
            f'Пожалуйста воспользуйтесь клавиатурой, чтобы узнать больше о нашем центре.',
            reply_markup=kb_client)

# Register handlers
def handlers_register(dp: Dispatcher):
    print('✅ Регистрируем хендлеры клиента')
    dp.register_message_handler(start_bot, commands=['start', 'help'])
    dp.register_message_handler(get_main_channel, Text(equals='Основной Канал', ignore_case=True))
    dp.register_message_handler(get_courses, Text(equals='Курсы', ignore_case=True))
    dp.register_message_handler(get_contacts, Text(equals='Контакты', ignore_case=True))
    dp.register_message_handler(get_work_hours, Text(equals='Режим работы', ignore_case=True))
    dp.register_message_handler(get_support, Text(equals='Служба поддержки', ignore_case=True))
    dp.register_message_handler(random_message)
