from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

but1 = KeyboardButton('Основной канал')
but2 = KeyboardButton('Контакты')
but3 = KeyboardButton('Режим работы')
but4 = KeyboardButton('Курсы')
but5 = KeyboardButton('Служба поддержки')

kb_client = ReplyKeyboardMarkup(resize_keyboard=True)
kb_client.add(but1).add(but2).insert(but3).add(but4).insert(but5)

kb_start = InlineKeyboardMarkup(row_width = 1).add(
    InlineKeyboardButton("Оформить подписку", callback_data='client_start_payment'),
    InlineKeyboardButton("Подробнее про закрытый канал", callback_data='client_start_info'),
    InlineKeyboardButton("Связаться", callback_data='client_start_support')
)