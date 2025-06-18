import os
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from aiogram.types.message import ContentType
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot, client_commands
from school_database import sqlite_db as db

logging.basicConfig(
    level=logging.INFO
)

PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")  # from BotFather
CURRENCY       = "KZT"                        # or "USD", "EUR", etc.

PRICE = types.LabeledPrice(label="Подписка на 1 месяц", amount=1000*100)  # в копейках (руб)

class PaymentState(StatesGroup):
    awaiting_payment = State()

# 1) /buy command: send the invoice

async def payment_handler(message: types.Message):
    if PROVIDER_TOKEN.split(':')[1] == 'TEST':
        await bot.send_message(message.chat.id, "Тестовый платеж!!!")

    await bot.send_invoice(message.chat.id,
                           title="Подписка на бота",
                           description="Активация подписки на бота на 1 месяц",
                           provider_token=PROVIDER_TOKEN,
                           currency= CURRENCY,
                           photo_url="https://www.aroged.com/wp-content/uploads/2022/06/Telegram-has-a-premium-subscription.jpg",
                           photo_width=416,
                           photo_height=234,
                           photo_size=416,
                           is_flexible=False,
                           prices=[PRICE],
                           start_parameter="one-month-subscription",
                           payload="test-invoice-payload")

# pre checkout  (must be answered in 10 seconds)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


# successful payment
async def successful_payment(message: types.Message):
    print("SUCCESSFUL PAYMENT:")
    db.update_record_payment(int(message.from_user.id))
    payment_info = message.successful_payment.dict()
    for k, v in payment_info.items():
        print(f"{k} = {v}")
    await bot.send_message(message.chat.id,
                           f"Платеж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} прошел успешно!!!")

#refunded payment
async def refund_payment(message: types.Message):
    print ("REFUND PAYMENT:")
    payment_info = message.refund_payment.dict()
    for k, v in payment_info.items():
        print(f"{k} = {v}")

    await bot.send_message(message.chat.id,
                           f"Платеж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} возвращен!!!")


def handlers_register(dp: Dispatcher):
    print('✅ Регистрируем хендлеры клиента, оплата')
    dp.register_message_handler(payment_handler, commands=['buy'])
    dp.register_pre_checkout_query_handler(pre_checkout_query, lambda query: True)
    dp.register_message_handler(successful_payment, lambda message: message.successful_payment is not None)