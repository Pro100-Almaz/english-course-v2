from aiogram.utils import executor
from create_bot import dp
from handlers import client, manage, common
from school_database import sqlite_db

async def on_startup(_):
    print('🚀 Бот запущен и подключен к Telegram')
    sqlite_db.bot_tables_sql()


client.handlers_register(dp)
manage.handlers_register_manage(dp)
common.register_common_handlers(dp)


executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
