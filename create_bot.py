from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

storage = MemoryStorage()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)

bot_address = os.getenv('BOT_NAME')

master_id = os.getenv('OWNER_NAME')

client_commands = ['/start', '/help', 'Преподаватели', 'Тренировки', 'Режим работы',\
                   'Контакты', '/moderate', '/buy']
