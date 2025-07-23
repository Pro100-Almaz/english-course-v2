import os
from aiogram.utils import executor
from create_bot import dp
from handlers import client, manage, common, payment
from school_database import sqlite_db
from aiogram import types

async def on_startup(_):
    print('🚀 Бот запущен и подключен к Telegram')
    sqlite_db.bot_tables_sql()

def on_shutdown(_):
    print('Бот сдох')

print("📦 Регистрируем manage")
manage.handlers_register_manage(dp)

print("📦 Регистрируем payment")
payment.handlers_register(dp)

print("📦 Регистрируем client")
client.handlers_register(dp)

print("📦 Регистрируем common")
common.register_common_handlers(dp)

print("⚙️ Запускаем executor...")
executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
