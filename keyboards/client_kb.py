from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

but1 = KeyboardButton('Основной канал')
but2 = KeyboardButton('Контакты')
but3 = KeyboardButton('Режим работы')
but4 = KeyboardButton('Курсы')
but5 = KeyboardButton('Служба поддержки')

kb_client = ReplyKeyboardMarkup(resize_keyboard=True)
kb_client.add(but1).add(but2).insert(but3).add(but4).insert(but5)