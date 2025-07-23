import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from aiogram.types.message import ContentType
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import bot
from school_database import sqlite_db as db
from handlers.tiptop import start_tiptop

logging.basicConfig(
    level=logging.INFO
)

async def cancel_handler(user_id: int):
    return db.update_user_payment_status(user_id, False)

# 1) /buy command: send the invoice
async def payment_handler(message: types.Message, user_id):
    await start_tiptop(message)

# successful payment
async def successful_payment(message: types.Message, user_id: int):
    try:
        # logging.info(f"SUCCESSFUL PAYMENT for user {user_id}")
        
        payment_info = message.successful_payment
        # logging.info(f"Payment details: {payment_info}")
        
        success = db.update_user_payment_status(user_id, True)
        
        if success:
            # Import keyboard here to avoid circular imports
            from keyboards import kb_client
            
            await bot.send_message(
                message.chat.id,
                f'✅ Ваш платёж успешно подтверждён!\n\n'
                f'🎉 Доступ открыт — добро пожаловать в наше сообщество!\n'
                f'Теперь вам доступны:\n'
                f'📌 Ежемесячные видеокурсы\n'
                f'Ссылка на видеоуроки \n'
                f'💡 Ежедневные задания, советы и фишки\n'
                f'Ссылка на главный канал\n'
                f'🎙 Живые эфиры каждую неделю\n'
                f'Ссылка на канал где будут записи с зум\n'
                f'🤝 Поддержка кураторов и участие в челленджах\n'
                f'Ссылка на техподдержку \n'
                f'👉 Не теряйте времени — начните обучение прямо сейчас!\n'
                f'Если появятся вопросы — пишите, мы всегда на связи.\n\n'
                f'🔥 Удачи и отличного старта!',
                reply_markup=kb_client
            )
            
            logging.info(f"Payment completed and database updated for user {user_id}")
        else:
            await bot.send_message(
                message.chat.id,
                "Платеж прошел успешно, но возникла ошибка при обновлении статуса. Обратитесь к администратору."
            )
            logging.error(f"Failed to update database for user {user_id}")
    except Exception as e:
        logging.error(f"Error processing successful payment: {e}")
        await bot.send_message(message.chat.id, "Ошибка при обработке платежа. Обратитесь к администратору.")


# Helper function to update user payment status


# Test command to check payment status
async def check_payment_status(message: types.Message):
    try:
        user_id = int(message.from_user.id)
        is_paid = db.record_payment(user_id)
        status = "✅ Оплачено" if is_paid else "❌ Не оплачено"
        await bot.send_message(
            message.chat.id,
            f"Статус оплаты для пользователя {user_id}: {status}"
        )
    except Exception as e:
        logging.error(f"Error checking payment status: {e}")
        await bot.send_message(message.chat.id, "Ошибка при проверке статуса оплаты.")



def handlers_register(dp: Dispatcher):
    print('✅ Регистрируем хендлеры оплаты')
    dp.register_message_handler(payment_handler, commands=['buy'])
    dp.register_message_handler(check_payment_status, commands=['check_payment'])
    dp.register_message_handler(
        successful_payment,
        content_types=ContentType.SUCCESSFUL_PAYMENT
    )