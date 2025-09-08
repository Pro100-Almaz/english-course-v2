import asyncio
import os
import traceback
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor
from aiohttp.web_fileresponse import content_type

from keyboards.client_kb import kb_start
from create_bot import dp
from pathlib import Path
from client import start_bot

PUBLIC_TERMINAL_ID = os.getenv("PUBLIC_TERMINAL_ID")
template_path = Path(__file__).parent.parent / 'templates' / 'pay.html'
PUBLIC_URL = os.getenv('PUBLIC_URL')


class FSMPaymentConfirm(StatesGroup):
    waitgin_for_check = State()

async def start_tiptop(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text='Оплатить',
                web_app=WebAppInfo(url=PUBLIC_URL)
            )
        ]]
    )
    await FSMPaymentConfirm.waitgin_for_check.set()
    await message.answer('Нажмите кнопку для оплаты:', reply_markup=keyboard)
    print("<UNK> <UNK> <UNK> <UNK> <UNK> <UNK> <UNK> <UNK> <UNK>")

@dp.message_handler(content_types=types.ContentType.PHOTO, state=FSMPaymentConfirm.waitgin_for_check)
async def process_payment(message: types.Message, state: FSMContext):
    print('process paymeny')
    await message.answer(text="Спасибо за оплату!\n"
                              "Ваша заявка успешно принята. Ссылка на закрытый Telegram-канал будет отправлена вам после того, как наш менеджер обработает ваши данные.\n"
                            "Пожалуйста, ожидайте — это может занять немного времени.\n"
                            "Если у вас возникнут вопросы, напишите нам — мы всегда на связи!\n"
                            "Спасибо, что учите английский вместе с нами! 💙✨", reply_markup=kb_start)
    await state.finish()

@dp.message_handler(content_type != types.ContentType.PHOTO, state=FSMPaymentConfirm.waitgin_for_check)
async def confirmation_request(message: types.Message, state: FSMContext):
    if message.content_type == types.ContentType.TEXT:
        if message.text.strip() == '/start':
            await state.finish()
            await start_bot(message)
    await message.answer(text="Прошу отправьте фото чека для подтверждения оплаты или напишите команду '/start'\n")

# aiohttp handler for the payment page
def create_app():
    app = web.Application()
    print("create_app is triggered")

    async def pay(request):
        try:
            # 1) Resolve & verify the template path
            tpl = template_path.resolve()
            print(f"🔍 Loading template from {tpl}")
            if not tpl.exists():
                raise FileNotFoundError(f"Template not found at {tpl}")

            # 2) Read & inject
            html = tpl.read_text(encoding="utf-8")
            html = html.replace("{{PUBLIC_TERMINAL_ID}}", PUBLIC_TERMINAL_ID or "")

            return web.Response(text=html, content_type="text/html")

        except Exception:
            # This will show the real error in your console
            traceback.print_exc()
            return web.Response(
                text="<h1>Internal Server Error</h1>",
                content_type="text/html",
                status=500
            )
    app.router.add_get('/pay', pay)
    return app