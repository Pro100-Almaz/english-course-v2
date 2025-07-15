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

# Get provider token from environment variable
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")  # from BotFather
CURRENCY       = "KZT"                        # or "USD", "EUR", etc.

# For testing, you can set a test token
if not PROVIDER_TOKEN:
    PROVIDER_TOKEN = "1234567890:TEST_TOKEN"  # Replace with your actual test token
    logging.warning("Using test provider token. Set PROVIDER_TOKEN environment variable for production.")

PRICE = types.LabeledPrice(label="Подписка на 1 месяц", amount=1000*100)  # в копейках (руб)

class PaymentState(StatesGroup):
    awaiting_payment = State()


# 1) /buy command: send the invoice
async def payment_handler(message: types.Message):
    await successful_payment(message)
    # if not PROVIDER_TOKEN:
    #     await bot.send_message(message.chat.id, "Ошибка: токен платежной системы не настроен. Обратитесь к администратору.")
    #     return
    #
    # try:
    #     if PROVIDER_TOKEN.split(':')[1] == 'TEST':
    #         await bot.send_message(message.chat.id, "🧪 Тестовый платеж! Используйте тестовые данные карты.")
    #
    #     await bot.send_invoice(
    #         message.chat.id,
    #         title="Подписка на бота",
    #         description="Активация подписки на бота на 1 месяц",
    #         provider_token=PROVIDER_TOKEN,
    #         currency=CURRENCY,
    #         photo_url="https://www.aroged.com/wp-content/uploads/2022/06/Telegram-has-a-premium-subscription.jpg",
    #         photo_width=416,
    #         photo_height=234,
    #         photo_size=416,
    #         is_flexible=False,
    #         prices=[PRICE],
    #         start_parameter="one-month-subscription",
    #         payload="test-invoice-payload"
    #     )
    # except Exception as e:
    #     logging.error(f"Error sending invoice: {e}")
    #     await bot.send_message(message.chat.id, "Ошибка при создании платежа. Попробуйте позже.")
    #

# pre checkout (must be answered in 10 seconds)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    try:
        await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)
        logging.info(f"Pre-checkout approved for user {pre_checkout_q.from_user.id}")
    except Exception as e:
        logging.error(f"Error in pre-checkout: {e}")
        await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=False, error_message="Ошибка при обработке платежа")


# successful payment
async def successful_payment(message: types.Message):
    try:
        user_id = int(message.from_user.id)
        # logging.info(f"SUCCESSFUL PAYMENT for user {user_id}")
        
        payment_info = message.successful_payment
        # logging.info(f"Payment details: {payment_info}")
        
        success = db.update_user_payment_status(user_id)
        
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


# refunded payment
async def refund_payment(message: types.Message):
    try:
        logging.info("REFUND PAYMENT:")
        payment_info = message.refund_payment.dict()
        for k, v in payment_info.items():
            logging.info(f"{k} = {v}")

        await bot.send_message(
            message.chat.id,
            f"❌ Платеж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} возвращен!"
        )
    except Exception as e:
        logging.error(f"Error processing refund: {e}")


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
    dp.register_pre_checkout_query_handler(pre_checkout_query, lambda query: True)
    dp.register_message_handler(
        successful_payment,
        content_types=ContentType.SUCCESSFUL_PAYMENT
    )

    dp.register_message_handler(
        refund_payment,
        lambda msg: hasattr(msg, 'refund_payment'),
        content_types=ContentType.SUCCESSFUL_PAYMENT

    )